# Partner API Documentation

**📦 FOR PARTNERS: Zebu, Angel, Upstox, etc.**

This folder contains all documentation required for integrating with QuantLeap's B2B2C Marketplace API.

---

## 🚀 Quick Start

**New to QuantLeap Partner API?** Start here:

1. **[Partner Integration Index](./PARTNER_INTEGRATION_INDEX.md)** - Overview and getting started guide
2. **[Quick Reference](./PARTNER_API_QUICK_REFERENCE.md)** - Quick reference for common operations
3. **[Full API Documentation](./PARTNER_API_DOCUMENTATION.md)** - Complete API reference with examples

---

## 📚 Documentation Files

### **Getting Started**

- **[PARTNER_INTEGRATION_INDEX.md](./PARTNER_INTEGRATION_INDEX.md)**
  - Complete partner integration guide
  - Architecture overview
  - Authentication setup
  - Integration workflow
  - **Start here if you're new!**

### **API Reference**

- **[PARTNER_API_DOCUMENTATION.md](./PARTNER_API_DOCUMENTATION.md)**
  - Complete API endpoint documentation
  - Request/response examples
  - Error handling
  - Best practices
  - **Your main reference document**

- **[SUBSCRIPTION_MANAGEMENT_API_REFERENCE.md](./SUBSCRIPTION_MANAGEMENT_API_REFERENCE.md)**
  - Subscription lifecycle management
  - Pause/resume/cancel operations
  - Status transitions
  - **Essential for user management**

- **[PARTNER_API_QUICK_REFERENCE.md](./PARTNER_API_QUICK_REFERENCE.md)**
  - Quick lookup for endpoints
  - Common code snippets
  - cURL examples
  - **Keep this handy during development**

### **OpenAPI Specifications**

- **[partner-api-openapi.json](./partner-api-openapi.json)**
  - OpenAPI 3.0.3 specification (JSON format)
  - Import into Postman, Insomnia, or any API client
  - Auto-generate client SDKs

- **[partner-api-openapi.yaml](./partner-api-openapi.yaml)**
  - OpenAPI 3.0.3 specification (YAML format)
  - Human-readable format
  - Use with Swagger UI

- **[OPENAPI_README.md](./OPENAPI_README.md)**
  - How to use OpenAPI specifications
  - Tools and recommendations
  - SDK generation guide

---

## 🔑 API Endpoints Summary

### **Base URL**
```
https://vrd3rrtyx4.execute-api.ap-south-1.amazonaws.com/dev
```

### **Authentication**
```http
Authorization: Bearer pk_zebu_live_XXXXXXXX
X-Partner-Secret: sk_zebu_live_YYYYYYYY
```

### **Available Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/partner/marketplace/templates` | GET | Browse available strategies |
| `/partner/marketplace/subscribe` | POST | Subscribe user to strategy |
| `/partner/subscriptions` | GET | List all subscriptions |
| `/partner/subscriptions/{id}` | GET | Get subscription details |
| `/partner/subscriptions/{id}` | DELETE | Cancel subscription |
| `/partner/subscriptions/{id}/pause` | PUT | Pause subscription |
| `/partner/subscriptions/{id}/resume` | PUT | Resume subscription |

---

## 🎯 Common Use Cases

### **1. Browse Available Strategies**
```bash
curl -X GET 'https://vrd3rrtyx4.execute-api.ap-south-1.amazonaws.com/dev/partner/marketplace/templates' \
  -H 'Authorization: Bearer pk_zebu_live_XXXXXXXX' \
  -H 'X-Partner-Secret: sk_zebu_live_YYYYYYYY'
```

### **2. Subscribe User to Strategy**
```bash
curl -X POST 'https://vrd3rrtyx4.execute-api.ap-south-1.amazonaws.com/dev/partner/marketplace/subscribe' \
  -H 'Authorization: Bearer pk_zebu_live_XXXXXXXX' \
  -H 'X-Partner-Secret: sk_zebu_live_YYYYYYYY' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_email": "user@example.com",
    "basket_id": "basket_admin_8f3e2a1b",
    "broker_account_id": "zebu_acc_12345",
    "custom_lot_multiplier": 1
  }'
```

### **3. Manage User Subscriptions**
```bash
# List all subscriptions
curl -X GET 'https://vrd3rrtyx4.execute-api.ap-south-1.amazonaws.com/dev/partner/subscriptions' \
  -H 'Authorization: Bearer pk_zebu_live_XXXXXXXX' \
  -H 'X-Partner-Secret: sk_zebu_live_YYYYYYYY'

# Pause subscription
curl -X PUT 'https://vrd3rrtyx4.execute-api.ap-south-1.amazonaws.com/dev/partner/subscriptions/sub_123/pause' \
  -H 'Authorization: Bearer pk_zebu_live_XXXXXXXX' \
  -H 'X-Partner-Secret: sk_zebu_live_YYYYYYYY'
```

---

## 💰 Revenue Model

- **Subscription Price**: ₹999/month per user
- **Partner Commission**: 30% (₹299.70)
- **QuantLeap Share**: 70% (₹699.30)
- **Payment**: Monthly, automated

---

## 🔒 Security Best Practices

1. **Never expose API keys** in frontend code
2. **Store secrets securely** in environment variables
3. **Use HTTPS** for all API calls
4. **Validate webhook signatures** (coming soon)
5. **Implement rate limiting** on your side
6. **Log API calls** for debugging and audit

---

## 📊 Rate Limits

- **Limit**: 60 requests per minute
- **Headers**:
  - `X-RateLimit-Limit`: Total limit
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset timestamp
- **429 Response**: Rate limit exceeded

---

## 🆘 Support

### **Technical Support**
- **Email**: api-support@quantleap.in
- **Response Time**: Within 24 hours
- **Include**: Request ID from error responses

### **Business Inquiries**
- **Email**: partnerships@quantleap.in
- **Phone**: +91-XXXXXXXXXX

### **Documentation Issues**
- **Report**: Github Issues (link TBD)
- **Contribute**: Pull requests welcome

---

## 📝 Changelog

### **Version 1.0.0** (October 10, 2025)
- ✅ Initial Partner API release
- ✅ Marketplace template browsing
- ✅ User subscription creation
- ✅ Subscription management (pause/resume/cancel)
- ✅ OpenAPI 3.0.3 specifications
- ✅ Complete documentation

### **Upcoming** (v1.1.0)
- 🔜 Webhooks support
- 🔜 Bulk subscription operations
- 🔜 Advanced analytics API
- 🔜 Custom branding options

---

## 🌐 Additional Resources

- **Production API**: Coming soon
- **Sandbox Environment**: Use development endpoint for testing
- **Status Page**: https://status.quantleap.in (coming soon)
- **API Changelog**: Updated monthly

---

## ⚖️ Terms of Service

By using the QuantLeap Partner API, you agree to:
- Our [Terms of Service](https://quantleap.in/terms)
- Our [Privacy Policy](https://quantleap.in/privacy)
- Our [Partner Agreement](https://quantleap.in/partner-agreement)

---

**Last Updated**: October 10, 2025
**API Version**: 1.0.0
**Status**: ✅ Production Ready
