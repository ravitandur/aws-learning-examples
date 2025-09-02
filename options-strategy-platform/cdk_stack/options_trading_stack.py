from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as targets,
    aws_logs as logs,
    aws_apigatewayv2 as apigatewayv2,
    aws_apigatewayv2_integrations as integrations,
    aws_cloudwatch as cloudwatch,
    aws_cognito as cognito,
    Duration,
    RemovalPolicy,
    CfnOutput,
    Fn
)
from constructs import Construct


class OptionsTradeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, deploy_env: str, config: dict, auth_stack_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.deploy_env = deploy_env
        self.config = config
        self.company_prefix = config['company']['short_name']
        self.project_name = config['project']
        self.env_config = config['environments'][deploy_env]
        self.options_config = config['projects']['options_trading']['config']
        self.auth_stack_name = auth_stack_name
        
        # Import auth stack outputs for cross-stack integration
        self.user_pool_id = Fn.import_value(f"{auth_stack_name}-UserPoolId")
        self.broker_accounts_table_name = Fn.import_value(f"{auth_stack_name}-BrokerAccountsTable")
        
        # Create all DynamoDB tables
        self._create_dynamodb_tables()
        
        # Create Lambda functions
        self._create_lambda_functions()
        
        # Create API Gateway
        self._create_api_gateway()
        
        # Create WebSocket API for real-time updates
        self._create_websocket_api()
        
        # Create EventBridge rules for scheduling
        self._create_event_rules()
        
        # Create CloudWatch dashboard
        self._create_cloudwatch_dashboard()
        
        # Create stack outputs
        self._create_outputs()
    
    def get_resource_name(self, resource_type: str) -> str:
        """Generate environment-specific resource names with company prefix"""
        return f"{self.company_prefix}-{self.project_name}-{self.deploy_env}-{resource_type}"
        
    def get_removal_policy(self) -> RemovalPolicy:
        """Get environment-specific removal policy"""
        policy = self.env_config['removal_policy']
        return RemovalPolicy.DESTROY if policy == "DESTROY" else RemovalPolicy.RETAIN
    
    def _create_dynamodb_tables(self):
        """Create all DynamoDB tables for options trading platform"""
        
        # Removal policy based on environment
        removal_policy = RemovalPolicy.DESTROY if self.env_config['removal_policy'] == 'DESTROY' else RemovalPolicy.RETAIN
        
        # 1. Options Baskets Table - Unified storage for user and admin baskets
        self.baskets_table = dynamodb.Table(
            self, f"OptionsBaskets{self.deploy_env.title()}",
            table_name=self.get_resource_name("options-baskets"),
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="basket_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=removal_policy,
            point_in_time_recovery=self.env_config.get('enable_point_in_time_recovery', False),
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        )
        
        # Add GSIs for marketplace and performance queries
        self.baskets_table.add_global_secondary_index(
            index_name="MarketplaceBaskets",
            partition_key=dynamodb.Attribute(name="visibility", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="created_at", type=dynamodb.AttributeType.STRING),
        )
        
        self.baskets_table.add_global_secondary_index(
            index_name="BasketsByCreatorType",
            partition_key=dynamodb.Attribute(name="created_by_type", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="total_return", type=dynamodb.AttributeType.NUMBER),
        )
        
        # 2. Options Strategies Table
        self.strategies_table = dynamodb.Table(
            self, f"OptionsStrategies{self.deploy_env.title()}",
            table_name=self.get_resource_name("options-strategies"),
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="strategy_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=removal_policy,
            point_in_time_recovery=self.env_config.get('enable_point_in_time_recovery', False),
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        )
        
        # Add GSIs for strategy queries
        self.strategies_table.add_global_secondary_index(
            index_name="StrategiesByBasket",
            partition_key=dynamodb.Attribute(name="basket_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="created_at", type=dynamodb.AttributeType.STRING),
        )
        
        self.strategies_table.add_global_secondary_index(
            index_name="ActiveStrategiesForExecution",
            partition_key=dynamodb.Attribute(name="status", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="next_execution", type=dynamodb.AttributeType.STRING),
        )
        
        # 3. Strategy Broker Allocations Table (KEY INNOVATION)
        self.strategy_broker_allocations_table = dynamodb.Table(
            self, f"StrategyBrokerAllocations{self.deploy_env.title()}",
            table_name=self.get_resource_name("strategy-broker-allocations"),
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="allocation_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=removal_policy,
            point_in_time_recovery=self.env_config.get('enable_point_in_time_recovery', False),
        )
        
        # GSI for strategy-specific broker queries
        self.strategy_broker_allocations_table.add_global_secondary_index(
            index_name="AllocationsByStrategy",
            partition_key=dynamodb.Attribute(name="strategy_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="priority", type=dynamodb.AttributeType.NUMBER),
        )
        
        # 4. Basket Subscriptions Table (Marketplace functionality)
        self.basket_subscriptions_table = dynamodb.Table(
            self, f"BasketSubscriptions{self.deploy_env.title()}",
            table_name=self.get_resource_name("basket-subscriptions"),
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="subscription_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=removal_policy,
            point_in_time_recovery=self.env_config.get('enable_point_in_time_recovery', False),
        )
        
        # 5. Strategy Executions Table
        self.strategy_executions_table = dynamodb.Table(
            self, f"StrategyExecutions{self.deploy_env.title()}",
            table_name=self.get_resource_name("strategy-executions"),
            partition_key=dynamodb.Attribute(name="strategy_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="execution_timestamp", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=removal_policy,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        )
        
        # 6. Order History Table
        self.order_history_table = dynamodb.Table(
            self, f"OrderHistory{self.deploy_env.title()}",
            table_name=self.get_resource_name("order-history"),
            partition_key=dynamodb.Attribute(name="execution_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="order_timestamp", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=removal_policy,
        )
        
        # 7. Position Tracking Table
        self.position_tracker_table = dynamodb.Table(
            self, f"PositionTracker{self.deploy_env.title()}",
            table_name=self.get_resource_name("position-tracker"),
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="position_key", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=removal_policy,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        )
        
        # 8. Performance Metrics Table
        self.performance_metrics_table = dynamodb.Table(
            self, f"PerformanceMetrics{self.deploy_env.title()}",
            table_name=self.get_resource_name("performance-metrics"),
            partition_key=dynamodb.Attribute(name="entity_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="date", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=removal_policy,
        )
        
        # 9. Market Data Cache Table (with TTL)
        self.market_data_cache_table = dynamodb.Table(
            self, f"MarketDataCache{self.deploy_env.title()}",
            table_name=self.get_resource_name("market-data-cache"),
            partition_key=dynamodb.Attribute(name="underlying_symbol", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="data_timestamp", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=removal_policy,
            time_to_live_attribute="ttl",  # Auto-expire old data
        )
    
    def _create_lambda_functions(self):
        """Create all Lambda functions for options trading"""
        
        # Common Lambda configuration following user_auth_broker_stack pattern
        lambda_env = {
            "ENVIRONMENT": self.deploy_env,
            "COMPANY_PREFIX": self.company_prefix,
            "PROJECT_NAME": self.project_name,
            "USER_POOL_ID": self.user_pool_id,
            "BROKER_ACCOUNTS_TABLE": self.broker_accounts_table_name,
            "REGION": self.region,
            # Options-specific environment variables
            "BASKETS_TABLE": self.baskets_table.table_name,
            "STRATEGIES_TABLE": self.strategies_table.table_name,
            "STRATEGY_BROKER_ALLOCATIONS_TABLE": self.strategy_broker_allocations_table.table_name,
            "BASKET_SUBSCRIPTIONS_TABLE": self.basket_subscriptions_table.table_name,
            "STRATEGY_EXECUTIONS_TABLE": self.strategy_executions_table.table_name,
            "ORDER_HISTORY_TABLE": self.order_history_table.table_name,
            "POSITION_TRACKER_TABLE": self.position_tracker_table.table_name,
            "PERFORMANCE_METRICS_TABLE": self.performance_metrics_table.table_name,
            "MARKET_DATA_CACHE_TABLE": self.market_data_cache_table.table_name,
        }
        
        # Create Lambda functions (placeholder implementations for now)
        self.lambda_functions = {}
        
        lambda_configs = [
            # Strategy Management
            ('basket-manager', 'Strategy management/basket_manager.py'),
            ('strategy-manager', 'Strategy management/strategy_manager.py'),
            ('strategy-broker-allocator', 'Strategy management/strategy_broker_allocator.py'),
            ('subscription-manager', 'Strategy management/subscription_manager.py'),
            
            # Execution Engine
            ('strategy-executor', 'Execution engine/strategy_executor.py'),
            ('order-manager', 'Execution engine/order_manager.py'),
            ('position-manager', 'Execution engine/position_manager.py'),
            ('risk-validator', 'Execution engine/risk_validator.py'),
            
            # Market Data
            ('market-data-fetcher', 'Market data/market_data_fetcher.py'),
            ('option-chain-manager', 'Market data/option_chain_manager.py'),
            ('volatility-calculator', 'Market data/volatility_calculator.py'),
            
            # Analytics
            ('performance-calculator', 'Analytics/performance_calculator.py'),
            ('greeks-calculator', 'Analytics/greeks_calculator.py'),
            ('strategy-analyzer', 'Analytics/strategy_analyzer.py'),
            
            # Real-time
            ('websocket-handler', 'Real-time/websocket_handler.py'),
            ('live-updates-processor', 'Real-time/live_updates_processor.py'),
        ]
        
        # Create Lambda functions with logRetention (avoids redeploy LogGroup errors)
        for function_name, description in lambda_configs:
            self.lambda_functions[function_name] = _lambda.Function(
                self, f"OptionsLambda{function_name.title().replace('-', '')}{self.deploy_env.title()}",
                function_name=self.get_resource_name(f"options-{function_name}"),
                runtime=_lambda.Runtime.PYTHON_3_11,
                code=_lambda.Code.from_asset("lambda_functions"),
                handler=f"option_baskets.{function_name.replace('-', '_')}.lambda_handler",
                environment=lambda_env,
                timeout=Duration.seconds(30),
                memory_size=512,
                log_retention=logs.RetentionDays.ONE_WEEK if self.env_config['log_retention_days'] == 7 
                             else logs.RetentionDays.ONE_MONTH if self.env_config['log_retention_days'] == 30 
                             else logs.RetentionDays.THREE_MONTHS,  # Use logRetention to avoid redeploy errors
                description=description,
            )
        
        # Grant DynamoDB permissions to all Lambda functions
        tables = [
            self.baskets_table,
            self.strategies_table, 
            self.strategy_broker_allocations_table,
            self.basket_subscriptions_table,
            self.strategy_executions_table,
            self.order_history_table,
            self.position_tracker_table,
            self.performance_metrics_table,
            self.market_data_cache_table,
        ]
        
        for function in self.lambda_functions.values():
            for table in tables:
                table.grant_read_write_data(function)
            
            # Grant access to Secrets Manager for broker credentials
            function.add_to_role_policy(
                iam.PolicyStatement(
                    actions=[
                        "secretsmanager:GetSecretValue",
                        "secretsmanager:DescribeSecret",
                    ],
                    resources=[f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:{self.company_prefix}-*"]
                )
            )
    
    def _create_api_gateway(self):
        """Create API Gateway with options trading endpoints"""
        
        # Create API Gateway
        self.api = apigateway.RestApi(
            self, f"OptionsApiGateway{self.deploy_env.title()}",
            rest_api_name=self.get_resource_name("options-api"),
            description=f"Options Trading API - {self.deploy_env} environment",
            deploy_options=apigateway.StageOptions(
                stage_name=self.deploy_env,
                logging_level=apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
            ),
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=self.env_config['cors_origins'],
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=['Content-Type', 'Authorization'],
            ),
        )
        
        # Create Cognito authorizer using imported User Pool
        # Reference the imported User Pool
        user_pool = cognito.UserPool.from_user_pool_id(
            self, f"ImportedUserPool{self.deploy_env.title()}",
            user_pool_id=self.user_pool_id
        )
        
        authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self, f"OptionsApiAuthorizer{self.deploy_env.title()}",
            cognito_user_pools=[user_pool],
            authorizer_name=self.get_resource_name("options-authorizer"),
        )
        
        # Create options resource group
        options_resource = self.api.root.add_resource("options")
        
        # Basket endpoints (secured with Cognito authorizer)
        baskets_resource = options_resource.add_resource("baskets")
        baskets_resource.add_method("GET", 
            apigateway.LambdaIntegration(self.lambda_functions['basket-manager']),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=authorizer
        )
        baskets_resource.add_method("POST", 
            apigateway.LambdaIntegration(self.lambda_functions['basket-manager']),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=authorizer
        )
        
        # Strategy endpoints (secured with Cognito authorizer)
        strategies_resource = options_resource.add_resource("strategies")
        strategies_resource.add_method("GET", 
            apigateway.LambdaIntegration(self.lambda_functions['strategy-manager']),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=authorizer
        )
        strategies_resource.add_method("POST", 
            apigateway.LambdaIntegration(self.lambda_functions['strategy-manager']),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=authorizer
        )
        
        # Execution endpoints (secured with Cognito authorizer)
        execution_resource = options_resource.add_resource("execution")
        execution_resource.add_method("POST", 
            apigateway.LambdaIntegration(self.lambda_functions['strategy-executor']),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=authorizer
        )
        
        # Market data endpoints (secured with Cognito authorizer)
        market_data_resource = options_resource.add_resource("market-data")
        market_data_resource.add_method("GET", 
            apigateway.LambdaIntegration(self.lambda_functions['market-data-fetcher']),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=authorizer
        )
    
    def _create_websocket_api(self):
        """Create WebSocket API for real-time updates"""
        
        if not self.options_config.get('enable_realtime_websocket', True):
            return
        
        # Create WebSocket API
        self.websocket_api = apigatewayv2.WebSocketApi(
            self, f"OptionsWebSocketApi{self.deploy_env.title()}",
            api_name=self.get_resource_name("options-websocket"),
            description=f"Options Trading WebSocket API - {self.deploy_env} environment",
        )
        
        # Add WebSocket stage
        self.websocket_stage = apigatewayv2.WebSocketStage(
            self, f"OptionsWebSocketStage{self.deploy_env.title()}",
            web_socket_api=self.websocket_api,
            stage_name=self.deploy_env,
            auto_deploy=True,
        )
    
    def _create_event_rules(self):
        """Create EventBridge rules for strategy scheduling"""
        
        # Create EventBridge rule for daily execution checks
        daily_execution_rule = events.Rule(
            self, f"OptionsDailyExecution{self.deploy_env.title()}",
            rule_name=self.get_resource_name("options-daily-execution"),
            description="Daily check for strategy executions",
            schedule=events.Schedule.cron(minute="0", hour="9", month="*", year="*"),  # 9 AM daily
        )
        
        # Add target to the rule
        daily_execution_rule.add_target(
            targets.LambdaFunction(
                self.lambda_functions['strategy-executor']
            )
        )
    
    def _create_cloudwatch_dashboard(self):
        """Create CloudWatch dashboard for monitoring"""
        
        dashboard_name = self.get_resource_name("options-dashboard")
        
        self.dashboard = cloudwatch.Dashboard(
            self, f"OptionsDashboard{self.deploy_env.title()}",
            dashboard_name=dashboard_name,
        )
        
        # Add widgets for Lambda functions, DynamoDB tables, API Gateway, etc.
        # This would be expanded with specific metrics widgets
    
    def _create_outputs(self):
        """Create CloudFormation outputs"""
        
        CfnOutput(
            self, "OptionsApiGatewayUrl",
            value=self.api.url,
            description="Options Trading API Gateway URL",
            export_name=f"{self.stack_name}-OptionsApiUrl"
        )
        
        CfnOutput(
            self, "OptionsBasketsTableName", 
            value=self.baskets_table.table_name,
            description="Options Baskets DynamoDB Table Name",
            export_name=f"{self.stack_name}-OptionsBasketsTable"
        )
        
        CfnOutput(
            self, "OptionsStrategiesTableName",
            value=self.strategies_table.table_name, 
            description="Options Strategies DynamoDB Table Name",
            export_name=f"{self.stack_name}-OptionsStrategiesTable"
        )
        
        if hasattr(self, 'websocket_api'):
            CfnOutput(
                self, "OptionsWebSocketUrl",
                value=self.websocket_stage.url,
                description="Options Trading WebSocket URL",
                export_name=f"{self.stack_name}-OptionsWebSocketUrl"
            )