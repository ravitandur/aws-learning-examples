# Subscription Management API Reference

Complete API reference for subscription management features available to both **QuantLeap Users** and **Partner Users** (Zebu, etc.).

## 🚀 Deployment Status

**✅ DEPLOYED AND OPERATIONAL**
- **Deployment Date**: October 10, 2025
- **Stack Name**: `ql-algo-trading-dev-options-trading-stack`
- **API Gateway**: `https://vrd3rrtyx4.execute-api.ap-south-1.amazonaws.com/dev/`
- **Lambda Function**: `ql-algo-trading-dev-options-subscription-manager`
- **Region**: `ap-south-1` (Mumbai)
- **Environment**: Development

All endpoints documented below are **live and operational** in AWS.

---

## 📊 Quick Comparison

| Feature | QuantLeap Users | Partner Users |
|---------|-----------------|---------------|
| **Base Path** | `/options/user/subscriptions` | `/partner/subscriptions` |
| **Authentication** | Cognito JWT Token | Partner API Key + Secret |
| **View All Subscriptions** | ✅ Own subscriptions only | ✅ All partner users' subscriptions |
| **Filter by User** | N/A (always current user) | ✅ Query param `?user_email=` |
| **Pause/Resume** | ✅ Self-service | ✅ On behalf of users |
| **Cancel** | ✅ Self-service | ✅ On behalf of users |

---

## 🔐 QuantLeap User API (Cognito Authentication)

**Base URL**: `https://vrd3rrtyx4.execute-api.ap-south-1.amazonaws.com/dev`

**Authentication**:
```http
Authorization: Bearer {cognito_jwt_token}
```

---

### **1. List All User Subscriptions**

```http
GET /options/user/subscriptions
```

**Description**: Get all subscriptions for the authenticated user.

**Headers**:
```http
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

**Response 200**:
```json
{
  "subscriptions": [
    {
      "subscription_id": "sub_direct_abc123",
      "template_basket_id": "basket_admin_iron_condor",
      "template_name": "Iron Condor Weekly - NIFTY",
      "template_owner_id": "admin@quantleap.in",
      "status": "ACTIVE",
      "subscribed_at": "2025-10-10T10:00:00Z",
      "paused_at": null,
      "resumed_at": null,
      "cancelled_at": null,
      "last_status_change_at": "2025-10-10T10:00:00Z",
      "subscription_price": 999,
      "partner_commission": 0,
      "partner_id": null,
      "broker_account_id": "zebu_acc_12345",
      "custom_lot_multiplier": 1.0,
      "next_billing_date": "2025-11-10T10:00:00Z",
      "auto_renew": true
    },
    {
      "subscription_id": "sub_direct_xyz789",
      "template_basket_id": "basket_admin_straddle",
      "template_name": "Weekly Straddle - BANKNIFTY",
      "status": "PAUSED",
      "subscribed_at": "2025-09-15T14:30:00Z",
      "paused_at": "2025-10-01T09:00:00Z",
      "subscription_price": 1499,
      "custom_lot_multiplier": 2.0,
      "broker_account_id": "angel_acc_67890"
    }
  ],
  "total": 2
}
```

**cURL Example**:
```bash
curl -X GET 'https://vrd3rrtyx4.execute-api.ap-south-1.amazonaws.com/dev/options/user/subscriptions' \
  -H 'Authorization: Bearer YOUR_COGNITO_TOKEN'
