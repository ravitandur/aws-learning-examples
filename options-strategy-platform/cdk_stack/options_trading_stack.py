import logging

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
    Duration,
    RemovalPolicy,
    CfnOutput,
    Fn
)
from constructs import Construct

logger = logging.getLogger(__name__)


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
        self.user_profiles_table_name = Fn.import_value(f"{auth_stack_name}-UserProfilesTable")

        # Create hybrid architecture tables
        self._create_hybrid_tables()

        # Create Lambda layers
        self._create_lambda_layers()

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

        # GSI1: Basket-Specific Allocation Queries (AllocationsByBasket) - INDUSTRY BEST PRACTICE
        # Purpose: Get all allocations for specific basket sorted by priority
        # Revolutionary basket-level allocation with inheritance to all strategies
        # Cost Optimization: Removed deprecated AllocationsByStrategy GSI (strategy-level allocation)
        self.trading_configurations_table.add_global_secondary_index(
            index_name="AllocationsByBasket",
            partition_key=dynamodb.Attribute(name="basket_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="entity_type_priority", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL
        )

        # GSI2: REMOVED - Previously UserExecutionSchedule
        # Replaced by efficient user_profiles table ActiveUsersIndex GSI
        # New approach: O(active_users) query performance instead of O(all_strategies)

        # GSI3: REMOVED - Previously TimeBasedExecutionDiscovery
        # Reason: Unused in codebase, redundant with user_profiles + GSI4 approach
        # Replaced by: ActiveUsersIndex (user_profiles) + GSI4 (UserScheduleDiscovery)
        # Benefits: Reduced DynamoDB costs, simplified architecture

        # GSI4: User-Centric Schedule Discovery (HIERARCHICAL ARCHITECTURE)
        # Purpose: User-specific strategy discovery with hierarchical schedule filtering
        # Query Pattern: PK="user_123" SK begins_with "SCHEDULE#WED#09:30"
        # Hierarchical: SCHEDULE -> WEEKDAY -> TIME -> TYPE -> STRATEGY
        # Ultimate Scalability: No 1MB DynamoDB query limits, unlimited user scaling
        # Benefits:
        # - User-specific result sets (5-50 strategies vs 10,000+ strategies)
        # - Hierarchical database-level filtering (weekday, time, type, strategy)
        # - Better error isolation (per-user processing)
        # - Fan-out pattern enables parallel user processing
        # - Self-documenting key structure for easier maintenance
        # GSI2: UserScheduleDiscovery - Revolutionary Lightweight Architecture
        # 🚀 REVOLUTIONARY CHANGE: 60-80% data reduction through just-in-time loading
        # Only essential fields for discovery, complete strategy loaded at execution time
        self.trading_configurations_table.add_global_secondary_index(
            index_name="UserScheduleDiscovery",
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="schedule_key", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.INCLUDE,
            non_key_attributes=[
                # 🎯 Lightweight Schedule Fields (only essential data)
                "strategy_id", "basket_id", "execution_time", "weekday",
                "status", "entity_type", "execution_type", "created_at", "updated_at", "sort_key"
                # 🚫 REMOVED: strategy_name, legs, broker_allocation, underlying, strategy_type, weekdays
                # ⚡ Performance: 5x data reduction, maintains 99.5% query reduction
            ]
        )

        # GSI3: MarketplaceDiscovery - B2B2C Marketplace Integration
        # Purpose: Browse marketplace templates by category with subscriber count ranking
        # Query Pattern: PK="MARKETPLACE#INCOME" SK=subscriber_count (desc)
        # Benefits:
        # - Category-based browsing (INCOME, CONSERVATIVE, AGGRESSIVE, etc.)
        # - Natural ranking by popularity (subscriber_count)
        # - Efficient partner API queries for external brokers (Zebu, Angel, etc.)
        # - Supports white-label marketplace integration
        self.trading_configurations_table.add_global_secondary_index(
            index_name="MarketplaceDiscovery",
            partition_key=dynamodb.Attribute(name="marketplace_category", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="subscriber_count", type=dynamodb.AttributeType.NUMBER),
            projection_type=dynamodb.ProjectionType.ALL
        )

        # GSI4: UserSubscriptions - User Subscription Management
        # Purpose: Query all subscriptions for a user with status filtering
        # Query Pattern: PK=user_id SK begins_with "ACTIVE#2025-10-10"
        # Benefits:
        # - Fast user subscription lookups
        # - Status-based filtering (ACTIVE, TRIAL, CANCELLED)
        # - Date-sorted for billing and analytics
        # - Optimized projection for subscription management UI
        self.trading_configurations_table.add_global_secondary_index(
            index_name="UserSubscriptions",
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="subscription_status_date", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.INCLUDE,
            non_key_attributes=[
                "subscription_id", "template_basket_id", "template_owner_id",
                "status", "pricing", "performance_tracking", "partner_api_key_id",
                "partner_id", "auto_linked_broker_account", "entity_type"
            ]
        )

        # GSI5: TemplateSubscribers - Reverse lookup for execution
        # Purpose: Find all users subscribed to a specific template basket
        # Query Pattern: PK=template_basket_id SK begins_with "ACTIVE#"
        # Benefits:
        # - Execution engine discovers subscribers
        # - Admin changes propagate to all subscribers
        # - Efficient subscriber analytics
        # - Partner revenue attribution
        self.trading_configurations_table.add_global_secondary_index(
            index_name="TemplateSubscribers",
            partition_key=dynamodb.Attribute(name="template_basket_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="subscription_status_date", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.INCLUDE,
            non_key_attributes=[
                "user_id", "subscription_id", "status", "auto_linked_broker_account",
                "partner_id", "created_at"
            ]
        )

        # GSI6: OrdersByStatus - Order Status Filtering and Real-time Updates
        # Purpose: Query orders by status for orders page filtering
        # Query Pattern: PK=user_id SK begins_with "status#timestamp"
        # Sort Key Format: "{status}#{timestamp}" (e.g., "OPEN#2025-12-11T09:30:00Z")
        # Benefits:
        # - Filter orders by status (PENDING, PLACED, OPEN, FILLED, CANCELLED, REJECTED)
        # - Chronological ordering within status
        # - Efficient real-time order tracking
        # - WebSocket update broadcasting
        self.trading_configurations_table.add_global_secondary_index(
            index_name="OrdersByStatus",
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="order_status_key", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.INCLUDE,
            non_key_attributes=[
                "order_id", "strategy_id", "basket_id", "broker_id", "client_id",
                "broker_order_id", "order_type", "transaction_type", "trading_mode",
                "exchange", "symbol", "quantity", "price", "trigger_price", "status",
                "fill_price", "filled_quantity", "execution_type", "placed_at", "updated_at"
            ]
        )

        # GSI7: TodayExecutions - Today's Execution Timeline Discovery
        # Purpose: Get all strategies executing today with entry/exit times
        # Query Pattern: PK=user_id SK begins_with "execution_date#entry_time"
        # Sort Key Format: "{date}#{entry_time}" (e.g., "2025-12-11#09:30")
        # Benefits:
        # - Today's timeline view with entry/exit countdown
        # - Chronological strategy execution ordering
        # - Quick status check for active/pending strategies
        # - Dashboard summary of daily execution plan
        self.trading_configurations_table.add_global_secondary_index(
            index_name="TodayExecutions",
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="today_execution_key", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.INCLUDE,
            non_key_attributes=[
                "strategy_id", "basket_id", "strategy_name", "execution_date",
                "entry_time", "exit_time", "status", "execution_status",
                "underlying", "strategy_type", "trading_mode", "broker_allocations"
            ]
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

        # Table 3: WebSocket Connections - Real-time Update Infrastructure
        # Purpose: Track active WebSocket connections for real-time order/position updates
        # TTL: Auto-cleanup stale connections after 24 hours
        self.websocket_connections_table = dynamodb.Table(
            self, f"WebSocketConnections{self.deploy_env.title()}",
            table_name=self.get_resource_name("websocket-connections"),
            partition_key=dynamodb.Attribute(name="connection_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=removal_policy,
            time_to_live_attribute="ttl",  # Auto-cleanup stale connections
        )

        # GSI: ConnectionsByUser - Find all connections for a specific user
        # Purpose: Broadcast updates to all user's active connections
        # Query Pattern: PK=user_id SK=connected_at (for connection ordering)
        self.websocket_connections_table.add_global_secondary_index(
            index_name="ConnectionsByUser",
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="connected_at", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL
        )

    def _create_lambda_layers(self):
        """Create Lambda layers for shared dependencies"""

        # Trading Dependencies Layer - contains requests and other broker API dependencies
        # To add more dependencies:
        # 1. Update lambda_layers/trading_dependencies/requirements.txt
        # 2. Run: pip3 install -r requirements.txt -t python/ --platform manylinux2014_x86_64 --only-binary=:all: --python-version 3.11
        # 3. Redeploy the stack
        self.trading_dependencies_layer = _lambda.LayerVersion(
            self, f"TradingDependenciesLayer{self.deploy_env.title()}",
            layer_version_name=self.get_resource_name("trading-dependencies-layer"),
            description="Trading dependencies including requests for broker API calls",
            code=_lambda.Code.from_asset("lambda_layers/trading_dependencies"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
            removal_policy=self.get_removal_policy(),
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
            "USER_PROFILES_TABLE": self.user_profiles_table_name,
            "REGION": self.region,
            # Phase 1 Hybrid Architecture - Two tables only
            "TRADING_CONFIGURATIONS_TABLE": self.trading_configurations_table.table_name,
            "EXECUTION_HISTORY_TABLE": self.execution_history_table.table_name,
            # WebSocket connections for real-time updates
            "WEBSOCKET_CONNECTIONS_TABLE": self.websocket_connections_table.table_name,
        }

        # Create Lambda functions (placeholder implementations for now)
        self.lambda_functions = {}

        lambda_configs = [
            # Strategy Management
            ('basket-manager', 'Strategy management/basket_manager.py'),
            ('strategy-manager', 'Strategy management/strategy_manager.py'),
            ('basket-broker-allocator', 'Strategy management/basket_broker_allocator.py'),

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

            # 🚀 Parallel Execution Engine (NEW)
            ('user-strategy-executor', '🚀 Execute strategies for single user in parallel - ZERO queries!'),
            ('single-strategy-executor', '🚀 Execute individual strategy with ultimate parallelization - ZERO queries!'),
            ('strategy-scheduler', '🕐 SQS-to-Express Step Function launcher for time-based strategy execution'),
        ]

        # Functions that need trading dependencies layer (requests for broker API calls)
        functions_needing_trading_layer = [
            'order-manager',
            'position-manager',
            'strategy-executor',
            'single-strategy-executor',
            'user-strategy-executor',
        ]

        # Create Lambda functions with logRetention (avoids redeploy LogGroup errors)
        for function_name, description in lambda_configs:
            # Determine if this function needs the trading dependencies layer
            layers = [self.trading_dependencies_layer] if function_name in functions_needing_trading_layer else []

            self.lambda_functions[function_name] = _lambda.Function(
                self, f"OptionsLambda{function_name.title().replace('-', '')}{self.deploy_env.title()}",
                function_name=self.get_resource_name(f"options-{function_name}"),
                runtime=_lambda.Runtime.PYTHON_3_11,
                code=_lambda.Code.from_asset("lambda_functions"),
                handler=f"option_baskets.{function_name.replace('-', '_')}.lambda_handler",
                environment=lambda_env,
                timeout=Duration.seconds(30),
                memory_size=512,
                layers=layers,  # Attach trading dependencies layer if needed
                log_retention=logs.RetentionDays.ONE_WEEK if self.env_config['log_retention_days'] == 7
                else logs.RetentionDays.ONE_MONTH if self.env_config['log_retention_days'] == 30
                else logs.RetentionDays.THREE_MONTHS,  # Use logRetention to avoid redeploy errors
                description=description,
            )

        # Grant DynamoDB permissions to all Lambda functions - Phase 1 Hybrid Architecture
        tables = [
            self.trading_configurations_table,  # Single table for all operational data
            self.execution_history_table,  # Separate table for execution records
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

            # Grant access to broker accounts table from auth stack
            function.add_to_role_policy(
                iam.PolicyStatement(
                    actions=[
                        "dynamodb:GetItem",
                        "dynamodb:Query",
                        "dynamodb:Scan"
                    ],
                    resources=[
                        f"arn:aws:dynamodb:{self.region}:{self.account}:table/{self.broker_accounts_table_name}",
                        f"arn:aws:dynamodb:{self.region}:{self.account}:table/{self.broker_accounts_table_name}/*"
                    ]
                )
            )

    # NOTE: _create_parallel_execution_infrastructure() REMOVED
    # Replaced by direct EventBridge → Lambda architecture (Strategy.Execution.Triggered events)

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

        # Global allocations endpoint - Get all allocations for current user across all baskets
        allocations_resource = options_resource.add_resource("allocations")
        allocations_resource.add_method("GET",
                                       apigateway.LambdaIntegration(self.lambda_functions['basket-broker-allocator']),
                                       authorization_type=apigateway.AuthorizationType.COGNITO,
                                       authorizer=authorizer
                                       )

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

        # Basket allocation endpoints - Industry Best Practice: Basket-Level Allocation
        basket_id_resource = baskets_resource.add_resource("{basket_id}")

        # PUT /options/baskets/{basket_id} - Update basket (including status updates)
        basket_id_resource.add_method("PUT",
                                     apigateway.LambdaIntegration(self.lambda_functions['basket-manager']),
                                     authorization_type=apigateway.AuthorizationType.COGNITO,
                                     authorizer=authorizer
                                     )

        # GET /options/baskets/{basket_id} - Get specific basket details
        basket_id_resource.add_method("GET",
                                     apigateway.LambdaIntegration(self.lambda_functions['basket-manager']),
                                     authorization_type=apigateway.AuthorizationType.COGNITO,
                                     authorizer=authorizer
                                     )

        # DELETE /options/baskets/{basket_id} - Delete basket
        basket_id_resource.add_method("DELETE",
                                     apigateway.LambdaIntegration(self.lambda_functions['basket-manager']),
                                     authorization_type=apigateway.AuthorizationType.COGNITO,
                                     authorizer=authorizer
                                     )

        allocations_resource = basket_id_resource.add_resource("allocations")
        
        # GET /options/baskets/{basket_id}/allocations - List basket allocations
        allocations_resource.add_method("GET",
                                        apigateway.LambdaIntegration(self.lambda_functions['basket-broker-allocator']),
                                        authorization_type=apigateway.AuthorizationType.COGNITO,
                                        authorizer=authorizer
                                        )
        
        # POST /options/baskets/{basket_id}/allocations - Create basket allocations
        allocations_resource.add_method("POST",
                                        apigateway.LambdaIntegration(self.lambda_functions['basket-broker-allocator']),
                                        authorization_type=apigateway.AuthorizationType.COGNITO,
                                        authorizer=authorizer
                                        )
        
        # Specific allocation operations
        allocation_id_resource = allocations_resource.add_resource("{allocation_id}")
        
        # GET /options/baskets/{basket_id}/allocations/{allocation_id} - Get specific allocation
        allocation_id_resource.add_method("GET",
                                          apigateway.LambdaIntegration(self.lambda_functions['basket-broker-allocator']),
                                          authorization_type=apigateway.AuthorizationType.COGNITO,
                                          authorizer=authorizer
                                          )
        
        # PUT /options/baskets/{basket_id}/allocations/{allocation_id} - Update allocation
        allocation_id_resource.add_method("PUT",
                                          apigateway.LambdaIntegration(self.lambda_functions['basket-broker-allocator']),
                                          authorization_type=apigateway.AuthorizationType.COGNITO,
                                          authorizer=authorizer
                                          )
        
        # DELETE /options/baskets/{basket_id}/allocations/{allocation_id} - Delete allocation
        allocation_id_resource.add_method("DELETE",
                                          apigateway.LambdaIntegration(self.lambda_functions['basket-broker-allocator']),
                                          authorization_type=apigateway.AuthorizationType.COGNITO,
                                          authorizer=authorizer
                                          )
        
        # Summary endpoint: GET /options/baskets/{basket_id}/allocations/summary
        summary_resource = allocations_resource.add_resource("summary")
        summary_resource.add_method("GET",
                                    apigateway.LambdaIntegration(self.lambda_functions['basket-broker-allocator']),
                                    authorization_type=apigateway.AuthorizationType.COGNITO,
                                    authorizer=authorizer
                                    )

        # Basket strategy endpoints - Basket-specific strategy management
        basket_strategies_resource = basket_id_resource.add_resource("strategies")
        
        # GET /options/baskets/{basket_id}/strategies - List strategies for specific basket
        basket_strategies_resource.add_method("GET",
                                            apigateway.LambdaIntegration(self.lambda_functions['strategy-manager']),
                                            authorization_type=apigateway.AuthorizationType.COGNITO,
                                            authorizer=authorizer
                                            )
        
        # POST /options/baskets/{basket_id}/strategies - Create strategy in specific basket
        basket_strategies_resource.add_method("POST",
                                            apigateway.LambdaIntegration(self.lambda_functions['strategy-manager']),
                                            authorization_type=apigateway.AuthorizationType.COGNITO,
                                            authorizer=authorizer
                                            )

        # Bulk delete endpoint - DELETE /options/baskets/{basket_id}/strategies/bulk-delete
        bulk_delete_resource = basket_strategies_resource.add_resource("bulk-delete")
        bulk_delete_resource.add_method("DELETE",
                                      apigateway.LambdaIntegration(self.lambda_functions['strategy-manager']),
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

        # Individual strategy endpoints (secured with Cognito authorizer)
        strategy_id_resource = strategies_resource.add_resource("{strategy_id}")
        strategy_id_resource.add_method("GET",
                                       apigateway.LambdaIntegration(self.lambda_functions['strategy-manager']),
                                       authorization_type=apigateway.AuthorizationType.COGNITO,
                                       authorizer=authorizer
                                       )
        strategy_id_resource.add_method("PUT",
                                       apigateway.LambdaIntegration(self.lambda_functions['strategy-manager']),
                                       authorization_type=apigateway.AuthorizationType.COGNITO,
                                       authorizer=authorizer
                                       )
        strategy_id_resource.add_method("DELETE",
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

        # =============================================================================
        # Trading Endpoints - Orders, Positions, Today's Executions
        # =============================================================================

        trading_resource = options_resource.add_resource("trading")

        # --- Orders Management ---
        orders_resource = trading_resource.add_resource("orders")

        # GET /options/trading/orders - List all orders with optional filters
        orders_resource.add_method("GET",
                                   apigateway.LambdaIntegration(self.lambda_functions['order-manager']),
                                   authorization_type=apigateway.AuthorizationType.COGNITO,
                                   authorizer=authorizer
                                   )

        # POST /options/trading/orders - Place new order
        orders_resource.add_method("POST",
                                   apigateway.LambdaIntegration(self.lambda_functions['order-manager']),
                                   authorization_type=apigateway.AuthorizationType.COGNITO,
                                   authorizer=authorizer
                                   )

        # Individual order operations
        order_id_resource = orders_resource.add_resource("{order_id}")

        # GET /options/trading/orders/{order_id} - Get order details
        order_id_resource.add_method("GET",
                                     apigateway.LambdaIntegration(self.lambda_functions['order-manager']),
                                     authorization_type=apigateway.AuthorizationType.COGNITO,
                                     authorizer=authorizer
                                     )

        # PUT /options/trading/orders/{order_id} - Modify order
        order_id_resource.add_method("PUT",
                                     apigateway.LambdaIntegration(self.lambda_functions['order-manager']),
                                     authorization_type=apigateway.AuthorizationType.COGNITO,
                                     authorizer=authorizer
                                     )

        # DELETE /options/trading/orders/{order_id} - Cancel order
        order_id_resource.add_method("DELETE",
                                     apigateway.LambdaIntegration(self.lambda_functions['order-manager']),
                                     authorization_type=apigateway.AuthorizationType.COGNITO,
                                     authorizer=authorizer
                                     )

        # --- Positions Management ---
        positions_resource = trading_resource.add_resource("positions")

        # GET /options/trading/positions - Get all positions
        positions_resource.add_method("GET",
                                      apigateway.LambdaIntegration(self.lambda_functions['position-manager']),
                                      authorization_type=apigateway.AuthorizationType.COGNITO,
                                      authorizer=authorizer
                                      )

        # GET /options/trading/positions/summary - Get P&L summary
        positions_summary_resource = positions_resource.add_resource("summary")
        positions_summary_resource.add_method("GET",
                                              apigateway.LambdaIntegration(self.lambda_functions['position-manager']),
                                              authorization_type=apigateway.AuthorizationType.COGNITO,
                                              authorizer=authorizer
                                              )

        # Individual position operations
        position_id_resource = positions_resource.add_resource("{position_id}")

        # GET /options/trading/positions/{position_id} - Get position details
        position_id_resource.add_method("GET",
                                        apigateway.LambdaIntegration(self.lambda_functions['position-manager']),
                                        authorization_type=apigateway.AuthorizationType.COGNITO,
                                        authorizer=authorizer
                                        )

        # POST /options/trading/positions/{position_id}/square-off - Square off position
        position_square_off_resource = position_id_resource.add_resource("square-off")
        position_square_off_resource.add_method("POST",
                                                apigateway.LambdaIntegration(self.lambda_functions['position-manager']),
                                                authorization_type=apigateway.AuthorizationType.COGNITO,
                                                authorizer=authorizer
                                                )

        # --- Today's Executions Timeline ---
        today_resource = trading_resource.add_resource("today")

        # GET /options/trading/today - Get today's execution timeline
        today_resource.add_method("GET",
                                  apigateway.LambdaIntegration(self.lambda_functions['strategy-executor']),
                                  authorization_type=apigateway.AuthorizationType.COGNITO,
                                  authorizer=authorizer
                                  )

        # GET /options/trading/today/summary - Get today's P&L summary
        today_summary_resource = today_resource.add_resource("summary")
        today_summary_resource.add_method("GET",
                                          apigateway.LambdaIntegration(self.lambda_functions['position-manager']),
                                          authorization_type=apigateway.AuthorizationType.COGNITO,
                                          authorizer=authorizer
                                          )

    def _create_websocket_api(self):
        """Create WebSocket API for real-time updates with handler integrations"""

        if not self.options_config.get('enable_realtime_websocket', True):
            return

        # Common environment variables for WebSocket handlers
        ws_lambda_env = {
            "ENVIRONMENT": self.deploy_env,
            "COMPANY_PREFIX": self.company_prefix,
            "PROJECT_NAME": self.project_name,
            "REGION": self.region,
            "WEBSOCKET_CONNECTIONS_TABLE": self.websocket_connections_table.table_name,
            "TRADING_CONFIGURATIONS_TABLE": self.trading_configurations_table.table_name,
        }

        # Create WebSocket connect handler Lambda
        self.ws_connect_handler = _lambda.Function(
            self, f"WsConnectHandler{self.deploy_env.title()}",
            function_name=self.get_resource_name("ws-connect-handler"),
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("lambda_functions"),
            handler="websocket.connect_handler.lambda_handler",
            environment=ws_lambda_env,
            timeout=Duration.seconds(10),
            memory_size=256,
            log_retention=logs.RetentionDays.ONE_WEEK if self.env_config['log_retention_days'] == 7
            else logs.RetentionDays.ONE_MONTH if self.env_config['log_retention_days'] == 30
            else logs.RetentionDays.THREE_MONTHS,
            description="WebSocket $connect route handler - authenticate and store connection"
        )

        # Create WebSocket disconnect handler Lambda
        self.ws_disconnect_handler = _lambda.Function(
            self, f"WsDisconnectHandler{self.deploy_env.title()}",
            function_name=self.get_resource_name("ws-disconnect-handler"),
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("lambda_functions"),
            handler="websocket.disconnect_handler.lambda_handler",
            environment=ws_lambda_env,
            timeout=Duration.seconds(10),
            memory_size=256,
            log_retention=logs.RetentionDays.ONE_WEEK if self.env_config['log_retention_days'] == 7
            else logs.RetentionDays.ONE_MONTH if self.env_config['log_retention_days'] == 30
            else logs.RetentionDays.THREE_MONTHS,
            description="WebSocket $disconnect route handler - cleanup connection"
        )

        # Create WebSocket message handler Lambda
        self.ws_message_handler = _lambda.Function(
            self, f"WsMessageHandler{self.deploy_env.title()}",
            function_name=self.get_resource_name("ws-message-handler"),
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("lambda_functions"),
            handler="websocket.message_handler.lambda_handler",
            environment=ws_lambda_env,
            timeout=Duration.seconds(30),
            memory_size=256,
            log_retention=logs.RetentionDays.ONE_WEEK if self.env_config['log_retention_days'] == 7
            else logs.RetentionDays.ONE_MONTH if self.env_config['log_retention_days'] == 30
            else logs.RetentionDays.THREE_MONTHS,
            description="WebSocket $default route handler - process messages"
        )

        # Grant DynamoDB permissions to WebSocket handlers
        for ws_handler in [self.ws_connect_handler, self.ws_disconnect_handler, self.ws_message_handler]:
            self.websocket_connections_table.grant_read_write_data(ws_handler)
            self.trading_configurations_table.grant_read_data(ws_handler)

        # Create WebSocket API with route integrations
        self.websocket_api = apigatewayv2.WebSocketApi(
            self, f"OptionsWebSocketApi{self.deploy_env.title()}",
            api_name=self.get_resource_name("options-websocket"),
            description=f"Options Trading WebSocket API - {self.deploy_env} environment",
            connect_route_options=apigatewayv2.WebSocketRouteOptions(
                integration=integrations.WebSocketLambdaIntegration(
                    "ConnectIntegration",
                    self.ws_connect_handler
                )
            ),
            disconnect_route_options=apigatewayv2.WebSocketRouteOptions(
                integration=integrations.WebSocketLambdaIntegration(
                    "DisconnectIntegration",
                    self.ws_disconnect_handler
                )
            ),
            default_route_options=apigatewayv2.WebSocketRouteOptions(
                integration=integrations.WebSocketLambdaIntegration(
                    "DefaultIntegration",
                    self.ws_message_handler
                )
            ),
        )

        # Add WebSocket stage
        self.websocket_stage = apigatewayv2.WebSocketStage(
            self, f"OptionsWebSocketStage{self.deploy_env.title()}",
            web_socket_api=self.websocket_api,
            stage_name=self.deploy_env,
            auto_deploy=True,
        )

        # Grant WebSocket API management permissions to all WebSocket handlers
        # This allows handlers to send messages back to connected clients
        for ws_handler in [self.ws_connect_handler, self.ws_disconnect_handler, self.ws_message_handler]:
            ws_handler.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["execute-api:ManageConnections"],
                    resources=[
                        f"arn:aws:execute-api:{self.region}:{self.account}:{self.websocket_api.api_id}/{self.deploy_env}/*"
                    ]
                )
            )

        # Store WebSocket URL in environment for broadcaster Lambda
        self.websocket_endpoint = f"https://{self.websocket_api.api_id}.execute-api.{self.region}.amazonaws.com/{self.deploy_env}"

    def _create_event_driven_execution_architecture(self):
        """
        Create sophisticated event-driven execution architecture
        Industry-leading design that surpasses retail platforms
        """

        # Create event emitter Lambda with EventBridge cron for timing events
        self._create_event_emitter_lambda()


        # Create event handlers for different event types
        self._create_event_handlers()

        # NOTE: Removed unused Step Functions (cleaned up architecture):
        # - user-strategy-execution (replaced by direct EventBridge → Lambda)
        # - express-execution (replaced by direct EventBridge → Lambda)
        # - individual-strategy-execution (replaced by direct EventBridge → Lambda)
        # - batch-strategy-executor (replaced by direct EventBridge → Lambda)
        # - single-strategy-standard/express-execution (replaced by direct EventBridge → Lambda)
        #
        # New architecture uses only master-precision-timer Step Function:
        # EventBridge Cron → master-precision-timer → event_emitter → EventBridge events → Lambda handlers

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
            "USER_PROFILES_TABLE": self.user_profiles_table_name,
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

        # Grant read permissions to user_profiles table for active user discovery
        self.event_emitter_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:Query",
                    "dynamodb:GetItem"
                ],
                resources=[
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/{self.user_profiles_table_name}",
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/{self.user_profiles_table_name}/index/ActiveUsersIndex"
                ]
            )
        )

        # Create Step Functions Express for TRUE 0-second precision timing
        self._create_master_precision_timer_step_function()

    # ============================================================================
    # NOTE: REMOVED UNUSED INFRASTRUCTURE (December 2025 Cleanup)
    # ============================================================================
    # The following infrastructure was removed in favor of direct EventBridge → Lambda:
    #
    # REMOVED SQS Infrastructure:
    # - _create_sqs_infrastructure() - strategy-batch-queue, single-strategy-queue, DLQs
    # - step-function-launcher Lambda
    #
    # REMOVED Step Functions:
    # - _create_express_execution_state_machine() - express-execution
    # - _create_strategy_execution_eventbridge_rule() - strategy-execution-trigger
    # - _create_individual_strategy_execution_state_machine() - individual-strategy-execution
    # - _create_individual_strategy_execution_eventbridge_rule()
    # - _create_batch_strategy_executor_step_function() - batch-strategy-executor
    # - _create_individual_strategy_eventbridge_role()
    # - _grant_individual_strategy_execution_permissions()
    # - _create_eventbridge_step_function_role()
    #
    # NEW ARCHITECTURE: Direct EventBridge → Lambda
    # - Source: qlalgo.options.trading
    # - DetailType: Strategy.Execution.Triggered
    # - Target: single-strategy-executor Lambda (direct invocation)
    # ============================================================================

    def _create_event_handlers(self):
        """Create event handlers for different event types"""

        # Create event handler Lambda functions
        event_handler_configs = [
            # Primary event handler - processes Active User Events
            ("active-user-event-handler", "Process Active User Events and emit sub-events"),

            # Sub-event handlers - individual handlers for each sub-event type
            ("strategy-entry-handler", "Handle strategy entry triggers"),
            ("strategy-exit-handler", "Handle strategy exit triggers"),
            ("stop-loss-handler", "Handle stop loss monitoring and exits"),
            ("target-profit-handler", "Handle target profit monitoring and exits"),
            ("trailing-sl-handler", "Handle trailing stop loss adjustments"),
            ("duplicate-order-handler", "Handle duplicate order detection"),
            ("re-entry-handler", "Handle strategy re-entry conditions"),
            ("re-execute-handler", "Handle failed execution retries"),
            ("position-sync-handler", "Handle position sync across brokers")
        ]

        self.event_handlers = {}

        for handler_name, description in event_handler_configs:
            # Enhanced environment for event handlers
            # NOTE: Step Functions and SQS removed - using direct EventBridge → Lambda
            handler_env = {
                "ENVIRONMENT": self.deploy_env,
                "COMPANY_PREFIX": self.company_prefix,
                "REGION": self.region,
                "TRADING_CONFIGURATIONS_TABLE": self.trading_configurations_table.table_name,
                "EXECUTION_HISTORY_TABLE": self.execution_history_table.table_name,
                # 🚀 Cross-stack integration - broker accounts from auth stack
                "BROKER_ACCOUNTS_TABLE": self.broker_accounts_table_name,
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

            # Grant EventBridge permissions for emitting events
            handler_lambda.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["events:PutEvents"],
                    resources=[f"arn:aws:events:{self.region}:{self.account}:event-bus/default"]
                )
            )

            # 🚀 Grant broker accounts table access for active-user-event-handler (cross-stack)
            if handler_name == "active-user-event-handler":
                handler_lambda.add_to_role_policy(
                    iam.PolicyStatement(
                        actions=[
                            "dynamodb:Query",
                            "dynamodb:GetItem"
                        ],
                        resources=[
                            f"arn:aws:dynamodb:{self.region}:{self.account}:table/{self.broker_accounts_table_name}",
                            f"arn:aws:dynamodb:{self.region}:{self.account}:table/{self.broker_accounts_table_name}/*"
                        ]
                    )
                )
                logger.info(f"🚀 Granted broker accounts table read permissions to {handler_name}")

            self.event_handlers[handler_name] = handler_lambda

        # Create EventBridge rules for event handlers
        self._create_event_handler_rules()

    def _create_event_handler_rules(self):
        """Create EventBridge rules to trigger event handlers"""

        # ============================================================================
        # ACTIVE USER EVENT - Primary event from event_emitter (v2.0 architecture)
        # Each active user receives one comprehensive event with all sub-events
        # ============================================================================
        active_user_event_rule = events.Rule(
            self, f"ActiveUserEventRule{self.deploy_env.title()}",
            rule_name=self.get_resource_name("active-user-event"),
            description="Process Active User Events containing all sub-events",
            event_pattern=events.EventPattern(
                source=["options.trading.active_user"],
                detail_type=["Active User Event"]
            )
        )

        active_user_event_rule.add_target(
            targets.LambdaFunction(self.event_handlers['active-user-event-handler'])
        )

        # ============================================================================
        # SUB-EVENT RULES - Triggered by active_user_event_handler
        # Industry-standard naming: Single source, detail_type for routing
        # Source: qlalgo.options.trading
        # Detail Type Pattern: {Category}.{Entity}.{Action}
        # ============================================================================

        # Strategy Entry Trigger - From active_user_event_handler
        strategy_entry_rule = events.Rule(
            self, f"StrategyEntryRule{self.deploy_env.title()}",
            rule_name=self.get_resource_name("strategy-entry-trigger"),
            description="Handle strategy entry sub-events",
            event_pattern=events.EventPattern(
                source=["qlalgo.options.trading"],
                detail_type=["Strategy.Entry.Triggered"]
            )
        )

        strategy_entry_rule.add_target(
            targets.LambdaFunction(self.event_handlers['strategy-entry-handler'])
        )

        # Strategy Exit Trigger - From active_user_event_handler
        strategy_exit_rule = events.Rule(
            self, f"StrategyExitRule{self.deploy_env.title()}",
            rule_name=self.get_resource_name("strategy-exit-trigger"),
            description="Handle strategy exit sub-events",
            event_pattern=events.EventPattern(
                source=["qlalgo.options.trading"],
                detail_type=["Strategy.Exit.Triggered"]
            )
        )

        strategy_exit_rule.add_target(
            targets.LambdaFunction(self.event_handlers['strategy-exit-handler'])
        )

        # Stop Loss Check - From active_user_event_handler
        user_stop_loss_rule = events.Rule(
            self, f"UserStopLossCheckRule{self.deploy_env.title()}",
            rule_name=self.get_resource_name("user-stop-loss-check"),
            description="Handle user-specific stop loss sub-events",
            event_pattern=events.EventPattern(
                source=["qlalgo.options.trading"],
                detail_type=["Risk.StopLoss.Check"]
            )
        )

        user_stop_loss_rule.add_target(
            targets.LambdaFunction(self.event_handlers['stop-loss-handler'])
        )

        # Target Profit Check - From active_user_event_handler
        target_profit_rule = events.Rule(
            self, f"TargetProfitCheckRule{self.deploy_env.title()}",
            rule_name=self.get_resource_name("target-profit-check"),
            description="Handle target profit sub-events",
            event_pattern=events.EventPattern(
                source=["qlalgo.options.trading"],
                detail_type=["Risk.TargetProfit.Check"]
            )
        )

        target_profit_rule.add_target(
            targets.LambdaFunction(self.event_handlers['target-profit-handler'])
        )

        # Trailing Stop Loss Check - From active_user_event_handler
        trailing_sl_rule = events.Rule(
            self, f"TrailingSlCheckRule{self.deploy_env.title()}",
            rule_name=self.get_resource_name("trailing-sl-check"),
            description="Handle trailing stop loss sub-events",
            event_pattern=events.EventPattern(
                source=["qlalgo.options.trading"],
                detail_type=["Risk.TrailingSL.Check"]
            )
        )

        trailing_sl_rule.add_target(
            targets.LambdaFunction(self.event_handlers['trailing-sl-handler'])
        )

        # Duplicate Order Check - From active_user_event_handler
        user_duplicate_order_rule = events.Rule(
            self, f"UserDuplicateOrderRule{self.deploy_env.title()}",
            rule_name=self.get_resource_name("user-duplicate-order-check"),
            description="Handle user-specific duplicate order sub-events",
            event_pattern=events.EventPattern(
                source=["qlalgo.options.trading"],
                detail_type=["Validation.DuplicateOrder.Check"]
            )
        )

        user_duplicate_order_rule.add_target(
            targets.LambdaFunction(self.event_handlers['duplicate-order-handler'])
        )

        # Re-Entry Check - From active_user_event_handler
        re_entry_rule = events.Rule(
            self, f"ReEntryCheckRule{self.deploy_env.title()}",
            rule_name=self.get_resource_name("re-entry-check"),
            description="Handle re-entry condition sub-events",
            event_pattern=events.EventPattern(
                source=["qlalgo.options.trading"],
                detail_type=["Strategy.ReEntry.Check"]
            )
        )

        re_entry_rule.add_target(
            targets.LambdaFunction(self.event_handlers['re-entry-handler'])
        )

        # Re-Execute Check - From active_user_event_handler
        re_execute_rule = events.Rule(
            self, f"ReExecuteCheckRule{self.deploy_env.title()}",
            rule_name=self.get_resource_name("re-execute-check"),
            description="Handle re-execution sub-events for failed orders",
            event_pattern=events.EventPattern(
                source=["qlalgo.options.trading"],
                detail_type=["Strategy.ReExecute.Check"]
            )
        )

        re_execute_rule.add_target(
            targets.LambdaFunction(self.event_handlers['re-execute-handler'])
        )

        # Position Sync - From active_user_event_handler
        position_sync_rule = events.Rule(
            self, f"PositionSyncRule{self.deploy_env.title()}",
            rule_name=self.get_resource_name("position-sync"),
            description="Handle position sync sub-events across brokers",
            event_pattern=events.EventPattern(
                source=["qlalgo.options.trading"],
                detail_type=["Sync.Position.Triggered"]
            )
        )

        position_sync_rule.add_target(
            targets.LambdaFunction(self.event_handlers['position-sync-handler'])
        )

        # ============================================================================
        # STRATEGY EXECUTION EVENT - From strategy_entry_handler / strategy_exit_handler
        # Routes execution events directly to single-strategy-executor Lambda
        # Pre-loaded allocation data passed in event (hybrid approach - Option 2)
        # ============================================================================
        strategy_execution_rule = events.Rule(
            self, f"StrategyExecutionRule{self.deploy_env.title()}",
            rule_name=self.get_resource_name("strategy-execution-triggered"),
            description="Execute strategy with pre-loaded allocation data from entry/exit handlers",
            event_pattern=events.EventPattern(
                source=["qlalgo.options.trading"],
                detail_type=["Strategy.Execution.Triggered"]
            )
        )

        strategy_execution_rule.add_target(
            targets.LambdaFunction(self.lambda_functions['single-strategy-executor'])
        )

    def _create_master_precision_timer_step_function(self):
        """
        🚀 Create Step Functions Express for TRUE 0-Second Precision Event Emission
        REVOLUTIONARY TIMING SYSTEM: Achieves institutional-grade precision with continuous loop
        """

        # Use already imported Step Functions constructs
        # Imports available as: stepfunctions (sfn), tasks

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
        definition = stepfunctions.DefinitionBody.from_string(json.dumps(definition_dict))

        # Create Standard Step Function for continuous execution during market hours
        self.master_precision_timer = stepfunctions.StateMachine(
            self, f"MasterPrecisionTimer{self.deploy_env.title()}",
            state_machine_name=self.get_resource_name("master-precision-timer"),
            definition_body=definition,
            role=step_function_role,
            state_machine_type=stepfunctions.StateMachineType.STANDARD,  # No time limits, continuous execution
            logs=stepfunctions.LogOptions(
                destination=logs.LogGroup(
                    self, f"MasterTimerStepFunctionLogs{self.deploy_env.title()}",
                    log_group_name=f"/aws/stepfunctions/{self.get_resource_name('master-precision-timer')}",
                    retention=logs.RetentionDays.ONE_WEEK,
                    removal_policy=RemovalPolicy.DESTROY
                ),
                level=stepfunctions.LogLevel.ALL,
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

        # Create EventBridge rule for operational window start (8:55 AM IST = 3:25 AM UTC)
        # This is a GENERIC operational window covering all exchanges (NSE, BSE, MCX, etc.)
        step_function_starter_rule = events.Rule(
            self, f"StepFunctionStarter{self.deploy_env.title()}",
            rule_name=self.get_resource_name("step-function-starter"),
            description="Start precision timer Step Function at operational window start (8:55 AM IST)",
            schedule=events.Schedule.cron(
                minute="25",  # 25 minutes past the hour
                hour="3",     # 3rd hour UTC = 8:55 AM IST (3:25 AM UTC)
                month="*",    # Every month
                year="*",     # Every year
                week_day="MON-FRI"  # Weekdays only
            ),
            enabled=True
        )

        # Target the Step Function for automatic execution
        step_function_starter_rule.add_target(
            targets.SfnStateMachine(
                self.master_precision_timer,
                input=events.RuleTargetInput.from_object({
                    "trigger_type": "OPERATIONAL_WINDOW_AUTO_START",
                    "operational_start_time": "08:55",
                    "operational_end_time": "23:55",
                    "trigger_source": "EVENTBRIDGE_CRON",
                    "execution_mode": "CONTINUOUS_STANDARD_WORKFLOW",
                    "expected_duration": "15_HOURS",  # 8:55 AM to 11:55 PM IST
                    "precision_target": "0_SECOND_INSTITUTIONAL_GRADE",
                    "note": "Generic operational window - exchange-specific hours handled at execution"
                })
            )
        )

        # Store reference for monitoring
        self.step_function_starter_rule = step_function_starter_rule

    # NOTE: _create_single_strategy_express_step_function() REMOVED
    # Replaced by direct EventBridge → Lambda architecture (Strategy.Execution.Triggered events)

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

        # NOTE: SQS Queue outputs removed - using direct EventBridge → Lambda architecture

        CfnOutput(
            self, "TradingDependenciesLayerArn",
            value=self.trading_dependencies_layer.layer_version_arn,
            description="Trading Dependencies Lambda Layer ARN",
            export_name=f"{self.stack_name}-TradingDependenciesLayerArn"
        )
