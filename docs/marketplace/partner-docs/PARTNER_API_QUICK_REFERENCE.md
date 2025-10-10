# QuantLeap Partner API - Quick Reference Card

> **Print this page for quick reference during development**

---

## 🔑 Authentication

```http
Authorization: Bearer pk_zebu_live_XXXXXXXX
X-Partner-Secret: sk_zebu_live_YYYYYYYY
```

---

## 🌐 Base URLs

| Environment | URL |
|-------------|-----|
| **Development** | `https://257y9owov2.execute-api.ap-south-1.amazonaws.com/dev` |
| **Production** | `https://api.quantleap.in/v1` *(coming soon)* |

---

## 📡 Endpoints

### **Browse Marketplace Templates**
```http
GET /partner/marketplace/templates?status=active&limit=20&offset=0
```

**Query Parameters**:
- `status` - Filter by status (`active`, `inactive`)
- `index_symbol` - Filter by index (`NIFTY`, `BANKNIFTY`, `FINNIFTY`, `MIDCPNIFTY`)
- `category` - Filter by category (`directional`, `neutral`, `volatility`, `income`)
- `limit` - Results per page (1-100, default: 20)
- `offset` - Skip N results (default: 0)

**Response 200**:
```json
{
  "templates": [
    {
      "basket_id": "basket_admin_8f3e2a1b",
      "basket_name": "Iron Condor Weekly - NIFTY",
      "subscription_price": 999,
      "subscriber_count": 127,
      ...
    }
  ],
  "total": 15,
  "limit": 20,
  "offset": 0
}
```

---

### **Subscribe User to Template**
```http
POST /partner/marketplace/subscribe
Content-Type: application/json
```

**Request Body**:
```json
{
  "user_email": "user@example.com",
  "basket_id": "basket_admin_8f3e2a1b",
  "broker_account_id": "zebu_acc_12345",
  "custom_lot_multiplier": 1,
  "metadata": {
    "source": "zebu_mobile_app",
    "campaign": "diwali_2025"
  }
}
```

**Response 201**:
```json
{
  "subscription_id": "sub_zebu_a7f3e2b1",
  "user_email": "user@example.com",
  "basket_id": "basket_admin_8f3e2a1b",
  "partner_id": "partner_zebu_live",
  "status": "active",
  "subscription_price": 999,
  "partner_commission": 299.7,
  "subscribed_at": "2025-10-10T10:15:30Z"
}
```

---

## ⚠️ Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| **400** | Bad Request | Validate request body/parameters |
| **401** | Unauthorized | Check API Key and Secret |
| **404** | Not Found | User or basket doesn't exist |
| **409** | Conflict | Duplicate subscription exists |
| **429** | Rate Limit | Wait and retry (max 60 req/min) |
| **500** | Server Error | Retry with exponential backoff |

**Error Response Format**:
```json
{
  "error": "bad_request",
  "message": "Invalid request body: 'user_email' is required",
  "code": "VALIDATION_ERROR",
  "request_id": "req_a7f3e2b1c4d5"
}
```

---

## 🚦 Rate Limiting

- **Limit**: 60 requests per minute
- **Algorithm**: Token bucket with DynamoDB tracking
- **Headers**:
  - `X-RateLimit-Limit: 60`
  - `X-RateLimit-Remaining: 45`
  - `X-RateLimit-Reset: 1696936200`

**Recommended Retry Logic**:
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

## 💰 Revenue Model

| Item | Value |
|------|-------|
| **Monthly Subscription** | ₹999 per user |
| **Partner Commission** | 30% (₹299.70) |
| **Platform Revenue** | 70% (₹699.30) |

**Revenue Tracking**: All subscriptions include `partner_id` for attribution.

---

## 🧪 Quick Test with cURL