```

---

### **2. Get Subscription Details**

```http
GET /options/user/subscriptions/{subscription_id}
```

**Description**: Get detailed information about a specific subscription including status history.

**Path Parameters**:
- `subscription_id` (required) - The subscription ID

**Response 200**:
```json
{
  "subscription": {
    "subscription_id": "sub_direct_abc123",
    "user_id": "user@example.com",
    "template_basket_id": "basket_admin_iron_condor",
    "template_owner_id": "admin@quantleap.in",
    "status": "ACTIVE",
    "subscribed_at": "2025-10-10T10:00:00Z",
    "paused_at": null,
    "resumed_at": null,
    "cancelled_at": null,
    "last_status_change_at": "2025-10-10T10:00:00Z",
    "status_history": [
      {
        "status": "ACTIVE",
        "timestamp": "2025-10-10T10:00:00Z",
        "changed_by": "user@example.com",
        "reason": "Initial subscription"
      }
    ],
    "subscription_price": 999,
    "partner_commission": 0,
    "partner_id": null,
    "broker_account_id": "zebu_acc_12345",
    "custom_lot_multiplier": 1.0,
    "next_billing_date": "2025-11-10T10:00:00Z",
    "auto_renew": true
  },
  "template": {
    "basket_name": "Iron Condor Weekly - NIFTY",
    "description": "Conservative weekly iron condor strategy on NIFTY",
    "is_marketplace_enabled": true,
    "expected_return_monthly": 8.5,
    "risk_level": "low"
  }
}
```

**Response 404**:
```json
{
  "error": "Subscription not found"
}
```

**cURL Example**:
```bash
curl -X GET 'https://api.quantleap.in/options/user/subscriptions/sub_direct_abc123' \
  -H 'Authorization: Bearer YOUR_COGNITO_TOKEN'
```

---

### **3. Pause Subscription**

```http
PUT /options/user/subscriptions/{subscription_id}/pause
```

**Description**: Temporarily pause an active subscription. Strategy execution stops but billing continues.

**Path Parameters**:
- `subscription_id` (required) - The subscription ID to pause

**Business Rules**:
- ✅ Can only pause `ACTIVE` subscriptions
- ✅ Strategy execution stops immediately
- ✅ Billing continues (user still charged monthly)
- ✅ Can be resumed at any time
- ✅ Status history tracked

**Response 200**:
```json
{
  "message": "Subscription paused successfully",
  "subscription_id": "sub_direct_abc123",
  "status": "PAUSED",
  "paused_at": "2025-10-15T14:30:00Z"
}
```

**Response 400** (Invalid status):
```json
{
  "error": "Invalid status transition",
  "message": "Can only pause ACTIVE subscriptions. Current status: PAUSED"
}
```

**Response 404**:
```json
{
  "error": "Subscription not found"
}
```

**cURL Example**:
```bash
curl -X PUT 'https://api.quantleap.in/options/user/subscriptions/sub_direct_abc123/pause' \
  -H 'Authorization: Bearer YOUR_COGNITO_TOKEN'
