# Quantleap Partner API Documentation
## For Zebu & External Broker Integration

**API Version**: v1
**Base URL**: `https://257y9owov2.execute-api.ap-south-1.amazonaws.com/dev`
**Environment**: Production
**Last Updated**: October 10, 2025

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [Webhooks (Future)](#webhooks)
8. [Code Examples](#code-examples)

---

## Quick Start

### Step 1: Get API Credentials

Contact Quantleap to receive your Partner API credentials:
```
API Key:    pk_zebu_live_XXXXXXXXXXXXXXXXXXXXXXXX
API Secret: sk_zebu_live_YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY
```

⚠️ **Security**: Never expose these credentials in frontend code or commit to version control.

### Step 2: Make Your First Request

```bash
curl -X GET "https://257y9owov2.execute-api.ap-south-1.amazonaws.com/dev/partner/marketplace/templates" \
  -H "Authorization: Bearer pk_zebu_live_XXXXXXXXXXXXXXXXXXXXXXXX" \
  -H "X-Partner-Secret: sk_zebu_live_YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY"
```

### Step 3: Subscribe a User

```bash
curl -X POST "https://257y9owov2.execute-api.ap-south-1.amazonaws.com/dev/partner/marketplace/subscribe" \
  -H "Authorization: Bearer pk_zebu_live_XXXXXXXXXXXXXXXXXXXXXXXX" \
  -H "X-Partner-Secret: sk_zebu_live_YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY" \
  -H "Content-Type: application/json" \
  -d '{
    "template_basket_id": "bsk_nifty_iron_condor_weekly",
    "user_email": "user@example.com",
    "user_name": "John Doe",
    "broker_client_id": "ZEBU123456",
    "lot_multiplier": 1,
    "auto_link_broker": true
  }'
```

---

## Authentication

### Headers Required

Every API request must include these headers:

| Header | Description | Example |
|--------|-------------|---------|
| `Authorization` | Bearer token with API key | `Bearer pk_zebu_live_XXX` |
| `X-Partner-Secret` | API secret for verification | `sk_zebu_live_YYY` |
| `Content-Type` | Required for POST requests | `application/json` |

### Authentication Flow

```
Request
   ↓
Extract API Key & Secret
   ↓
Validate with bcrypt (secure hash comparison)
   ↓
Check Rate Limits
   ↓
Validate Permissions
   ↓
Allow/Deny Request
```

### Security Best Practices

✅ **DO**:
- Store credentials in environment variables
- Use HTTPS only
- Rotate keys annually
- Monitor API usage
- Implement retry logic with exponential backoff

❌ **DON'T**:
- Expose credentials in frontend JavaScript
- Commit credentials to git
- Share credentials via email/chat
- Use same credentials across environments
- Log credentials in application logs

---

## API Endpoints

### 1. Browse Marketplace Templates

Browse all available algorithmic trading strategies.

**Endpoint**: `GET /partner/marketplace/templates`

**Authentication**: Required

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `category` | string | No | All | Filter by index: `NIFTY`, `BANKNIFTY`, `FINNIFTY` |
| `difficulty` | string | No | All | Filter by level: `BEGINNER`, `INTERMEDIATE`, `ADVANCED` |
| `pricing_type` | string | No | All | Filter by pricing: `FREE`, `PAID` |
| `tags` | string | No | All | Comma-separated tags: `WEEKLY,MONTHLY` |
| `page` | integer | No | 1 | Page number for pagination |
| `per_page` | integer | No | 10 | Items per page (max: 50) |

**Request Example**:

```http
GET /partner/marketplace/templates?category=NIFTY&difficulty=INTERMEDIATE&page=1&per_page=10
Host: 257y9owov2.execute-api.ap-south-1.amazonaws.com
Authorization: Bearer pk_zebu_live_XXXXXXXXXXXXXXXXXXXXXXXX
X-Partner-Secret: sk_zebu_live_YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY
```

**Response** (200 OK):

```json
{
  "statusCode": 200,
  "templates": [
    {
      "basket_id": "bsk_nifty_iron_condor_weekly",
      "template_owner_id": "admin_quantleap",
      "name": "NIFTY Iron Condor - Weekly",
      "description": "Conservative weekly Iron Condor strategy on NIFTY index with built-in risk controls. Suitable for traders seeking consistent income with limited risk.",
      "marketplace_config": {
        "is_template": true,
        "visibility": "PUBLIC",
        "category": "NIFTY",
        "difficulty_level": "INTERMEDIATE",
        "tags": [
          "NIFTY",
          "WEEKLY",
          "IRON_CONDOR",
          "LIMITED_RISK",
          "INCOME"
        ],
        "pricing": {
          "type": "PAID",
          "monthly_fee": 999,
          "currency": "INR",
          "trial_period_days": 0
        }
      },
      "strategy_summary": {
        "index": "NIFTY",
        "entry_time": "09:20",
        "exit_time": "15:20",
        "num_legs": 4,
        "expiry_type": "WEEKLY",
        "trading_type": "INTRADAY",
        "execution_days": [
          "MONDAY",
          "TUESDAY",
          "WEDNESDAY",
          "THURSDAY",
          "FRIDAY"
        ]
      },
      "risk_profile": {
        "max_loss": "LIMITED",
        "max_profit": "LIMITED",
        "risk_reward_ratio": "1:2",
        "capital_required_per_lot": 50000
      },
      "performance": {
        "subscriber_count": 45,
        "avg_monthly_return_pct": 12.5,
        "max_drawdown_pct": 8.2,
        "win_rate_pct": 72.5,
        "sharpe_ratio": 1.8,
        "backtest_period": "2024-01-01 to 2025-09-30"
      },
      "created_at": "2025-09-15T10:00:00Z",
      "updated_at": "2025-10-08T14:30:00Z"
    },
    {
      "basket_id": "bsk_banknifty_straddle_monthly",
      "template_owner_id": "admin_quantleap",
      "name": "BANKNIFTY Straddle - Monthly",
      "description": "Aggressive monthly straddle strategy on BANKNIFTY for experienced traders comfortable with unlimited risk.",
      "marketplace_config": {
        "is_template": true,
        "visibility": "PUBLIC",
        "category": "BANKNIFTY",
        "difficulty_level": "ADVANCED",
        "tags": [
          "BANKNIFTY",
          "MONTHLY",
          "STRADDLE",
          "HIGH_RISK",
          "VOLATILITY"
        ],
        "pricing": {
          "type": "PAID",
          "monthly_fee": 1499,
          "currency": "INR",
          "trial_period_days": 7
        }
      },
      "strategy_summary": {
        "index": "BANKNIFTY",
        "entry_time": "10:00",
        "exit_time": "15:15",
        "num_legs": 2,
        "expiry_type": "MONTHLY",
        "trading_type": "POSITIONAL",
        "execution_days": [
          "MONDAY"
        ]
      },
      "risk_profile": {
        "max_loss": "UNLIMITED",
        "max_profit": "LIMITED",
        "risk_reward_ratio": "UNLIMITED:1",
        "capital_required_per_lot": 150000
      },
      "performance": {
        "subscriber_count": 32,
        "avg_monthly_return_pct": 18.3,
        "max_drawdown_pct": 15.7,
        "win_rate_pct": 65.0,
        "sharpe_ratio": 1.5,
        "backtest_period": "2024-01-01 to 2025-09-30"
      },
      "created_at": "2025-08-20T10:00:00Z",
      "updated_at": "2025-10-05T11:20:00Z"
    }
  ],
  "pagination": {
    "total": 15,
    "page": 1,
    "per_page": 10,
    "total_pages": 2,
    "has_next": true
  }
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `basket_id` | string | Unique identifier for strategy template |
| `name` | string | Display name of strategy |
| `description` | string | Detailed description for users |
| `marketplace_config.category` | string | Index traded: NIFTY, BANKNIFTY, etc. |
| `marketplace_config.difficulty_level` | string | BEGINNER, INTERMEDIATE, ADVANCED |
| `marketplace_config.pricing.monthly_fee` | number | Monthly subscription fee in INR |
| `strategy_summary.entry_time` | string | Strategy entry time (HH:MM format, IST) |
| `strategy_summary.exit_time` | string | Strategy exit time (HH:MM format, IST) |
| `strategy_summary.num_legs` | integer | Number of option legs in strategy |
| `performance.subscriber_count` | integer | Total active subscribers |
| `performance.avg_monthly_return_pct` | float | Average monthly return % |
| `performance.win_rate_pct` | float | Percentage of winning trades |

---

### 2. Subscribe User to Strategy

Create a subscription for a Zebu user to an algorithmic trading strategy.

**Endpoint**: `POST /partner/marketplace/subscribe`

**Authentication**: Required

**Request Body**:

```json
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

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `template_basket_id` | string | Yes | - | Strategy template ID from browse endpoint |
| `user_email` | string | Yes | - | User's email (creates account if new) |
| `user_name` | string | Yes | - | User's full name |
| `broker_client_id` | string | Yes | - | Zebu client ID for order execution |
| `lot_multiplier` | integer | No | 1 | Number of lots to trade (1-10) |
| `auto_link_broker` | boolean | No | true | Auto-link Zebu broker account |

**Request Example**:

```http
POST /partner/marketplace/subscribe
Host: 257y9owov2.execute-api.ap-south-1.amazonaws.com
Authorization: Bearer pk_zebu_live_XXXXXXXXXXXXXXXXXXXXXXXX
X-Partner-Secret: sk_zebu_live_YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY
Content-Type: application/json

{
  "template_basket_id": "bsk_nifty_iron_condor_weekly",
  "user_email": "john.doe@example.com",
  "user_name": "John Doe",
  "broker_client_id": "ZEBU123456",
  "lot_multiplier": 2,
  "auto_link_broker": true
}
```

**Response** (200 OK):

```json
{
  "statusCode": 200,
  "message": "Subscription created successfully",
  "subscription": {
    "subscription_id": "sub_zebu_johndoe_bsk456_20251010",
    "user_id": "usr_john_doe_zebu_123456",
    "user_email": "john.doe@example.com",
    "template_basket_id": "bsk_nifty_iron_condor_weekly",
    "template_name": "NIFTY Iron Condor - Weekly",
    "template_owner_id": "admin_quantleap",
    "status": "ACTIVE",
    "pricing": {
      "monthly_fee": 999,
      "currency": "INR",
      "billing_cycle": "MONTHLY",
      "billing_start_date": "2025-10-10",
      "next_billing_date": "2025-11-10",
      "payment_method": "ZEBU_WALLET"
    },
    "broker_allocation": {
      "allocation_id": "alloc_zebu123456_bsk456",
      "broker_id": "zebu",
      "broker_name": "Zebu Share and Wealth Managements",
      "client_id": "ZEBU123456",
      "lot_multiplier": 2,
      "status": "ACTIVE",
      "linked_at": "2025-10-10T10:15:30Z"
    },
    "execution_info": {
      "next_execution_date": "2025-10-11",
      "next_execution_time": "09:20:00",
      "timezone": "Asia/Kolkata"
    },
    "partner_attribution": {
      "partner_id": "zebu",
      "partner_name": "Zebu Share and Wealth Managements",
      "partner_api_key_id": "pk_zebu_live_XXX",
      "commission_rate": 0.30,
      "monthly_commission_inr": 299.70
    },
    "created_at": "2025-10-10T10:15:30Z",
    "updated_at": "2025-10-10T10:15:30Z"
  }
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `subscription_id` | string | Unique subscription identifier |
| `user_id` | string | Quantleap user ID (created if new) |
| `status` | string | ACTIVE, PAUSED, CANCELLED, EXPIRED |
| `broker_allocation.allocation_id` | string | Broker allocation ID for tracking |
| `broker_allocation.lot_multiplier` | integer | Number of lots user is trading |
| `execution_info.next_execution_date` | string | Next trading day |
| `partner_attribution.monthly_commission_inr` | float | Zebu's monthly commission |

---

## Data Models

### Strategy Template Object

```typescript
interface StrategyTemplate {
  basket_id: string;                    // Unique identifier
  template_owner_id: string;            // Admin who created it
  name: string;                         // Display name
  description: string;                  // Long description
  marketplace_config: {
    is_template: boolean;               // Always true
    visibility: 'PUBLIC' | 'PRIVATE';   // Public for marketplace
    category: string;                   // NIFTY, BANKNIFTY, etc.
    difficulty_level: string;           // BEGINNER, INTERMEDIATE, ADVANCED
    tags: string[];                     // Searchable tags
    pricing: {
      type: 'FREE' | 'PAID';
      monthly_fee: number;              // In INR
      currency: string;                 // Always INR
      trial_period_days: number;        // Free trial days
    };
  };
  strategy_summary: {
    index: string;                      // NIFTY, BANKNIFTY, etc.
    entry_time: string;                 // HH:MM format (IST)
    exit_time: string;                  // HH:MM format (IST)
    num_legs: number;                   // Number of option legs
    expiry_type: string;                // WEEKLY, MONTHLY
    trading_type: string;               // INTRADAY, POSITIONAL
    execution_days: string[];           // Days strategy executes
  };
  risk_profile: {
    max_loss: string;                   // LIMITED, UNLIMITED
    max_profit: string;                 // LIMITED, UNLIMITED
    risk_reward_ratio: string;          // e.g., "1:2"
    capital_required_per_lot: number;   // In INR
  };
  performance: {
    subscriber_count: number;           // Total subscribers
    avg_monthly_return_pct: number;     // Average return %
    max_drawdown_pct: number;           // Maximum drawdown %
    win_rate_pct: number;               // Win rate %
    sharpe_ratio: number;               // Risk-adjusted return
    backtest_period: string;            // Date range
  };
  created_at: string;                   // ISO 8601 timestamp
  updated_at: string;                   // ISO 8601 timestamp
}
```

### Subscription Object

```typescript
interface Subscription {
  subscription_id: string;              // Unique identifier
  user_id: string;                      // Quantleap user ID
  user_email: string;                   // User email
  template_basket_id: string;           // Strategy template ID
  template_name: string;                // Strategy name
  template_owner_id: string;            // Admin ID
  status: 'ACTIVE' | 'PAUSED' | 'CANCELLED' | 'EXPIRED';
  pricing: {
    monthly_fee: number;                // In INR
    currency: string;                   // Always INR
    billing_cycle: string;              // MONTHLY
    billing_start_date: string;         // YYYY-MM-DD
    next_billing_date: string;          // YYYY-MM-DD
    payment_method: string;             // ZEBU_WALLET
  };
  broker_allocation: {
    allocation_id: string;              // Broker allocation ID
    broker_id: string;                  // Always "zebu"
    broker_name: string;                // Full broker name
    client_id: string;                  // Zebu client ID
    lot_multiplier: number;             // Number of lots
    status: 'ACTIVE' | 'INACTIVE';
    linked_at: string;                  // ISO 8601 timestamp
  };
  execution_info: {
    next_execution_date: string;        // YYYY-MM-DD
    next_execution_time: string;        // HH:MM:SS
    timezone: string;                   // Asia/Kolkata
  };
  partner_attribution: {
    partner_id: string;                 // "zebu"
    partner_name: string;               // Full name
    partner_api_key_id: string;         // API key used
    commission_rate: number;            // 0.30 (30%)
    monthly_commission_inr: number;     // Commission amount
  };
  created_at: string;                   // ISO 8601 timestamp
  updated_at: string;                   // ISO 8601 timestamp
}
```

---

## Error Handling

### Error Response Format

All errors follow this structure:

```json
{
  "statusCode": 400,
  "error": "Error message summary",
  "details": {
    "field_name": "Specific error for this field"
  },
  "request_id": "req_abc123xyz",
  "timestamp": "2025-10-10T10:15:30Z"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Invalid API key or secret |
| 403 | Forbidden | Permission denied |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource already exists (duplicate subscription) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error (contact support) |
| 503 | Service Unavailable | Temporary unavailability (retry) |

### Common Error Scenarios

#### 401 Unauthorized

```json
{
  "statusCode": 401,
  "error": "Invalid API key or secret",
  "details": {
    "message": "API key validation failed. Please check your credentials."
  },
  "request_id": "req_auth_fail_123",
  "timestamp": "2025-10-10T10:15:30Z"
}
```

**Solution**: Verify API key and secret are correct.

#### 429 Rate Limit Exceeded

```json
{
  "statusCode": 429,
  "error": "Rate limit exceeded: 60 requests per minute",
  "details": {
    "limit": 60,
    "window": "60 seconds",
    "retry_after": 45
  },
  "request_id": "req_rate_limit_456",
  "timestamp": "2025-10-10T10:15:30Z"
}
```

**Headers**:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1696932000
Retry-After: 45
```

**Solution**: Wait for `Retry-After` seconds before retrying.

#### 409 Duplicate Subscription

```json
{
  "statusCode": 409,
  "error": "User already subscribed to this strategy",
  "details": {
    "user_email": "john.doe@example.com",
    "template_basket_id": "bsk_nifty_iron_condor_weekly",
    "existing_subscription_id": "sub_existing_123"
  },
  "request_id": "req_duplicate_789",
  "timestamp": "2025-10-10T10:15:30Z"
}
```

**Solution**: Check if user already has active subscription before creating new one.

#### 400 Validation Error

```json
{
  "statusCode": 400,
  "error": "Invalid request parameters",
  "details": {
    "user_email": "Invalid email format",
    "lot_multiplier": "Must be between 1 and 10",
    "template_basket_id": "Strategy template not found"
  },
  "request_id": "req_validation_101",
  "timestamp": "2025-10-10T10:15:30Z"
}
```

**Solution**: Fix validation errors and retry.

### Error Handling Best Practices

```javascript
// Example: Robust error handling
async function subscribeUser(templateId, userData) {
  try {
    const response = await fetch(`${BASE_URL}/partner/marketplace/subscribe`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'X-Partner-Secret': API_SECRET,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        template_basket_id: templateId,
        ...userData
      })
    });

    const data = await response.json();

    // Check rate limit headers
    const rateLimit = {
      limit: response.headers.get('X-RateLimit-Limit'),
      remaining: response.headers.get('X-RateLimit-Remaining'),
      reset: response.headers.get('X-RateLimit-Reset')
    };

    if (response.status === 429) {
      const retryAfter = response.headers.get('Retry-After');
      console.log(`Rate limited. Retry after ${retryAfter} seconds`);
      await sleep(retryAfter * 1000);
      return subscribeUser(templateId, userData); // Retry
    }

    if (response.status === 409) {
      console.log('User already subscribed:', data.details.existing_subscription_id);
      return { success: false, reason: 'ALREADY_SUBSCRIBED' };
    }

    if (response.status === 401) {
      console.error('Authentication failed. Check API credentials.');
      throw new Error('AUTH_FAILED');
    }

    if (!response.ok) {
      console.error('API Error:', data);
      throw new Error(data.error);
    }

    return { success: true, subscription: data.subscription };

  } catch (error) {
    console.error('Network or unexpected error:', error);
    throw error;
  }
}
```

---

## Rate Limiting

### Limits

| Endpoint | Rate Limit | Window | Burst |
|----------|-----------|--------|-------|
| Browse Templates | 60 requests | Per minute | 100 |
| Subscribe | 60 requests | Per minute | 100 |

### Rate Limit Headers

Every response includes rate limit information:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1696932000
```

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Total requests allowed in window |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Unix timestamp when limit resets |

