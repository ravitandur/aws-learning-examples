# CDK Stack Creation Agent

## Purpose
This agent specializes in creating AWS CDK stack files that follow consistent naming conventions, configuration patterns, and best practices while avoiding hardcoded values.

## Core Principles

### 1. Zero Hardcoded Values
- Never hardcode company prefixes like "ql-"
- Never hardcode project names like "algo-trading" 
- Never hardcode email addresses or domains
- All values must come from configuration files
- Use parameterized patterns for all resource naming

### 2. Consistent Naming Conventions
- **Resource Naming**: `{company_prefix}-{project_name}-{environment}-{resource_type}`
- **Stack Names**: `{company_prefix}-{project_name}-{environment}-{module}-stack`
- **Construct IDs**: PascalCase with environment suffix where needed
- **Function Names**: Use `get_resource_name(resource_type)` method

### 3. Configuration-Driven Design
- All environment-specific values from `shared_config/environments.json`
- Company and project details from config
- Cross-stack dependencies parameterized
- Environment policies (DESTROY/RETAIN) from config

### 4. Lambda Logging Pattern (CORRECTED)
- **ISSUE**: Explicit LogGroup creation causes "LogGroup already exists" errors on redeploy
- **SOLUTION**: Use `logRetention` parameter (simpler, more reliable, handles redeploys)
- **DEPRECATION**: `logRetention` shows warning but works correctly and avoids redeploy issues
- **NAMING**: LogGroups auto-created as `/aws/lambda/{function-name}` with proper retention

### 5. Standard Lambda Runtime
- **DEFAULT RUNTIME**: Always use `_lambda.Runtime.PYTHON_3_11` for all Lambda functions
- **NO EXCEPTIONS**: Never use older Python versions (3.9, 3.10) without explicit justification
- **CONSISTENCY**: All Lambda functions in a stack must use the same Python runtime
- **FUTURE-PROOF**: Python 3.11 provides better performance and latest security patches

### 6. Consistent Naming Pattern Requirements
- **MODULE PREFIX CONSISTENCY**: Both construct IDs and resource names MUST follow consistent module-prefix patterns across ALL resources in a stack
- **LOGGROUP CONSTRUCT PATTERN**: Use `{ModulePrefix}Lambda{FunctionName}LogGroup{Environment}` format (e.g., `AuthLambdaUserRegistrationLogGroupDev`, `OptionsLambdaBasketManagerLogGroupDev`)
- **LAMBDA CONSTRUCT PATTERN**: Use `{ModulePrefix}Lambda{FunctionName}{Environment}` format (e.g., `AuthLambdaUserRegistrationDev`, `OptionsLambdaBasketManagerDev`)
- **RESOURCE NAME PATTERN**: Use `{module-prefix}-{function-name}` format for all resource names (e.g., `auth-user-registration`, `options-basket-manager`)
- **MODULE IDENTIFICATION**: Each stack must use a consistent module prefix throughout (Auth, Options, Market, Trading, etc.)
- **CROSS-STACK ALIGNMENT**: All stacks within a project must follow the same naming pattern approach
- **NO MIXED PATTERNS**: Never mix simple descriptive names with module-prefixed patterns within the same stack
- **ENFORCEMENT**: Reject any stack that mixes patterns like `"UserRegistrationFunctionLogGroup"` with `"OptionsLambdaMarketDataLogGroupDev"`

## Required Configuration Schema

```json
{
  "company": {
    "name": "Company Name",
    "short_name": "prefix",
    "email": "company@domain.com"
  },
  "project": "project-name",
  "environments": {
    "dev": {
      "removal_policy": "DESTROY",
      "cors_origins": ["http://localhost:3000"],
      "log_retention_days": 7,
      "token_validity_hours": 24,
      "dashboard_prefix": "Dev",
      "enable_point_in_time_recovery": false
    },
    "staging": {
      "removal_policy": "RETAIN",
      "cors_origins": ["https://staging.example.com"],
      "log_retention_days": 30,
      "token_validity_hours": 8,
      "dashboard_prefix": "Staging", 
      "enable_point_in_time_recovery": true
    },
    "production": {
      "removal_policy": "RETAIN",
      "cors_origins": ["https://example.com"],
      "log_retention_days": 90,
      "token_validity_hours": 1,
      "dashboard_prefix": "Prod",
      "enable_point_in_time_recovery": true
    }
  },
  "aws": {
    "default_region": "ap-south-1",
    "default_profile": "default"
  }
}
```

## Stack Template Structure

