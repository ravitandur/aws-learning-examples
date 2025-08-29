# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Module 2**: User Authentication & Broker Management for Algorithmic Trading Platform

This AWS CDK project implements user authentication using AWS Cognito with broker account management for Indian stock market trading platform. Part of progressive learning series to build complete algo trading platform.

**🚀 Status**: ✅ Completed & Tested with Enterprise Logging  
**🎯 Goal**: Foundation for algo trading platform user management  
**📊 Focus**: AWS Cognito + DynamoDB + API Gateway + Secrets Manager

## Implementation Plan Captured

### Architecture Overview
```
User Registration Flow:
Frontend → API Gateway + Cognito Authorizer → Lambda Functions → DynamoDB + Secrets Manager
```

### Phase 1: Core Authentication (Week 1)
- AWS Cognito User Pool with custom attributes (full_name, state)
- Phone number (+91) and email verification
- API Gateway endpoints for auth operations
- DynamoDB UserProfiles table

### Phase 2: Broker Account Management (Week 2)
- DynamoDB BrokerAccounts table with GSI
- Secrets Manager for Zerodha API credentials
- Broker account CRUD operations
- Zerodha API integration testing

### Phase 3: Security & Validation (Week 3)
- Indian phone number validation (+91 format)
- All Indian states validation
- Lambda triggers for Cognito
- Security enhancements and rate limiting

## Multi-Environment Architecture

### **Quantleap Analytics (ql) Resource Naming**
All resources follow pattern: `ql-algo-trading-{environment}-{resource}`

**Environments:**
- **dev** - Development with DESTROY policy, 24h tokens, 7-day log retention
- **staging** - Pre-production with RETAIN policy, 8h tokens, 30-day logs
- **production** - Live environment with RETAIN policy, 1h tokens, 90-day logs

**Environment Configuration:** `config/environments.json`
- Company: Quantleap Analytics LLP (ql)
- Project: algo-trading
- Environment-specific: removal policies, CORS origins, token validity, log retention

## Key Commands

### Deployment
- `./deploy.sh -e dev -p account2` - Deploy to development
- `./deploy.sh -e staging -p account2` - Deploy to staging  
- `./deploy.sh -e production -p account2` - Deploy to production
- `cdk destroy ql-algo-trading-dev-auth-broker-stack --profile account2` - Clean up environment
- `source venv/bin/activate && cdk synth --context environment=dev` - Synthesize for environment
- `source venv/bin/activate && cdk deploy ql-algo-trading-dev-auth-broker-stack --profile account2 --require-approval never` - Manual deployment

### Testing APIs
```bash
# User registration test
curl -X POST https://api-gateway-url/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "email": "user@example.com", 
    "full_name": "Test User",
    "state": "Karnataka",
    "password": "TempPassword123!"
  }'

# Broker account addition
curl -X POST https://api-gateway-url/broker-accounts \
  -H "Authorization: Bearer {cognito-jwt-token}" \
  -H "Content-Type: application/json" \
  -d '{
    "broker_name": "zerodha",
    "api_key": "your_zerodha_api_key",
    "api_secret": "your_zerodha_api_secret"
  }'
```

## Architecture Details

### AWS Services Used
1. **AWS Cognito**: User pools, custom attributes, phone/email verification
2. **DynamoDB**: User profiles and broker accounts (NoSQL patterns)
3. **API Gateway**: REST APIs with Cognito authorizer
4. **Lambda**: Authentication logic, CRUD operations
5. **Secrets Manager**: Secure Zerodha credential storage

### Data Models

#### Cognito User Pool Schema
```json
{
  "username": "+919876543210",
  "attributes": {
    "email": "user@example.com",
    "phone_number": "+919876543210", 
    "custom:full_name": "Ravi Tandur",
    "custom:state": "Karnataka"
  }
}
```

#### DynamoDB Tables
```yaml
UserProfiles:
  PK: user_id (Cognito sub)
  Attributes: full_name, email, phone_number, state, created_at

BrokerAccounts:
  PK: user_id
  SK: broker_account_id  
  Attributes: broker_name, account_type, api_key_secret_arn, status
  GSI: BrokerAccountsByUser (PK: user_id, SK: created_at)
```

### Indian Market Specifications
- **Phone Validation**: `^\+91[6-9]\d{9}$` pattern
- **All Indian States**: Complete list for dropdown/validation
- **Zerodha Integration**: API credentials in Secrets Manager
- **Timezone**: IST (UTC+5:30) for all timestamps
- **Region**: ap-south-1 (Mumbai) for data residency

## Cost Optimization
- **Expected**: ~$5-7/month for learning phase (single user)
- **Serverless-first**: Pay per use model
- **Free tier**: Cognito, Lambda, DynamoDB on-demand
- **Monitoring**: CloudWatch basic tier

## Security Considerations
- Secrets Manager for broker API credentials
- Cognito JWT tokens for API authorization
- Request rate limiting on API Gateway
- Encryption at rest for DynamoDB
- Indian phone number format validation
- Email verification required

## Enterprise Logging Implementation

