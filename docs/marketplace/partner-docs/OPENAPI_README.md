# QuantLeap Partner API - OpenAPI Specification

## Overview

This directory contains the official OpenAPI 3.0.3 specification for the QuantLeap Partner API. The specification is available in both **JSON** and **YAML** formats for maximum compatibility with different tools and workflows.

## Files

- **[partner-api-openapi.json](partner-api-openapi.json)** - OpenAPI specification in JSON format
- **[partner-api-openapi.yaml](partner-api-openapi.yaml)** - OpenAPI specification in YAML format

Both files contain identical API definitions and are kept in sync. Use whichever format is preferred by your tooling.

## Quick Start

### 1. View the API Documentation

You can view the interactive API documentation using any OpenAPI-compatible tool:

#### **Swagger UI (Online)**
Upload the specification file to [Swagger Editor](https://editor.swagger.io/)

#### **Swagger UI (Local)**
```bash
# Using Docker
docker run -p 8080:8080 \
  -e SWAGGER_JSON=/docs/partner-api-openapi.json \
  -v $(pwd):/docs \
  swaggerapi/swagger-ui

# Open http://localhost:8080
```

#### **Redoc (Online)**
Upload to [Redoc Try](https://redocly.github.io/redoc/)

#### **Postman**
1. Open Postman
2. Click **Import** → **Upload Files**
3. Select `partner-api-openapi.json` or `partner-api-openapi.yaml`
4. Postman will automatically generate a collection with all endpoints

### 2. Generate API Client Libraries

Use OpenAPI Generator to create client libraries in your preferred language:

#### **Node.js/TypeScript Client**
```bash
# Install OpenAPI Generator
npm install @openapitools/openapi-generator-cli -g

# Generate TypeScript client
openapi-generator-cli generate \
  -i docs/partner-api-openapi.yaml \
  -g typescript-axios \
  -o ./generated-client/typescript

# Usage example
import { DefaultApi, Configuration } from './generated-client/typescript';

const config = new Configuration({
  basePath: 'https://257y9owov2.execute-api.ap-south-1.amazonaws.com/dev',
  apiKey: 'Bearer pk_zebu_live_XXXXXXXX',
  headers: {
    'X-Partner-Secret': 'sk_zebu_live_YYYYYYYY'
  }
});

const api = new DefaultApi(config);
const templates = await api.getMarketplaceTemplates({ status: 'active' });
```

#### **Python Client**
```bash
# Generate Python client
openapi-generator-cli generate \
  -i docs/partner-api-openapi.yaml \
  -g python \
  -o ./generated-client/python

# Usage example
from generated_client import ApiClient, Configuration, DefaultApi

config = Configuration(
    host="https://257y9owov2.execute-api.ap-south-1.amazonaws.com/dev",
    api_key={
        'Authorization': 'Bearer pk_zebu_live_XXXXXXXX',
        'X-Partner-Secret': 'sk_zebu_live_YYYYYYYY'
    }
)

with ApiClient(config) as api_client:
    api = DefaultApi(api_client)
    templates = api.get_marketplace_templates(status='active')
```

#### **Java Client**
```bash
# Generate Java client
openapi-generator-cli generate \
  -i docs/partner-api-openapi.yaml \
  -g java \
  -o ./generated-client/java \
  --library okhttp-gson
```

#### **Other Languages**
OpenAPI Generator supports 50+ languages and frameworks:
```bash
# List all available generators
openapi-generator-cli list

# Popular options: php, ruby, go, kotlin, swift, csharp, etc.
```

### 3. Validate API Requests

Use the specification to validate your API requests before sending:

```bash
# Install Spectral (OpenAPI linter/validator)
npm install -g @stoplight/spectral-cli

# Validate the spec
spectral lint docs/partner-api-openapi.yaml

# Validate a request body
spectral lint -r docs/partner-api-openapi.yaml your-request.json
```

## API Endpoints Summary

### **Marketplace Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/partner/marketplace/templates` | Browse available strategy templates |
| `POST` | `/partner/marketplace/subscribe` | Subscribe user to a template |

### **Authentication**

All Partner API endpoints require two headers:

```http
Authorization: Bearer pk_zebu_live_XXXXXXXX
X-Partner-Secret: sk_zebu_live_YYYYYYYY
```

### **Rate Limiting**

- **Limit**: 60 requests per minute
- **Algorithm**: Token bucket
- **Headers**:
  - `X-RateLimit-Limit`: Total requests allowed per minute
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Unix timestamp when limit resets

## Testing the API

### **Using cURL**

```bash
# Browse marketplace templates
curl -X GET 'https://257y9owov2.execute-api.ap-south-1.amazonaws.com/dev/partner/marketplace/templates?status=active&limit=10' \
  -H 'Authorization: Bearer pk_zebu_live_XXXXXXXX' \
  -H 'X-Partner-Secret: sk_zebu_live_YYYYYYYY'

# Subscribe a user
curl -X POST 'https://257y9owov2.execute-api.ap-south-1.amazonaws.com/dev/partner/marketplace/subscribe' \
  -H 'Authorization: Bearer pk_zebu_live_XXXXXXXX' \
  -H 'X-Partner-Secret: sk_zebu_live_YYYYYYYY' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_email": "user@example.com",
    "basket_id": "basket_admin_8f3e2a1b",
    "broker_account_id": "zebu_acc_12345",
    "custom_lot_multiplier": 1,
    "metadata": {
      "source": "zebu_mobile_app"
    }
  }'
```

### **Using HTTPie**

```bash
# Browse templates (cleaner syntax)
http GET 'https://257y9owov2.execute-api.ap-south-1.amazonaws.com/dev/partner/marketplace/templates' \
  Authorization:'Bearer pk_zebu_live_XXXXXXXX' \
  X-Partner-Secret:'sk_zebu_live_YYYYYYYY' \
  status==active \
  limit==10

# Subscribe user
http POST 'https://257y9owov2.execute-api.ap-south-1.amazonaws.com/dev/partner/marketplace/subscribe' \
  Authorization:'Bearer pk_zebu_live_XXXXXXXX' \
  X-Partner-Secret:'sk_zebu_live_YYYYYYYY' \
  user_email=user@example.com \
  basket_id=basket_admin_8f3e2a1b \
  broker_account_id=zebu_acc_12345
```

## Mock Server for Testing

Create a mock server from the specification for testing without hitting production:

### **Using Prism (Recommended)**

```bash
# Install Prism
npm install -g @stoplight/prism-cli

# Start mock server
prism mock docs/partner-api-openapi.yaml

# Server runs at http://localhost:4010
# All endpoints return example responses from the spec
```

### **Using Postman Mock Server**

1. Import the OpenAPI spec into Postman
2. Click on the collection → **...** → **Mock Collection**
3. Configure mock server settings
4. Get a mock server URL for testing

## Contract Testing

Use the OpenAPI spec for contract testing between your integration and our API:

### **Using Pact (Consumer-Driven Contract Testing)**

```javascript
// Example with Pact.js
const { Pact } = require('@pact-foundation/pact');
const { getMarketplaceTemplates } = require('./zebu-integration');

const provider = new Pact({
  consumer: 'Zebu-Platform',
  provider: 'QuantLeap-Partner-API',
  spec: 3, // OpenAPI version
});

describe('Partner API Contract', () => {
  it('should fetch marketplace templates', async () => {
    await provider.addInteraction({
      state: 'templates exist',
      uponReceiving: 'a request for templates',
      withRequest: {
        method: 'GET',
        path: '/partner/marketplace/templates',
        headers: {
          'Authorization': 'Bearer pk_zebu_test_123',
          'X-Partner-Secret': 'sk_zebu_test_456'
        }
      },
      willRespondWith: {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: {
          templates: [{
            basket_id: 'basket_admin_test',
            basket_name: 'Test Strategy'
          }]
        }
      }
    });

    const response = await getMarketplaceTemplates();
    expect(response.templates).toHaveLength(1);
  });
});
```

## Documentation Generation

Generate beautiful static documentation from the specification:

### **Using Redoc CLI**

```bash
# Install Redoc CLI
npm install -g redoc-cli

# Generate HTML documentation
redoc-cli bundle docs/partner-api-openapi.yaml \
  -o docs/partner-api-documentation.html \
  --title "QuantLeap Partner API" \
  --options.theme.colors.primary.main="#2563eb"

# Open the generated HTML file
open docs/partner-api-documentation.html
```

### **Using Swagger Codegen**

```bash
# Generate HTML documentation
swagger-codegen generate \
  -i docs/partner-api-openapi.yaml \
  -l html2 \
  -o docs/swagger-html
```

## API Versioning

The current API version is **v1.0.0**. Version information is included in:

- **Specification**: `info.version: 1.0.0`
- **Base URL**: `/v1` (production) or `/dev` (development)

Future versions will be released as:
- **Minor versions** (1.1.0): Backward-compatible additions
- **Major versions** (2.0.0): Breaking changes (new base URL like `/v2`)

## Schema Validation

Use JSON Schema validators to ensure your requests match the specification:

```javascript
const Ajv = require('ajv');
const openapi = require('./partner-api-openapi.json');

const ajv = new Ajv();
const subscribeSchema = openapi.paths['/partner/marketplace/subscribe'].post.requestBody.content['application/json'].schema;

const validate = ajv.compile(subscribeSchema);
const valid = validate({
  user_email: 'user@example.com',
  basket_id: 'basket_admin_123',
  broker_account_id: 'zebu_acc_456'
});

if (!valid) {
  console.error('Validation errors:', validate.errors);
}
```

## Support and Issues

- **Technical Support**: api-support@quantleap.in
- **Report Issues**: Include your `request_id` from error responses
- **SLA**: 99.9% uptime guarantee
- **Response Time**:
  - Critical issues: < 2 hours
  - Non-critical: < 24 hours

## Additional Resources

- **[API Documentation](PARTNER_API_DOCUMENTATION.md)** - Developer guide with code examples
- **[Integration Index](PARTNER_INTEGRATION_INDEX.md)** - Complete documentation overview
- **[Postman Collection](coming-soon)** - Pre-configured requests for testing
- **[Integration Examples](coming-soon)** - Full integration code in multiple languages

## Changelog

### v1.0.0 (2025-10-10)
- Initial release
- Browse marketplace templates endpoint
- Subscribe user endpoint
- Token bucket rate limiting (60 req/min)
- Complete schema definitions for all entities
- Comprehensive error handling (400, 401, 404, 409, 429, 500)

### Upcoming (v1.1.0)
- Webhook support for subscription events
- Partner revenue dashboard API
- Subscription management endpoints (update, cancel)
- Advanced filtering and search
- Batch subscription operations

---

**Ready to integrate?** Start with the [Quick Start](#quick-start) guide above or explore the [full API documentation](PARTNER_API_DOCUMENTATION.md).