```python
from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_iam as iam,
    aws_cognito as cognito,
    aws_logs as logs,
    Duration,
    RemovalPolicy,
    CfnOutput,
    Fn
)
from constructs import Construct
from typing import Dict, Any


class ExampleStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, 
                 deploy_env: str, config: Dict[str, Any], 
                 dependency_stack_name: str = None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Store configuration (NEVER hardcode)
        self.deploy_env = deploy_env
        self.config = config
        self.company_prefix = config['company']['short_name']
        self.project_name = config['project']
        self.env_config = config['environments'][deploy_env]
        
        # Cross-stack dependencies (if needed)
        if dependency_stack_name:
            self.dependency_stack_name = dependency_stack_name
            self._import_dependencies()
        
        # Create resources in logical order
        self._create_dynamodb_tables()
        self._create_lambda_functions()
        self._create_api_gateway()
        self._create_outputs()
    
    def get_resource_name(self, resource_type: str) -> str:
        """Generate environment-specific resource names with company prefix"""
        return f"{self.company_prefix}-{self.project_name}-{self.deploy_env}-{resource_type}"
        
    def get_removal_policy(self) -> RemovalPolicy:
        """Get environment-specific removal policy"""
        policy = self.env_config['removal_policy']
        return RemovalPolicy.DESTROY if policy == "DESTROY" else RemovalPolicy.RETAIN
    
    def _import_dependencies(self):
        """Import resources from dependency stacks"""
        # Example cross-stack imports
        self.imported_user_pool_id = Fn.import_value(f"{self.dependency_stack_name}-UserPoolId")
        self.imported_table_name = Fn.import_value(f"{self.dependency_stack_name}-TableName")
    
    def _create_dynamodb_tables(self):
        """Create DynamoDB tables following standard patterns"""
        # Example table creation
        self.example_table = dynamodb.Table(
            self, f"ExampleTable{self.deploy_env.title()}",
            table_name=self.get_resource_name("example-table"),
            partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="sk", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=self.get_removal_policy(),
            point_in_time_recovery=self.env_config.get('enable_point_in_time_recovery', False),
        )
    
    def _create_lambda_functions(self):
        """Create Lambda functions with standardized configuration"""
        # Standard Lambda environment variables
        lambda_env = {
            "ENVIRONMENT": self.deploy_env,
            "COMPANY_PREFIX": self.company_prefix,
            "PROJECT_NAME": self.project_name,
            "REGION": self.region,
            "EXAMPLE_TABLE": self.example_table.table_name,
        }
        
        # Add imported resources if available
        if hasattr(self, 'imported_user_pool_id'):
            lambda_env["USER_POOL_ID"] = self.imported_user_pool_id
        
        # Create LogGroup explicitly (replaces deprecated logRetention)
        log_group = logs.LogGroup(
            self, f"ExampleFunctionLogGroup{self.deploy_env.title()}",
            log_group_name=f"/aws/lambda/{self.get_resource_name('example-function')}",
            retention=logs.RetentionDays.ONE_WEEK if self.env_config['log_retention_days'] == 7 
                      else logs.RetentionDays.ONE_MONTH if self.env_config['log_retention_days'] == 30 
                      else logs.RetentionDays.THREE_MONTHS,
            removal_policy=self.get_removal_policy()
        )
        
        self.example_function = _lambda.Function(
            self, f"ExampleFunction{self.deploy_env.title()}",
            function_name=self.get_resource_name("example-function"),
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("lambda_functions/example"),
            handler="handler.lambda_handler",
            environment=lambda_env,
            timeout=Duration.seconds(30),
            memory_size=512,
            log_group=log_group,  # Use LogGroup instead of deprecated logRetention
            description="Example function for the stack"
        )
        
        # Grant table permissions
        self.example_table.grant_read_write_data(self.example_function)
    
    def _create_api_gateway(self):
        """Create API Gateway with standard configuration"""
        self.api = apigateway.RestApi(
            self, f"ExampleApi{self.deploy_env.title()}",
            rest_api_name=self.get_resource_name("api"),
            description=f"{self.config['company']['name']} API - {self.deploy_env} environment",
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
        
        # Create Cognito authorizer if User Pool is imported
        if hasattr(self, 'imported_user_pool_id'):
            user_pool = cognito.UserPool.from_user_pool_id(
                self, f"ImportedUserPool{self.deploy_env.title()}",
                user_pool_id=self.imported_user_pool_id
            )
            
            authorizer = apigateway.CognitoUserPoolsAuthorizer(
                self, f"ApiAuthorizer{self.deploy_env.title()}",
                cognito_user_pools=[user_pool],
                authorizer_name=f"{self.company_prefix}-{self.project_name}-authorizer-{self.deploy_env}",
            )
        
        # Create API resources and methods
        example_resource = self.api.root.add_resource("example")
        example_resource.add_method("GET", 
            apigateway.LambdaIntegration(self.example_function),
            authorization_type=apigateway.AuthorizationType.COGNITO if hasattr(self, 'imported_user_pool_id') else apigateway.AuthorizationType.NONE,
            authorizer=authorizer if 'authorizer' in locals() else None
        )
    
    def _create_outputs(self):
        """Create CloudFormation outputs with consistent naming"""
        CfnOutput(
            self, "ApiGatewayUrl",
            value=self.api.url,
            description="API Gateway URL",
            export_name=f"{self.stack_name}-ApiUrl"
        )
        
        CfnOutput(
            self, "ExampleTableName", 
            value=self.example_table.table_name,
            description="Example DynamoDB Table Name",
            export_name=f"{self.stack_name}-ExampleTable"
        )
```