### Rate Limit Algorithm

**Token Bucket** with distributed tracking in DynamoDB:
- Tokens refill at constant rate (60/minute = 1/second)
- Burst capacity allows temporary spikes
- Per-partner tracking (Zebu has separate quota)

### Best Practices

```javascript
// Implement exponential backoff
async function apiCallWithRetry(apiFunction, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await apiFunction();

      if (response.headers.get('X-RateLimit-Remaining') < 5) {
        console.warn('Approaching rate limit, slowing down...');
        await sleep(1000); // Slow down when approaching limit
      }

      return response;

    } catch (error) {
      if (error.statusCode === 429 && i < maxRetries - 1) {
        const retryAfter = error.headers.get('Retry-After') || Math.pow(2, i);
        console.log(`Retry ${i + 1}/${maxRetries} after ${retryAfter}s`);
        await sleep(retryAfter * 1000);
        continue;
      }
      throw error;
    }
  }
}
```

---

## Webhooks (Future Enhancement)

### Coming Soon

Quantleap will support webhooks for real-time notifications:

**Planned Events**:
- `subscription.created` - New subscription created
- `subscription.cancelled` - Subscription cancelled
- `execution.completed` - Strategy execution finished
- `execution.failed` - Strategy execution failed

**Webhook Payload Example**:
```json
{
  "event": "subscription.created",
  "timestamp": "2025-10-10T10:15:30Z",
  "data": {
    "subscription_id": "sub_123",
    "user_email": "user@example.com",
    "template_basket_id": "bsk_456"
  }
}
```