```

**JavaScript Example**:
```javascript
const response = await fetch(
  `https://api.quantleap.in/options/user/subscriptions/${subscriptionId}/pause`,
  {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${cognitoToken}`,
      'Content-Type': 'application/json'
    }
  }
);

const result = await response.json();
console.log(result.message); // "Subscription paused successfully"
```

---

### **4. Resume Subscription**

```http
PUT /options/user/subscriptions/{subscription_id}/resume
```

**Description**: Resume a paused subscription. Strategy execution resumes on next market open.

**Path Parameters**:
- `subscription_id` (required) - The subscription ID to resume

**Business Rules**:
- ✅ Can only resume `PAUSED` subscriptions
- ✅ Strategy execution resumes immediately
- ✅ Billing was never stopped
- ✅ Status history preserved

**Response 200**:
```json
{
  "message": "Subscription resumed successfully",
  "subscription_id": "sub_direct_abc123",
  "status": "ACTIVE",
  "resumed_at": "2025-10-20T09:00:00Z"
}
```

**Response 400** (Invalid status):
```json
{
  "error": "Invalid status transition",
  "message": "Can only resume PAUSED subscriptions. Current status: ACTIVE"
}
```

**cURL Example**:
```bash
curl -X PUT 'https://api.quantleap.in/options/user/subscriptions/sub_direct_abc123/resume' \
  -H 'Authorization: Bearer YOUR_COGNITO_TOKEN'
```

---

### **5. Cancel Subscription**

```http
DELETE /options/user/subscriptions/{subscription_id}
```

**Description**: Permanently cancel a subscription. This action cannot be undone.

**Path Parameters**:
- `subscription_id` (required) - The subscription ID to cancel

**Business Rules**:
- ✅ Can cancel from `ACTIVE` or `PAUSED` status
- ✅ Strategy execution stops immediately
- ✅ Billing stops (no future charges)
- ❌ **Cannot be resumed** (permanent action)
- ✅ Template subscriber count decremented
- ✅ User can create new subscription if desired

**Response 200**:
```json
{
  "message": "Subscription cancelled successfully",
  "subscription_id": "sub_direct_abc123",
  "status": "CANCELLED",
  "cancelled_at": "2025-10-25T16:45:00Z"
}
```

**Response 404**:
```json
{
  "error": "Subscription not found"
}
```

**cURL Example**:
```bash
curl -X DELETE 'https://api.quantleap.in/options/user/subscriptions/sub_direct_abc123' \
  -H 'Authorization: Bearer YOUR_COGNITO_TOKEN'
```

---

## 🤝 Partner API (Partner Authentication)

**Base URL**: `https://257y9owov2.execute-api.ap-south-1.amazonaws.com/dev`

**Authentication**:
```http
Authorization: Bearer pk_zebu_live_XXXXXXXX
X-Partner-Secret: sk_zebu_live_YYYYYYYY
```

---

### **1. List All Partner Subscriptions**

```http
GET /partner/subscriptions
```

**Description**: Get all subscriptions created by this partner. Supports filtering by user email.

**Query Parameters**:
- `user_email` (optional) - Filter by specific user email
- `status` (optional) - Filter by status (`ACTIVE`, `PAUSED`, `CANCELLED`, `EXPIRED`)
- `limit` (optional) - Results per page (default: 50, max: 100)
- `offset` (optional) - Pagination offset (default: 0)

**Headers**:
```http
Authorization: Bearer pk_zebu_live_XXXXXXXX
X-Partner-Secret: sk_zebu_live_YYYYYYYY
Content-Type: application/json
```

**Response 200**:
```json
{
  "subscriptions": [
    {
      "subscription_id": "sub_zebu_001",
      "user_id": "user1@example.com",
      "template_basket_id": "basket_admin_iron_condor",
      "template_name": "Iron Condor Weekly - NIFTY",
      "status": "ACTIVE",
      "subscribed_at": "2025-10-10T10:00:00Z",
      "subscription_price": 999,
      "partner_commission": 299.7,
      "partner_id": "partner_zebu_live",
      "broker_account_id": "zebu_acc_12345",
      "custom_lot_multiplier": 1.0,
      "next_billing_date": "2025-11-10T10:00:00Z"
    },
    {
      "subscription_id": "sub_zebu_002",
      "user_id": "user2@example.com",
      "template_basket_id": "basket_admin_iron_condor",
      "template_name": "Iron Condor Weekly - NIFTY",
      "status": "PAUSED",
      "subscribed_at": "2025-10-08T14:20:00Z",
      "paused_at": "2025-10-12T11:30:00Z",
      "subscription_price": 999,
      "partner_commission": 299.7,
      "broker_account_id": "zebu_acc_67890",
      "custom_lot_multiplier": 2.0
    }
  ],
  "total": 2,
  "partner_id": "partner_zebu_live",
  "limit": 50,
  "offset": 0
}
```

**Filter by Specific User**:
```http
GET /partner/subscriptions?user_email=user1@example.com
```

**Response with Filter**:
```json
{
  "subscriptions": [
    {
      "subscription_id": "sub_zebu_001",
      "user_id": "user1@example.com",
      "status": "ACTIVE",
      ...
    }
  ],
  "total": 1,
  "partner_id": "partner_zebu_live",
  "filtered_by": "user1@example.com"
}
```

**Response 401** (Invalid credentials):
```json
{
  "error": "Unauthorized",
  "message": "Invalid Partner API Key or Secret"
}
```

**cURL Example**:
```bash
# List all partner subscriptions
curl -X GET 'https://api.quantleap.in/partner/subscriptions' \
  -H 'Authorization: Bearer pk_zebu_live_XXXXXXXX' \
  -H 'X-Partner-Secret: sk_zebu_live_YYYYYYYY'

# Filter by user
curl -X GET 'https://api.quantleap.in/partner/subscriptions?user_email=user@example.com' \
  -H 'Authorization: Bearer pk_zebu_live_XXXXXXXX' \
  -H 'X-Partner-Secret: sk_zebu_live_YYYYYYYY'
```

**JavaScript Example**:
```javascript
const axios = require('axios');

const client = axios.create({
  baseURL: 'https://api.quantleap.in',
  headers: {
    'Authorization': 'Bearer pk_zebu_live_XXXXXXXX',
    'X-Partner-Secret': 'sk_zebu_live_YYYYYYYY'
  }
});

// List all subscriptions
const allSubs = await client.get('/partner/subscriptions');
console.log(`Total: ${allSubs.data.total}`);

// Filter by user
const userSubs = await client.get('/partner/subscriptions', {
  params: { user_email: 'user@example.com' }
});
```

---

### **2. Get Partner Subscription Details**

```http
GET /partner/subscriptions/{subscription_id}
```

**Description**: Get detailed information about a specific subscription created by this partner.

**Path Parameters**:
- `subscription_id` (required) - The subscription ID

**Security**: Partner can only view subscriptions where `partner_id` matches their credentials.

**Response 200**:
```json
{
  "subscription": {
    "subscription_id": "sub_zebu_001",
    "user_id": "user@example.com",
    "template_basket_id": "basket_admin_iron_condor",
    "status": "ACTIVE",
    "subscribed_at": "2025-10-10T10:00:00Z",
    "status_history": [
      {
        "status": "ACTIVE",
        "timestamp": "2025-10-10T10:00:00Z",
        "changed_by": "partner_zebu_live",
        "reason": "Partner subscription via API"
      }
    ],
    "subscription_price": 999,
    "partner_commission": 299.7,
    "partner_id": "partner_zebu_live",
    "broker_account_id": "zebu_acc_12345",
    "custom_lot_multiplier": 1.0
  },
  "template": {
    "basket_name": "Iron Condor Weekly - NIFTY",
    "description": "Conservative weekly iron condor strategy",
    "is_marketplace_enabled": true
  }
}
```

**Response 403** (Forbidden):
```json
{
  "error": "Forbidden",
  "message": "This subscription does not belong to your partner account"
}
```

**Response 404**:
```json
{
  "error": "Subscription not found"
}
```

**cURL Example**:
```bash
curl -X GET 'https://api.quantleap.in/partner/subscriptions/sub_zebu_001' \
  -H 'Authorization: Bearer pk_zebu_live_XXXXXXXX' \
  -H 'X-Partner-Secret: sk_zebu_live_YYYYYYYY'
```

---

### **3. Pause Partner Subscription**

```http
PUT /partner/subscriptions/{subscription_id}/pause
```

**Description**: Pause a subscription on behalf of a partner user.

**Path Parameters**:
- `subscription_id` (required) - The subscription ID to pause

**Use Case**: Zebu user requests pause via Zebu app → Zebu backend calls this endpoint → User never visits QuantLeap platform.

**Business Rules**: Same as QuantLeap user pause (ACTIVE → PAUSED only)

**Security**: Validates that `partner_id` matches the subscription.

**Response 200**:
```json
{
  "message": "Subscription paused successfully",
  "subscription_id": "sub_zebu_001",
  "status": "PAUSED",
  "paused_at": "2025-10-15T14:30:00Z"
}
```

**Response 403**:
```json
{
  "error": "Forbidden",
  "message": "This subscription does not belong to your partner account"
}
```

**Response 400**:
```json
{
  "error": "Invalid status transition",
  "message": "Can only pause ACTIVE subscriptions. Current status: PAUSED"
}
```

**cURL Example**:
```bash
curl -X PUT 'https://api.quantleap.in/partner/subscriptions/sub_zebu_001/pause' \
  -H 'Authorization: Bearer pk_zebu_live_XXXXXXXX' \
  -H 'X-Partner-Secret: sk_zebu_live_YYYYYYYY'
```

**Node.js Example**:
```javascript
// Zebu backend service
async function pauseUserSubscription(subscriptionId) {
  const response = await fetch(
    `https://api.quantleap.in/partner/subscriptions/${subscriptionId}/pause`,
    {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${process.env.QUANTLEAP_API_KEY}`,
        'X-Partner-Secret': process.env.QUANTLEAP_API_SECRET
      }
    }
  );

  if (response.status === 403) {
    throw new Error('Subscription does not belong to Zebu');
  }

  return await response.json();
}
```

---

### **4. Resume Partner Subscription**

```http
PUT /partner/subscriptions/{subscription_id}/resume
```

**Description**: Resume a paused subscription on behalf of a partner user.

**Path Parameters**:
- `subscription_id` (required) - The subscription ID to resume

**Business Rules**: Same as QuantLeap user resume (PAUSED → ACTIVE only)

**Response 200**:
```json
{
  "message": "Subscription resumed successfully",
  "subscription_id": "sub_zebu_001",
  "status": "ACTIVE",
  "resumed_at": "2025-10-20T09:00:00Z"
}
```

**Response 403**:
```json
{
  "error": "Forbidden",
  "message": "This subscription does not belong to your partner account"
}
```

**cURL Example**:
```bash
curl -X PUT 'https://api.quantleap.in/partner/subscriptions/sub_zebu_001/resume' \
  -H 'Authorization: Bearer pk_zebu_live_XXXXXXXX' \
  -H 'X-Partner-Secret: sk_zebu_live_YYYYYYYY'
```

---

### **5. Cancel Partner Subscription**

```http
DELETE /partner/subscriptions/{subscription_id}
```

**Description**: Permanently cancel a subscription on behalf of a partner user.

**Path Parameters**:
- `subscription_id` (required) - The subscription ID to cancel

**Business Rules**: Same as QuantLeap user cancel (permanent, cannot be resumed)

**Security**: Validates `partner_id` ownership. Partner commission tracking preserved for historical reporting.

**Response 200**:
```json
{
  "message": "Subscription cancelled successfully",
  "subscription_id": "sub_zebu_001",
  "status": "CANCELLED",
  "cancelled_at": "2025-10-25T16:45:00Z"
}
```

**Response 403**:
```json
{
  "error": "Forbidden",
  "message": "This subscription does not belong to your partner account"
}
```

**cURL Example**:
```bash
curl -X DELETE 'https://api.quantleap.in/partner/subscriptions/sub_zebu_001' \
  -H 'Authorization: Bearer pk_zebu_live_XXXXXXXX' \
  -H 'X-Partner-Secret: sk_zebu_live_YYYYYYYY'
```

---

## 📊 Status Transitions

### **Valid Transitions**

```mermaid
graph LR
    A[ACTIVE] -->|pause| B[PAUSED]
    B -->|resume| A
    A -->|cancel| C[CANCELLED]
    B -->|cancel| C
```

| From Status | Action | To Status | Reversible? |
|-------------|--------|-----------|-------------|
| `ACTIVE` | Pause | `PAUSED` | ✅ Yes |
| `PAUSED` | Resume | `ACTIVE` | ✅ Yes |
| `ACTIVE` | Cancel | `CANCELLED` | ❌ No |
| `PAUSED` | Cancel | `CANCELLED` | ❌ No |

### **Invalid Transitions**

| Current Status | Attempted Action | Result |
|---------------|------------------|---------|
| `PAUSED` | Pause again | ❌ 400 Bad Request |
| `ACTIVE` | Resume | ❌ 400 Bad Request |
| `CANCELLED` | Pause | ❌ 400 Bad Request |
| `CANCELLED` | Resume | ❌ 400 Bad Request |
| `CANCELLED` | Cancel again | ❌ 400 Bad Request |

---

## 🔄 Subscription Lifecycle Examples

### **Example 1: Normal Usage**

```javascript
// Day 1: User subscribes
POST /options/marketplace/subscribe/basket_admin_123
// Status: ACTIVE

// Day 10: User temporarily pauses
PUT /options/user/subscriptions/sub_abc123/pause
// Status: PAUSED (billing continues)

// Day 15: User resumes
PUT /options/user/subscriptions/sub_abc123/resume
// Status: ACTIVE (execution resumes)

// Day 30: User permanently cancels
DELETE /options/user/subscriptions/sub_abc123
// Status: CANCELLED (billing stops, cannot be resumed)
```

### **Example 2: Partner User via Zebu**

```javascript
// Day 1: Zebu subscribes user
POST /partner/marketplace/subscribe
Body: { user_email: "user@example.com", basket_id: "..." }
// Status: ACTIVE, partner_id: "partner_zebu_live"

// Day 5: User requests pause via Zebu app
PUT /partner/subscriptions/sub_zebu_001/pause
// Status: PAUSED (Zebu API call)

// Day 8: User resumes via Zebu app
PUT /partner/subscriptions/sub_zebu_001/resume
// Status: ACTIVE (Zebu API call)

// Day 20: User cancels via Zebu app
DELETE /partner/subscriptions/sub_zebu_001
// Status: CANCELLED (Zebu API call)
// Partner commission history preserved for reporting
```

---

## 🚦 Rate Limiting

### **QuantLeap Users**
- **Limit**: Unlimited (protected by Cognito authentication)
- **Protection**: AWS WAF for DDoS

### **Partner API**
- **Limit**: 60 requests per minute (all endpoints combined)
- **Algorithm**: Token bucket with DynamoDB tracking

**Rate Limit Headers**:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1696936200
```

**Response 429** (Rate Limit Exceeded):
```json
{
  "error": "rate_limit",
  "message": "Rate limit exceeded. Maximum 60 requests per minute allowed.",
  "code": "RATE_LIMIT_EXCEEDED",
  "details": {
    "limit": 60,
    "remaining": 0,
    "reset_at": "2025-10-10T10:30:00Z"
  }
}
```

**Retry Strategy**:
```javascript
async function retryWithBackoff(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error.status === 429 && i < maxRetries - 1) {
        const delay = Math.min(1000 * Math.pow(2, i), 30000);
        await new Promise(resolve => setTimeout(resolve, delay));
      } else {
        throw error;
      }
    }
  }
}
```

---

## 🧪 Complete Testing Example

### **Postman Collection**

```json
{
  "info": {
    "name": "QuantLeap Subscription Management",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "QuantLeap User - List Subscriptions",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{cognito_token}}"
          }
        ],
        "url": "{{base_url}}/options/user/subscriptions"
      }
    },
    {
      "name": "QuantLeap User - Pause Subscription",
      "request": {
        "method": "PUT",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{cognito_token}}"
          }
        ],
        "url": "{{base_url}}/options/user/subscriptions/{{subscription_id}}/pause"
      }
    },
    {
      "name": "Partner API - List Subscriptions",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{partner_api_key}}"
          },
          {
            "key": "X-Partner-Secret",
            "value": "{{partner_secret}}"
          }
        ],
        "url": "{{base_url}}/partner/subscriptions"
      }
    }
  ]
}
```

---

## 📝 Summary

### **QuantLeap Users**
- ✅ 5 endpoints for complete self-service subscription management
- ✅ Cognito JWT authentication
- ✅ Can pause/resume/cancel own subscriptions
- ✅ Status history tracked

### **Partner Users**
- ✅ 5 endpoints for managing all partner user subscriptions
- ✅ Partner API Key + Secret authentication
- ✅ Can view, pause, resume, cancel on behalf of users
- ✅ Filter by user email
- ✅ Revenue attribution preserved
- ✅ Security: Partner ownership validated

### **Status Management**
- ✅ `ACTIVE` ⇄ `PAUSED` (reversible)
- ✅ `ACTIVE/PAUSED` → `CANCELLED` (permanent)
- ✅ Strategy executor respects status
- ✅ Complete audit trail via status_history

---

**Version**: 1.0.0
**Last Updated**: October 10, 2025
**Status**: Implementation Ready