## Resource Patterns

### DynamoDB Table Pattern
```python
table = dynamodb.Table(
    self, f"TableName{self.deploy_env.title()}",
    table_name=self.get_resource_name("table-name"),
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    sort_key=dynamodb.Attribute(name="sk", type=dynamodb.AttributeType.STRING),  # Optional
    billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
    removal_policy=self.get_removal_policy(),
    point_in_time_recovery=self.env_config.get('enable_point_in_time_recovery', False),
    stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,  # If needed
)

# Add GSI if needed
table.add_global_secondary_index(
    index_name="GSIName",
    partition_key=dynamodb.Attribute(name="gsi_pk", type=dynamodb.AttributeType.STRING),
    sort_key=dynamodb.Attribute(name="gsi_sk", type=dynamodb.AttributeType.STRING),
)
```

### Lambda Function Pattern (CORRECTED - Use logRetention)
```python
# ✅ RECOMMENDED: Use logRetention parameter (handles redeploys gracefully)
# ISSUE RESOLVED: Avoids "LogGroup already exists" errors on redeploy

lambda_function = _lambda.Function(
    self, f"OptionsLambdaFunctionName{self.deploy_env.title()}",  # Module-prefixed construct ID
    function_name=self.get_resource_name("options-function-name"),  # Module-prefixed resource name
    runtime=_lambda.Runtime.PYTHON_3_11,  # 🚨 MANDATORY: Always Python 3.11 (never 3.9, 3.10)
    code=_lambda.Code.from_asset("lambda_functions/folder"),
    handler="module.lambda_handler",
    environment={
        "ENVIRONMENT": self.deploy_env,
        "COMPANY_PREFIX": self.company_prefix,
        "PROJECT_NAME": self.project_name,
        "REGION": self.region,
        # Add resource-specific variables
    },
    timeout=Duration.seconds(30),
    memory_size=512,
    log_retention=logs.RetentionDays.ONE_WEEK if self.env_config['log_retention_days'] == 7 
                  else logs.RetentionDays.ONE_MONTH if self.env_config['log_retention_days'] == 30 
                  else logs.RetentionDays.THREE_MONTHS,  # ✅ USE THIS: Works reliably
    description="Function description"
    # ✅ DEPRECATION NOTE: Shows warning but prevents redeploy errors
    # ❌ AVOID: log_group parameter causes "LogGroup exists" errors on redeploy
)

# Grant permissions
lambda_function.add_to_role_policy(
    iam.PolicyStatement(
        actions=["specific:actions"],
        resources=[f"arn:aws:service:{self.region}:{self.account}:resource/{self.company_prefix}-*"]
    )
)
```

### Cognito User Pool Pattern
```python
user_pool = cognito.UserPool(
    self, f"UserPool{self.deploy_env.title()}",
    user_pool_name=self.get_resource_name("users"),
    sign_in_aliases=cognito.SignInAliases(email=True, phone=True),
    auto_verify=cognito.AutoVerifiedAttrs(email=True, phone=True),
    standard_attributes=cognito.StandardAttributes(
        email=cognito.StandardAttribute(required=True),
        phone_number=cognito.StandardAttribute(required=True),
    ),
    custom_attributes={
        "full_name": cognito.StringAttribute(min_len=1, max_len=100),
        "state": cognito.StringAttribute(min_len=1, max_len=50),
    },
    password_policy=cognito.PasswordPolicy(
        min_length=8,
        require_lowercase=True,
        require_uppercase=True,
        require_digits=True,
        require_symbols=True
    ),
    account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
    removal_policy=self.get_removal_policy()
)

user_pool_client = cognito.UserPoolClient(
    self, f"UserPoolClient{self.deploy_env.title()}",
    user_pool=user_pool,
    auth_flows=cognito.AuthFlow(
        user_password=True,
        user_srp=True
    ),
    id_token_validity=Duration.hours(self.env_config['token_validity_hours']),
    access_token_validity=Duration.hours(self.env_config['token_validity_hours']),
    refresh_token_validity=Duration.days(30)
)
```

