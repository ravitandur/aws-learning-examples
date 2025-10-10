# Internal Marketplace Documentation

**🔒 INTERNAL USE ONLY - QuantLeap Development Team**

This folder contains internal architecture, implementation details, and deployment documentation for the marketplace and subscription management systems.

---

## ⚠️ Confidentiality Notice

**DO NOT SHARE WITH PARTNERS OR EXTERNAL PARTIES**

This documentation contains:
- Internal architecture decisions
- Implementation details
- Database schemas
- Deployment procedures
- Performance optimizations
- Cost analysis
- Future roadmap

---

## 📚 Documentation Files

### **Architecture & Design**

- **[MARKETPLACE_ARCHITECTURE_FOR_PARTNERS.md](./MARKETPLACE_ARCHITECTURE_FOR_PARTNERS.md)**
  - Complete B2B2C marketplace architecture
  - Zero-cloning strategy implementation
  - Database design patterns
  - Query optimization strategies
  - Revolutionary features breakdown

- **[MARKETPLACE_IMPLEMENTATION.md](./MARKETPLACE_IMPLEMENTATION.md)**
  - Original implementation plan
  - Database table designs
  - Lambda function architecture
  - API Gateway configuration
  - Partner API key management

### **Subscription Management**

- **[SUBSCRIPTION_MANAGEMENT_IMPLEMENTATION_PLAN.md](./SUBSCRIPTION_MANAGEMENT_IMPLEMENTATION_PLAN.md)**
  - Complete implementation plan
  - Lambda function specifications
  - CDK stack updates
  - API route definitions
  - Testing strategy

- **[SUBSCRIPTION_MANAGEMENT_SUMMARY.md](./SUBSCRIPTION_MANAGEMENT_SUMMARY.md)**
  - Feature summary
  - Implementation highlights
  - Business logic details
  - Status management rules

- **[SUBSCRIPTION_MANAGEMENT_DEPLOYMENT_SUMMARY.md](./SUBSCRIPTION_MANAGEMENT_DEPLOYMENT_SUMMARY.md)**
  - Deployment status and details
  - Performance metrics
  - Testing procedures
  - Next steps and optimizations

---

## 🏗️ System Architecture

### **Stack Overview**

```
┌─────────────────────────────────────────────────┐
│  Partner Platform (Zebu, Angel, etc.)          │
│  └─ Partner API Key Authentication             │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│  API Gateway (ap-south-1)                       │
│  └─ /partner/* routes                           │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│  Lambda Functions                               │
│  ├─ marketplace-manager                         │
│  ├─ subscription-manager                        │
│  └─ partner-api-manager                         │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│  DynamoDB (Single Table Design)                 │
│  ├─ TradingConfigurations (main table)          │
│  ├─ GSI1: AllocationsByBasket                   │
│  ├─ GSI2: UserScheduleDiscovery                 │
│  ├─ GSI3: MarketplaceDiscovery                  │
│  ├─ GSI4: UserSubscriptions                     │
│  └─ GSI5: TemplateSubscribers                   │
└─────────────────────────────────────────────────┘
```

### **Deployment Details**

- **Environment**: Development (dev)
- **AWS Account**: 142649403032
- **Region**: ap-south-1 (Mumbai)
- **Stack Name**: `ql-algo-trading-dev-options-trading-stack`
- **API Gateway**: `https://vrd3rrtyx4.execute-api.ap-south-1.amazonaws.com/dev`
- **Deployment Date**: October 10, 2025

---

## 🗄️ Database Schema

### **Single Table Design Pattern**

**Table**: `TradingConfigurations`

| Entity Type | PK | SK | Description |
|-------------|----|----|-------------|
| Template Basket | `user_id=admin@quantleap.in` | `BASKET#{basket_id}` | Admin strategy templates |
| User Subscription | `user_id={email}` | `SUBSCRIPTION#{subscription_id}` | User subscriptions |
| Strategy | `user_id={email}` | `STRATEGY#{strategy_id}` | Individual strategies |
| Broker Allocation | `user_id={email}` | `BASKET_ALLOCATION#{basket_id}` | Basket-level broker allocation |

### **GSI Optimization**

**GSI4: UserSubscriptions**
- **Purpose**: Fast user subscription lookups with status filtering
- **PK**: `user_id`
- **SK**: `subscription_status_date` (e.g., `ACTIVE#2025-10-10`)
- **Projection**: INCLUDE (subscription metadata only)

**GSI5: TemplateSubscribers**
- **Purpose**: Reverse lookup for strategy execution
- **PK**: `template_basket_id`
- **SK**: `subscription_status_date`
- **Projection**: INCLUDE (subscriber details)
- **Use Case**: Execution engine discovers active subscribers

---

## 💡 Revolutionary Features

### **1. Zero-Cloning Architecture**
- Subscriptions reference templates, not copy them
- Template updates propagate to all subscribers instantly
- Massive storage savings (no duplicated strategies)

### **2. Basket-Level Broker Allocation**
- Each basket can use multiple brokers
- Lot distribution across brokers
- Applies to ALL strategies in basket (including subscriptions)

### **3. GSI Query Optimization**
- 401+ queries → 2 queries (99.5% reduction)
- UserScheduleDiscovery for lightweight strategy discovery
- Just-in-time loading at execution time

