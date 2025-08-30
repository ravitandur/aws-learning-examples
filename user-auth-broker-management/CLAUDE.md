# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Module 2**: User Authentication & Broker Management for Algorithmic Trading Platform

This AWS CDK project implements user authentication using AWS Cognito with broker account management for Indian stock market trading platform. Part of progressive learning series to build complete algo trading platform.

**🚀 Status**: ✅ Completed & Tested with Full-Stack Integration + Complete Frontend  
**🎯 Goal**: Foundation for algo trading platform user management  
**📊 Focus**: AWS Cognito + DynamoDB + API Gateway + Secrets Manager + React Frontend

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

# Forgot password test
curl -X POST https://api-gateway-url/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'

# Reset password test
curl -X POST https://api-gateway-url/auth/confirm-forgot-password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "confirmation_code": "123456",
    "new_password": "NewPassword123!"
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

### ✅ Complete React Frontend Integration (August 2025)

#### **Frontend Architecture & Setup**
- **Technology Stack**: React.js + TypeScript + TailwindCSS + Lucide React Icons + Axios
- **Design System**: Professional algorithmic trading platform UI with Inter font
- **Styling**: TailwindCSS with custom primary colors and dark mode support
- **Project Structure**: Unified frontend in root directory for modular development
- **Environment Configuration**: Multi-environment support with dev/staging/production API endpoints
- **Authentication**: JWT token management with ID token for Cognito authorizer

#### **Key Frontend Components Created**
- **Authentication System**: 
  - `AuthContext.tsx` - Global state management with useReducer, includes forgot password flow
  - `LoginForm.tsx` - Email/phone login with Indian validation
  - `RegisterForm.tsx` - Complete registration with all Indian states
  - `ForgotPasswordForm.tsx` - Password reset with email validation and success states
  - `AuthPage.tsx` - Unified auth interface with login/register/forgot password modes

- **Broker Management System**:
  - `BrokerAccountsList.tsx` - Main broker management interface
  - `AddBrokerAccountForm.tsx` - Comprehensive broker account creation
  - `BrokerAccountCard.tsx` - Individual account display and actions
  - `BrokersPage.tsx` - Complete broker management page

- **Core Application**:
  - `Dashboard.tsx` - Dynamic dashboard with real broker account counts
  - `Navigation.tsx` - App navigation with authentication state
  - `App.tsx` - Main application routing and auth protection

#### **Critical Integration Fixes Applied**
1. **JWT Token Authentication Issue**:
   - **Problem**: Frontend using `accessToken`, backend expecting `idToken`
   - **Solution**: Updated `apiClient.ts` to send ID token in Authorization header
   - **Impact**: Fixed 401 Unauthorized errors on protected routes

2. **API Response Format Mismatch**:
   - **Backend Response**: `{ broker_accounts: [...], count: N }`  
   - **Frontend Expected**: `{ success: true, data: [...] }`
   - **Solution**: Updated backend to return standardized API response format
   - **Files Modified**: `broker_account_manager.py` GET and POST handlers

3. **TypeScript Interface Alignment**:
   - **Problem**: Frontend expecting `status` property, backend returning `account_status`
   - **Solution**: Updated `BrokerAccount` interface and `BrokerAccountCard.tsx`
   - **Impact**: Fixed runtime errors with undefined property access

4. **Dashboard Data Integration**:
   - **Problem**: Dashboard showing hardcoded "0" broker accounts
   - **Solution**: Added real-time data fetching from `brokerService.getBrokerAccounts()`
   - **Impact**: Dashboard now shows accurate account counts

#### **User Experience Features**
- **Indian Market Specialization**:
  - Complete Indian states dropdown (36 states/UTs)
  - Phone number validation for +91 format
  - Indian timezone and currency formatting

- **Security & UX**:
  - Secure credential storage messaging (AWS Secrets Manager)
  - Form validation with real-time feedback
  - Loading states and error handling
  - Professional algorithmic trading platform design with TailwindCSS
  - Inter font for clean, modern typography
  - Lucide React icons for consistent iconography

- **Broker Integration**:
  - Zerodha-specific setup instructions
  - API key/secret validation by broker type
  - Connection testing functionality
  - Credential management with show/hide toggles

#### **Forgot Password Implementation (August 2025)**