---

## Code Examples

### Node.js / Express

```javascript
const express = require('express');
const fetch = require('node-fetch');

const app = express();
app.use(express.json());

// Configuration
const QUANTLEAP_API_KEY = process.env.QUANTLEAP_API_KEY;
const QUANTLEAP_SECRET = process.env.QUANTLEAP_SECRET;
const QUANTLEAP_BASE_URL = 'https://257y9owov2.execute-api.ap-south-1.amazonaws.com/dev';

// Helper function for API calls
async function callQuantleapAPI(endpoint, method = 'GET', body = null) {
  const options = {
    method,
    headers: {
      'Authorization': `Bearer ${QUANTLEAP_API_KEY}`,
      'X-Partner-Secret': QUANTLEAP_SECRET,
      'Content-Type': 'application/json'
    }
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`${QUANTLEAP_BASE_URL}${endpoint}`, options);
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || 'API call failed');
  }

  return data;
}

// Endpoint: Browse marketplace
app.get('/api/marketplace/strategies', async (req, res) => {
  try {
    const { category, difficulty } = req.query;
    const queryParams = new URLSearchParams();

    if (category) queryParams.append('category', category);
    if (difficulty) queryParams.append('difficulty', difficulty);

    const data = await callQuantleapAPI(
      `/partner/marketplace/templates?${queryParams}`
    );

    res.json(data.templates);
  } catch (error) {
    console.error('Error fetching marketplace:', error);
    res.status(500).json({ error: error.message });
  }
});

// Endpoint: Subscribe user
app.post('/api/marketplace/subscribe', async (req, res) => {
  try {
    const {
      strategy_id,
      user_email,
      user_name,
      zebu_client_id,
      lot_multiplier
    } = req.body;

    // Validate input
    if (!strategy_id || !user_email || !zebu_client_id) {
      return res.status(400).json({
        error: 'Missing required fields'
      });
    }

    const subscriptionData = {
      template_basket_id: strategy_id,
      user_email,
      user_name,
      broker_client_id: zebu_client_id,
      lot_multiplier: lot_multiplier || 1,
      auto_link_broker: true
    };

    const data = await callQuantleapAPI(
      '/partner/marketplace/subscribe',
      'POST',
      subscriptionData
    );

    res.json({
      success: true,
      subscription: data.subscription
    });

  } catch (error) {
    console.error('Error subscribing user:', error);
    res.status(500).json({ error: error.message });
  }
});

app.listen(3000, () => {
  console.log('Zebu API server running on port 3000');
});
```

