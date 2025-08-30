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
            self, "AlgoTradingUserPool",
            user_pool_name=self.get_resource_name("users"),
            sign_in_aliases=cognito.SignInAliases(
                email=True,
                phone=True
            ),
            auto_verify=cognito.AutoVerifiedAttrs(
                email=True
            ),
            self_sign_up_enabled=True,  # Enable self-signup for standard signup flow
            email=cognito.UserPoolEmail.with_cognito("quantleapanalytics@gmail.com"),  # Configure email sending
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
            self, "AlgoTradingUserPoolClient",
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

        # DynamoDB table for user profiles
        user_profiles_table = dynamodb.Table(
            self, "UserProfiles",
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

        # DynamoDB table for broker accounts
        broker_accounts_table = dynamodb.Table(
            self, "BrokerAccounts", 
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

        # Lambda function for user registration
        user_registration_lambda = _lambda.Function(
            self, "UserRegistrationFunction",
            function_name=self.get_resource_name("user-registration"),
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda_functions/auth"),
            handler="user_registration.lambda_handler",
            timeout=Duration.seconds(30),
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
            self, "UserAuthFunction",
            function_name=self.get_resource_name("user-auth"),
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda_functions/auth"),
            handler="user_auth.lambda_handler",
            timeout=Duration.seconds(30),
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
            self, "ForgotPasswordFunction",
            function_name=self.get_resource_name("forgot-password"),
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda_functions/auth"),
            handler="forgot_password.lambda_handler",
            timeout=Duration.seconds(30),
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
            self, "ConfirmForgotPasswordFunction",
            function_name=self.get_resource_name("confirm-forgot-password"),
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda_functions/auth"),
            handler="confirm_forgot_password.lambda_handler",
            timeout=Duration.seconds(30),
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
            self, "ResendVerificationFunction",
            function_name=self.get_resource_name("resend-verification"),
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda_functions/auth"),
            handler="resend_verification_code.lambda_handler",
            timeout=Duration.seconds(30),
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
            self, "VerifyEmailFunction",
            function_name=self.get_resource_name("verify-email"),
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda_functions/auth"),
            handler="verify_email.lambda_handler",
            timeout=Duration.seconds(30),
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
            self, "BrokerAccountFunction",
            function_name=self.get_resource_name("broker-accounts"),
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda_functions/broker_accounts"),
            handler="broker_account_manager.lambda_handler",
            timeout=Duration.seconds(30),
            environment={
                "ENVIRONMENT": self.deploy_env,
                "COMPANY_PREFIX": self.company_prefix,
                "PROJECT_NAME": self.project_name,
                "BROKER_ACCOUNTS_TABLE": broker_accounts_table.table_name,
                "REGION": self.region
            }
        )

        # Lambda function for broker OAuth handling
        broker_oauth_lambda = _lambda.Function(
            self, "BrokerOAuthFunction",
            function_name=self.get_resource_name("broker-oauth"),
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda_functions/broker_oauth"),
            handler="zerodha_oauth_handler.lambda_handler",
            timeout=Duration.seconds(30),
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
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:UpdateSecret",
                    "secretsmanager:DescribeSecret"
                ],
                resources=[f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:{self.company_prefix}-*-credentials-{self.deploy_env}-*", f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:{self.company_prefix}-*-oauth-tokens-{self.deploy_env}-*"]
            )
        )

        # API Gateway with Cognito authorizer
        api = apigateway.RestApi(
            self, "AlgoTradingAPI",
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
            self, "CognitoAuthorizer",
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
            self, "AlgoTradingDashboard",
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

        # Outputs
        CfnOutput(
            self, "UserPoolId",
            value=user_pool.user_pool_id,
            description="Cognito User Pool ID"
        )

        CfnOutput(
            self, "UserPoolClientId", 
            value=user_pool_client.user_pool_client_id,
            description="Cognito User Pool Client ID"
        )

        CfnOutput(
            self, "ApiGatewayUrl",
            value=api.url,
            description="API Gateway URL"
        )

        CfnOutput(
            self, "UserProfilesTableName",
            value=user_profiles_table.table_name,
            description="User Profiles DynamoDB Table Name"
        )

        CfnOutput(
            self, "BrokerAccountsTableName",
            value=broker_accounts_table.table_name,
            description="Broker Accounts DynamoDB Table Name"
        )

        CfnOutput(
            self, "DashboardUrl",
            value=f"https://console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={dashboard.dashboard_name}",
            description="CloudWatch Dashboard URL"
        )