**✅ Complete Standard Password Reset Flow**
- **Flow Implementation**: 
  1. User enters email → Verification code sent to email
  2. "Check Your Email" confirmation screen with "Continue to Enter Code" button
  3. User enters 6-digit code + new password + confirm password
  4. "Password Reset Successful" screen → "Continue to Sign In"
  5. User logs in with new password

- **Frontend Components**: 
  - `ForgotPasswordForm.tsx` - Email submission with "Continue to Enter Code" navigation
  - `ResetPasswordForm.tsx` - Verification code + new password entry form
  - `AuthPage.tsx` - Complete state management for forgot-password and reset-password modes
  - `AuthContext.tsx` - Integrated methods: `forgotPassword()`, `resetPassword()`

- **Backend Integration**:
  - `/auth/forgot-password` endpoint - AWS Cognito `forgot_password()` API
  - `/auth/confirm-forgot-password` endpoint - AWS Cognito `confirm_forgot_password()` API
  - `authService.ts` - Complete API integration for both endpoints
  - Email delivery through AWS Cognito (configured with quantleapanalytics@gmail.com)

- **Security & Validation**:
  - 6-digit verification code validation
  - Strong password requirements (8+ chars, uppercase, lowercase, number, special character)
  - Password confirmation matching validation
  - Real-time form validation with error feedback
  - Secure AWS Cognito backend integration

- **User Experience Features**:
  - Professional UI with password visibility toggles (show/hide)
  - Loading states and comprehensive error handling
  - Mobile-responsive design with TailwindCSS styling
  - Clear navigation flow between all reset states
  - Success confirmations at each step

- **Technical Implementation**:
  - Complete TypeScript integration with proper interfaces
  - Context methods: `forgotPassword(email: string)`, `resetPassword(email, code, newPassword)`
  - API endpoints: `/auth/forgot-password`, `/auth/confirm-forgot-password`
  - State management for reset flow: forgot-password → reset-password → login modes

#### **Design System & UI Architecture (August 2025)**

