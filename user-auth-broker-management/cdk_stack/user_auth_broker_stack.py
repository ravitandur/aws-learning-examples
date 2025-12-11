from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_cognito as cognito,
    aws_dynamodb as dynamodb,
    aws_secretsmanager as secretsmanager,
    aws_iam as iam,
    aws_logs as logs,
    aws_cloudwatch as cloudwatch,
    aws_ec2 as ec2,
    CfnOutput
)
from constructs import Construct
import json
from typing import Dict, Any

class UserAuthBrokerStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, 
                 deploy_env: str, config: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.deploy_env = deploy_env
        self.config = config
        self.company_prefix = config['company']['short_name']
        self.project_name = config['project']
        self.env_config = config['environments'][deploy_env]
        
        # Create all resources
        self.create_resources()
        
    def get_resource_name(self, resource_type: str) -> str:
        """Generate environment-specific resource names with company prefix"""
        return f"{self.company_prefix}-{self.project_name}-{self.deploy_env}-{resource_type}"
        
    def get_removal_policy(self) -> RemovalPolicy:
        """Get environment-specific removal policy"""
        policy = self.env_config['removal_policy']
        return RemovalPolicy.DESTROY if policy == "DESTROY" else RemovalPolicy.RETAIN

    def create_resources(self):
        """Create all AWS resources for the stack"""
        # Cognito User Pool for authentication
        user_pool = cognito.UserPool(
            self, f"AuthUserPool{self.deploy_env.title()}",
            user_pool_name=self.get_resource_name("users"),
            sign_in_aliases=cognito.SignInAliases(
                email=True,
                phone=True
            ),
            auto_verify=cognito.AutoVerifiedAttrs(
                email=True
            ),
            self_sign_up_enabled=True,  # Enable self-signup for standard signup flow
            email=cognito.UserPoolEmail.with_cognito(self.config['company']['email']),  # Configure email sending
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(
                    required=True,
                    mutable=True
                ),
                phone_number=cognito.StandardAttribute(
                    required=True,
                    mutable=True
                ),
                fullname=cognito.StandardAttribute(
                    required=True,
                    mutable=True
                )
            ),
            custom_attributes={
                "state": cognito.StringAttribute(
                    min_len=2,
                    max_len=50,
                    mutable=True
                )
            },
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_AND_PHONE_WITHOUT_MFA,
            removal_policy=self.get_removal_policy()
        )

        # User Pool Client for API access
        user_pool_client = cognito.UserPoolClient(
            self, f"AuthUserPoolClient{self.deploy_env.title()}",
            user_pool=user_pool,
            user_pool_client_name=self.get_resource_name("client"),
            generate_secret=False,  # For frontend applications
            auth_flows=cognito.AuthFlow(
                admin_user_password=True,
                custom=True,
                user_password=True,
                user_srp=True
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                    implicit_code_grant=True
                ),
                scopes=[cognito.OAuthScope.EMAIL, cognito.OAuthScope.OPENID, cognito.OAuthScope.PROFILE],
                callback_urls=self.env_config['cors_origins'] + [url + "/callback" for url in self.env_config['cors_origins'] if not url.startswith('http://localhost')],
                logout_urls=self.env_config['cors_origins'] + [url + "/logout" for url in self.env_config['cors_origins'] if not url.startswith('http://localhost')]
            ),
            access_token_validity=Duration.hours(self.env_config['token_validity_hours']),
            id_token_validity=Duration.hours(self.env_config['token_validity_hours']),
            refresh_token_validity=Duration.days(30)
        )

        # Cognito Admin Group for marketplace management
        admin_group = cognito.CfnUserPoolGroup(
            self, f"AdminGroup{self.deploy_env.title()}",
            user_pool_id=user_pool.user_pool_id,
            group_name="Admins",
            description="Platform administrators with marketplace template management",
            precedence=0  # Highest precedence
        )

        # DynamoDB table for user profiles
        user_profiles_table = dynamodb.Table(
            self, f"AuthUserProfiles{self.deploy_env.title()}",
            table_name=self.get_resource_name("user-profiles"),
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            removal_policy=self.get_removal_policy(),
            point_in_time_recovery=self.env_config['enable_point_in_time_recovery']
        )
        
        # GSI: Active Users Index for efficient active user queries
        # Purpose: Query only active users without scanning entire table
        # Query Pattern: status = "active" → gets only active users
        # Performance: O(active_users) instead of O(all_users)
        # Benefits: Unlimited scalability regardless of total user count
        user_profiles_table.add_global_secondary_index(
            index_name="ActiveUsersIndex",
            partition_key=dynamodb.Attribute(name="status", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="created_at", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.KEYS_ONLY  # Only need user_id, status, created_at
        )

        # DynamoDB table for broker accounts
        broker_accounts_table = dynamodb.Table(
            self, f"AuthBrokerAccounts{self.deploy_env.title()}", 
            table_name=self.get_resource_name("broker-accounts"),
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="client_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            removal_policy=self.get_removal_policy(),
            point_in_time_recovery=self.env_config['enable_point_in_time_recovery']
        )

        # GSI for querying broker accounts by user
        broker_accounts_table.add_global_secondary_index(
            index_name=f"{self.get_resource_name('broker-accounts')}-user-index",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            )
        )

        # VPC for broker API outbound calls with static IP (NAT Gateway)
        # This enables all Lambda functions making external broker API calls to use a single
        # static IP that can be whitelisted by brokers like Zebu
        vpc_config = self.env_config.get('vpc', {})
        broker_vpc = ec2.Vpc(
            self, f"BrokerVpc{self.deploy_env.title()}",
            vpc_name=self.get_resource_name("broker-vpc"),
            ip_addresses=ec2.IpAddresses.cidr(vpc_config.get('cidr', '10.0.0.0/16')),
            max_azs=vpc_config.get('max_azs', 2),
            nat_gateways=vpc_config.get('nat_gateways', 1),
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ]
        )

        # VPC Endpoints for AWS services (reduces NAT traffic and cost)
        # DynamoDB uses Gateway Endpoint (free)
        broker_vpc.add_gateway_endpoint(
            "DynamoDBEndpoint",
            service=ec2.GatewayVpcEndpointAwsService.DYNAMODB
        )

        # Secrets Manager uses Interface Endpoint (reduces NAT traffic)
        if vpc_config.get('enable_vpc_endpoints', True):
            broker_vpc.add_interface_endpoint(
                "SecretsManagerEndpoint",
                service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER
            )

        # Security group for Lambda functions that need to call external broker APIs
        broker_lambda_sg = ec2.SecurityGroup(
            self, f"BrokerLambdaSG{self.deploy_env.title()}",
            vpc=broker_vpc,
            security_group_name=self.get_resource_name("broker-lambda-sg"),
            description="Security group for broker API Lambda functions",
            allow_all_outbound=True  # Allow outbound to broker APIs
        )

        # Lambda functions with logRetention (avoids redeploy LogGroup errors)
        # Removed explicit LogGroup creation to prevent "LogGroup already exists" errors on redeploy

        # Lambda function for user registration
        user_registration_lambda = _lambda.Function(
            self, f"AuthLambdaUserRegistration{self.deploy_env.title()}",
            function_name=self.get_resource_name("auth-user-registration"),
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("lambda_functions/auth"),
            handler="user_registration.lambda_handler",
            timeout=Duration.seconds(30),
            log_retention=logs.RetentionDays.ONE_WEEK if self.env_config['log_retention_days'] == 7 
                           else logs.RetentionDays.ONE_MONTH if self.env_config['log_retention_days'] == 30 
                           else logs.RetentionDays.THREE_MONTHS,
            environment={
                "ENVIRONMENT": self.deploy_env,
                "COMPANY_PREFIX": self.company_prefix,
                "PROJECT_NAME": self.project_name,
                "USER_POOL_ID": user_pool.user_pool_id,
                "USER_POOL_CLIENT_ID": user_pool_client.user_pool_client_id,
                "USER_PROFILES_TABLE": user_profiles_table.table_name,
                "REGION": self.region
            }
        )

        # Lambda function for user authentication
        user_auth_lambda = _lambda.Function(
            self, f"AuthLambdaUserAuth{self.deploy_env.title()}",
            function_name=self.get_resource_name("auth-user-auth"),
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("lambda_functions/auth"),
            handler="user_auth.lambda_handler",
            timeout=Duration.seconds(30),
            log_retention=logs.RetentionDays.ONE_WEEK if self.env_config['log_retention_days'] == 7 
                           else logs.RetentionDays.ONE_MONTH if self.env_config['log_retention_days'] == 30 
                           else logs.RetentionDays.THREE_MONTHS,
            environment={
                "ENVIRONMENT": self.deploy_env,
                "COMPANY_PREFIX": self.company_prefix,
                "PROJECT_NAME": self.project_name,
                "USER_POOL_ID": user_pool.user_pool_id,
                "USER_POOL_CLIENT_ID": user_pool_client.user_pool_client_id,
                "REGION": self.region
            }
        )

        # Lambda function for forgot password
        forgot_password_lambda = _lambda.Function(
            self, f"AuthLambdaForgotPassword{self.deploy_env.title()}",
            function_name=self.get_resource_name("auth-forgot-password"),
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("lambda_functions/auth"),
            handler="forgot_password.lambda_handler",
            timeout=Duration.seconds(30),
            log_retention=logs.RetentionDays.ONE_WEEK if self.env_config['log_retention_days'] == 7 
                           else logs.RetentionDays.ONE_MONTH if self.env_config['log_retention_days'] == 30 
                           else logs.RetentionDays.THREE_MONTHS,
            environment={
                "ENVIRONMENT": self.deploy_env,
                "COMPANY_PREFIX": self.company_prefix,
                "PROJECT_NAME": self.project_name,
                "USER_POOL_ID": user_pool.user_pool_id,
                "USER_POOL_CLIENT_ID": user_pool_client.user_pool_client_id,
                "REGION": self.region
            }
        )

        # Lambda function for confirm forgot password
        confirm_forgot_password_lambda = _lambda.Function(
            self, f"AuthLambdaConfirmForgotPassword{self.deploy_env.title()}",
            function_name=self.get_resource_name("auth-confirm-forgot-password"),
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("lambda_functions/auth"),
            handler="confirm_forgot_password.lambda_handler",
            timeout=Duration.seconds(30),
            log_retention=logs.RetentionDays.ONE_WEEK if self.env_config['log_retention_days'] == 7 
                           else logs.RetentionDays.ONE_MONTH if self.env_config['log_retention_days'] == 30 
                           else logs.RetentionDays.THREE_MONTHS,
            environment={
                "ENVIRONMENT": self.deploy_env,
                "COMPANY_PREFIX": self.company_prefix,
                "PROJECT_NAME": self.project_name,
                "USER_POOL_ID": user_pool.user_pool_id,
                "USER_POOL_CLIENT_ID": user_pool_client.user_pool_client_id,
                "REGION": self.region
            }
        )

        # Lambda function for resend verification code
        resend_verification_lambda = _lambda.Function(
            self, f"AuthLambdaResendVerification{self.deploy_env.title()}",
            function_name=self.get_resource_name("auth-resend-verification"),
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("lambda_functions/auth"),
            handler="resend_verification_code.lambda_handler",
            timeout=Duration.seconds(30),
            log_retention=logs.RetentionDays.ONE_WEEK if self.env_config['log_retention_days'] == 7 
                           else logs.RetentionDays.ONE_MONTH if self.env_config['log_retention_days'] == 30 
                           else logs.RetentionDays.THREE_MONTHS,
            environment={
                "ENVIRONMENT": self.deploy_env,
                "COMPANY_PREFIX": self.company_prefix,
                "PROJECT_NAME": self.project_name,
                "USER_POOL_ID": user_pool.user_pool_id,
                "USER_POOL_CLIENT_ID": user_pool_client.user_pool_client_id,
                "REGION": self.region
            }
        )

        # Lambda function for verify email
        verify_email_lambda = _lambda.Function(
            self, f"AuthLambdaVerifyEmail{self.deploy_env.title()}",
            function_name=self.get_resource_name("auth-verify-email"),
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("lambda_functions/auth"),
            handler="verify_email.lambda_handler",
            timeout=Duration.seconds(30),
            log_retention=logs.RetentionDays.ONE_WEEK if self.env_config['log_retention_days'] == 7 
                           else logs.RetentionDays.ONE_MONTH if self.env_config['log_retention_days'] == 30 
                           else logs.RetentionDays.THREE_MONTHS,
            environment={
                "ENVIRONMENT": self.deploy_env,
                "COMPANY_PREFIX": self.company_prefix,
                "PROJECT_NAME": self.project_name,
                "USER_POOL_ID": user_pool.user_pool_id,
                "USER_POOL_CLIENT_ID": user_pool_client.user_pool_client_id,
                "REGION": self.region
            }
        )

        # Lambda function for broker account management
        broker_account_lambda = _lambda.Function(
            self, f"AuthLambdaBrokerAccount{self.deploy_env.title()}",
            function_name=self.get_resource_name("auth-broker-account"),
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("lambda_functions/broker_accounts"),
            handler="broker_account_manager.lambda_handler",
            timeout=Duration.seconds(30),
            log_retention=logs.RetentionDays.ONE_WEEK if self.env_config['log_retention_days'] == 7 
                           else logs.RetentionDays.ONE_MONTH if self.env_config['log_retention_days'] == 30 
                           else logs.RetentionDays.THREE_MONTHS,
            environment={
                "ENVIRONMENT": self.deploy_env,
                "COMPANY_PREFIX": self.company_prefix,
                "PROJECT_NAME": self.project_name,
                "BROKER_ACCOUNTS_TABLE": broker_accounts_table.table_name,
                "REGION": self.region
            }
        )

        # Lambda function for broker OAuth handling
        # Placed in VPC with NAT Gateway for static IP (required for broker IP whitelisting)
        broker_oauth_lambda = _lambda.Function(
            self, f"AuthLambdaBrokerOauth{self.deploy_env.title()}",
            function_name=self.get_resource_name("auth-broker-oauth"),
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("lambda_functions/broker_oauth", bundling={
                "image": _lambda.Runtime.PYTHON_3_11.bundling_image,
                "command": [
                    "bash", "-c",
                    "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output"
                ]
            }),
            handler="refactored_oauth_handler.lambda_handler",
            timeout=Duration.seconds(30),
            log_retention=logs.RetentionDays.ONE_WEEK if self.env_config['log_retention_days'] == 7
                           else logs.RetentionDays.ONE_MONTH if self.env_config['log_retention_days'] == 30
                           else logs.RetentionDays.THREE_MONTHS,
            vpc=broker_vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[broker_lambda_sg],
            environment={
                "ENVIRONMENT": self.deploy_env,
                "STAGE": self.deploy_env,
                "COMPANY_PREFIX": self.company_prefix,
                "PROJECT_NAME": self.project_name,
                "BROKER_ACCOUNTS_TABLE": broker_accounts_table.table_name,
                "REGION": self.region
            }
        )

        # Lambda function for broker connection testing
        # Placed in VPC with NAT Gateway for static IP (required for broker IP whitelisting)
        broker_connection_test_lambda = _lambda.Function(
            self, f"AuthLambdaBrokerConnectionTest{self.deploy_env.title()}",
            function_name=self.get_resource_name("auth-broker-connection-test"),
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("lambda_functions/broker_accounts"),
            handler="connection_tester.lambda_handler",
            timeout=Duration.seconds(30),
            log_retention=logs.RetentionDays.ONE_WEEK if self.env_config['log_retention_days'] == 7
                           else logs.RetentionDays.ONE_MONTH if self.env_config['log_retention_days'] == 30
                           else logs.RetentionDays.THREE_MONTHS,
            vpc=broker_vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[broker_lambda_sg],
            environment={
                "ENVIRONMENT": self.deploy_env,
                "COMPANY_PREFIX": self.company_prefix,
                "PROJECT_NAME": self.project_name,
                "BROKER_ACCOUNTS_TABLE": broker_accounts_table.table_name,
                "REGION": self.region
            }
        )

        # Grant permissions to Lambda functions
        user_profiles_table.grant_read_write_data(user_registration_lambda)
        broker_accounts_table.grant_read_write_data(broker_account_lambda)
        broker_accounts_table.grant_read_write_data(broker_oauth_lambda)
        broker_accounts_table.grant_read_data(broker_connection_test_lambda)
        
        # Grant Cognito permissions
        user_registration_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cognito-idp:AdminCreateUser",
                    "cognito-idp:AdminSetUserPassword",
                    "cognito-idp:AdminUpdateUserAttributes",
                    "cognito-idp:AdminGetUser",
                    "cognito-idp:AdminDeleteUser",
                    "cognito-idp:SignUp"
                ],
                resources=[user_pool.user_pool_arn]
            )
        )

        user_auth_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cognito-idp:AdminInitiateAuth",
                    "cognito-idp:AdminRespondToAuthChallenge",
                    "cognito-idp:AdminGetUser"
                ],
                resources=[user_pool.user_pool_arn]
            )
        )

        # Grant Cognito permissions for forgot password Lambda functions
        forgot_password_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cognito-idp:ForgotPassword"
                ],
                resources=[user_pool.user_pool_arn]
            )
        )

        confirm_forgot_password_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cognito-idp:ConfirmForgotPassword"
                ],
                resources=[user_pool.user_pool_arn]
            )
        )

        # Grant Cognito permissions for verification Lambda functions
        resend_verification_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cognito-idp:ResendConfirmationCode",
                    "cognito-idp:ListUsers",
                    "cognito-idp:AdminUpdateUserAttributes",
                    "cognito-idp:GetUserAttributeVerificationCode"
                ],
                resources=[user_pool.user_pool_arn]
            )
        )

        verify_email_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cognito-idp:ConfirmSignUp",
                    "cognito-idp:ListUsers",
                    "cognito-idp:AdminUpdateUserAttributes",
                    "cognito-idp:AdminConfirmSignUp",
                    "cognito-idp:VerifyUserAttribute"
                ],
                resources=[user_pool.user_pool_arn]
            )
        )

        # Grant Secrets Manager permissions for broker credentials
        broker_account_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:CreateSecret",
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:UpdateSecret",
                    "secretsmanager:DeleteSecret",
                    "secretsmanager:DescribeSecret"
                ],
                resources=[f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:{self.company_prefix}-*-credentials-{self.deploy_env}-*", f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:{self.company_prefix}-*-oauth-tokens-{self.deploy_env}-*"]
            )
        )

        # Grant Secrets Manager permissions for OAuth Lambda
        broker_oauth_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:CreateSecret",
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:UpdateSecret",
                    "secretsmanager:DescribeSecret"
                ],
                resources=[f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:{self.company_prefix}-*-credentials-{self.deploy_env}-*", f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:{self.company_prefix}-*-oauth-tokens-{self.deploy_env}-*"]
            )
        )

        # Grant Secrets Manager permissions for connection testing Lambda
        broker_connection_test_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue"
                ],
                resources=[f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:{self.company_prefix}-*-credentials-{self.deploy_env}-*"]
            )
        )

        # API Gateway with Cognito authorizer
        api = apigateway.RestApi(
            self, f"AuthApiGateway{self.deploy_env.title()}",
            rest_api_name=self.get_resource_name("api"),
            description=f"API for {self.config['company']['name']} algorithmic trading platform - {self.deploy_env} environment",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=self.env_config['cors_origins'],
                allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                allow_headers=["Content-Type", "Authorization", "X-Requested-With"]
            ),
            deploy_options=apigateway.StageOptions(
                stage_name=self.deploy_env,
                description=f"API Gateway stage for {self.deploy_env} environment"
            )
        )

        # Cognito authorizer for API Gateway
        cognito_authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self, f"AuthCognitoAuthorizer{self.deploy_env.title()}",
            cognito_user_pools=[user_pool]
        )

        # Auth endpoints (no authorization required)
        auth_resource = api.root.add_resource("auth")
        
        auth_resource.add_resource("register").add_method(
            "POST",
            apigateway.LambdaIntegration(user_registration_lambda)
        )
        
        auth_resource.add_resource("login").add_method(
            "POST", 
            apigateway.LambdaIntegration(user_auth_lambda)
        )
        
        # Forgot password endpoints (no authorization required)
        auth_resource.add_resource("forgot-password").add_method(
            "POST",
            apigateway.LambdaIntegration(forgot_password_lambda)
        )
        
        auth_resource.add_resource("confirm-forgot-password").add_method(
            "POST",
            apigateway.LambdaIntegration(confirm_forgot_password_lambda)
        )

        # Verification endpoints (no authorization required)
        auth_resource.add_resource("resend-verification").add_method(
            "POST",
            apigateway.LambdaIntegration(resend_verification_lambda)
        )
        
        auth_resource.add_resource("verify-email").add_method(
            "POST",
            apigateway.LambdaIntegration(verify_email_lambda)
        )

        # Broker account endpoints (authorization required)
        broker_resource = api.root.add_resource("broker-accounts")
        
        broker_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(broker_account_lambda),
            authorizer=cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        broker_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(broker_account_lambda),
            authorizer=cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )

        # Individual broker account operations
        broker_account_resource = broker_resource.add_resource("{client_id}")
        
        broker_account_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(broker_account_lambda),
            authorizer=cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        broker_account_resource.add_method(
            "DELETE",
            apigateway.LambdaIntegration(broker_account_lambda),
            authorizer=cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # Connection test endpoint for broker accounts
        verify_resource = broker_account_resource.add_resource("verify")
        
        verify_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(broker_connection_test_lambda),
            authorizer=cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # OAuth endpoints for broker authentication
        oauth_resource = broker_account_resource.add_resource("oauth")
        oauth_action_resource = oauth_resource.add_resource("{oauth_action}")
        
        oauth_action_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(broker_oauth_lambda),
            authorizer=cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        oauth_action_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(broker_oauth_lambda),
            authorizer=cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )

        # CloudWatch Dashboard for monitoring
        dashboard = cloudwatch.Dashboard(
            self, f"AuthDashboard{self.deploy_env.title()}",
            dashboard_name=f"{self.env_config['dashboard_prefix']}-{self.get_resource_name('dashboard')}",
            widgets=[
                [
                    # API Gateway metrics
                    cloudwatch.GraphWidget(
                        title=f"API Gateway Requests - {self.deploy_env.title()}",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/ApiGateway",
                                metric_name="Count",
                                dimensions_map={
                                    "ApiName": api.rest_api_name
                                },
                                statistic="Sum",
                                period=Duration.minutes(5)
                            ),
                            cloudwatch.Metric(
                                namespace="AWS/ApiGateway", 
                                metric_name="4XXError",
                                dimensions_map={
                                    "ApiName": api.rest_api_name
                                },
                                statistic="Sum",
                                period=Duration.minutes(5)
                            )
                        ],
                        width=6,
                        height=6
                    ),
                    # Lambda metrics
                    cloudwatch.GraphWidget(
                        title=f"Lambda Invocations - {self.deploy_env.title()}",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/Lambda",
                                metric_name="Invocations",
                                dimensions_map={
                                    "FunctionName": user_registration_lambda.function_name
                                },
                                statistic="Sum",
                                period=Duration.minutes(5)
                            ),
                            cloudwatch.Metric(
                                namespace="AWS/Lambda",
                                metric_name="Invocations", 
                                dimensions_map={
                                    "FunctionName": broker_account_lambda.function_name
                                },
                                statistic="Sum",
                                period=Duration.minutes(5)
                            )
                        ],
                        width=6,
                        height=6
                    )
                ]
            ]
        )

        # Environment-specific outputs
        CfnOutput(
            self, "Environment",
            value=self.deploy_env,
            description="Deployment Environment"
        )

        CfnOutput(
            self, "CompanyPrefix", 
            value=self.company_prefix,
            description="Company Resource Prefix"
        )

        # Outputs with exports for cross-stack integration
        CfnOutput(
            self, "UserPoolId",
            value=user_pool.user_pool_id,
            description="Cognito User Pool ID",
            export_name=f"{self.stack_name}-UserPoolId"
        )

        CfnOutput(
            self, "UserPoolClientId", 
            value=user_pool_client.user_pool_client_id,
            description="Cognito User Pool Client ID",
            export_name=f"{self.stack_name}-UserPoolClientId"
        )

        CfnOutput(
            self, "ApiGatewayUrl",
            value=api.url,
            description="API Gateway URL",
            export_name=f"{self.stack_name}-ApiUrl"
        )

        CfnOutput(
            self, "UserProfilesTableName",
            value=user_profiles_table.table_name,
            description="User Profiles DynamoDB Table Name",
            export_name=f"{self.stack_name}-UserProfilesTable"
        )

        CfnOutput(
            self, "BrokerAccountsTableName",
            value=broker_accounts_table.table_name,
            description="Broker Accounts DynamoDB Table Name",
            export_name=f"{self.stack_name}-BrokerAccountsTable"
        )

        CfnOutput(
            self, "DashboardUrl",
            value=f"https://console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={dashboard.dashboard_name}",
            description="CloudWatch Dashboard URL"
        )

        # VPC outputs for cross-stack usage (options trading stack can import for broker execution)
        CfnOutput(
            self, "BrokerVpcId",
            value=broker_vpc.vpc_id,
            description="VPC ID for broker API Lambda functions",
            export_name=f"{self.stack_name}-BrokerVpcId"
        )

        CfnOutput(
            self, "BrokerVpcPrivateSubnets",
            value=",".join([subnet.subnet_id for subnet in broker_vpc.private_subnets]),
            description="Private subnet IDs for broker Lambda functions",
            export_name=f"{self.stack_name}-BrokerVpcPrivateSubnets"
        )

        CfnOutput(
            self, "BrokerLambdaSecurityGroup",
            value=broker_lambda_sg.security_group_id,
            description="Security group ID for broker Lambda functions",
            export_name=f"{self.stack_name}-BrokerLambdaSG"
        )

        # Note: NAT Gateway Elastic IP can be found via AWS Console (VPC > NAT Gateways)
        # or via CLI: aws ec2 describe-nat-gateways --profile account2 --region ap-south-1
        # This IP should be provided to Zebu for whitelisting