### Python / Flask

```python
from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Configuration
QUANTLEAP_API_KEY = os.environ.get('QUANTLEAP_API_KEY')
QUANTLEAP_SECRET = os.environ.get('QUANTLEAP_SECRET')
QUANTLEAP_BASE_URL = 'https://257y9owov2.execute-api.ap-south-1.amazonaws.com/dev'

def call_quantleap_api(endpoint, method='GET', body=None):
    """Helper function for Quantleap API calls"""
    headers = {
        'Authorization': f'Bearer {QUANTLEAP_API_KEY}',
        'X-Partner-Secret': QUANTLEAP_SECRET,
        'Content-Type': 'application/json'
    }

    url = f'{QUANTLEAP_BASE_URL}{endpoint}'

    if method == 'GET':
        response = requests.get(url, headers=headers)
    elif method == 'POST':
        response = requests.post(url, headers=headers, json=body)

    response.raise_for_status()
    return response.json()

@app.route('/api/marketplace/strategies', methods=['GET'])
def browse_marketplace():
    """Browse marketplace strategies"""
    try:
        category = request.args.get('category')
        difficulty = request.args.get('difficulty')

        params = {}
        if category:
            params['category'] = category
        if difficulty:
            params['difficulty'] = difficulty

        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        endpoint = f'/partner/marketplace/templates?{query_string}'

        data = call_quantleap_api(endpoint)
        return jsonify(data['templates'])

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/marketplace/subscribe', methods=['POST'])
def subscribe_user():
    """Subscribe user to strategy"""
    try:
        body = request.json

        # Validate required fields
        required = ['strategy_id', 'user_email', 'zebu_client_id']
        if not all(field in body for field in required):
            return jsonify({'error': 'Missing required fields'}), 400

        subscription_data = {
            'template_basket_id': body['strategy_id'],
            'user_email': body['user_email'],
            'user_name': body.get('user_name', ''),
            'broker_client_id': body['zebu_client_id'],
            'lot_multiplier': body.get('lot_multiplier', 1),
            'auto_link_broker': True
        }

        data = call_quantleap_api(
            '/partner/marketplace/subscribe',
            method='POST',
            body=subscription_data
        )

        return jsonify({
            'success': True,
            'subscription': data['subscription']
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=3000)
```

