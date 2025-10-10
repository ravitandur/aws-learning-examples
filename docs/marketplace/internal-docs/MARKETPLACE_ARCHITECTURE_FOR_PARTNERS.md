# Quantleap Analytics - B2B2C Marketplace Architecture
## Partner Integration Guide for Zebu & External Brokers

**Version**: 1.0
**Date**: October 10, 2025
**Platform**: Quantleap Algo Trading Platform
**Document Type**: Architecture & Integration Guide

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Business Model](#business-model)
4. [Data Flow & System Components](#data-flow--system-components)
5. [Integration Patterns](#integration-patterns)
6. [API Reference](#api-reference)
7. [Authentication & Security](#authentication--security)
8. [Revenue Attribution](#revenue-attribution)
9. [Deployment Architecture](#deployment-architecture)
10. [Testing & Go-Live](#testing--go-live)

---

## 1. Executive Summary

### What is the Marketplace?

The Quantleap Algo Trading Marketplace is a **B2B2C platform** where:
- **Platform (Quantleap)**: Creates and manages algorithmic trading strategies
- **Broker Partners (Zebu)**: White-label the marketplace in their portal
- **End Users**: Subscribe to strategies through their broker's platform

### Key Benefits for Zebu

✅ **Revenue Sharing**: 30% of subscription fees
✅ **White-Label Integration**: Seamless embedding in your portal
✅ **Zero Strategy Maintenance**: Quantleap manages all strategies
✅ **Auto User Linking**: Automatic broker account association
✅ **Real-Time Updates**: Strategy changes propagate instantly
✅ **Institutional-Grade Execution**: 0-second precision timing

### Business Case Example

```
Monthly Subscription: ₹999/strategy
100 Zebu users subscribe

Revenue Split:
├─> Quantleap: ₹69,930 (70%)
└─> Zebu: ₹29,970 (30%)

Annual for 100 users: ₹3,59,640 (Zebu commission)
Annual for 1000 users: ₹35,96,400 (Zebu commission)
```

---

## 2. Architecture Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ZEBU TRADING PLATFORM                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │        Marketplace Widget (Embedded in Zebu Portal)     │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │ │
│  │  │ Browse       │  │ Strategy     │  │ Subscribe    │ │ │
│  │  │ Strategies   │  │ Details      │  │ Button       │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
│                            ↓                                 │
│                   Zebu Backend API                           │
│                            ↓                                 │
└────────────────────────────┼─────────────────────────────────┘
                             ↓
              ┌──────────────┴──────────────┐
              │  Partner API Authentication  │
              │  (API Key + Secret)          │
              └──────────────┬──────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│              QUANTLEAP ALGO TRADING PLATFORM                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Partner API Gateway                        │ │
│  │  GET  /partner/marketplace/templates                    │ │
│  │  POST /partner/marketplace/subscribe                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                            ↓                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Business Logic Layer (Lambda Functions)         │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │ │
│  │  │ Marketplace  │  │ Subscription │  │ Partner API  │ │ │
│  │  │ Manager      │  │ Manager      │  │ Manager      │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
│                            ↓                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Data Layer (DynamoDB)                      │ │
│  │  - Trading Configurations (Strategies)                  │ │
│  │  - User Subscriptions                                   │ │
│  │  - Partner Revenue Attribution                          │ │
│  │  - Broker Account Linking                               │ │
│  └────────────────────────────────────────────────────────┘ │
│                            ↓                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           Strategy Execution Engine                     │ │
│  │  - 0-Second Precision Step Functions                    │ │
│  │  - Multi-Broker Parallel Execution                      │ │
│  │  - Real-Time Market Data Integration                    │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                             ↓
              ┌──────────────┴──────────────┐
              │     Broker APIs (Zebu)       │
              │  - Order Placement           │
              │  - Position Management       │
              │  - Account Information       │
              └──────────────────────────────┘
```

### 2.2 Component Overview

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API Gateway** | AWS API Gateway | REST API endpoint for partner integration |
| **Authentication** | Custom API Key + Secret | Secure partner authentication with rate limiting |
| **Business Logic** | AWS Lambda (Python 3.11) | Marketplace, subscription, and partner management |
| **Database** | DynamoDB | Single-table design with GSI optimization |
| **Execution Engine** | AWS Step Functions | 0-second precision strategy execution |
| **Monitoring** | CloudWatch | Real-time monitoring and alerting |

---

## 3. Business Model

### 3.1 Shared Template Model (Zero-Cloning Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                  QUANTLEAP ADMIN CREATES                     │
│                                                              │
│   ┌──────────────────────────────────────────────────┐     │
│   │  Strategy Template (Single Source of Truth)       │     │
│   │  - Strategy Name: "Iron Condor Weekly"           │     │
│   │  - Entry Time: 09:20 AM                          │     │
│   │  - Index: NIFTY                                   │     │
│   │  - Legs: 4 (Buy/Sell Calls/Puts)                │     │
│   │  - Risk Controls: SL, Target, Trailing           │     │
│   └──────────────────────────────────────────────────┘     │
│                            │                                 │
│                            │ ONE STRATEGY                    │
│                            │ MANY SUBSCRIBERS                │
│                            ↓                                 │
└─────────────────────────────────────────────────────────────┘
                             │
            ┌────────────────┼────────────────┐
            ↓                ↓                ↓
    ┌───────────┐    ┌───────────┐    ┌───────────┐
    │  Zebu     │    │  Zebu     │    │  Zebu     │
    │  User 1   │    │  User 2   │    │  User 3   │
    │           │    │           │    │           │
    │ REFERENCE │    │ REFERENCE │    │ REFERENCE │
    │ to Admin  │    │ to Admin  │    │ to Admin  │
    │ Strategy  │    │ Strategy  │    │ Strategy  │
    └───────────┘    └───────────┘    └───────────┘
         │                │                │
         ↓                ↓                ↓
    ┌───────────┐    ┌───────────┐    ┌───────────┐
    │ User owns │    │ User owns │    │ User owns │
    │ Broker    │    │ Broker    │    │ Broker    │
    │ Allocation│    │ Allocation│    │ Allocation│
    │           │    │           │    │           │
    │ Zebu A/C  │    │ Zebu A/C  │    │ Zebu A/C  │
    │ 1 lot     │    │ 2 lots    │    │ 3 lots    │
    └───────────┘    └───────────┘    └───────────┘
```

### 3.2 Key Principles

#### **NO CLONING** ✅
- Users subscribe by **reference** to admin strategy
- Admin updates propagate **instantly** to all subscribers
- Single source of truth ensures consistency

#### **USER-OWNED EXECUTION** ✅
- Users specify their own broker account
- Users control lot multipliers
- Users can pause/resume independently

#### **REVENUE ATTRIBUTION** ✅
- Every subscription tracked to partner
- Monthly commission calculated automatically
- Transparent reporting dashboard

---

## 4. Data Flow & System Components

### 4.1 User Subscription Flow

```
Step 1: User Browses Marketplace (via Zebu Portal)
┌─────────────────────────────────────────────┐
│ GET /partner/marketplace/templates          │
│                                             │
│ Request Headers:                            │
│   Authorization: Bearer pk_zebu_live_XXX    │
│   X-Partner-Secret: sk_zebu_live_YYY        │
│                                             │
│ Query Parameters:                           │
│   ?category=NIFTY                           │
│   ?difficulty=INTERMEDIATE                  │
│   ?pricing_type=PAID                        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Response: List of Available Strategies      │
│                                             │
│ [                                           │
│   {                                         │
│     "basket_id": "bsk_12345",               │
│     "name": "Iron Condor Weekly",           │
│     "description": "Weekly NIFTY strategy", │
│     "category": "NIFTY",                    │
│     "difficulty": "INTERMEDIATE",           │
│     "pricing": {                            │
│       "type": "PAID",                       │
│       "monthly_fee": 999,                   │
│       "currency": "INR"                     │
│     },                                      │
│     "performance": {                        │
│       "subscriber_count": 45,               │
│       "avg_monthly_return": 12.5            │
│     },                                      │
│     "tags": ["NIFTY", "WEEKLY", "OPTIONS"] │
│   }                                         │
│ ]                                           │
└─────────────────────────────────────────────┘
```

```
Step 2: User Subscribes (via Zebu Portal)
┌─────────────────────────────────────────────┐
│ POST /partner/marketplace/subscribe         │
│                                             │
│ Request Headers:                            │
│   Authorization: Bearer pk_zebu_live_XXX    │
│   X-Partner-Secret: sk_zebu_live_YYY        │
│   Content-Type: application/json            │
│                                             │
│ Request Body:                               │
│ {                                           │
│   "template_basket_id": "bsk_12345",        │
│   "user_email": "user@example.com",         │
│   "user_name": "John Doe",                  │
│   "broker_client_id": "ZEBU123456",         │
│   "lot_multiplier": 1,                      │
│   "auto_link_broker": true                  │
│ }                                           │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Quantleap Platform Processing:              │
│                                             │
│ 1. Validate partner API key & secret       │
│ 2. Check rate limits (60 req/min)          │
│ 3. Get or create user account              │
│ 4. Create subscription (by reference)       │
│ 5. Auto-link Zebu broker account           │
│ 6. Create broker allocation                 │
│ 7. Track revenue attribution to Zebu       │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Response: Subscription Created              │
│                                             │
│ {                                           │
│   "statusCode": 200,                        │
│   "subscription": {                         │
│     "subscription_id": "sub_67890",         │
│     "user_id": "usr_abc123",                │
│     "template_basket_id": "bsk_12345",      │
│     "status": "ACTIVE",                     │
│     "pricing": {                            │
│       "monthly_fee": 999,                   │
│       "next_billing_date": "2025-11-10"    │
│     },                                      │
│     "broker_allocation": {                  │
│       "allocation_id": "alloc_xyz789",      │
│       "broker_id": "zebu",                  │
│       "client_id": "ZEBU123456",            │
│       "lot_multiplier": 1                   │
│     },                                      │
│     "partner_attribution": {                │
│       "partner_id": "zebu",                 │
│       "commission_rate": 0.30               │
│     }                                       │
│   }                                         │
│ }                                           │
└─────────────────────────────────────────────┘
```

### 4.2 Strategy Execution Flow

```
Daily at 09:20 AM IST (Strategy Entry Time)
┌─────────────────────────────────────────────┐
│  Master Precision Timer (Step Function)     │
│  - Emits market events at 0-second boundary │
│  - Institutional-grade timing precision      │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Strategy Executor (Lambda Function)         │
│                                             │
│  1. Query all ACTIVE subscriptions          │
│     (using TemplateSubscribers GSI)         │
│                                             │
│  2. For each subscriber:                    │
│     - Fetch admin's strategy config         │
│     - Fetch user's broker allocation        │
│     - Combine: Admin strategy + User broker │
│                                             │
│  3. Execute in parallel across all users    │
└─────────────────────────────────────────────┘
                    ↓
            ┌───────┴───────┐
            ↓               ↓
    ┌───────────┐   ┌───────────┐
    │ Zebu User │   │ Zebu User │
    │ Execution │   │ Execution │
    │           │   │           │
    │ Strategy: │   │ Strategy: │
    │ Admin cfg │   │ Admin cfg │
    │           │   │           │
    │ Broker:   │   │ Broker:   │
    │ User A/C  │   │ User A/C  │
    │ ZEBU123   │   │ ZEBU456   │
    │           │   │           │
    │ Lots: 1   │   │ Lots: 2   │
    └───────────┘   └───────────┘
            ↓               ↓
    ┌───────────┐   ┌───────────┐
    │ Zebu API  │   │ Zebu API  │
    │ Order     │   │ Order     │
    │ Placement │   │ Placement │
    └───────────┘   └───────────┘
```

### 4.3 Admin Strategy Update Propagation

```
Admin Updates Strategy (e.g., changes Stop Loss from 20% to 15%)
┌─────────────────────────────────────────────┐
│  Admin Action: Update Strategy              │
│  PUT /options/baskets/{basket_id}           │
│                                             │
│  {                                          │
│    "stop_loss": 15  // Changed from 20     │
│  }                                          │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  DynamoDB Update (Single Source of Truth)   │
│  - Updates admin's strategy record          │
│  - NO cloning, NO propagation needed        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Next Execution (09:20 AM Next Day)         │
│                                             │
│  All subscribers automatically get:         │
│  - NEW stop loss (15%)                      │
│  - Because they reference admin's strategy  │
│  - Zero delay, instant propagation          │
└─────────────────────────────────────────────┘
```

---

## 5. Integration Patterns

### 5.1 Embedded Widget Pattern (Recommended)

**Use Case**: Zebu wants to embed marketplace directly in their trading platform

```javascript
// Zebu Frontend Code (React/Angular/Vue)

// Step 1: Fetch marketplace templates from Zebu backend
const fetchMarketplace = async () => {
  // Zebu backend calls Quantleap Partner API
  const response = await fetch('/zebu-api/marketplace/templates');
  return await response.json();
};

// Step 2: Display marketplace in Zebu portal
<MarketplaceWidget templates={templates} onSubscribe={handleSubscribe} />

// Step 3: Handle subscription
const handleSubscribe = async (templateId, lotMultiplier) => {
  // Zebu backend calls Quantleap Partner API
  const response = await fetch('/zebu-api/marketplace/subscribe', {
    method: 'POST',
    body: JSON.stringify({
      template_id: templateId,
      user_email: currentUser.email,
      broker_client_id: currentUser.zebuClientId,
      lot_multiplier: lotMultiplier
    })
  });

  if (response.ok) {
    showSuccess('Subscribed successfully!');
  }
};
```

```javascript
// Zebu Backend Code (Node.js/Python/Java)

// Configuration
const QUANTLEAP_API_KEY = process.env.QUANTLEAP_API_KEY;
const QUANTLEAP_SECRET = process.env.QUANTLEAP_SECRET;
const QUANTLEAP_BASE_URL = 'https://257y9owov2.execute-api.ap-south-1.amazonaws.com/dev';

// Browse marketplace
app.get('/zebu-api/marketplace/templates', async (req, res) => {
  const response = await fetch(`${QUANTLEAP_BASE_URL}/partner/marketplace/templates`, {
    headers: {
      'Authorization': `Bearer ${QUANTLEAP_API_KEY}`,
      'X-Partner-Secret': QUANTLEAP_SECRET
    }
  });

  const data = await response.json();
  res.json(data);
});

// Subscribe user
app.post('/zebu-api/marketplace/subscribe', async (req, res) => {
  const { template_id, user_email, broker_client_id, lot_multiplier } = req.body;

  const response = await fetch(`${QUANTLEAP_BASE_URL}/partner/marketplace/subscribe`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${QUANTLEAP_API_KEY}`,
      'X-Partner-Secret': QUANTLEAP_SECRET,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      template_basket_id: template_id,
      user_email: user_email,
      user_name: req.user.name,
      broker_client_id: broker_client_id,
      lot_multiplier: lot_multiplier,
      auto_link_broker: true
    })
  });

  const data = await response.json();
  res.json(data);
});
```

### 5.2 Deep Link Pattern (Alternative)

**Use Case**: Zebu wants to redirect users to Quantleap platform

```javascript
// Zebu redirects user to Quantleap with partner token
const marketplaceUrl = `https://app.quantleap.in/marketplace?partner=zebu&token=${partnerToken}`;
window.location.href = marketplaceUrl;

// User subscribes on Quantleap platform
// Revenue automatically attributed to Zebu
```

### 5.3 API-Only Pattern

**Use Case**: Zebu builds completely custom UI

```javascript
// Zebu has complete control over UI/UX
// Uses Quantleap only as backend API
// Full white-label experience
```

---

## 6. API Reference

### 6.1 Authentication

**API Key Structure**:
```
API Key:    pk_zebu_live_32characteralphanumeric
API Secret: sk_zebu_live_48characteralphanumeric
```

**Request Headers**:
```http
Authorization: Bearer pk_zebu_live_XXXXXXXXXXXXXXXXXXXXXXXX
X-Partner-Secret: sk_zebu_live_YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY
```

### 6.2 Browse Marketplace

**Endpoint**: `GET /partner/marketplace/templates`

**Request**:
```http
GET /partner/marketplace/templates?category=NIFTY&difficulty=INTERMEDIATE&pricing_type=PAID
Authorization: Bearer pk_zebu_live_XXX
X-Partner-Secret: sk_zebu_live_YYY
```

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | string | No | Filter by index: NIFTY, BANKNIFTY, FINNIFTY |
| `difficulty` | string | No | BEGINNER, INTERMEDIATE, ADVANCED |
| `pricing_type` | string | No | FREE, PAID |

**Response** (200 OK):
```json
{
  "statusCode": 200,
  "templates": [
    {
      "basket_id": "bsk_nifty_iron_condor_weekly",
      "template_owner_id": "admin_quantleap",
      "name": "NIFTY Iron Condor - Weekly",
      "description": "Conservative weekly Iron Condor strategy on NIFTY index with built-in risk controls",
      "marketplace_config": {
        "is_template": true,
        "visibility": "PUBLIC",
        "category": "NIFTY",
        "difficulty_level": "INTERMEDIATE",
        "tags": ["NIFTY", "WEEKLY", "IRON_CONDOR", "LIMITED_RISK"],
        "pricing": {
          "type": "PAID",
          "monthly_fee": 999,
          "currency": "INR"
        }
      },
      "performance": {
        "subscriber_count": 45,
        "avg_monthly_return_pct": 12.5,
        "max_drawdown_pct": 8.2,
        "win_rate_pct": 72.5
      },
      "strategy_summary": {
        "index": "NIFTY",
        "entry_time": "09:20",
        "exit_time": "15:20",
        "num_legs": 4,
        "expiry_type": "WEEKLY"
      },
      "created_at": "2025-09-15T10:00:00Z",
      "updated_at": "2025-10-08T14:30:00Z"
    }
  ],
  "pagination": {
    "total": 15,
    "page": 1,
    "per_page": 10
  }
}
```

### 6.3 Subscribe to Strategy

**Endpoint**: `POST /partner/marketplace/subscribe`

**Request**:
```http
POST /partner/marketplace/subscribe
Authorization: Bearer pk_zebu_live_XXX
X-Partner-Secret: sk_zebu_live_YYY
Content-Type: application/json

{
  "template_basket_id": "bsk_nifty_iron_condor_weekly",
  "user_email": "john.doe@example.com",
  "user_name": "John Doe",
  "broker_client_id": "ZEBU123456",
  "lot_multiplier": 1,
  "auto_link_broker": true
}
```

**Request Body Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `template_basket_id` | string | Yes | ID of strategy template to subscribe |
| `user_email` | string | Yes | User's email (will create account if new) |
| `user_name` | string | Yes | User's full name |
| `broker_client_id` | string | Yes | Zebu client ID for execution |
| `lot_multiplier` | integer | No | Number of lots (default: 1) |
| `auto_link_broker` | boolean | No | Auto-link Zebu account (default: true) |

**Response** (200 OK):
```json
{
  "statusCode": 200,
  "message": "Subscription created successfully",
  "subscription": {
    "subscription_id": "sub_zebu_user123_bsk456",
    "user_id": "usr_john_doe_zebu",
    "template_basket_id": "bsk_nifty_iron_condor_weekly",
    "template_owner_id": "admin_quantleap",
    "status": "ACTIVE",
    "pricing": {
      "monthly_fee": 999,
      "currency": "INR",
      "billing_start_date": "2025-10-10",
      "next_billing_date": "2025-11-10"
    },
    "broker_allocation": {
      "allocation_id": "alloc_zebu123456_bsk456",
      "broker_id": "zebu",
      "client_id": "ZEBU123456",
      "lot_multiplier": 1,
      "status": "ACTIVE"
    },
    "partner_attribution": {
      "partner_id": "zebu",
      "partner_api_key_id": "pk_zebu_live_XXX",
      "commission_rate": 0.30,
      "monthly_commission": 299.70
    },
    "created_at": "2025-10-10T10:15:30Z"
  }
}
```

**Error Responses**:

**401 Unauthorized**:
```json
{
  "statusCode": 401,
  "error": "Invalid API key or secret"
}
```

**429 Rate Limit Exceeded**:
```json
{
  "statusCode": 429,
  "error": "Rate limit exceeded: 60 requests per minute"
}
```

**400 Bad Request**:
```json
{
  "statusCode": 400,
  "error": "Invalid request parameters",
  "details": {
    "user_email": "Invalid email format"
  }
}
```

**409 Conflict**:
```json
{
  "statusCode": 409,
  "error": "User already subscribed to this strategy"
}
```

### 6.4 Rate Limits

| Endpoint | Rate Limit | Window |
|----------|-----------|--------|
| Browse Templates | 60 requests | Per minute |
| Subscribe | 60 requests | Per minute |

**Rate Limit Headers** (in response):
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1696932000
```

---

## 7. Authentication & Security

### 7.1 Partner API Key Generation

**Quantleap Admin Process**:
```
1. Zebu signs partnership agreement
2. Quantleap admin creates partner API key
3. Admin provides credentials (ONE TIME ONLY)
4. Zebu stores securely in environment variables
```

**Security Best Practices**:
```bash
# Store in environment variables (DO NOT commit to git)
QUANTLEAP_API_KEY=pk_zebu_live_XXXXXXXX
QUANTLEAP_SECRET=sk_zebu_live_YYYYYYYY

# Never log credentials
# Never expose in frontend code
# Rotate keys annually or if compromised
```

### 7.2 Authentication Flow

```
┌─────────────────────────────────────────────┐
│ Zebu Backend Request                        │
│ Authorization: Bearer pk_zebu_live_XXX      │
│ X-Partner-Secret: sk_zebu_live_YYY          │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Quantleap Partner Auth Middleware           │
│                                             │
│ 1. Extract API key from Authorization header│
│ 2. Extract secret from X-Partner-Secret     │
│ 3. Fetch partner config from DynamoDB       │
│ 4. Verify secret with bcrypt                │
│ 5. Check rate limits (token bucket)         │
│ 6. Validate permissions                     │
└─────────────────────────────────────────────┘
                    ↓
            ┌───────┴───────┐
            ↓               ↓
    ┌───────────┐   ┌───────────┐
    │ ✅ Valid  │   │ ❌ Invalid │
    │ Continue  │   │ 401/429    │
    └───────────┘   └───────────┘
```

### 7.3 IP Whitelisting (Optional)

**For enhanced security, Quantleap can whitelist Zebu's server IPs**:
```json
{
  "partner_id": "zebu",
  "allowed_ips": [
    "203.0.113.10",
    "203.0.113.11",
    "203.0.113.12"
  ]
}
```

---

## 8. Revenue Attribution

### 8.1 Commission Calculation

**Formula**:
```
Monthly Commission = Subscription Fee × Commission Rate

Example:
Subscription Fee: ₹999
Commission Rate: 30%
Zebu Commission: ₹299.70 per user per month
```

### 8.2 Attribution Tracking

**Every subscription stores partner attribution**:
```json
{
  "subscription_id": "sub_12345",
  "user_id": "usr_abc",
  "template_basket_id": "bsk_strategy",
  "partner_attribution": {
    "partner_id": "zebu",
    "partner_api_key_id": "pk_zebu_live_XXX",
    "commission_rate": 0.30,
    "monthly_commission": 299.70,
    "billing_start_date": "2025-10-10"
  }
}
```

### 8.3 Revenue Reporting (Future Enhancement)

**Planned Dashboard for Zebu**:
```
Monthly Revenue Report (October 2025)
─────────────────────────────────────
Total Subscribers: 150
Active Subscriptions: 142
Revenue Generated: ₹141,858
Zebu Commission (30%): ₹42,557.40

Top Performing Strategies:
1. NIFTY Iron Condor - 45 subscribers
2. BANKNIFTY Straddle - 32 subscribers
3. FINNIFTY Butterfly - 28 subscribers
```

---

## 9. Deployment Architecture

### 9.1 AWS Infrastructure

```
┌─────────────────────────────────────────────────────────────┐
│                       AWS REGION: ap-south-1                 │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              API Gateway (REST API)                     │ │
│  │  - Endpoint: 257y9owov2.execute-api.ap-south-1.aws...  │ │
│  │  - Custom domain: api.quantleap.in (optional)          │ │
│  │  - Rate limiting: 10,000 req/sec                       │ │
│  │  - Throttling: 5,000 req/sec burst                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                            ↓                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           Lambda Functions (Python 3.11)                │ │
│  │                                                         │ │
│  │  marketplace-manager:                                   │ │
│  │    - Memory: 512 MB                                    │ │
│  │    - Timeout: 30 seconds                               │ │
│  │    - Concurrent executions: 100                        │ │
│  │                                                         │ │
│  │  subscription-manager:                                  │ │
│  │    - Memory: 512 MB                                    │ │
│  │    - Timeout: 30 seconds                               │ │
│  │    - Handles subscription creation                     │ │
│  │                                                         │ │
│  │  partner-api-manager:                                   │ │
│  │    - Memory: 256 MB                                    │ │
│  │    - Admin-only access                                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                            ↓                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           DynamoDB (Single Table Design)                │ │
│  │                                                         │ │
│  │  Table: trading-configurations                          │ │
│  │    - Read Capacity: On-Demand                          │ │
│  │    - Write Capacity: On-Demand                         │ │
│  │    - Point-in-Time Recovery: Enabled                   │ │
│  │                                                         │ │
│  │  GSI Indexes:                                           │ │
│  │    1. MarketplaceDiscovery - Browse by category        │ │
│  │    2. UserSubscriptions - User subscription queries    │ │
│  │    3. TemplateSubscribers - Find subscribers           │ │
│  └────────────────────────────────────────────────────────┘ │
│                            ↓                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           CloudWatch Monitoring                         │ │
│  │  - API Gateway metrics                                  │ │
│  │  - Lambda execution logs                                │ │
│  │  - DynamoDB performance metrics                         │ │
│  │  - Custom business metrics (subscriptions, revenue)    │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 9.2 Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| **API Latency** | < 500ms (p99) | Browse marketplace |
| **Subscription Creation** | < 2 seconds | Includes account creation |
| **Concurrent Requests** | 10,000/sec | API Gateway limit |
| **Data Consistency** | Strong | DynamoDB default |
| **Availability** | 99.99% | AWS SLA |

### 9.3 Scalability

**Current Capacity**:
- Supports 100,000+ concurrent subscribers
- Handles 1,000+ subscriptions per minute
- Zero downtime deployments

**Auto-Scaling**:
- Lambda scales automatically to demand
- DynamoDB on-demand scaling
- API Gateway handles burst traffic

---

## 10. Testing & Go-Live

### 10.1 Development Environment

**Test API Endpoint**:
```
Base URL: https://257y9owov2.execute-api.ap-south-1.amazonaws.com/dev
```

**Test Credentials** (Provided by Quantleap):
```
API Key:    pk_zebu_test_XXXXXXXXXXXXXXXX
API Secret: sk_zebu_test_YYYYYYYYYYYYYYYY
```

### 10.2 Testing Checklist

**Phase 1: API Integration Testing**
- [ ] Successfully authenticate with test credentials
- [ ] Browse marketplace templates
- [ ] Handle pagination correctly
- [ ] Parse response data correctly
- [ ] Handle API errors gracefully
- [ ] Implement rate limit handling
- [ ] Test timeout scenarios

**Phase 2: Subscription Flow Testing**
- [ ] Create subscription for test user
- [ ] Verify auto broker account linking
- [ ] Test duplicate subscription prevention
- [ ] Verify subscription status updates
- [ ] Test unsubscribe flow (if implemented)

**Phase 3: End-to-End Testing**
- [ ] User browses marketplace in Zebu portal
- [ ] User subscribes to strategy
- [ ] Verify execution happens next trading day
- [ ] Check orders placed in Zebu account
- [ ] Verify position management
- [ ] Test stop loss and target triggers

**Phase 4: Error Handling**
- [ ] Invalid API credentials
- [ ] Rate limit exceeded
- [ ] Network timeouts
- [ ] Invalid user data
- [ ] Insufficient broker balance
- [ ] Market closed scenarios

### 10.3 Go-Live Checklist

**Pre-Launch**:
- [ ] Production API credentials received
- [ ] Production endpoints configured
- [ ] Error monitoring setup
- [ ] Support escalation process defined
- [ ] User communication plan ready
- [ ] Legal agreements signed

**Launch Day**:
- [ ] Deploy to production
- [ ] Monitor API metrics
- [ ] Monitor first subscriptions
- [ ] Verify first executions
- [ ] User support ready

**Post-Launch**:
- [ ] Weekly revenue reports
- [ ] Monthly performance review
- [ ] User feedback collection
- [ ] Continuous improvement

---

## 11. Support & SLA

### 11.1 Technical Support

**Quantleap Support Channels**:
```
Email: partners@quantleap.in
Phone: +91-XXXX-XXXXXX (24/7 for critical issues)
Slack: zebu-quantleap-integration (Real-time chat)
Ticket System: support.quantleap.in
```

**Response Times**:
| Severity | Response Time | Resolution Time |
|----------|--------------|-----------------|
| Critical (API down) | 15 minutes | 2 hours |
| High (Execution failure) | 1 hour | 4 hours |
| Medium (Performance issue) | 4 hours | 24 hours |
| Low (Enhancement request) | 24 hours | As scheduled |

### 11.2 Service Level Agreement (SLA)

**Availability**: 99.9% uptime
```
Monthly Downtime Allowance: 43.2 minutes
Quarterly Downtime Allowance: 2.16 hours
Annual Downtime Allowance: 8.64 hours
```

**Performance**:
- API Response Time (p95): < 500ms
- Subscription Creation: < 2 seconds
- Execution Timing Accuracy: 0-second precision

**Maintenance Windows**:
- Scheduled: Sundays 02:00-04:00 AM IST
- Notification: 48 hours advance notice
- Emergency: As needed with immediate notification

---

## 12. Appendix

### 12.1 Glossary

| Term | Definition |
|------|------------|
| **Template** | Admin-created strategy that users can subscribe to |
| **Subscription** | User's reference to a template (not a copy) |
| **Broker Allocation** | User's specification of which broker account to use |
| **Lot Multiplier** | Number of lots user wants to trade |
| **Partner Attribution** | Tracking which partner brought the user |
| **0-Second Precision** | Execution at exact 0th second of minute boundary |
| **GSI** | Global Secondary Index (DynamoDB query optimization) |

### 12.2 Sample Code Repositories

**Coming Soon**: Quantleap will provide sample integration code for:
- Node.js backend integration
- Python backend integration
- React frontend widget
- Postman collection for testing

### 12.3 Regulatory & Compliance

**SEBI Compliance**:
- All strategies are for educational purposes
- Users must understand risk of algo trading
- Quantleap is registered as algo platform
- Zebu responsible for user KYC/onboarding

**Data Privacy**:
- GDPR compliant data handling
- User data encrypted at rest and transit
- Data retention: 7 years (regulatory requirement)
- User can request data deletion after account closure

### 12.4 FAQ

**Q: Can users modify subscribed strategies?**
A: No. Users subscribe by reference to admin strategy. They can only control lot size and broker account.

**Q: What happens if admin deletes a strategy?**
A: All subscriptions automatically deactivated. Users notified. No further executions.

**Q: Can users subscribe to multiple strategies?**
A: Yes, unlimited subscriptions per user.

**Q: How are conflicting strategies handled?**
A: Each strategy executes independently. Users responsible for risk management.

**Q: What if user's broker account is inactive?**
A: Execution fails gracefully. User notified. Subscription remains active.

**Q: Can Zebu create custom pricing for users?**
A: Currently no. Future enhancement planned for partner-specific pricing.

**Q: How are refunds handled?**
A: Contact Quantleap support. Handled case-by-case based on policy.

---

## 13. Contact Information

**Partnership Team**:
```
Quantleap Analytics LLP
Email: partners@quantleap.in
Website: https://quantleap.in
```

**Technical Integration**:
```
Engineering Team
Email: tech@quantleap.in
Slack: zebu-quantleap-integration
```

**Billing & Revenue**:
```
Finance Team
Email: finance@quantleap.in
```

---

**Document Version**: 1.0
**Last Updated**: October 10, 2025
**Next Review**: January 10, 2026

---

**© 2025 Quantleap Analytics LLP. All Rights Reserved.**

This document is confidential and proprietary to Quantleap Analytics LLP and Zebu. It may not be shared, copied, or distributed without written permission.
