"""
Options Marketplace Stack - B2B2C Marketplace Integration

This stack handles all marketplace-related functionality:
- Marketplace template browsing and discovery
- User subscription management
- Partner API integration for white-label solutions
- Admin marketplace management

Separated from main options trading stack for:
- Better resource management (CloudFormation 500 resource limit)
- Independent scaling and deployment
- Clear separation of concerns
"""

import os
import json
import logging
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    Fn,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_iam as iam,
    aws_logs as logs,
    aws_dynamodb as dynamodb,
    aws_cognito as cognito,
)
from constructs import Construct

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketplaceStack(Stack):
    """
    Options Marketplace Stack for B2B2C Integration

    Features:
    - Marketplace template browsing (public and partner)
    - User subscription management (subscribe, pause, resume, cancel)
    - Partner API integration for white-label brokers
    - Admin marketplace management (enable/disable templates)
    """

    def __init__(self, scope: Construct, construct_id: str,
                 deploy_env: str, config: dict,
                 auth_stack_name: str,
                 options_stack_name: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.deploy_env = deploy_env
        self.config = config
        self.env_config = config['environments'][deploy_env]
        self.company_prefix = config['company']['short_name']
        self.project_name = config['project']

        # Store stack names for imports
        self.auth_stack_name = auth_stack_name
        self.options_stack_name = options_stack_name

        # Import cross-stack references (includes Lambda layer)
        self._import_cross_stack_resources()

        # Create API Gateway (separate from options trading API)
        self._create_api_gateway()

        # Create Lambda functions (uses imported layer)
        self._create_lambda_functions()

        # Create API Gateway resources
        self._create_api_routes()

        # Create stack outputs
        self._create_outputs()

    def get_resource_name(self, resource_name: str) -> str:
        """Generate consistent resource names"""
        return f"{self.company_prefix}-{self.deploy_env}-marketplace-{resource_name}"

    def _import_cross_stack_resources(self):
        """Import resources from auth and options trading stacks"""

        # Import from auth stack
        self.user_pool_id = Fn.import_value(f"{self.auth_stack_name}-UserPoolId")
        self.broker_accounts_table_name = Fn.import_value(f"{self.auth_stack_name}-BrokerAccountsTable")

        # Import from options trading stack
        self.trading_configurations_table_name = Fn.import_value(
            f"{self.options_stack_name}-TradingConfigurationsTable"
        )

        # Import Lambda layer ARN from options trading stack
        self.trading_layer_arn = Fn.import_value(
            f"{self.options_stack_name}-TradingDependenciesLayerArn"
        )

        # Reference existing DynamoDB table (for permissions)
        self.trading_configurations_table = dynamodb.Table.from_table_name(
            self, "ImportedTradingConfigTable",
            self.trading_configurations_table_name
        )

        # Reference Cognito User Pool for authorization
        self.user_pool = cognito.UserPool.from_user_pool_id(
            self, "ImportedUserPool",
            self.user_pool_id
        )

        # Reference existing Lambda layer
        self.shared_layer = _lambda.LayerVersion.from_layer_version_arn(
            self, "ImportedTradingLayer",
            self.trading_layer_arn
        )

        logger.info(f"Imported cross-stack resources from {self.auth_stack_name} and {self.options_stack_name}")

    def _create_api_gateway(self):
        """Create separate API Gateway for marketplace endpoints"""

        self.api = apigateway.RestApi(
            self, f"MarketplaceApi{self.deploy_env.title()}",
            rest_api_name=self.get_resource_name("api"),
            description="Marketplace API for B2B2C Integration",
            deploy_options=apigateway.StageOptions(
                stage_name=self.deploy_env,
                logging_level=apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                metrics_enabled=True,
                throttling_rate_limit=1000,
                throttling_burst_limit=2000
            ),
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=[
                    "Content-Type",
                    "Authorization",
                    "X-Amz-Date",
                    "X-Api-Key",
                    "X-Amz-Security-Token",
                    "X-Partner-Api-Key"  # Custom header for partner API
                ],
                allow_credentials=True
            )
        )

        # Create Cognito authorizer
        self.authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self, f"MarketplaceAuthorizer{self.deploy_env.title()}",
            cognito_user_pools=[self.user_pool],
            authorizer_name=self.get_resource_name("cognito-authorizer")
        )

        logger.info(f"Created Marketplace API Gateway: {self.api.rest_api_name}")

    def _create_lambda_functions(self):
        """Create marketplace Lambda functions"""

        # Base environment variables for all functions
        base_env = {
            "ENVIRONMENT": self.deploy_env,
            "COMPANY_PREFIX": self.company_prefix,
            "PROJECT_NAME": self.project_name,
            "USER_POOL_ID": self.user_pool_id,
            "BROKER_ACCOUNTS_TABLE": self.broker_accounts_table_name,
            "TRADING_CONFIGURATIONS_TABLE": self.trading_configurations_table_name,
            "REGION": self.region,
        }

        # Lambda function configurations
        lambda_configs = [
            {
                "name": "marketplace-manager",
                "handler": "market_place.marketplace_manager.lambda_handler",
                "description": "Marketplace template browsing and admin management",
                "timeout": 30,
                "memory": 256
            },
            {
                "name": "subscription-manager",
                "handler": "market_place.subscription_manager.lambda_handler",
                "description": "User and partner subscription management",
                "timeout": 30,
                "memory": 256
            },
            {
                "name": "partner-api-manager",
                "handler": "market_place.partner_api_manager.lambda_handler",
                "description": "Partner API key management and authentication",
                "timeout": 30,
                "memory": 256
            }
        ]

        self.lambda_functions = {}

        for config in lambda_configs:
            func = _lambda.Function(
                self, f"MarketplaceLambda{config['name'].title().replace('-', '')}{self.deploy_env.title()}",
                function_name=self.get_resource_name(config['name']),
                runtime=_lambda.Runtime.PYTHON_3_11,
                code=_lambda.Code.from_asset("lambda_functions"),
                handler=config['handler'],
                environment=base_env,
                timeout=Duration.seconds(config['timeout']),
                memory_size=config['memory'],
                layers=[self.shared_layer],
                log_retention=logs.RetentionDays.ONE_WEEK if self.env_config['log_retention_days'] == 7
                else logs.RetentionDays.ONE_MONTH if self.env_config['log_retention_days'] == 30
                else logs.RetentionDays.THREE_MONTHS,
                description=config['description']
            )

            # Grant DynamoDB permissions for trading configurations table
            self.trading_configurations_table.grant_read_write_data(func)

            # Grant broker accounts table read access (using ARN-based permissions)
            func.add_to_role_policy(
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

            self.lambda_functions[config['name']] = func
            logger.info(f"Created Lambda function: {config['name']}")

    def _create_api_routes(self):
        """Create API Gateway routes for marketplace"""

        # =============================================================================
        # Marketplace & B2B2C Integration - Admin & User Endpoints
        # Base path: /marketplace
        # =============================================================================

        marketplace_resource = self.api.root.add_resource("marketplace")

        # GET /marketplace/templates - Browse marketplace templates
        templates_resource = marketplace_resource.add_resource("templates")
        templates_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(self.lambda_functions['marketplace-manager']),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=self.authorizer
        )

        # POST /marketplace/subscribe/{basket_id} - Subscribe to template
        subscribe_resource = marketplace_resource.add_resource("subscribe")
        subscribe_basket_resource = subscribe_resource.add_resource("{basket_id}")
        subscribe_basket_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(self.lambda_functions['subscription-manager']),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=self.authorizer
        )

        # =============================================================================
        # User Subscription Management
        # Base path: /subscriptions
        # =============================================================================

        subscriptions_resource = self.api.root.add_resource("subscriptions")

        # GET /subscriptions - Get user's subscriptions
        subscriptions_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(self.lambda_functions['subscription-manager']),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=self.authorizer
        )

        # Subscription management by ID
        subscription_id_resource = subscriptions_resource.add_resource("{subscription_id}")

        # GET /subscriptions/{subscription_id} - Get subscription details
        subscription_id_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(self.lambda_functions['subscription-manager']),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=self.authorizer
        )

        # PUT /subscriptions/{subscription_id} - Update subscription
        subscription_id_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(self.lambda_functions['subscription-manager']),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=self.authorizer
        )

        # DELETE /subscriptions/{subscription_id} - Cancel subscription
        subscription_id_resource.add_method(
            "DELETE",
            apigateway.LambdaIntegration(self.lambda_functions['subscription-manager']),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=self.authorizer
        )

        # PUT /subscriptions/{subscription_id}/pause - Pause subscription
        pause_resource = subscription_id_resource.add_resource("pause")
        pause_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(self.lambda_functions['subscription-manager']),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=self.authorizer
        )

        # PUT /subscriptions/{subscription_id}/resume - Resume subscription
        resume_resource = subscription_id_resource.add_resource("resume")
        resume_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(self.lambda_functions['subscription-manager']),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=self.authorizer
        )

        # =============================================================================
        # Admin Marketplace Management
        # Base path: /admin
        # =============================================================================

        admin_resource = self.api.root.add_resource("admin")
        admin_marketplace_resource = admin_resource.add_resource("marketplace")

        # POST /admin/marketplace/enable/{basket_id} - Enable marketplace for basket
        enable_resource = admin_marketplace_resource.add_resource("enable")
        enable_basket_resource = enable_resource.add_resource("{basket_id}")
        enable_basket_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(self.lambda_functions['marketplace-manager']),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=self.authorizer
        )

        # PUT /admin/marketplace/disable/{basket_id} - Disable marketplace for basket
        disable_resource = admin_marketplace_resource.add_resource("disable")
        disable_basket_resource = disable_resource.add_resource("{basket_id}")
        disable_basket_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(self.lambda_functions['marketplace-manager']),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=self.authorizer
        )

        # Admin Partner API Key Management
        admin_partners_resource = admin_resource.add_resource("partner-api-keys")

        # POST /admin/partner-api-keys - Create partner API key
        admin_partners_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(self.lambda_functions['partner-api-manager']),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=self.authorizer
        )

        # GET /admin/partner-api-keys - List partner API keys
        admin_partners_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(self.lambda_functions['partner-api-manager']),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=self.authorizer
        )

        # PUT /admin/partner-api-keys/{key_id} - Update partner API key
        admin_partner_key_resource = admin_partners_resource.add_resource("{key_id}")
        admin_partner_key_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(self.lambda_functions['partner-api-manager']),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=self.authorizer
        )

        # DELETE /admin/partner-api-keys/{key_id} - Revoke partner API key
        admin_partner_key_resource.add_method(
            "DELETE",
            apigateway.LambdaIntegration(self.lambda_functions['partner-api-manager']),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=self.authorizer
        )

        # =============================================================================
        # Partner API Endpoints (B2B2C White-Label Integration)
        # Base path: /partner
        # No Cognito auth - uses custom Partner API key authentication
        # =============================================================================

        partner_resource = self.api.root.add_resource("partner")
        partner_marketplace_resource = partner_resource.add_resource("marketplace")

        # GET /partner/marketplace/templates - Browse templates via Partner API
        partner_templates_resource = partner_marketplace_resource.add_resource("templates")
        partner_templates_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(self.lambda_functions['marketplace-manager']),
            authorization_type=apigateway.AuthorizationType.NONE
        )

        # POST /partner/marketplace/subscribe - Partner API subscription
        partner_subscribe_resource = partner_marketplace_resource.add_resource("subscribe")
        partner_subscribe_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(self.lambda_functions['subscription-manager']),
            authorization_type=apigateway.AuthorizationType.NONE
        )

        # Partner subscription management endpoints
        partner_subscriptions_resource = partner_resource.add_resource("subscriptions")

        # GET /partner/subscriptions - List all partner subscriptions
        partner_subscriptions_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(self.lambda_functions['subscription-manager']),
            authorization_type=apigateway.AuthorizationType.NONE
        )

        # Partner subscription management by ID
        partner_subscription_id_resource = partner_subscriptions_resource.add_resource("{subscription_id}")

        # GET /partner/subscriptions/{subscription_id} - Get subscription details
        partner_subscription_id_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(self.lambda_functions['subscription-manager']),
            authorization_type=apigateway.AuthorizationType.NONE
        )

        # DELETE /partner/subscriptions/{subscription_id} - Cancel subscription
        partner_subscription_id_resource.add_method(
            "DELETE",
            apigateway.LambdaIntegration(self.lambda_functions['subscription-manager']),
            authorization_type=apigateway.AuthorizationType.NONE
        )

        # PUT /partner/subscriptions/{subscription_id}/pause - Pause subscription
        partner_pause_resource = partner_subscription_id_resource.add_resource("pause")
        partner_pause_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(self.lambda_functions['subscription-manager']),
            authorization_type=apigateway.AuthorizationType.NONE
        )

        # PUT /partner/subscriptions/{subscription_id}/resume - Resume subscription
        partner_resume_resource = partner_subscription_id_resource.add_resource("resume")
        partner_resume_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(self.lambda_functions['subscription-manager']),
            authorization_type=apigateway.AuthorizationType.NONE
        )

        logger.info("Created marketplace API routes")

    def _create_outputs(self):
        """Create stack outputs for cross-stack references"""

        CfnOutput(
            self, "MarketplaceApiUrl",
            value=self.api.url,
            description="Marketplace API Gateway URL",
            export_name=f"{self.stack_name}-MarketplaceApiUrl"
        )

        CfnOutput(
            self, "MarketplaceManagerArn",
            value=self.lambda_functions['marketplace-manager'].function_arn,
            description="Marketplace Manager Lambda ARN",
            export_name=f"{self.stack_name}-MarketplaceManagerArn"
        )

        CfnOutput(
            self, "SubscriptionManagerArn",
            value=self.lambda_functions['subscription-manager'].function_arn,
            description="Subscription Manager Lambda ARN",
            export_name=f"{self.stack_name}-SubscriptionManagerArn"
        )

        CfnOutput(
            self, "PartnerApiManagerArn",
            value=self.lambda_functions['partner-api-manager'].function_arn,
            description="Partner API Manager Lambda ARN",
            export_name=f"{self.stack_name}-PartnerApiManagerArn"
        )
