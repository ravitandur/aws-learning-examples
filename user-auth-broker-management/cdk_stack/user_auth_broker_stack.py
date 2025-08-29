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

class UserAuthBrokerStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Cognito User Pool for authentication
        user_pool = cognito.UserPool(
            self, "AlgoTradingUserPool",
            user_pool_name="algo-trading-users",
            sign_in_aliases=cognito.SignInAliases(
                email=True,
                phone=True
            ),
            auto_verify=cognito.AutoVerifiedAttrs(
                email=True,
                phone=True
            ),
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
            removal_policy=RemovalPolicy.DESTROY  # For learning environment
        )

        # User Pool Client for API access
        user_pool_client = cognito.UserPoolClient(
            self, "AlgoTradingUserPoolClient",
            user_pool=user_pool,
            user_pool_client_name="algo-trading-client",
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
                callback_urls=["http://localhost:3000/callback"],  # For testing
                logout_urls=["http://localhost:3000/logout"]
            ),
            access_token_validity=Duration.hours(1),
            id_token_validity=Duration.hours(1),
            refresh_token_validity=Duration.days(30)
        )

        # DynamoDB table for user profiles
        user_profiles_table = dynamodb.Table(
            self, "UserProfiles",
            table_name="user-profiles",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,  # For learning environment
            point_in_time_recovery=True
        )

        # DynamoDB table for broker accounts
        broker_accounts_table = dynamodb.Table(
            self, "BrokerAccounts", 
            table_name="broker-accounts",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="broker_account_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,  # For learning environment
            point_in_time_recovery=True
        )

        # GSI for querying broker accounts by user
        broker_accounts_table.add_global_secondary_index(
            index_name="UserBrokerAccountsIndex",
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
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda_functions/auth"),
            handler="user_registration.lambda_handler",
            timeout=Duration.seconds(30),
            environment={
                "USER_POOL_ID": user_pool.user_pool_id,
                "USER_PROFILES_TABLE": user_profiles_table.table_name,
                "REGION": self.region
            }
        )

        # Lambda function for user authentication
        user_auth_lambda = _lambda.Function(
            self, "UserAuthFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda_functions/auth"),
            handler="user_auth.lambda_handler",
            timeout=Duration.seconds(30),
            environment={
                "USER_POOL_ID": user_pool.user_pool_id,
                "USER_POOL_CLIENT_ID": user_pool_client.user_pool_client_id,
                "REGION": self.region
            }
        )

        # Lambda function for broker account management
        broker_account_lambda = _lambda.Function(
            self, "BrokerAccountFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda_functions/broker_accounts"),
            handler="broker_account_manager.lambda_handler",
            timeout=Duration.seconds(30),
            environment={
                "BROKER_ACCOUNTS_TABLE": broker_accounts_table.table_name,
                "REGION": self.region
            }
        )

        # Grant permissions to Lambda functions
        user_profiles_table.grant_read_write_data(user_registration_lambda)
        broker_accounts_table.grant_read_write_data(broker_account_lambda)
        
        # Grant Cognito permissions
        user_registration_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cognito-idp:AdminCreateUser",
                    "cognito-idp:AdminSetUserPassword",
                    "cognito-idp:AdminUpdateUserAttributes",
                    "cognito-idp:AdminGetUser",
                    "cognito-idp:AdminDeleteUser"
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
                resources=[f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:zerodha-credentials-*"]
            )
        )

        # API Gateway with Cognito authorizer
        api = apigateway.RestApi(
            self, "AlgoTradingAPI",
            rest_api_name="algo-trading-api",
            description="API for algorithmic trading platform user management",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=["http://localhost:3000"],  # For testing
                allow_methods=["GET", "POST", "PUT", "DELETE"],
                allow_headers=["Content-Type", "Authorization"]
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
        broker_account_resource = broker_resource.add_resource("{broker_account_id}")
        
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

        # CloudWatch Dashboard for monitoring
        dashboard = cloudwatch.Dashboard(
            self, "AlgoTradingDashboard",
            dashboard_name="AlgoTrading-UserAuth-Dashboard",
            widgets=[
                [
                    # API Gateway metrics
                    cloudwatch.GraphWidget(
                        title="API Gateway Requests",
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
                        title="Lambda Function Invocations",
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