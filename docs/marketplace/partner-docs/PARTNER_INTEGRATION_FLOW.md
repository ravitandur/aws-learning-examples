# Partner Integration Flow - Complete Guide

**QuantLeap Algo Trading Platform - B2B2C Marketplace**

**Audience**: Broker Partners (Zebu, Angel, Upstox, etc.)
**Version**: 1.0
**Last Updated**: October 10, 2025

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Integration Architecture](#integration-architecture)
3. [Complete User Journey](#complete-user-journey)
4. [API Integration Steps](#api-integration-steps)
5. [Data Flow & Architecture](#data-flow--architecture)
6. [Security & Authentication](#security--authentication)
7. [Error Handling](#error-handling)
8. [Testing Guide](#testing-guide)
9. [Go-Live Checklist](#go-live-checklist)

---

## 1. Overview

### **What This Integration Enables**

Your users can subscribe to professional algorithmic trading strategies created by QuantLeap and execute them automatically using their broker accounts.

### **Key Benefits for Your Users**

- ✅ **Professional Strategies**: Access to institutional-grade options trading strategies
- ✅ **Automated Execution**: Strategies execute automatically during market hours
- ✅ **Multiple Subscriptions**: Users can subscribe to multiple strategies
- ✅ **Seamless Integration**: Everything works within your portal
- ✅ **Daily OAuth**: Simple daily login for security

### **Revenue Model**

- **User Subscription**: ₹999/month per strategy
- **Partner Commission**: 30% (₹299.70)
- **QuantLeap Share**: 70% (₹699.30)
- **Payment**: Monthly automated settlement

---

## 2. Integration Architecture

### **High-Level Flow**

```
┌─────────────────────────────────────────────────────────────┐
│                   YOUR TRADING PORTAL                        │
│  User browses strategies → Subscribes → Daily OAuth login    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────┐
│              YOUR BACKEND SERVER                             │
│  Calls QuantLeap Partner API with API Key + Secret          │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────┐
│         QUANTLEAP ALGO TRADING PLATFORM                      │
│  Manages strategies, subscriptions, and execution            │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────┐
│              YOUR BROKER APIs                                │
│  Orders placed using user's daily OAuth token                │
└──────────────────────────────────────────────────────────────┘
```

### **Three-Phase Integration**

1. **Phase 1**: One-time broker account setup (api_key + api_secret stored)
2. **Phase 2**: Daily OAuth login (access_token refreshed daily)
3. **Phase 3**: Strategy subscriptions (unlimited, all use same broker account)

---

## 3. Complete User Journey

### **Step-by-Step User Experience**

#### **🔧 Phase 1: One-Time Broker Account Setup** (Done Once Per User)

**When**: First time user wants to use algo trading features

**User Action**:
1. User logs into your portal
2. User navigates to "Algo Trading" section
3. User clicks "Enable Algo Trading"
4. User enters their broker credentials (api_key, api_secret)

**Your Backend Action**:
```javascript
// Call QuantLeap Partner API
POST https://api.quantleap.in/partner/broker-accounts

Headers:
  Authorization: Bearer pk_zebu_live_YOUR_API_KEY
  X-Partner-Secret: sk_zebu_live_YOUR_SECRET_KEY
  Content-Type: application/json

Body:
{
  "user_email": "user@example.com",
  "broker_name": "zebu",
  "client_id": "ZEBU123",
  "api_key": "user_zebu_api_key",
  "api_secret": "user_zebu_api_secret"
}

Response (201 Created):
{
  "success": true,
  "message": "Broker account created successfully",
  "broker_account": {
    "user_id": "partner-user-user-at-example-com",
    "client_id": "ZEBU123",
    "broker_name": "zebu",
    "account_status": "enabled",
    "has_credentials": true,
    "has_oauth_token": false
  }
}
```

**What Happens**:
- ✅ User's api_key and api_secret are securely stored in AWS Secrets Manager
- ✅ Broker account entry created in QuantLeap database
- ✅ OAuth token placeholder created (to be filled daily)
- ✅ Credentials are PERMANENT (stored once, used forever)

---

#### **🔐 Phase 2: Daily OAuth Login** (Every Trading Day)

**When**: Every morning before market opens (recommended: 8:30 AM IST)

**User Action**:
1. User logs into your portal
2. System prompts: "Complete today's broker login"
3. User clicks "Login to Zebu"
4. Redirected to Zebu OAuth page
5. User enters Zebu credentials
6. Redirected back to your portal

**Your Backend Action**:

**Step 2.1: Initiate OAuth Flow**
```javascript
POST https://api.quantleap.in/partner/broker-accounts/{client_id}/oauth/initiate

Headers:
  Authorization: Bearer pk_zebu_live_YOUR_API_KEY
  X-Partner-Secret: sk_zebu_live_YOUR_SECRET_KEY
  Content-Type: application/json

Body:
{
  "user_email": "user@example.com"
}

Response (200 OK):
{
  "oauth_url": "https://kambala.zebu.in/connect/login?api_key=xxx&state=yyy",
  "state": "yyy",
  "expires_in": 300
}
```

**Step 2.2: Redirect User**
```javascript
// Redirect user to oauth_url
window.location.href = response.oauth_url;
```

**Step 2.3: Handle OAuth Callback**

User completes OAuth on Zebu → Redirected to your callback URL with `request_token`

```javascript
// Your callback URL receives: ?request_token=xxx&state=yyy

POST https://api.quantleap.in/partner/broker-accounts/{client_id}/oauth/callback

Headers:
  Authorization: Bearer pk_zebu_live_YOUR_API_KEY
  X-Partner-Secret: sk_zebu_live_YOUR_SECRET_KEY
  Content-Type: application/json

Body:
{
  "user_email": "user@example.com",
  "request_token": "xxx",
  "state": "yyy"
}

Response (200 OK):
{
  "success": true,
  "message": "OAuth login successful",
  "token_expires_at": "2025-10-10T15:30:00Z",
  "valid_until": "3:30 PM IST"
}
```

**What Happens**:
- ✅ QuantLeap exchanges request_token for access_token with Zebu
- ✅ access_token stored in Secrets Manager (overwrites yesterday's token)
- ✅ Token expiry time recorded (typically 8 hours)
- ✅ User's broker account marked as "ready for trading"

**Important Notes**:
- 🕐 Token expires at ~3:30 PM IST daily
- 🔄 User must complete OAuth every trading day
- ⚠️ If OAuth not completed, strategies won't execute
- 📱 Consider push notifications to remind users

---

#### **📦 Phase 3: Strategy Subscription** (Unlimited, Anytime)

**When**: User wants to subscribe to a strategy

**User Action**:
1. User browses available strategies in marketplace
2. User clicks "Subscribe" on a strategy
3. User configures lot multiplier (e.g., 2x)
4. User confirms subscription

**Your Backend Action**:

**Step 3.1: Browse Available Strategies** (Optional)
```javascript
GET https://api.quantleap.in/partner/marketplace/templates

Headers:
  Authorization: Bearer pk_zebu_live_YOUR_API_KEY
  X-Partner-Secret: sk_zebu_live_YOUR_SECRET_KEY

Response (200 OK):
{
  "templates": [
    {
      "template_id": "basket_admin_iron_condor",
      "name": "Iron Condor Weekly",
      "description": "Weekly iron condor on NIFTY",
      "index": "NIFTY",
      "entry_time": "09:20",
      "pricing": {
        "type": "PAID",
        "monthly_fee": 999,
        "currency": "INR"
      },
      "performance_metrics": {
        "win_rate": 75.5,
        "avg_monthly_return": 12.3,
        "max_drawdown": 8.2
      }
    }
  ]
}
```

**Step 3.2: Subscribe User to Strategy**
```javascript
POST https://api.quantleap.in/partner/marketplace/subscribe

Headers:
  Authorization: Bearer pk_zebu_live_YOUR_API_KEY
  X-Partner-Secret: sk_zebu_live_YOUR_SECRET_KEY
  Content-Type: application/json

Body:
{
  "user_email": "user@example.com",
  "template_id": "basket_admin_iron_condor",
  "broker_client_id": "ZEBU123",
  "lot_multiplier": 2.0,
  "auto_link_broker": true
}

Response (201 Created):
{
  "message": "Subscription created successfully",
  "subscription_id": "sub_abc123",
  "user_id": "partner-user-user-at-example-com",
  "template_id": "basket_admin_iron_condor",
  "status": "ACTIVE",
  "broker_allocation": {
    "allocation_id": "alloc_xyz789",
    "client_id": "ZEBU123",
    "broker_id": "zebu",
    "lot_multiplier": 2.0,
    "status": "ACTIVE"
  },
  "next_billing_date": "2025-11-10T00:00:00Z",
  "revenue_share": {
    "partner_commission": 299.7,
    "platform_fee": 699.3,
    "currency": "INR"
  }
}
```

**What Happens**:
- ✅ Subscription entity created in QuantLeap database
- ✅ Broker allocation created linking to user's broker account
- ✅ Subscription status set to ACTIVE
- ✅ Next billing date calculated
- ✅ Revenue attribution recorded for your partner account

**Important Notes**:
- 🔗 Subscription references existing broker account (no credentials needed)
- 🔢 User can have multiple subscriptions (all use same broker account)
- 💰 Each subscription bills separately (₹999/month each)
- 🎛️ User can pause/cancel anytime

---

#### **⚡ Phase 4: Automatic Strategy Execution** (Daily, Automatic)

**When**: Strategy entry time (e.g., 9:20 AM IST)

**User Action**: **NOTHING** - Fully automatic!

**What Happens Behind the Scenes**:

```
9:20 AM IST: EventBridge triggers Strategy Executor

Step 1: Find Active Subscriptions
  → Query: All ACTIVE subscriptions for this template
  → Result: 100 users subscribed to "Iron Condor Weekly"

Step 2: For Each Subscriber
  → Get broker allocation (client_id: ZEBU123)
  → Lookup broker account in BrokerAccounts table
  → Retrieve oauth_token_secret_arn

Step 3: Get Daily Access Token
  → Call AWS Secrets Manager with oauth_token_secret_arn
  → Extract access_token (updated this morning at 8:30 AM)
  → Validate token hasn't expired

Step 4: Execute Strategy
  → Read strategy configuration from admin template
  → Calculate positions based on lot_multiplier (2x)
  → Place orders via Zebu API using access_token

Step 5: Record Execution
  → Log all orders placed
  → Update execution history
  → Send notifications (optional)
```

**Order Placement Flow**:
```javascript
// QuantLeap calls YOUR broker API
POST https://kambala.zebu.in/api/v1/orders

Headers:
  Authorization: Bearer {daily_access_token}

Body:
{
  "tradingsymbol": "NIFTY25OCT2424500CE",
  "exchange": "NFO",
  "transaction_type": "BUY",
  "quantity": 100,  // 2 lots (user's lot_multiplier)
  "product": "MIS",
  "order_type": "LIMIT",
  "price": 150.50
}
```

**Execution Guarantees**:
- ✅ **0-Second Precision**: Orders placed at exact strategy time
- ✅ **Parallel Execution**: All users executed simultaneously
- ✅ **Automatic Retry**: Failed orders retried 3 times
- ✅ **Error Notifications**: Users notified of execution issues
- ✅ **Weekend Protection**: No executions on weekends/holidays

---

## 4. API Integration Steps

### **Prerequisites**

1. **Obtain Partner API Credentials**
   - Contact QuantLeap to get your API key and secret
   - Format: `pk_zebu_live_XXXXXXXX` and `sk_zebu_live_YYYYYYYY`
   - Store securely (never expose in frontend code)

2. **Setup Your Callback URL**
   - Configure OAuth redirect URL in your portal
   - Example: `https://yourportal.com/algo-trading/oauth/callback`
   - Share with QuantLeap for whitelisting

3. **Configure Environment**
   - Development: `https://api-dev.quantleap.in`
   - Production: `https://api.quantleap.in`

### **API Endpoints Summary**

| Endpoint | Method | Purpose | Phase |
|----------|--------|---------|-------|
| `/partner/broker-accounts` | POST | Create broker account | Phase 1 |
| `/partner/broker-accounts/{client_id}/oauth/initiate` | POST | Start OAuth flow | Phase 2 |
| `/partner/broker-accounts/{client_id}/oauth/callback` | POST | Complete OAuth | Phase 2 |
| `/partner/marketplace/templates` | GET | List strategies | Phase 3 |
| `/partner/marketplace/subscribe` | POST | Subscribe user | Phase 3 |
| `/partner/subscriptions` | GET | List subscriptions | Management |
| `/partner/subscriptions/{id}` | DELETE | Cancel subscription | Management |
| `/partner/subscriptions/{id}/pause` | PUT | Pause subscription | Management |
| `/partner/subscriptions/{id}/resume` | PUT | Resume subscription | Management |

---

## 5. Data Flow & Architecture

### **Database Architecture**

#### **Your User → QuantLeap User Mapping**

```
Your User Email: user@example.com
    ↓
QuantLeap User ID: partner-user-user-at-example-com
    ↓
Stores:
  - Broker Account (ZEBU123)
  - Subscriptions (multiple)
  - Execution History
```

#### **Data Entities**

**1. Broker Account** (Created Once)
```json
{
  "user_id": "partner-user-user-at-example-com",
  "client_id": "ZEBU123",
  "broker_name": "zebu",
  "api_key_secret_arn": "arn:aws:secretsmanager:...:api-credentials",
  "oauth_token_secret_arn": "arn:aws:secretsmanager:...:oauth-tokens",
  "token_expires_at": "2025-10-10T15:30:00Z",
  "last_oauth_login": "2025-10-10T08:30:00Z",
  "account_status": "enabled"
}
```

**2. Subscription** (Multiple Per User)
```json
{
  "user_id": "partner-user-user-at-example-com",
  "subscription_id": "sub_abc123",
  "template_basket_id": "basket_admin_iron_condor",
  "partner_id": "partner_zebu_live",
  "status": "ACTIVE",
  "subscription_date": "2025-10-10T10:00:00Z",
  "next_billing_date": "2025-11-10T00:00:00Z",
  "pricing": {
    "monthly_fee": 999,
    "partner_commission": 299.7
  }
}
```

**3. Broker Allocation** (Links Subscription → Broker Account)
```json
{
  "user_id": "partner-user-user-at-example-com",
  "allocation_id": "alloc_xyz789",
  "basket_id": "basket_admin_iron_condor",
  "client_id": "ZEBU123",
  "broker_id": "zebu",
  "lot_multiplier": 2.0,
  "priority": 1
}
```

### **Execution Time Data Flow**

```
┌─────────────────────────────────────────────────────────────┐
│  1. Strategy Executor Finds Active Subscriptions            │
│     Query GSI: template_basket_id = basket_admin_iron_condor │
│     Filter: status = ACTIVE                                  │
│     Result: 100 active subscriptions                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────┐
│  2. For Each Subscription, Get Broker Allocation            │
│     Query GSI: basket_id = basket_admin_iron_condor          │
│     Filter: user_id = partner-user-xxx                       │
│     Result: allocation with client_id = ZEBU123              │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────┐
│  3. Lookup Broker Account (Cross-Stack)                     │
│     Table: BrokerAccounts                                    │
│     Key: user_id + client_id                                 │
│     Result: oauth_token_secret_arn                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────┐
│  4. Retrieve Daily OAuth Token                              │
│     AWS Secrets Manager.get_secret_value()                   │
│     Result: access_token (valid until 3:30 PM)               │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────┐
│  5. Place Orders via Broker API                             │
│     POST https://kambala.zebu.in/api/v1/orders              │
│     Headers: Authorization: Bearer {access_token}            │
│     Body: Order details with lot_multiplier applied          │
└──────────────────────────────────────────────────────────────┘
```

---

## 6. Security & Authentication

### **Partner API Authentication**

**All Partner API calls require TWO headers**:

```http
Authorization: Bearer pk_zebu_live_XXXXXXXX
X-Partner-Secret: sk_zebu_live_YYYYYYYY
```

**Security Best Practices**:

1. ✅ **Never expose API keys in frontend code**
   - Store keys in environment variables
   - All API calls from your backend server

2. ✅ **Use HTTPS only**
   - All API endpoints enforce TLS 1.2+
   - Certificate pinning recommended

3. ✅ **Implement rate limiting**
   - QuantLeap enforces 60 requests/minute
   - Implement exponential backoff for retries

4. ✅ **Validate OAuth state parameter**
   - Always verify state matches on callback
   - Prevents CSRF attacks

5. ✅ **Log API interactions**
   - Log all API calls (excluding secrets)
   - Retain logs for 90 days minimum

### **User Credential Security**

**What QuantLeap Stores**:
- ✅ User's api_key and api_secret (encrypted in AWS Secrets Manager)
- ✅ Daily OAuth access_token (encrypted in AWS Secrets Manager)
- ✅ Token expiry timestamps

**What QuantLeap NEVER Stores**:
- ❌ User's broker login password
- ❌ User's broker TOTP/2FA codes
- ❌ User's personal information beyond email

**Encryption Standards**:
- AWS Secrets Manager with AES-256 encryption
- Secrets encrypted at rest and in transit
- Automatic key rotation every 90 days

---

## 7. Error Handling

### **Common Error Scenarios**

#### **1. Broker Account Creation Fails**

**Error Response**:
```json
{
  "statusCode": 400,
  "error": "Invalid broker credentials",
  "message": "API key validation failed with broker",
  "details": {
    "broker_response": "Invalid api_key"
  }
}
```

**Resolution**:
- Verify user entered correct api_key and api_secret
- Check broker account is active and not suspended
- Ensure API access enabled in broker settings

#### **2. OAuth Token Expired**

**Error Response**:
```json
{
  "statusCode": 401,
  "error": "OAuth token expired",
  "message": "User must complete daily OAuth login",
  "token_expired_at": "2025-10-10T15:30:00Z"
}
```

**Resolution**:
- Prompt user to complete OAuth flow again
- Send push notification: "Complete daily broker login"
- Display banner in portal: "Algo trading inactive - login required"

#### **3. Strategy Execution Failed**

**Error Response** (via webhook):
```json
{
  "event": "execution_failed",
  "subscription_id": "sub_abc123",
  "user_email": "user@example.com",
  "error": "Insufficient funds",
  "broker_response": {
    "code": "AB-1003",
    "message": "Available margin: ₹5000, Required: ₹15000"
  },
  "timestamp": "2025-10-10T09:20:05Z"
}
```

**Resolution**:
- Notify user via email/SMS
- Suggest adding funds to broker account
- Provide option to reduce lot_multiplier

#### **4. Subscription Already Exists**

**Error Response**:
```json
{
  "statusCode": 409,
  "error": "Duplicate subscription",
  "message": "User already subscribed to this strategy",
  "existing_subscription_id": "sub_xyz456"
}
```

**Resolution**:
- Show user their existing subscription
- Offer option to update lot_multiplier
- Suggest pausing/canceling before resubscribing

### **Error Handling Best Practices**

```javascript
async function subscribeUser(userEmail, templateId, lotMultiplier) {
  try {
    const response = await fetch('https://api.quantleap.in/partner/marketplace/subscribe', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.QUANTLEAP_API_KEY}`,
        'X-Partner-Secret': process.env.QUANTLEAP_SECRET_KEY,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_email: userEmail,
        template_id: templateId,
        broker_client_id: user.brokerId,
        lot_multiplier: lotMultiplier
      })
    });

    const data = await response.json();

    if (!response.ok) {
      // Handle specific error codes
      if (response.status === 409) {
        return {
          success: false,
          error: 'DUPLICATE_SUBSCRIPTION',
          message: 'You are already subscribed to this strategy'
        };
      }

      if (response.status === 401) {
        return {
          success: false,
          error: 'OAUTH_REQUIRED',
          message: 'Please complete daily broker login first'
        };
      }

      // Generic error
      throw new Error(data.message || 'Subscription failed');
    }

    return { success: true, data };

  } catch (error) {
    console.error('Subscription error:', error);

    // Log to your monitoring system
    logError('subscription_failed', {
      user_email: userEmail,
      template_id: templateId,
      error: error.message
    });

    return {
      success: false,
      error: 'UNKNOWN_ERROR',
      message: 'Something went wrong. Please try again.'
    };
  }
}
```

---

## 8. Testing Guide

### **Development Environment**

**Base URL**: `https://api-dev.quantleap.in`

**Test API Credentials**:
```
API Key: pk_zebu_test_XXXXXXXX
Secret Key: sk_zebu_test_YYYYYYYY
```

### **Test Scenarios**

#### **Test 1: Broker Account Creation**

```bash
curl -X POST https://api-dev.quantleap.in/partner/broker-accounts \
  -H 'Authorization: Bearer pk_zebu_test_XXXXXXXX' \
  -H 'X-Partner-Secret: sk_zebu_test_YYYYYYYY' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_email": "testuser@zebu.com",
    "broker_name": "zebu",
    "client_id": "TEST123",
    "api_key": "test_api_key",
    "api_secret": "test_api_secret"
  }'

# Expected: 201 Created
```

#### **Test 2: OAuth Flow**

```bash
# Step 1: Initiate OAuth
curl -X POST https://api-dev.quantleap.in/partner/broker-accounts/TEST123/oauth/initiate \
  -H 'Authorization: Bearer pk_zebu_test_XXXXXXXX' \
  -H 'X-Partner-Secret: sk_zebu_test_YYYYYYYY' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_email": "testuser@zebu.com"
  }'

# Expected: 200 OK with oauth_url

# Step 2: Complete OAuth (use mock request_token in dev)
curl -X POST https://api-dev.quantleap.in/partner/broker-accounts/TEST123/oauth/callback \
  -H 'Authorization: Bearer pk_zebu_test_XXXXXXXX' \
  -H 'X-Partner-Secret: sk_zebu_test_YYYYYYYY' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_email": "testuser@zebu.com",
    "request_token": "mock_token_12345",
    "state": "state_from_step1"
  }'

# Expected: 200 OK with token expiry
```

#### **Test 3: Strategy Subscription**

```bash
curl -X POST https://api-dev.quantleap.in/partner/marketplace/subscribe \
  -H 'Authorization: Bearer pk_zebu_test_XXXXXXXX' \
  -H 'X-Partner-Secret: sk_zebu_test_YYYYYYYY' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_email": "testuser@zebu.com",
    "template_id": "basket_admin_test_strategy",
    "broker_client_id": "TEST123",
    "lot_multiplier": 1.0
  }'

# Expected: 201 Created with subscription details
```

#### **Test 4: List User Subscriptions**

```bash
curl -X GET 'https://api-dev.quantleap.in/partner/subscriptions?user_email=testuser@zebu.com' \
  -H 'Authorization: Bearer pk_zebu_test_XXXXXXXX' \
  -H 'X-Partner-Secret: sk_zebu_test_YYYYYYYY'

# Expected: 200 OK with array of subscriptions
```

### **Mock Data Available in Dev**

- **Test Strategies**: 3 pre-configured strategies
- **Mock OAuth**: No real Zebu credentials needed
- **Simulated Execution**: Orders logged but not placed
- **No Billing**: All subscriptions free in dev environment

---

## 9. Go-Live Checklist

### **Pre-Launch** (2 weeks before)

- [ ] **API Integration Complete**
  - [ ] Broker account creation tested
  - [ ] OAuth flow working end-to-end
  - [ ] Subscription creation functional
  - [ ] Error handling implemented

- [ ] **Security Review**
  - [ ] API keys stored securely (env variables)
  - [ ] HTTPS enforced on all endpoints
  - [ ] OAuth state validation implemented
  - [ ] Rate limiting configured

- [ ] **User Experience**
  - [ ] Clear UI for OAuth login prompt
  - [ ] Subscription management interface
  - [ ] Error messages user-friendly
  - [ ] Push notifications configured

- [ ] **Documentation**
  - [ ] User guide created
  - [ ] Support team trained
  - [ ] FAQ documented
  - [ ] Contact escalation path defined

### **Launch Week**

- [ ] **Soft Launch** (Day 1-3)
  - [ ] Enable for 10 beta users
  - [ ] Monitor API logs daily
  - [ ] Collect user feedback
  - [ ] Fix critical issues

- [ ] **Gradual Rollout** (Day 4-7)
  - [ ] Enable for 100 users
  - [ ] Monitor execution success rate
  - [ ] Track OAuth completion rate
  - [ ] Measure subscription conversion

### **Post-Launch** (First Month)

- [ ] **Monitoring**
  - [ ] Daily API health check
  - [ ] Weekly execution reports
  - [ ] Monthly revenue reconciliation
  - [ ] User satisfaction surveys

- [ ] **Optimization**
  - [ ] Analyze drop-off points
  - [ ] Improve OAuth completion rate
  - [ ] Reduce error rates
  - [ ] Enhance user education

### **Success Metrics**

| Metric | Target | Measurement |
|--------|--------|-------------|
| **OAuth Completion Rate** | > 80% | Daily logins / Active users |
| **Subscription Conversion** | > 15% | Subscriptions / Portal visitors |
| **Execution Success Rate** | > 95% | Successful orders / Total orders |
| **User Retention (30 days)** | > 70% | Active subs / Initial subs |
| **Revenue per User** | ₹999+ | Avg subscription value |

---

## 📞 Support & Contact

### **Technical Support**

- **Email**: partners@quantleap.in
- **Response Time**: < 4 hours (business hours)
- **Escalation**: critical@quantleap.in (< 1 hour)

### **Integration Assistance**

- **Developer Portal**: https://developers.quantleap.in
- **API Status**: https://status.quantleap.in
- **Slack Channel**: #partner-integration (request access)

### **Business Inquiries**

- **Partnerships**: partnerships@quantleap.in
- **Billing**: billing@quantleap.in
- **Compliance**: compliance@quantleap.in

---

## 📖 Additional Resources

- [Partner API Documentation](./PARTNER_API_DOCUMENTATION.md) - Complete API reference
- [Quick Reference Guide](./PARTNER_API_QUICK_REFERENCE.md) - Common code snippets
- [OpenAPI Specification](./partner-api-openapi.json) - Import into Postman
- [Subscription Management](./SUBSCRIPTION_MANAGEMENT_API_REFERENCE.md) - User management APIs

---

**Last Updated**: October 10, 2025
**Document Version**: 1.0
**Status**: Production Ready

---

## 🎯 Quick Summary

**3 Simple Steps to Integration**:

1. **One-Time Setup**: Call `/partner/broker-accounts` with user's api_key/api_secret
2. **Daily OAuth**: Call `/partner/broker-accounts/{id}/oauth/initiate` each morning
3. **Subscribe**: Call `/partner/marketplace/subscribe` for each strategy subscription

**Key Points**:
- ✅ Credentials stored once, OAuth refreshed daily
- ✅ Multiple subscriptions use same broker account
- ✅ Execution fully automatic (no user action needed)
- ✅ 30% commission on all subscriptions
- ✅ Monthly automated settlement

**Questions?** Contact partners@quantleap.in