**✅ Professional Algorithmic Trading Platform Look**
- **TailwindCSS Integration**: Custom configuration with algorithmic trading color scheme
- **Typography**: Inter font family for professional, clean readability
- **Color Palette**: Custom primary blue colors (#3b82f6) with 50-900 shades for consistency
- **Dark Mode Support**: Built-in dark mode toggle with `class` strategy
- **Icon System**: Lucide React icons for consistent, modern iconography
- **Responsive Design**: Mobile-first approach with responsive breakpoints

**✅ Component Architecture**:
- **Form Components**: Consistent styling across login, register, forgot password, and broker forms
- **Loading States**: Professional spinners and skeleton loading patterns
- **Error Handling**: Consistent error alert components with dismiss functionality
- **Button System**: Primary, secondary, and danger button variants
- **Input Components**: Standardized form inputs with validation states

**✅ Layout System**:
- **Authentication Pages**: Gradient background with centered card layout
- **Dashboard Layout**: Sidebar navigation with main content area
- **Responsive Navigation**: Collapsible sidebar for mobile devices
- **Grid Systems**: Consistent spacing and layout patterns

#### **Technical Achievements**
- **Authentication Flow**: Complete login → forgot password → dashboard → broker management workflow
- **State Management**: Robust context-based auth state with automatic token refresh
- **Error Handling**: Comprehensive error boundaries and user feedback
- **Type Safety**: Full TypeScript integration with proper interface definitions
- **Performance**: Optimized API calls and component rendering
- **Design Consistency**: Professional algorithmic trading platform aesthetic throughout

## Latest Enhancement: Enhanced Broker Account Management (August 2025)

### ✅ Complete Data Structure Overhaul
**Problem**: Original UUID-based broker_account_id was redundant since client_id is unique per user
**Solution**: Redesigned to use client_id as natural sort key with enhanced data model

#### **New Broker Account Structure**
```python
# DynamoDB Schema (Updated)
{
  "user_id": "cognito-user-sub",           # Partition Key
  "client_id": "user-defined-unique-id",   # Sort Key (replaces broker_account_id UUID)
  "broker_name": "zerodha|angel|finvasia|zebu",
  "group": "BFW|KOU|PMS",                  # Account classification
  "capital": Decimal("100000.00"),         # Trading capital (Decimal for DynamoDB)
  "description": "My primary trading account",
  "account_status": "enabled|disabled",
  "api_key_secret_arn": "arn:aws:secretsmanager:...",     # API credentials
  "oauth_token_secret_arn": "arn:aws:secretsmanager:...", # OAuth tokens (separate)
  "token_expires_at": "2025-08-30T18:00:00Z",
  "last_oauth_login": "2025-08-30T09:00:00Z",
  "created_at": "2025-08-30T10:00:00Z",
  "updated_at": "2025-08-30T15:30:00Z"
}
```

#### **Dual Secrets Manager Storage Pattern**
- **API Credentials**: `ql-{broker}-api-credentials-{env}-{user_id}-{client_id}`
- **OAuth Tokens**: `ql-{broker}-oauth-tokens-{env}-{user_id}-{client_id}`
- **Benefit**: Separate lifecycle management for permanent vs temporary credentials

#### **OAuth Integration for Daily Sessions**
**New Endpoints**:
- `POST /broker-accounts/{client_id}/oauth/login` - Initiate OAuth flow
- `POST /broker-accounts/{client_id}/oauth/callback` - Handle OAuth callback  
- `GET /broker-accounts/{client_id}/oauth/status` - Check token validity

**Zerodha OAuth Flow**: 
1. Generate secure state parameter → Zerodha login URL
2. User authorizes → callback with request_token
3. Exchange request_token for access_token → store in OAuth secret
4. Daily session management with automatic expiry handling

#### **Field Edit Restrictions**
**Immutable After Creation**: `broker_name`, `client_id`, `group`, `user_id`
**Editable Fields**: `api_key`, `api_secret`, `capital`, `description`
**Implementation**: Backend validation + frontend form restrictions

#### **Multi-Broker Support**
- **Zerodha**: Full OAuth integration with API validation patterns
- **Angel One**: API credential management (OAuth future enhancement)  
- **Finvasia**: API credential management
- **Zebu**: API credential management

### ✅ Technical Implementation Details

#### **Backend Lambda Updates**
- **DynamoDB Schema**: Migrated from UUID to client_id as natural sort key
- **DecimalEncoder**: Added custom JSON encoder for DynamoDB Decimal type serialization
- **Dual Storage**: Separate Secrets Manager entries for API credentials vs OAuth tokens
- **Field Validation**: Comprehensive broker-specific validation patterns

#### **Frontend React Integration**  
- **TypeScript Interfaces**: Complete migration from broker_account_id to client_id
- **Form Components**: Updated to capture new fields (client_id, capital, description)
- **Edit Restrictions**: Form validation preventing immutable field changes
- **OAuth UI**: Ready for OAuth flow integration (status indicators, login buttons)

#### **Critical Fixes Applied**
1. **DynamoDB Decimal Support**: Added DecimalEncoder for capital field JSON serialization
2. **API Gateway Conflicts**: Resolved path parameter conflicts during deployment
3. **TypeScript Compilation**: Fixed all frontend references to new field structure
4. **Environment Configuration**: Updated frontend .env with new API Gateway endpoint

### ✅ Deployment & Testing Status
- **API Gateway**: `https://cgsdoaq0i1.execute-api.ap-south-1.amazonaws.com/dev/`
- **DynamoDB Table**: `ql-algo-trading-dev-broker-accounts` with new schema
- **Frontend Configuration**: Updated with correct API endpoint and environment variables
- **TypeScript Compilation**: Clean build with no errors
- **Infrastructure**: Successfully deployed with all new OAuth endpoints

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
- ✅ **Complete React frontend with full-stack integration**
- ✅ **JWT authentication flow with proper token handling**
- ✅ **Real-time dashboard with dynamic broker account counts**
- ✅ **Indian market specialized UI/UX features**
- ✅ **TypeScript integration with comprehensive error handling**
- ✅ **Complete forgot password functionality with email-based reset flow**
- ✅ **Enhanced broker account management with client_id natural keys**
- ✅ **OAuth integration architecture for daily trading sessions**
- ✅ **Dual Secrets Manager storage for credential lifecycle management**
- ✅ **Multi-broker support (Zerodha, Angel One, Finvasia, Zebu)**
- ✅ **Field edit restrictions for data integrity**
- ✅ **DynamoDB Decimal type handling for financial data**
- ✅ Foundation ready for market data integration (Module 3)

## Next Module Integration
This module provides authenticated user foundation for:
- Module 3: Market data APIs and real-time feeds
- Module 4: Trading strategy execution
- Module 5: Portfolio management and P&L tracking