### CloudWatch LogGroup Pattern
```python
# Explicit LogGroup creation (replaces deprecated logRetention in Lambda functions)
log_group = logs.LogGroup(
    self, f"ServiceLogGroup{self.deploy_env.title()}",
    log_group_name=f"/aws/lambda/{self.get_resource_name('service-name')}",  # Standard Lambda log group naming
    retention=logs.RetentionDays.ONE_WEEK if self.env_config['log_retention_days'] == 7 
              else logs.RetentionDays.ONE_MONTH if self.env_config['log_retention_days'] == 30 
              else logs.RetentionDays.THREE_MONTHS,
    removal_policy=self.get_removal_policy()
)

# For custom log groups (non-Lambda)
custom_log_group = logs.LogGroup(
    self, f"CustomLogGroup{self.deploy_env.title()}",
    log_group_name=f"/custom/{self.get_resource_name('application')}/logs",
    retention=logs.RetentionDays.TWO_WEEKS,
    removal_policy=self.get_removal_policy()
)

# For multiple Lambda functions - create log groups in a loop
lambda_configs = [
    ('function-one', 'Function one description'),
    ('function-two', 'Function two description'),
]

log_groups = {}
for function_name, description in lambda_configs:
    log_groups[function_name] = logs.LogGroup(
        self, f"{function_name.title().replace('-', '')}LogGroup{self.deploy_env.title()}",
        log_group_name=f"/aws/lambda/{self.get_resource_name(function_name)}",
        retention=logs.RetentionDays.ONE_WEEK if self.env_config['log_retention_days'] == 7 
                  else logs.RetentionDays.ONE_MONTH if self.env_config['log_retention_days'] == 30 
                  else logs.RetentionDays.THREE_MONTHS,
        removal_policy=self.get_removal_policy()
    )
```

## Usage Guidelines

### 1. Stack Creation Process
1. Analyze requirements and identify resource needs
2. Determine cross-stack dependencies
3. Create stack class following the template structure
4. Implement resource creation methods
5. Add proper exports for dependent stacks
6. Include monitoring and security configurations

### 2. Configuration Requirements
- Always validate that required config keys exist
- Use environment-specific configurations
- Parameterize all naming and resource configurations
- Include proper error handling for missing config

### 3. Testing and Validation
- Test CDK synthesis with all environments (dev/staging/production)
- Validate cross-stack imports work correctly
- Ensure all resources follow naming conventions
- Verify no hardcoded values remain

### 4. Documentation Standards
- Include clear docstrings for all methods
- Document cross-stack dependencies
- Provide configuration examples
- Include deployment instructions

## Common Mistakes to Avoid

1. **Hardcoded Values**: Never hardcode company prefix, project name, or environment-specific values
2. **Inconsistent Naming**: Always use `get_resource_name()` for resource names
3. **Missing Environment Logic**: Always use environment-specific removal policies and configurations
4. **Cross-Stack Issues**: Properly handle optional cross-stack dependencies
5. **Security Gaps**: Always follow principle of least privilege for IAM permissions
6. **Missing Exports**: Export all resources that might be needed by other stacks
7. **🚨 CRITICAL ERROR: Missing LogGroup for Lambda Functions**:
   - **NEVER CREATE**: Lambda functions without explicit LogGroup
   - **ALWAYS REQUIRE**: `log_group=log_group_variable` parameter in ALL Lambda functions
   - **FAILURE TO COMPLY**: Stack will not pass review and must be rejected
   - **ENFORCEMENT**: Every Lambda function creation MUST be preceded by LogGroup creation

8. **🚨 CRITICAL ERROR: Wrong Python Runtime Version**:
   - **NEVER USE**: `_lambda.Runtime.PYTHON_3_9` or `_lambda.Runtime.PYTHON_3_10`
   - **ALWAYS USE**: `_lambda.Runtime.PYTHON_3_11` for ALL Lambda functions
   - **NO EXCEPTIONS**: All Lambda functions must use consistent Python 3.11 runtime
   - **PERFORMANCE**: Python 3.11 provides better performance and security patches

9. **⚠️ DEPRECATED: Using logRetention in Lambda Functions**: 
   - **DON'T USE**: `log_retention=logs.RetentionDays.ONE_WEEK` in Lambda function creation
   - **USE INSTEAD**: Create explicit `logs.LogGroup` and pass it via `log_group` parameter
   - **WARNING**: logRetention will be removed in the next AWS CDK major release
   - **MIGRATION IMPACT**: Log group names will change when migrating existing stacks