### Shared Logging Architecture
- **Location**: `../shared_utils/logger.py` - Shared across all AWS learning modules
- **Deployment**: Automatically copied to Lambda functions during deployment via `deploy.sh`
- **Format**: Structured JSON logging for CloudWatch integration

### Key Components
```python
from shared_utils.logger import setup_logger, log_lambda_event, log_user_action, log_api_response

# Setup structured logger
logger = setup_logger(__name__)

# Log Lambda invocations (sanitized)
log_lambda_event(logger, event, context)

# Log user actions for audit
log_user_action(logger, user_id, "registration", {"state": "Karnataka"})

# Log API responses
log_api_response(logger, 201, user_id, response_size=1024)
```

### Security Features
- **Sensitive Data Protection**: Automatic redaction of `password`, `api_secret`, `api_key`, `token`
- **Event Sanitization**: Lambda events are sanitized before logging
- **Audit Trail**: All user actions tracked with context

### Critical Security Fix Applied
- **Issue**: Broker Lambda was logging entire event including API secrets in plain text
- **Fix**: Replaced all `print()` statements with structured logging using `log_lambda_event()`
- **Impact**: API secrets and credentials are now automatically redacted

### CloudWatch Integration
```sql
-- User registration tracking
fields @timestamp, user_id, action
| filter event_type = "user_action" and action = "registration"

-- API error monitoring
fields @timestamp, status_code, message
| filter status_code >= 400
| stats count() by status_code
```

## Comprehensive Testing Results

### ✅ User Authentication
- **Registration Flow**: Tested with phone +919885577812, email ravitandur@gmail.com, state Telangana
- **Cognito Integration**: User creation, JWT token generation, custom attributes
- **Validation**: Indian phone format, state validation, password complexity
- **DynamoDB**: User profile storage and retrieval confirmed

### ✅ Broker Account Management
- **CRUD Operations**: All operations (Create, Read, Update, Delete) validated
- **Secrets Manager**: Zerodha credentials stored securely with proper ARN references
- **Authorization**: JWT token verification working correctly
- **Data Sanitization**: Sensitive data excluded from all API responses

### ✅ Security & Logging
- **Enterprise Logging**: Structured JSON logs implemented across all Lambda functions
- **Sensitive Data Protection**: All credentials, passwords, tokens automatically redacted
- **Access Control**: Only authenticated users can access their own data
- **Audit Trail**: Complete tracking of user actions and system events

### ✅ Deployment & Infrastructure
- **CDK Deployment**: Clean deployment using industry best practices
- **Dependency Management**: Lambda dependencies handled by CDK bundling
- **Git Hygiene**: No unnecessary files in Lambda directories
- **Virtual Environment**: Proper isolation of development dependencies

## Recent Improvements (August 2025)

### ✅ Module-Specific Stack Naming
- **Problem**: Generic stack name `ql-algo-trading-dev-stack` didn't indicate module purpose
- **Solution**: Updated to `ql-algo-trading-dev-auth-broker-stack` for clear module identification
- **Impact**: Supports modular architecture with multiple stacks per environment
- **Future Stacks**: `ql-algo-trading-dev-market-data-stack`, `ql-algo-trading-dev-trading-engine-stack`

### ✅ Environment-Specific API Gateway Stages
- **Problem**: API Gateway always used `/prod/` stage regardless of environment
- **Before**: `https://api-id.execute-api.region.amazonaws.com/prod/auth/register`
- **After**: `https://api-id.execute-api.region.amazonaws.com/dev/auth/register`
- **Implementation**: Added `deploy_options=apigateway.StageOptions(stage_name=self.deploy_env)`
- **Benefit**: Clear environment distinction in URLs prevents accidental production calls

### ✅ Enhanced CDK Deployment Process
- **Permission Issues**: Resolved CDK execution role conflicts with explicit admin policies
- **Deployment Command**: `cdk deploy ql-algo-trading-dev-auth-broker-stack --require-approval never --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess`
- **Bootstrap Command**: `cdk bootstrap --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess`

### ✅ Complete End-to-End Validation
- **Multi-Environment Testing**: Validated dev/staging/production naming patterns
- **API Endpoint Testing**: All endpoints work with environment-specific URLs
- **User Flows**: Registration → Authentication → Broker Management fully functional
- **Test Users**: Successfully created test users in multiple states (Karnataka, Maharashtra, Gujarat, Telangana)

## Success Criteria - All Completed
- ✅ User registration with Indian phone/state validation
- ✅ Secure Zerodha credential storage and retrieval
- ✅ Complete authentication API endpoints
- ✅ Broker account management CRUD operations
- ✅ Enterprise-grade structured logging implementation
- ✅ Critical security vulnerabilities fixed
- ✅ Comprehensive testing validation
- ✅ **Module-specific stack naming for scalable architecture**
- ✅ **Environment-specific API Gateway stages**
- ✅ **Robust multi-environment deployment process**
- ✅ Foundation ready for market data integration (Module 3)

## Next Module Integration
This module provides authenticated user foundation for:
- Module 3: Market data APIs and real-time feeds
- Module 4: Trading strategy execution
- Module 5: Portfolio management and P&L tracking