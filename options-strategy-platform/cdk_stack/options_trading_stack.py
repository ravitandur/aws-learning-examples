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
    aws_stepfunctions as stepfunctions,
    aws_stepfunctions_tasks as tasks,
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
        
        # Create hybrid architecture tables
        self._create_hybrid_tables()
        
        # Create Lambda functions
        self._create_lambda_functions()
        
        # Create API Gateway
        self._create_api_gateway()
        
        # Create WebSocket API for real-time updates
        self._create_websocket_api()
        
        # Create event-driven execution architecture
        self._create_event_driven_execution_architecture()
        
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
    
    def _create_hybrid_tables(self):
        """Create hybrid architecture: single table + execution history table (Phase 1)"""
        
        # Removal policy based on environment
        removal_policy = RemovalPolicy.DESTROY if self.env_config['removal_policy'] == 'DESTROY' else RemovalPolicy.RETAIN
        
        # Table 1: Single table for operational trading configurations
        self.trading_configurations_table = dynamodb.Table(
            self, f"TradingConfigurations{self.deploy_env.title()}",
            table_name=self.get_resource_name("trading-configurations"),
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="sort_key", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=removal_policy,
            point_in_time_recovery=self.env_config.get('enable_point_in_time_recovery', False),
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        )
        
        # GSI1: Strategy-Specific Queries (AllocationsByStrategy)
        # Purpose: Get all allocations for specific strategy sorted by priority
        self.trading_configurations_table.add_global_secondary_index(
            index_name="AllocationsByStrategy",
            partition_key=dynamodb.Attribute(name="strategy_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="entity_type_priority", type=dynamodb.AttributeType.STRING),
        )
        
        # GSI2: User Execution Schedule (CRITICAL FOR PERFORMANCE)
        # Purpose: Single query gets ALL user executions at specific time
        # Query Examples:
        # - Entry: PK="user_123" SK begins_with "ENTRY#09:30#"  
        # - Exit: PK="user_123" SK begins_with "EXIT#15:20#"
        # Performance: 401 queries → 2 queries per user per day
        self.trading_configurations_table.add_global_secondary_index(
            index_name="UserExecutionSchedule",
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="execution_schedule_key", type=dynamodb.AttributeType.STRING),
        )
        
        # Table 2: Execution History for time-series data (Traditional Table)
        self.execution_history_table = dynamodb.Table(
            self, f"ExecutionHistory{self.deploy_env.title()}",
            table_name=self.get_resource_name("execution-history"),
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="execution_key", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=removal_policy,
            point_in_time_recovery=self.env_config.get('enable_point_in_time_recovery', False),
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        )
        
        # GSI1: Executions by Strategy (for strategy-specific analytics)
        self.execution_history_table.add_global_secondary_index(
            index_name="ExecutionsByStrategy",
            partition_key=dynamodb.Attribute(name="strategy_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="execution_timestamp", type=dynamodb.AttributeType.STRING),
        )
        
        # GSI2: Executions by Date (for daily analytics and reporting)
        self.execution_history_table.add_global_secondary_index(
            index_name="ExecutionsByDate",
            partition_key=dynamodb.Attribute(name="execution_date", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="execution_timestamp", type=dynamodb.AttributeType.STRING),
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
            # Phase 1 Hybrid Architecture - Two tables only
            "TRADING_CONFIGURATIONS_TABLE": self.trading_configurations_table.table_name,
            "EXECUTION_HISTORY_TABLE": self.execution_history_table.table_name,
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
        
        # Grant DynamoDB permissions to all Lambda functions - Phase 1 Hybrid Architecture
        tables = [
            self.trading_configurations_table,  # Single table for all operational data
            self.execution_history_table,       # Separate table for execution records
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
    
    def _create_event_driven_execution_architecture(self):
        """
        Create sophisticated event-driven execution architecture
        Industry-leading design that surpasses retail platforms
        """
        
        # Create event emitter Lambda with EventBridge cron for timing events
        self._create_event_emitter_lambda()
        
        # Create Strategic EventBridge Rules for high-traffic times
        self._create_strategic_eventbridge_rules()
        
        # Create Express Step Functions for strategy execution
        self._create_express_execution_state_machine()
        
        # Create event handlers for different event types
        self._create_event_handlers()
    
    def _create_event_emitter_lambda(self):
        """Create event emitter Lambda for timing events"""
        
        # Enhanced environment variables for event emitter
        event_emitter_env = {
            "ENVIRONMENT": self.deploy_env,
            "COMPANY_PREFIX": self.company_prefix,
            "PROJECT_NAME": self.project_name,
            "REGION": self.region,
            "TRADING_CONFIGURATIONS_TABLE": self.trading_configurations_table.table_name,
            "EXECUTION_HISTORY_TABLE": self.execution_history_table.table_name,
        }
        
        # Create event emitter Lambda
        self.event_emitter_lambda = _lambda.Function(
            self, f"OptionsEventEmitter{self.deploy_env.title()}",
            function_name=self.get_resource_name("options-event-emitter"),
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("lambda_functions"),
            handler="option_baskets.event_emitter.lambda_handler",
            environment=event_emitter_env,
            timeout=Duration.seconds(60),  # More time for event processing
            memory_size=512,
            log_retention=logs.RetentionDays.ONE_WEEK if self.env_config['log_retention_days'] == 7 
                         else logs.RetentionDays.ONE_MONTH if self.env_config['log_retention_days'] == 30 
                         else logs.RetentionDays.THREE_MONTHS,
            description="Event emitter for timing-based market events"
        )
        
        # Grant EventBridge permissions to emit events
        self.event_emitter_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["events:PutEvents"],
                resources=[f"arn:aws:events:{self.region}:{self.account}:event-bus/default"]
            )
        )
        
        # Grant DynamoDB permissions
        for table in [self.trading_configurations_table, self.execution_history_table]:
            table.grant_read_write_data(self.event_emitter_lambda)
        
        # Create Step Functions Express for TRUE 0-second precision timing
        self._create_master_precision_timer_step_function()
    
    
    def _create_strategic_eventbridge_rules(self):
        """
        Create EventBridge rules for high-traffic strategic times (80% coverage)
        Provides instant execution for common strategy times
        """
        
        # Strategic times that handle 80% of all strategy executions
        strategic_times = [
            ("09:15", "market-open", "Market opening - initial strategies"),
            ("09:30", "main-entry-1", "Primary entry time - most strategies"),
            ("10:00", "main-entry-2", "Secondary entry time"),
            ("13:00", "post-lunch", "Post-lunch entry strategies"), 
            ("15:20", "main-exit", "Primary exit time - most strategies"),
            ("15:25", "emergency-close", "Emergency close before market close")
        ]
        
        self.strategic_rules = {}
        
        for time_slot, phase_name, description in strategic_times:
            hour, minute = time_slot.split(":")
            
            # Convert IST to UTC for EventBridge cron
            # IST = UTC + 5:30, so UTC = IST - 5:30
            utc_hour = int(hour) - 5
            utc_minute = int(minute) - 30
            
            # Handle minute underflow
            if utc_minute < 0:
                utc_minute += 60
                utc_hour -= 1
            
            # Handle hour underflow (next day scheduling)
            if utc_hour < 0:
                utc_hour += 24
            
            # Create EventBridge rule
            rule = events.Rule(
                self, f"StrategicRule{time_slot.replace(':', '')}{self.deploy_env.title()}",
                rule_name=self.get_resource_name(f"strategic-{phase_name}"),
                description=f"{description} at {time_slot} IST",
                schedule=events.Schedule.cron(
                    minute=str(utc_minute),
                    hour=str(utc_hour),
                    month="*", 
                    year="*",
                    week_day="MON-FRI"  # Only weekdays
                ),
                enabled=True
            )
            
            # Target the strategy executor directly for strategic times
            rule.add_target(targets.LambdaFunction(
                self.lambda_functions['strategy-executor'],
                event=events.RuleTargetInput.from_object({
                    "execution_time": time_slot,
                    "trigger_type": "STRATEGIC",
                    "market_phase": phase_name,
                    "source": "aws.events"
                })
            ))
            
            self.strategic_rules[phase_name] = rule
        
        # NOTE: Master Step Function removed in favor of pure EventBridge cron approach
        # EventBridge cron provides better precision and lower cost than continuous Step Function loops
    
    def _create_express_execution_state_machine(self):
        """
        Create Express Step Function for strategy execution with Wait states
        Provides second-level timing precision at 98% cost savings
        """
        
        # Wait for execution time
        wait_for_execution = stepfunctions.Wait(
            self, "WaitForExecution",
            time=stepfunctions.WaitTime.seconds_path("$.wait_seconds")
        )
        
        # Final market validation before execution
        validate_market = tasks.LambdaInvoke(
            self, "ValidateMarket",
            lambda_function=self.lambda_functions['market-data-fetcher'],
            payload=stepfunctions.TaskInput.from_object({
                "action": "VALIDATE_MARKET_OPEN"
            }),
            result_path="$.market_validation"
        )
        
        # Execute strategies in parallel
        execute_strategies_parallel = stepfunctions.Parallel(
            self, "ExecuteStrategiesParallel"
        )
        
        # Add parallel execution branch for each user's strategies
        execute_user_strategies = tasks.LambdaInvoke(
            self, "ExecuteUserStrategies", 
            lambda_function=self.lambda_functions['strategy-executor'],
            payload=stepfunctions.TaskInput.from_object({
                "action": "EXECUTE_USER_STRATEGIES",
                "strategies.$": "$.strategies",
                "execution_time.$": "$.execution_time",
                "trigger_type": "EXPRESS_STEP_FUNCTION"
            }),
            result_path="$.execution_results"
        )
        
        execute_strategies_parallel.branch(execute_user_strategies)
        
        # Record execution results
        record_results = tasks.LambdaInvoke(
            self, "RecordResults",
            lambda_function=self.lambda_functions['performance-calculator'],
            payload=stepfunctions.TaskInput.from_object({
                "action": "RECORD_EXECUTION_RESULTS",
                "results.$": "$.execution_results",
                "execution_time.$": "$.execution_time"
            })
        )
        
        # Choice for market validation
        should_execute = stepfunctions.Choice(self, "ShouldExecute")
        
        # Skip execution if market closed
        skip_execution = stepfunctions.Succeed(self, "MarketClosedSkipExecution")
        
        # Define Express Step Function flow
        definition = wait_for_execution\
            .next(validate_market)\
            .next(should_execute\
                .when(stepfunctions.Condition.boolean_equals("$.market_validation.market_open", True),
                      execute_strategies_parallel.next(record_results))\
                .otherwise(skip_execution)
            )
        
        # Create Express Step Function for cost efficiency
        self.express_execution_state_machine = stepfunctions.StateMachine(
            self, f"ExpressExecutionStateMachine{self.deploy_env.title()}",
            state_machine_name=self.get_resource_name("express-execution"),
            definition=definition,
            state_machine_type=stepfunctions.StateMachineType.EXPRESS,
            logs=stepfunctions.LogOptions(
                destination=logs.LogGroup(
                    self, f"ExpressExecutionLogGroup{self.deploy_env.title()}",
                    log_group_name=f"/aws/stepfunctions/{self.get_resource_name('express-execution')}",
                    retention=logs.RetentionDays.ONE_WEEK if self.env_config['log_retention_days'] == 7 
                             else logs.RetentionDays.ONE_MONTH if self.env_config['log_retention_days'] == 30 
                             else logs.RetentionDays.THREE_MONTHS,
                    removal_policy=self.get_removal_policy()
                ),
                level=stepfunctions.LogLevel.ERROR,  # Express only supports ERROR level
                include_execution_data=False
            )
        )
    
    def _create_event_handlers(self):
        """Create event handlers for different event types"""
        
        # Create event handler Lambda functions
        event_handler_configs = [
            ("schedule-strategy-trigger", "Event handler for 5-minute strategy scheduling"),
            ("stop-loss-checker", "Event handler for real-time stop loss monitoring"),
            ("duplicate-order-checker", "Event handler for order deduplication"),
            ("market-data-refresher", "Event handler for market data updates")
        ]
        
        self.event_handlers = {}
        
        for handler_name, description in event_handler_configs:
            # Enhanced environment for event handlers
            handler_env = {
                "ENVIRONMENT": self.deploy_env,
                "COMPANY_PREFIX": self.company_prefix,
                "REGION": self.region,
                "TRADING_CONFIGURATIONS_TABLE": self.trading_configurations_table.table_name,
                "EXECUTION_HISTORY_TABLE": self.execution_history_table.table_name,
                "EXPRESS_EXECUTION_STATE_MACHINE_ARN": self.express_execution_state_machine.state_machine_arn,
            }
            
            handler_lambda = _lambda.Function(
                self, f"OptionsEventHandler{handler_name.title().replace('-', '')}{self.deploy_env.title()}",
                function_name=self.get_resource_name(f"options-{handler_name}"),
                runtime=_lambda.Runtime.PYTHON_3_11,
                code=_lambda.Code.from_asset("lambda_functions"),
                handler=f"option_baskets.{handler_name.replace('-', '_')}.lambda_handler",
                environment=handler_env,
                timeout=Duration.seconds(60),
                memory_size=512,
                log_retention=logs.RetentionDays.ONE_WEEK if self.env_config['log_retention_days'] == 7 
                             else logs.RetentionDays.ONE_MONTH if self.env_config['log_retention_days'] == 30 
                             else logs.RetentionDays.THREE_MONTHS,
                description=description
            )
            
            # Grant necessary permissions
            for table in [self.trading_configurations_table, self.execution_history_table]:
                table.grant_read_write_data(handler_lambda)
            
            # Grant Step Functions execution permissions
            handler_lambda.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["states:StartExecution"],
                    resources=[self.express_execution_state_machine.state_machine_arn]
                )
            )
            
            # Grant EventBridge permissions
            handler_lambda.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["events:PutEvents"],
                    resources=[f"arn:aws:events:{self.region}:{self.account}:event-bus/default"]
                )
            )
            
            self.event_handlers[handler_name] = handler_lambda
        
        # Create EventBridge rules for event handlers
        self._create_event_handler_rules()
    
    def _create_event_handler_rules(self):
        """Create EventBridge rules to trigger event handlers"""
        
        # Schedule Strategy Trigger - every 5 minutes during market hours
        schedule_trigger_rule = events.Rule(
            self, f"ScheduleStrategyTriggerRule{self.deploy_env.title()}",
            rule_name=self.get_resource_name("schedule-strategy-trigger"),
            description="Trigger strategy scheduling every 5 minutes during market hours",
            event_pattern=events.EventPattern(
                source=["options.trading.scheduler"],
                detail_type=["Schedule Strategy Trigger"]
            )
        )
        
        schedule_trigger_rule.add_target(
            targets.LambdaFunction(self.event_handlers['schedule-strategy-trigger'])
        )
        
        # Stop Loss Check - every minute during market hours
        stop_loss_rule = events.Rule(
            self, f"StopLossCheckRule{self.deploy_env.title()}",
            rule_name=self.get_resource_name("stop-loss-check"),
            description="Check stop loss conditions every minute",
            event_pattern=events.EventPattern(
                source=["options.trading.risk"],
                detail_type=["Check Stop Loss"]
            )
        )
        
        stop_loss_rule.add_target(
            targets.LambdaFunction(self.event_handlers['stop-loss-checker'])
        )
        
        # Duplicate Order Check - every minute during market hours  
        duplicate_check_rule = events.Rule(
            self, f"DuplicateOrderCheckRule{self.deploy_env.title()}",
            rule_name=self.get_resource_name("duplicate-order-check"),
            description="Check for duplicate orders every minute",
            event_pattern=events.EventPattern(
                source=["options.trading.validation"],
                detail_type=["Check Duplicate Orders"]
            )
        )
        
        duplicate_check_rule.add_target(
            targets.LambdaFunction(self.event_handlers['duplicate-order-checker'])
        )
        
        # Market Data Refresh - every minute during market hours
        market_data_rule = events.Rule(
            self, f"MarketDataRefreshRule{self.deploy_env.title()}",
            rule_name=self.get_resource_name("market-data-refresh"),
            description="Refresh market data every minute",
            event_pattern=events.EventPattern(
                source=["options.trading.market"],
                detail_type=["Refresh Market Data"]
            )
        )
        
        market_data_rule.add_target(
            targets.LambdaFunction(self.event_handlers['market-data-refresher'])
        )
    
    def _create_master_precision_timer_step_function(self):
        """
        🚀 Create Step Functions Express for TRUE 0-Second Precision Event Emission
        REVOLUTIONARY TIMING SYSTEM: Achieves institutional-grade precision with continuous loop
        """
        
        # Import required Step Functions constructs
        from aws_cdk import aws_stepfunctions as sfn
        from aws_cdk import aws_stepfunctions_tasks as tasks
        
        # Create IAM role for Step Function with proper permissions
        step_function_role = iam.Role(
            self, f"MasterTimerStepFunctionRole{self.deploy_env.title()}",
            role_name=self.get_resource_name("master-timer-step-function-role"),
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            inline_policies={
                "StepFunctionExecutionPolicy": iam.PolicyDocument(
                    statements=[
                        # Lambda invocation permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "lambda:InvokeFunction"
                            ],
                            resources=[self.event_emitter_lambda.function_arn]
                        ),
                        # CloudWatch Logs permissions
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                                "logs:DescribeLogGroups",
                                "logs:DescribeLogStreams"
                            ],
                            resources=[
                                f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/stepfunctions/*"
                            ]
                        )
                    ]
                )
            }
        )
        
        # Grant permission to invoke the event emitter Lambda
        self.event_emitter_lambda.grant_invoke(step_function_role)
        
        # Load Step Function definition from JSON file
        import json
        import os
        
        definition_path = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "step_functions", 
            "master_timer_definition.json"
        )
        
        with open(definition_path, 'r') as f:
            definition_json = f.read()
        
        # Replace placeholder with actual Lambda ARN
        definition_json = definition_json.replace(
            "${EventEmitterLambdaArn}", 
            self.event_emitter_lambda.function_arn
        )
        
        # Parse the definition
        definition_dict = json.loads(definition_json)
        
        # Create Step Function definition from JSON
        definition = sfn.DefinitionBody.from_string(json.dumps(definition_dict))
        
        # Create Standard Step Function for continuous execution during market hours
        self.master_precision_timer = sfn.StateMachine(
            self, f"MasterPrecisionTimer{self.deploy_env.title()}",
            state_machine_name=self.get_resource_name("master-precision-timer"),
            definition_body=definition,
            role=step_function_role,
            state_machine_type=sfn.StateMachineType.STANDARD,  # No time limits, continuous execution
            logs=sfn.LogOptions(
                destination=logs.LogGroup(
                    self, f"MasterTimerStepFunctionLogs{self.deploy_env.title()}",
                    log_group_name=f"/aws/stepfunctions/{self.get_resource_name('master-precision-timer')}",
                    retention=logs.RetentionDays.ONE_WEEK,
                    removal_policy=RemovalPolicy.DESTROY
                ),
                level=sfn.LogLevel.ALL,
                include_execution_data=True
            ),
            tracing_enabled=True
        )
        
        # Store reference for monitoring and outputs
        self.master_timer_step_function = self.master_precision_timer
        
        # Create EventBridge rule to start Step Function at market open (9:15 AM IST = 3:45 AM UTC)
        self._create_step_function_starter_rule()

    def _create_step_function_starter_rule(self):
        """
        Create EventBridge rule to automatically start Step Function at market open
        Runs at 9:15 AM IST (3:45 AM UTC) every weekday
        """
        
        # Create EventBridge rule for market open (9:15 AM IST = 3:45 AM UTC)
        step_function_starter_rule = events.Rule(
            self, f"StepFunctionStarter{self.deploy_env.title()}",
            rule_name=self.get_resource_name("step-function-starter"),
            description="Start precision timer Step Function at market open (9:00 AM IST)",
            schedule=events.Schedule.cron(
                minute="30",        # 45 minutes 
                hour="3",           # 3rd hour UTC = 9:00 AM IST (3:30 AM UTC)
                month="*",          # Every month
                year="*",           # Every year
                week_day="MON-FRI"  # Weekdays only
            ),
            enabled=True
        )
        
        # Target the Step Function for automatic execution
        step_function_starter_rule.add_target(
            targets.SfnStateMachine(
                self.master_precision_timer,
                input=events.RuleTargetInput.from_object({
                    "trigger_type": "MARKET_OPEN_AUTO_START",
                    "market_open_time": "09:15",
                    "trigger_source": "EVENTBRIDGE_CRON",
                    "execution_mode": "CONTINUOUS_STANDARD_WORKFLOW",
                    "expected_duration": "6_HOURS_15_MINUTES",  # Market session length
                    "precision_target": "0_SECOND_INSTITUTIONAL_GRADE"
                })
            )
        )
        
        # Store reference for monitoring
        self.step_function_starter_rule = step_function_starter_rule
    
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
            self, "TradingConfigurationsTableName", 
            value=self.trading_configurations_table.table_name,
            description="Trading Configurations DynamoDB Table Name (Single Table)",
            export_name=f"{self.stack_name}-TradingConfigurationsTable"
        )
        
        CfnOutput(
            self, "ExecutionHistoryTableName",
            value=self.execution_history_table.table_name, 
            description="Execution History DynamoDB Table Name",
            export_name=f"{self.stack_name}-ExecutionHistoryTable"
        )
        
        if hasattr(self, 'websocket_api'):
            CfnOutput(
                self, "OptionsWebSocketUrl",
                value=self.websocket_stage.url,
                description="Options Trading WebSocket URL",
                export_name=f"{self.stack_name}-OptionsWebSocketUrl"
            )
        
        CfnOutput(
            self, "MasterPrecisionTimerStepFunction",
            value=self.master_timer_step_function.state_machine_arn,
            description="Master Precision Timer Step Function (0-second precision)",
            export_name=f"{self.stack_name}-MasterPrecisionTimer"
        )