### React Frontend Widget

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

// Configure axios instance
const api = axios.create({
  baseURL: '/api/marketplace' // Zebu backend proxy
});

function MarketplaceWidget() {
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    category: 'ALL',
    difficulty: 'ALL'
  });

  // Fetch strategies
  useEffect(() => {
    fetchStrategies();
  }, [filter]);

  const fetchStrategies = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filter.category !== 'ALL') params.category = filter.category;
      if (filter.difficulty !== 'ALL') params.difficulty = filter.difficulty;

      const response = await api.get('/strategies', { params });
      setStrategies(response.data);
    } catch (error) {
      console.error('Error fetching strategies:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (strategyId) => {
    try {
      const response = await api.post('/subscribe', {
        strategy_id: strategyId,
        user_email: currentUser.email,
        user_name: currentUser.name,
        zebu_client_id: currentUser.zebuClientId,
        lot_multiplier: 1
      });

      if (response.data.success) {
        alert('Subscribed successfully!');
      }
    } catch (error) {
      console.error('Subscription error:', error);
      alert('Subscription failed. Please try again.');
    }
  };

  return (
    <div className="marketplace-widget">
      <h2>Algorithmic Trading Strategies</h2>

      {/* Filters */}
      <div className="filters">
        <select
          value={filter.category}
          onChange={(e) => setFilter({...filter, category: e.target.value})}
        >
          <option value="ALL">All Indices</option>
          <option value="NIFTY">NIFTY</option>
          <option value="BANKNIFTY">BANKNIFTY</option>
          <option value="FINNIFTY">FINNIFTY</option>
        </select>

        <select
          value={filter.difficulty}
          onChange={(e) => setFilter({...filter, difficulty: e.target.value})}
        >
          <option value="ALL">All Levels</option>
          <option value="BEGINNER">Beginner</option>
          <option value="INTERMEDIATE">Intermediate</option>
          <option value="ADVANCED">Advanced</option>
        </select>
      </div>

      {/* Strategy List */}
      {loading ? (
        <div>Loading strategies...</div>
      ) : (
        <div className="strategy-grid">
          {strategies.map(strategy => (
            <StrategyCard
              key={strategy.basket_id}
              strategy={strategy}
              onSubscribe={handleSubscribe}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function StrategyCard({ strategy, onSubscribe }) {
  return (
    <div className="strategy-card">
      <h3>{strategy.name}</h3>
      <p className="description">{strategy.description}</p>

      <div className="strategy-details">
        <span className="badge">{strategy.marketplace_config.category}</span>
        <span className="badge">{strategy.marketplace_config.difficulty_level}</span>
      </div>

      <div className="performance">
        <div>
          <strong>Avg Monthly Return:</strong>
          <span>{strategy.performance.avg_monthly_return_pct}%</span>
        </div>
        <div>
          <strong>Win Rate:</strong>
          <span>{strategy.performance.win_rate_pct}%</span>
        </div>
        <div>
          <strong>Subscribers:</strong>
          <span>{strategy.performance.subscriber_count}</span>
        </div>
      </div>

      <div className="pricing">
        <strong>₹{strategy.marketplace_config.pricing.monthly_fee}</strong>
        <span>/month</span>
      </div>

      <button
        className="subscribe-btn"
        onClick={() => onSubscribe(strategy.basket_id)}
      >
        Subscribe Now
      </button>
    </div>
  );
}

export default MarketplaceWidget;
```

---

## Testing

### Test Credentials

**Development Environment**:
```
Base URL: https://257y9owov2.execute-api.ap-south-1.amazonaws.com/dev
API Key:  pk_zebu_test_XXXXXXXXXXXXXXXX (Contact Quantleap)
Secret:   sk_zebu_test_YYYYYYYYYYYYYYYY (Contact Quantleap)
```

### Postman Collection

Download our Postman collection for easy testing:
[Coming Soon - Will be provided by Quantleap team]

### Test Scenarios

1. **Authentication Test**
```bash
curl -X GET "${BASE_URL}/partner/marketplace/templates" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "X-Partner-Secret: ${SECRET}"
```

2. **Browse Marketplace**
```bash
curl -X GET "${BASE_URL}/partner/marketplace/templates?category=NIFTY" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "X-Partner-Secret: ${SECRET}"
```

3. **Subscribe Test User**
```bash
curl -X POST "${BASE_URL}/partner/marketplace/subscribe" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "X-Partner-Secret: ${SECRET}" \
  -H "Content-Type: application/json" \
  -d '{
    "template_basket_id": "bsk_test_strategy",
    "user_email": "test@zebu.com",
    "user_name": "Test User",
    "broker_client_id": "ZEBUTEST001",
    "lot_multiplier": 1
  }'
```

---

## Support

### Technical Support

**Email**: tech@quantleap.in
**Slack**: zebu-quantleap-integration
**Documentation**: https://docs.quantleap.in

### Response Times

| Priority | Response Time | Resolution Time |
|----------|--------------|-----------------|
| Critical | 15 minutes | 2 hours |
| High | 1 hour | 4 hours |
| Medium | 4 hours | 24 hours |
| Low | 24 hours | As scheduled |

---

## Changelog

### Version 1.0 (2025-10-10)
- Initial Partner API release
- Browse marketplace endpoint
- Subscribe endpoint
- Authentication with API key + secret
- Rate limiting implementation

---

**© 2025 Quantleap Analytics LLP. All Rights Reserved.**

This document is confidential and intended only for Zebu Share and Wealth Managements.