10. **🚨 CRITICAL ERROR: Inconsistent Naming Patterns**:
   - **MODULE PREFIX REQUIRED**: Both construct IDs and resource names must use consistent module prefixes across ALL resources
   - **CONSTRUCT ID PATTERN**: Must use `{ModulePrefix}Lambda{FunctionName}LogGroup{Environment}` for LogGroups
   - **LAMBDA CONSTRUCT PATTERN**: Must use `{ModulePrefix}Lambda{FunctionName}{Environment}` for Lambda functions  
   - **RESOURCE NAME PATTERN**: Must use `{module-prefix}-{function-name}` for resource names
   - **BAD EXAMPLE**: Mixing `"UserRegistrationFunctionLogGroup"` with `"OptionsLambdaMarketDataLogGroupDev"`
   - **GOOD EXAMPLE**: All using `"AuthLambdaUserRegistrationLogGroupDev"` and `"OptionsLambdaBasketManagerLogGroupDev"`
   - **CROSS-STACK ALIGNMENT**: All stacks in a project must follow the same naming approach
   - **ENFORCEMENT**: Reject stacks with mixed naming patterns immediately

## AWS CDK Migration Notes

### logRetention Deprecation (2024)
AWS CDK has deprecated the `logRetention` parameter in Lambda functions. This affects:
- All `_lambda.Function` constructs using `log_retention` parameter
- Custom Resources and internal CDK constructs (may still show warnings)
- Existing stacks will continue to work but should be migrated

**Migration Steps:**
1. Create explicit `logs.LogGroup` constructs
2. Replace `log_retention` parameter with `log_group` parameter
3. Update construct IDs to avoid naming conflicts
4. Test deployment in non-production environments first

**Breaking Changes:**
- Log group names will change from auto-generated to explicit names
- Existing log groups may need manual cleanup after migration
- Any code referencing log group names will need updates

**Benefits of Migration:**
- Full control over log group configuration
- Better resource management and tagging
- Consistent with AWS CDK future direction
- More customization options (encryption, subscription filters, etc.)

## Agent Responsibilities

When creating CDK stacks, this agent will:

1. **Analyze Requirements**: Understand the functional requirements and AWS services needed
2. **Apply Patterns**: Use established patterns for resource creation and configuration
3. **Ensure Consistency**: Follow naming conventions and configuration management practices
4. **Validate Configuration**: Ensure all required configuration values are present
5. **Generate Clean Code**: Produce well-structured, documented, and maintainable CDK code
6. **Include Monitoring**: Add appropriate CloudWatch dashboards and alarms
7. **Security First**: Implement proper IAM permissions and security configurations
8. **🚨 ENFORCE LogGroup Mandate**: REJECT any Lambda function creation without explicit LogGroup
9. **🔍 Validate Compliance**: Ensure every Lambda function has `log_group` parameter before approval

## Code Review Checklist

Before approving any CDK stack, verify:

- [ ] ✅ **LogGroup Created**: Every Lambda function has explicit LogGroup construct
- [ ] ✅ **LogGroup Parameter**: Every Lambda function uses `log_group=log_group_variable`
- [ ] ✅ **Python 3.11 Runtime**: Every Lambda function uses `_lambda.Runtime.PYTHON_3_11`
- [ ] ❌ **No Old Python**: No `PYTHON_3_9` or `PYTHON_3_10` runtime versions found
- [ ] ❌ **No logRetention**: No deprecated `log_retention` parameters found
- [ ] ✅ **Environment Config**: LogGroup retention uses `self.env_config['log_retention_days']`
- [ ] ✅ **Naming Consistent**: LogGroup names follow `{Function}LogGroup{Environment}` pattern
- [ ] ✅ **Removal Policy**: LogGroup has proper `removal_policy=self.get_removal_policy()`
- [ ] ✅ **Module Prefix Pattern**: All construct IDs follow `{ModulePrefix}Lambda{Function}LogGroup{Environment}` pattern
- [ ] ✅ **Resource Name Pattern**: All resource names follow `{module-prefix}-{function-name}` pattern
- [ ] ❌ **No Mixed Patterns**: No mixing of simple descriptive names with module-prefixed patterns

**REJECTION CRITERIA**: Any Lambda function without explicit LogGroup OR using outdated Python runtime OR inconsistent naming patterns must be rejected immediately.

This agent ensures that all generated CDK stacks are consistent, maintainable, and follow the established architectural patterns while being completely configurable without hardcoded values.