```bash
# Export credentials
export API_KEY="pk_zebu_test_XXXXXXXX"
export API_SECRET="sk_zebu_test_YYYYYYYY"
export BASE_URL="https://257y9owov2.execute-api.ap-south-1.amazonaws.com/dev"

# Browse templates
curl -X GET "${BASE_URL}/partner/marketplace/templates?status=active" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "X-Partner-Secret: ${API_SECRET}"

# Subscribe user
curl -X POST "${BASE_URL}/partner/marketplace/subscribe" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "X-Partner-Secret: ${API_SECRET}" \
  -H "Content-Type: application/json" \
  -d '{
    "user_email": "test@example.com",
    "basket_id": "basket_admin_test",
    "broker_account_id": "zebu_test_123"
  }'
```

---

## 📦 Node.js/TypeScript Quick Start

```typescript
import axios from 'axios';

const API_KEY = process.env.QUANTLEAP_API_KEY!;
const API_SECRET = process.env.QUANTLEAP_API_SECRET!;
const BASE_URL = 'https://257y9owov2.execute-api.ap-south-1.amazonaws.com/dev';

const client = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Authorization': `Bearer ${API_KEY}`,
    'X-Partner-Secret': API_SECRET,
    'Content-Type': 'application/json'
  }
});

// Browse templates
const templates = await client.get('/partner/marketplace/templates', {
  params: { status: 'active', limit: 20 }
});

// Subscribe user
const subscription = await client.post('/partner/marketplace/subscribe', {
  user_email: 'user@example.com',
  basket_id: 'basket_admin_8f3e2a1b',
  broker_account_id: 'zebu_acc_12345'
});
```

---

## 🐍 Python Quick Start

```python
import os
import requests

API_KEY = os.getenv('QUANTLEAP_API_KEY')
API_SECRET = os.getenv('QUANTLEAP_API_SECRET')
BASE_URL = 'https://257y9owov2.execute-api.ap-south-1.amazonaws.com/dev'

headers = {
    'Authorization': f'Bearer {API_KEY}',
    'X-Partner-Secret': API_SECRET,
    'Content-Type': 'application/json'
}

# Browse templates
response = requests.get(
    f'{BASE_URL}/partner/marketplace/templates',
    headers=headers,
    params={'status': 'active', 'limit': 20}
)
templates = response.json()

# Subscribe user
response = requests.post(
    f'{BASE_URL}/partner/marketplace/subscribe',
    headers=headers,
    json={
        'user_email': 'user@example.com',
        'basket_id': 'basket_admin_8f3e2a1b',
        'broker_account_id': 'zebu_acc_12345'
    }
)
subscription = response.json()
```

---

## 🔧 OpenAPI Spec Tools

```bash
# Generate TypeScript client
openapi-generator-cli generate \
  -i docs/partner-api-openapi.yaml \
  -g typescript-axios \
  -o ./generated-client

# Start mock server
prism mock docs/partner-api-openapi.yaml

# View in Swagger UI
docker run -p 8080:8080 \
  -e SWAGGER_JSON=/docs/partner-api-openapi.json \
  -v $(pwd)/docs:/docs \
  swaggerapi/swagger-ui
```

---

## 🆘 Support

| Type | Contact | Response Time |
|------|---------|---------------|
| **Technical** | api-support@quantleap.in | < 2 hours (critical) |
| **Business** | partnerships@quantleap.in | < 24 hours |
| **SLA** | 99.9% uptime | Automated monitoring |

**Include in support requests**:
- `request_id` from error response
- Timestamp (ISO 8601)
- HTTP method and endpoint
- Response status code

---

## 📚 Full Documentation

| Document | Purpose |
|----------|---------|
| **[Integration Index](PARTNER_INTEGRATION_INDEX.md)** | Complete documentation overview |
| **[API Documentation](PARTNER_API_DOCUMENTATION.md)** | Developer guide with examples |
| **[OpenAPI Specs](partner-api-openapi.json)** | Machine-readable API definition |

---

## ✅ Pre-Launch Checklist

- [ ] API credentials received (Key + Secret)
- [ ] Base URL configured (dev or production)
- [ ] Authentication headers implemented
- [ ] Rate limiting handled (60 req/min)
- [ ] Error handling for all status codes
- [ ] Test subscriptions verified
- [ ] Revenue attribution tracking confirmed
- [ ] Monitoring and alerting configured

---

**Version**: 1.0.0 | **Updated**: October 10, 2025 | **Format**: Quick Reference