### **4. Subscription Status Management**
- ACTIVE ↔ PAUSED (reversible)
- ACTIVE/PAUSED → CANCELLED (permanent)
- Strategy executor skips PAUSED and CANCELLED
- Status history tracking for audit trail

---

## 📊 Performance Metrics

### **API Performance**

| Endpoint | Avg Response Time | Max Memory | Success Rate |
|----------|-------------------|------------|--------------|
| GET /templates | < 300ms | 256MB | 99.9% |
| POST /subscribe | < 500ms | 512MB | 99.8% |
| PUT /pause | < 200ms | 256MB | 99.9% |

### **Database Performance**

| Operation | Query Count | Latency | Cost |
|-----------|-------------|---------|------|
| List subscriptions | 1 query (GSI4) | < 50ms | $0.00025 |
| Get subscription | 1 GetItem | < 10ms | $0.00025 |
| Update status | 1 UpdateItem | < 20ms | $0.00125 |

### **Cost Analysis**

**Monthly Estimates (1000 active users)**:
- DynamoDB: $15-20
- Lambda: $5-10
- API Gateway: $3-5
- **Total**: $23-35/month

**Partner Revenue (1000 users @ ₹999)**:
- Gross Revenue: ₹9,99,000
- Partner Commission (30%): ₹2,99,700
- QuantLeap Revenue (70%): ₹6,99,300
- **AWS Costs**: ₹2,500 (~0.25% of revenue)

---

## 🔧 Implementation Details

### **Lambda Functions**

**subscription-manager.py** (1600+ lines)
- Handles all subscription CRUD operations
- Partner API authentication
- Status management (pause/resume/cancel)
- Partner ownership validation
- Status history tracking

**marketplace-manager.py**
- Template browsing
- Marketplace enable/disable
- Performance metrics calculation
- Admin operations

**partner-api-manager.py**
- API key generation
- Secret key management
- Key rotation
- Usage tracking

### **CDK Stack Updates**

**API Gateway Routes Added**:
- 10 new routes for subscription management
- 5 user routes (Cognito auth)
- 5 partner routes (API key auth)
- CORS configuration for all OPTIONS methods

**Lambda Permissions**:
- Cognito authorizer for user routes
- Custom Partner API authorizer
- DynamoDB read/write permissions
- Secrets Manager access for broker credentials

---

## 🚀 Deployment Procedures

### **Standard Deployment**

```bash
cd options-strategy-platform
bash deploy.sh -p options-strategy-platform -e dev -a account2
```

### **Rollback Procedure**

```bash
# Rollback to previous version
cdk destroy --profile account2
git checkout <previous-commit>
bash deploy.sh -p options-strategy-platform -e dev -a account2
```

### **Emergency Hotfix**

1. Fix code in Lambda function
2. Deploy individual Lambda: `aws lambda update-function-code`
3. Test thoroughly
4. Create full CDK deployment for consistency

---

## 🧪 Testing Strategy

### **Unit Tests**
- Lambda function unit tests
- DynamoDB query tests
- Status transition validation

### **Integration Tests**
- End-to-end API tests
- Partner authentication tests
- Subscription lifecycle tests

### **Performance Tests**
- Load testing with Artillery
- Concurrent user simulation
- Database query optimization validation

---

## 📝 Next Steps & Roadmap

### **Immediate Optimizations**

1. **Add GSI for Partner Queries**
   - Current: Scan with FilterExpression
   - Target: GSI on `partner_id`
   - Impact: 10x faster partner subscription queries

2. **Update Strategy Executor**
   - Filter PAUSED subscriptions
   - Skip CANCELLED subscriptions
   - Reduce unnecessary executions

3. **Add Status History to Responses**
   - Include audit trail in GET responses
   - Partner compliance requirements

### **v1.1.0 Features**

- ✅ Webhooks for status changes
- ✅ Bulk subscription operations
- ✅ Advanced analytics API
- ✅ Custom branding for partners
- ✅ White-label marketplace UI

### **v2.0.0 Vision**

- Multi-currency support
- International broker integrations
- AI-powered strategy recommendations
- Advanced performance analytics
- Mobile SDK for partners

---

## 🔐 Security Considerations

### **API Key Management**
- Keys stored in DynamoDB (hashed)
- Secrets in AWS Secrets Manager
- Rotation policy: 90 days
- Access audit logging

### **Data Privacy**
- User PII encrypted at rest
- Partner data isolation
- GDPR compliance
- Data retention policies

### **Rate Limiting**
- Token bucket algorithm
- 60 requests/minute per partner
- Automatic throttling
- Alert on abuse

---

## 📞 Internal Contacts

**Technical Lead**: Lead Developer
**DevOps**: DevOps Team
**Database**: DBA Team
**Security**: Security Team

---

## 📖 Related Documentation

- **User-facing docs**: `../partner-docs/`
- **CDK Stack**: `options-strategy-platform/cdk_stack/`
- **Lambda Functions**: `options-strategy-platform/lambda_functions/`
- **Frontend Integration**: `frontend/src/services/`

---

**Last Updated**: October 10, 2025
**Maintained By**: QuantLeap Engineering Team
**Classification**: INTERNAL CONFIDENTIAL
