# User Authentication & Broker Management

**🔗 GitHub Repository**: https://github.com/ravitandur/aws-learning-examples  
**📦 Module**: 2 of AWS Learning Series for Algorithmic Trading Platform  
**🚀 Status**: ✅ Completed & Tested

AWS Cognito-based user authentication system with secure broker account management for Indian stock market algo trading platform.

## Architecture Overview

This module implements the user management foundation for an algorithmic trading platform, focusing on:

- **User Registration**: Phone, email, full name, and Indian state
- **Authentication**: AWS Cognito with JWT tokens
- **Broker Integration**: Secure Zerodha API credential management  
- **Indian Market Focus**: Phone validation, state selection, IST timezone

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   API Client    │ ──▶│   API Gateway    │ ──▶│   Lambda Functions  │
│                 │    │   + Cognito      │    │   + DynamoDB        │
│                 │    │   Authorizer     │    │   + Secrets Manager │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
```

## Learning Objectives

### AWS Services Mastery
- **AWS Cognito**: User pools, custom attributes, verification
- **DynamoDB**: NoSQL modeling, GSI patterns, on-demand billing
- **API Gateway**: REST APIs, Cognito authorizers, validation
- **Lambda Functions**: Authentication logic, CRUD operations
- **Secrets Manager**: Secure credential storage and rotation

### Indian Market Integration
- Phone number validation for Indian numbers (+91)
- Complete Indian states list for registration
- Zerodha API credential secure storage
- IST timezone handling for trading platform

## API Endpoints

### Authentication
- `POST /auth/register` - User registration with verification
- `POST /auth/login` - User authentication
- `POST /auth/verify` - Phone/email verification
- `GET /auth/profile` - User profile retrieval
- `PUT /auth/profile` - Profile updates

### Broker Management
- `POST /broker-accounts` - Add broker account (Zerodha)
- `GET /broker-accounts` - List user's broker accounts
- `PUT /broker-accounts/{id}` - Update broker account
- `DELETE /broker-accounts/{id}` - Remove broker account
- `POST /broker-accounts/{id}/verify` - Test broker API connection

## Data Models

### User Registration
```json
{
  "phone_number": "+919876543210",
  "email": "trader@example.com",
  "full_name": "Ravi Tandur", 
  "state": "Karnataka",
  "password": "SecurePassword123!"
}
```

### Broker Account
```json
{
  "broker_name": "zerodha",
  "account_type": "trading",
  "api_key": "your_zerodha_api_key",
  "api_secret": "your_zerodha_api_secret"
}
```

## Prerequisites

- AWS CLI configured with `account2` profile
- Python 3.9+
- AWS CDK installed globally
- Zerodha API access (api_key and api_secret)

## Quick Start

1. **Navigate to module**:
   ```bash
   cd user-auth-broker-management
   ```

2. **Deploy the stack**:
   ```bash
   ./deploy.sh -p account2
   ```

3. **Test user registration**:
   ```bash
   # Register new user
   curl -X POST https://your-api-gateway/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "phone_number": "+919876543210",
       "email": "your@email.com",
       "full_name": "Your Name",
       "state": "Your State",
       "password": "YourPassword123!"
     }'
   ```

4. **Add broker account**:
   ```bash
   # Add Zerodha account (after login)
   curl -X POST https://your-api-gateway/broker-accounts \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "broker_name": "zerodha",
       "api_key": "your_zerodha_api_key", 
       "api_secret": "your_zerodha_secret"
     }'
   ```

## Security Features

- **Secure Credentials**: Zerodha API keys stored in AWS Secrets Manager
- **JWT Authentication**: Cognito-issued tokens for API access
- **Phone Verification**: Indian phone number format validation
- **Email Verification**: Required for account activation
- **Rate Limiting**: API Gateway throttling protection
- **Encryption**: DynamoDB encryption at rest
- **Enterprise Logging**: Structured JSON logging with sensitive data protection

## Cost Optimization

**Expected monthly costs for learning/development:**
- Cognito User Pool: $0 (free tier: 50K MAUs)
- DynamoDB: ~$1-2 (on-demand pricing)  
- Lambda: ~$0.20 (free tier: 1M requests)
- API Gateway: ~$3.50 (1M calls)
- Secrets Manager: ~$0.40 per secret
- **Total: ~$5-7/month**

## Enterprise Logging System

This module implements a comprehensive structured logging system shared across all AWS learning modules.

### Logging Architecture
- **Structured JSON Logs**: All Lambda functions use consistent JSON format
- **Sensitive Data Protection**: Automatic redaction of passwords, API keys, secrets
- **CloudWatch Integration**: Logs are searchable and queryable
- **Shared Utilities**: Common logging functions across all modules
- **Audit Trail**: Complete tracking of user actions and API responses

### Key Logging Features
```json
{
  "timestamp": "2025-08-29T19:42:15,123",
  "level": "INFO", 
  "logger": "user_registration",
  "message": "User registered successfully",
  "user_id": "c103bd6a-70e1-70f0-4055-41bbcdaf1142",
  "event_type": "user_action",
  "action": "registration",
  "aws_request_id": "abc123-def456"
}
```

### CloudWatch Queries
```sql
-- Find all user registrations today
fields @timestamp, user_id, action
| filter event_type = "user_action" and action = "registration"
| sort @timestamp desc

-- Find API errors  
fields @timestamp, status_code, message
| filter status_code >= 400
| stats count() by status_code
```

## Testing Results

✅ **Comprehensive Testing Completed**

### User Authentication Testing
- **Registration**: Successfully tested with Indian phone number (+919885577812) and Telangana state
- **Validation**: Phone number format, email format, and state validation working
- **Cognito Integration**: User pool creation, JWT token generation validated
- **DynamoDB**: User profile storage and retrieval confirmed

### Broker Account Management Testing
- **CRUD Operations**: Create, read, update, delete broker accounts validated
- **Secrets Manager**: Secure storage and retrieval of Zerodha API credentials
- **Authorization**: JWT token-based access control working correctly
- **Data Sanitization**: Sensitive data properly excluded from responses

### Security Testing
- **Critical Fix**: Removed dangerous logging of API secrets in plain text
- **Data Protection**: All sensitive fields (passwords, api_secret, api_key) are redacted
- **Access Control**: Only authenticated users can manage their broker accounts
- **Encryption**: All data encrypted in transit and at rest

## Indian States Supported

Complete list of all 28 states and 8 union territories:
- Andhra Pradesh, Arunachal Pradesh, Assam, Bihar, Chhattisgarh
- Goa, Gujarat, Haryana, Himachal Pradesh, Jharkhand, Karnataka
- Kerala, Madhya Pradesh, Maharashtra, Manipur, Meghalaya, Mizoram
- Nagaland, Odisha, Punjab, Rajasthan, Sikkim, Tamil Nadu, Telangana
- Tripura, Uttar Pradesh, Uttarakhand, West Bengal
- Andaman and Nicobar Islands, Chandigarh, Dadra and Nagar Haveli
- Daman and Diu, Delhi, Jammu and Kashmir, Ladakh, Lakshadweep, Puducherry

## Next Steps

After completing this module, you'll have:
- ✅ Authenticated user management system
- ✅ Secure broker account storage
- ✅ Foundation for trading platform features

**Module 3 Preview**: Market data integration with real-time NSE/BSE feeds using the authenticated user context from this module.

## Troubleshooting

- **Phone verification fails**: Ensure number format is `+919876543210`
- **State validation error**: Use exact state names from supported list
- **API Gateway 403**: Check Cognito JWT token validity
- **Zerodha connection fails**: Verify API credentials in AWS console