# Subscription Management Implementation Plan

## 📋 Overview

Complete implementation plan for subscription management features (view, cancel, pause, resume) for both **QuantLeap direct users** and **Partner users** (Zebu, etc.).

---

## 🎯 Requirements

### **Current State**
- ✅ Subscribe functionality (both user types)
- ✅ View subscriptions (QuantLeap users only)
- ✅ Cancel/Unsubscribe (QuantLeap users only)
- ❌ Pause subscription (not implemented)
- ❌ Resume subscription (not implemented)
- ❌ Partner API subscription management (not implemented)

### **Target State**
- ✅ Subscribe functionality (both user types)
- ✅ View subscriptions (both user types)
- ✅ Cancel/Unsubscribe (both user types)
- ✅ Pause subscription (both user types)
- ✅ Resume subscription (both user types)
- ✅ Partner API subscription management (complete)

---

## 📊 Feature Matrix

| Feature | QuantLeap Users | Partner Users (Zebu) | Status |
|---------|-----------------|----------------------|--------|
| **View All Subscriptions** | ✅ Implemented | ❌ Missing | Need to implement |
| **View Single Subscription** | ❌ Missing | ❌ Missing | Need to implement |
| **Cancel Subscription** | ✅ Implemented | ❌ Missing | Need to implement |
| **Pause Subscription** | ❌ Missing | ❌ Missing | Need to implement |
| **Resume Subscription** | ❌ Missing | ❌ Missing | Need to implement |

---

## 🏗️ Architecture Design

### **1. API Endpoints**

#### **QuantLeap Users (Cognito Authentication)**

| Method | Endpoint | Purpose | Current Status |
|--------|----------|---------|----------------|
| `GET` | `/options/user/subscriptions` | List all user subscriptions | ✅ Implemented |
| `GET` | `/options/user/subscriptions/{subscription_id}` | Get subscription details | ❌ Need to add |
| `DELETE` | `/options/user/subscriptions/{subscription_id}` | Cancel subscription | ✅ Implemented |
| `PUT` | `/options/user/subscriptions/{subscription_id}/pause` | Pause subscription | ❌ Need to add |
| `PUT` | `/options/user/subscriptions/{subscription_id}/resume` | Resume subscription | ❌ Need to add |

#### **Partner Users (Partner API Authentication)**

| Method | Endpoint | Purpose | Current Status |
|--------|----------|---------|----------------|
| `GET` | `/partner/subscriptions` | List all partner's user subscriptions | ❌ Need to add |
| `GET` | `/partner/subscriptions?user_email={email}` | Filter by specific user | ❌ Need to add |
| `GET` | `/partner/subscriptions/{subscription_id}` | Get subscription details | ❌ Need to add |
| `DELETE` | `/partner/subscriptions/{subscription_id}` | Cancel subscription | ❌ Need to add |
| `PUT` | `/partner/subscriptions/{subscription_id}/pause` | Pause subscription | ❌ Need to add |
| `PUT` | `/partner/subscriptions/{subscription_id}/resume` | Resume subscription | ❌ Need to add |

---

## 📐 Data Model Changes

### **Subscription Status Enum**

```python
SUBSCRIPTION_STATUS = {
    'ACTIVE': 'Active subscription, executions running',
    'PAUSED': 'Temporarily paused by user, no executions',
    'CANCELLED': 'Permanently cancelled, no executions',
    'EXPIRED': 'Payment failed or subscription ended'
}
```

### **Subscription Entity**

```python
{
    "user_id": "user@example.com",
    "sort_key": "SUBSCRIPTION#sub_zebu_001",

    # Core fields (existing)
    "subscription_id": "sub_zebu_001",
    "template_basket_id": "basket_admin_iron_condor",
    "template_owner_id": "admin@quantleap.in",
    "partner_id": "partner_zebu_live",  # or null for direct users
    "broker_account_id": "zebu_acc_12345",

    # Status fields (enhance)
    "status": "ACTIVE",  # ACTIVE | PAUSED | CANCELLED | EXPIRED
    "subscription_status_date": "ACTIVE#2025-10-10",  # For GSI queries

    # Timestamps (existing + new)
    "subscribed_at": "2025-10-10T10:00:00Z",
    "cancelled_at": null,  # Set when cancelled
    "paused_at": null,  # NEW: Set when paused
    "resumed_at": null,  # NEW: Set when resumed
    "last_status_change_at": "2025-10-10T10:00:00Z",  # NEW: Track last change

    # Status history (NEW)
    "status_history": [
        {
            "status": "ACTIVE",
            "timestamp": "2025-10-10T10:00:00Z",
            "changed_by": "user@example.com",
            "reason": "Initial subscription"
        },
        {
            "status": "PAUSED",
            "timestamp": "2025-10-15T14:30:00Z",
            "changed_by": "user@example.com",
            "reason": "User paused via UI"
        },
        {
            "status": "ACTIVE",
            "timestamp": "2025-10-20T09:00:00Z",
            "changed_by": "user@example.com",
            "reason": "User resumed via UI"
        }
    ],

    # Billing (existing)
    "subscription_price": 999,
    "partner_commission": 299.7,
    "next_billing_date": "2025-11-10T10:00:00Z",
    "auto_renew": true,

    # Custom config (existing)
    "custom_lot_multiplier": 1.0
}
```

---

## 🔧 Implementation Steps

### **Phase 1: Backend - QuantLeap User Endpoints** (2-3 days)

#### **Step 1.1: Add Pause Functionality**

**File**: `options-strategy-platform/lambda_functions/option_baskets/subscription_manager.py`

```python
def pause_subscription(user_id: str, subscription_id: str, table):
    """
    Pause user subscription
    - Changes status from ACTIVE → PAUSED
    - Records pause timestamp
    - Adds to status history
    - Strategy executor will skip PAUSED subscriptions
    """
    try:
        now = datetime.now(timezone.utc).isoformat()

        # Get current subscription to validate status
        response = table.get_item(
            Key={
                'user_id': user_id,
                'sort_key': f'SUBSCRIPTION#{subscription_id}'
            }
        )

        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Subscription not found'})
            }

        subscription = response['Item']
        current_status = subscription.get('status')

        # Validate status transition
        if current_status != 'ACTIVE':
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Invalid status transition',
                    'message': f'Can only pause ACTIVE subscriptions. Current status: {current_status}'
                })
            }

        # Update subscription status
        status_history_entry = {
            'status': 'PAUSED',
            'timestamp': now,
            'changed_by': user_id,
            'reason': 'User paused subscription'
        }

        response = table.update_item(
            Key={
                'user_id': user_id,
                'sort_key': f'SUBSCRIPTION#{subscription_id}'
            },
            UpdateExpression='''
                SET #status = :status,
                    paused_at = :paused_at,
                    last_status_change_at = :change_time,
                    subscription_status_date = :status_date,
                    status_history = list_append(
                        if_not_exists(status_history, :empty_list),
                        :history_entry
                    )
            ''',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'PAUSED',
                ':paused_at': now,
                ':change_time': now,
                ':status_date': f'PAUSED#{datetime.now(timezone.utc).strftime("%Y-%m-%d")}',
                ':history_entry': [status_history_entry],
                ':empty_list': []
            },
            ReturnValues='ALL_NEW'
        )

        logger.info("Subscription paused", extra={
            "user_id": user_id,
            "subscription_id": subscription_id
        })

        log_user_action(logger, user_id, "subscription_paused", {
            "subscription_id": subscription_id
        })

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Subscription paused successfully',
                'subscription_id': subscription_id,
                'status': 'PAUSED',
                'paused_at': now
            })
        }

    except Exception as e:
        logger.error("Failed to pause subscription", extra={
            "error": str(e),
            "user_id": user_id,
            "subscription_id": subscription_id
        })
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to pause subscription',
                'message': str(e)
            })
        }
```

#### **Step 1.2: Add Resume Functionality**

```python
def resume_subscription(user_id: str, subscription_id: str, table):
    """
    Resume paused subscription
    - Changes status from PAUSED → ACTIVE
    - Records resume timestamp
    - Adds to status history
    - Strategy executor will start executing again
    """
    try:
        now = datetime.now(timezone.utc).isoformat()

        # Get current subscription to validate status
        response = table.get_item(
            Key={
                'user_id': user_id,
                'sort_key': f'SUBSCRIPTION#{subscription_id}'
            }
        )

        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Subscription not found'})
            }

        subscription = response['Item']
        current_status = subscription.get('status')

        # Validate status transition
        if current_status != 'PAUSED':
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Invalid status transition',
                    'message': f'Can only resume PAUSED subscriptions. Current status: {current_status}'
                })
            }

        # Update subscription status
        status_history_entry = {
            'status': 'ACTIVE',
            'timestamp': now,
            'changed_by': user_id,
            'reason': 'User resumed subscription'
        }

        response = table.update_item(
            Key={
                'user_id': user_id,
                'sort_key': f'SUBSCRIPTION#{subscription_id}'
            },
            UpdateExpression='''
                SET #status = :status,
                    resumed_at = :resumed_at,
                    last_status_change_at = :change_time,
                    subscription_status_date = :status_date,
                    status_history = list_append(
                        if_not_exists(status_history, :empty_list),
                        :history_entry
                    )
            ''',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'ACTIVE',
                ':resumed_at': now,
                ':change_time': now,
                ':status_date': f'ACTIVE#{datetime.now(timezone.utc).strftime("%Y-%m-%d")}',
                ':history_entry': [status_history_entry],
                ':empty_list': []
            },
            ReturnValues='ALL_NEW'
        )

        logger.info("Subscription resumed", extra={
            "user_id": user_id,
            "subscription_id": subscription_id
        })

        log_user_action(logger, user_id, "subscription_resumed", {
            "subscription_id": subscription_id
        })

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Subscription resumed successfully',
                'subscription_id': subscription_id,
                'status': 'ACTIVE',
                'resumed_at': now
            })
        }

    except Exception as e:
        logger.error("Failed to resume subscription", extra={
            "error": str(e),
            "user_id": user_id,
            "subscription_id": subscription_id
        })
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to resume subscription',
                'message': str(e)
            })
        }
```

#### **Step 1.3: Add Get Single Subscription**

```python
def get_subscription_details(user_id: str, subscription_id: str, table):
    """Get detailed information about a specific subscription"""
    try:
        response = table.get_item(
            Key={
                'user_id': user_id,
                'sort_key': f'SUBSCRIPTION#{subscription_id}'
            }
        )

        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Subscription not found'
                })
            }

        subscription = response['Item']

        # Get template details
        template_response = table.get_item(
            Key={
                'user_id': subscription.get('template_owner_id'),
                'sort_key': f'BASKET#{subscription.get("template_basket_id")}'
            }
        )

        template_info = None
        if 'Item' in template_response:
            template = template_response['Item']
            template_info = {
                'basket_name': template.get('basket_name'),
                'description': template.get('description'),
                'is_marketplace_enabled': template.get('is_marketplace_enabled', False)
            }

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'subscription': subscription,
                'template': template_info
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        logger.error("Failed to get subscription details", extra={
            "error": str(e),
            "user_id": user_id,
            "subscription_id": subscription_id
        })
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to get subscription details',
                'message': str(e)
            })
        }
```

#### **Step 1.4: Update Lambda Handler**

```python
def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Subscription Manager Handler"""

    log_lambda_event(logger, event, context)

    try:
        http_method = event['httpMethod']
        path = event.get('path', '')
        path_parameters = event.get('pathParameters', {})

        # Get authenticated user from Cognito or Partner API
        user_id = None
        partner_info = None

        # Check if this is a partner API request
        if path.startswith('/partner/'):
            partner_info = validate_partner_request(event, dynamodb_table)
            if 'statusCode' in partner_info and partner_info['statusCode'] != 200:
                return partner_info
        else:
            # Regular user (Cognito)
            user_id = event['requestContext']['authorizer']['claims']['email']

        # Route to appropriate handler

        # ========== QuantLeap User Endpoints ==========

        if path.startswith('/options/user/subscriptions'):
            subscription_id = path_parameters.get('subscription_id')

            if http_method == 'GET' and not subscription_id:
                # GET /options/user/subscriptions - List all
                return get_user_subscriptions(user_id, dynamodb_table)

            elif http_method == 'GET' and subscription_id:
                # GET /options/user/subscriptions/{id} - Get details
                return get_subscription_details(user_id, subscription_id, dynamodb_table)

            elif http_method == 'DELETE' and subscription_id:
                # DELETE /options/user/subscriptions/{id} - Cancel
                return cancel_subscription(user_id, subscription_id, dynamodb_table)

            elif http_method == 'PUT' and subscription_id and path.endswith('/pause'):
                # PUT /options/user/subscriptions/{id}/pause
                return pause_subscription(user_id, subscription_id, dynamodb_table)

            elif http_method == 'PUT' and subscription_id and path.endswith('/resume'):
                # PUT /options/user/subscriptions/{id}/resume
                return resume_subscription(user_id, subscription_id, dynamodb_table)

        # ========== Partner API Endpoints ==========

        elif path.startswith('/partner/subscriptions'):
            subscription_id = path_parameters.get('subscription_id')
            query_params = event.get('queryStringParameters', {}) or {}

            if http_method == 'GET' and not subscription_id:
                # GET /partner/subscriptions - List all partner subscriptions
                return get_partner_subscriptions(partner_info, query_params, dynamodb_table)

            elif http_method == 'GET' and subscription_id:
                # GET /partner/subscriptions/{id} - Get details
                return get_partner_subscription_details(partner_info, subscription_id, dynamodb_table)

            elif http_method == 'DELETE' and subscription_id:
                # DELETE /partner/subscriptions/{id} - Cancel
                return cancel_partner_subscription(partner_info, subscription_id, dynamodb_table)

            elif http_method == 'PUT' and subscription_id and path.endswith('/pause'):
                # PUT /partner/subscriptions/{id}/pause
                return pause_partner_subscription(partner_info, subscription_id, dynamodb_table)

            elif http_method == 'PUT' and subscription_id and path.endswith('/resume'):
                # PUT /partner/subscriptions/{id}/resume
                return resume_partner_subscription(partner_info, subscription_id, dynamodb_table)

        # Unknown route
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Route not found'})
        }

    except Exception as e:
        logger.error("Lambda handler error", extra={"error": str(e)})
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'message': str(e)})
        }
```

---

### **Phase 2: Backend - Partner API Endpoints** (2-3 days)

#### **Step 2.1: List Partner Subscriptions**

```python
def get_partner_subscriptions(partner_info: Dict, query_params: Dict, table):
    """
    Get all subscriptions created by this partner
    Supports filtering by user_email
    """
    try:
        partner_id = partner_info['partner_id']
        user_email = query_params.get('user_email')

        if user_email:
            # Filter by specific user
            response = table.query(
                IndexName='PartnerSubscriptions',  # GSI: partner_id + user_id
                KeyConditionExpression='partner_id = :partner_id AND user_id = :user_id',
                ExpressionAttributeValues={
                    ':partner_id': partner_id,
                    ':user_id': user_email
                }
            )
        else:
            # Get all partner subscriptions
            response = table.query(
                IndexName='PartnerSubscriptions',
                KeyConditionExpression='partner_id = :partner_id',
                ExpressionAttributeValues={
                    ':partner_id': partner_id
                }
            )

        subscriptions = response.get('Items', [])

        # Enrich with template information
        for subscription in subscriptions:
            template_id = subscription.get('template_basket_id')
            template_owner_id = subscription.get('template_owner_id')

            if template_id and template_owner_id:
                template_response = table.get_item(
                    Key={
                        'user_id': template_owner_id,
                        'sort_key': f'BASKET#{template_id}'
                    }
                )

                if 'Item' in template_response:
                    subscription['template_name'] = template_response['Item'].get('basket_name')

        logger.info("Partner subscriptions retrieved", extra={
            "partner_id": partner_id,
            "count": len(subscriptions),
            "filtered_user": user_email
        })

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'subscriptions': subscriptions,
                'total': len(subscriptions),
                'partner_id': partner_id
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        logger.error("Failed to get partner subscriptions", extra={
            "error": str(e),
            "partner_id": partner_info.get('partner_id')
        })
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to get partner subscriptions',
                'message': str(e)
            })
        }
```

#### **Step 2.2: Partner Cancel/Pause/Resume**

```python
def cancel_partner_subscription(partner_info: Dict, subscription_id: str, table):
    """
    Cancel subscription on behalf of partner user
    Validates that subscription belongs to this partner
    """
    try:
        partner_id = partner_info['partner_id']

        # Get subscription to validate partner ownership
        # Since we don't know user_id, query by subscription_id using GSI
        response = table.query(
            IndexName='SubscriptionIndex',  # GSI: subscription_id
            KeyConditionExpression='subscription_id = :sub_id',
            ExpressionAttributeValues={':sub_id': subscription_id}
        )

        if not response.get('Items'):
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'Subscription not found'
                })
            }

        subscription = response['Items'][0]
        subscription_partner_id = subscription.get('partner_id')

        # Validate partner ownership
        if subscription_partner_id != partner_id:
            return {
                'statusCode': 403,
                'body': json.dumps({
                    'error': 'Forbidden',
                    'message': 'This subscription does not belong to your partner account'
                })
            }

        user_id = subscription.get('user_id')

        # Use existing cancel_subscription function
        return cancel_subscription(user_id, subscription_id, table)

    except Exception as e:
        logger.error("Failed to cancel partner subscription", extra={
            "error": str(e),
            "partner_id": partner_info.get('partner_id'),
            "subscription_id": subscription_id
        })
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to cancel subscription',
                'message': str(e)
            })
        }


def pause_partner_subscription(partner_info: Dict, subscription_id: str, table):
    """Pause subscription on behalf of partner user"""
    # Similar validation logic as cancel, then call pause_subscription
    pass  # Implementation similar to cancel_partner_subscription


def resume_partner_subscription(partner_info: Dict, subscription_id: str, table):
    """Resume subscription on behalf of partner user"""
    # Similar validation logic as cancel, then call resume_subscription
    pass  # Implementation similar to cancel_partner_subscription
```

---

### **Phase 3: Infrastructure - API Gateway Routes** (1 day)

**File**: `options-strategy-platform/cdk_stack/options_trading_stack.py`

#### **Step 3.1: QuantLeap User Routes**

```python
# Add after existing user subscription routes (around line 685)

# GET /options/user/subscriptions/{subscription_id} - Get details
user_subscription_id_resource.add_method("GET",
    apigateway.LambdaIntegration(self.lambda_functions['subscription-manager']),
    authorization_type=apigateway.AuthorizationType.COGNITO,
    authorizer=authorizer
)

# PUT /options/user/subscriptions/{subscription_id}/pause - Pause
user_pause_resource = user_subscription_id_resource.add_resource("pause")
user_pause_resource.add_method("PUT",
    apigateway.LambdaIntegration(self.lambda_functions['subscription-manager']),
    authorization_type=apigateway.AuthorizationType.COGNITO,
    authorizer=authorizer
)

# PUT /options/user/subscriptions/{subscription_id}/resume - Resume
user_resume_resource = user_subscription_id_resource.add_resource("resume")
user_resume_resource.add_method("PUT",
    apigateway.LambdaIntegration(self.lambda_functions['subscription-manager']),
    authorization_type=apigateway.AuthorizationType.COGNITO,
    authorizer=authorizer
)
```

#### **Step 3.2: Partner API Routes**

```python
# Add after existing partner routes (around line 766)

# Partner subscription management
partner_subscriptions_resource = partner_resource.add_resource("subscriptions")

# GET /partner/subscriptions - List partner subscriptions
partner_subscriptions_resource.add_method("GET",
    apigateway.LambdaIntegration(self.lambda_functions['subscription-manager']),
    authorization_type=apigateway.AuthorizationType.NONE
)

# GET /partner/subscriptions/{subscription_id} - Get details
partner_subscription_id_resource = partner_subscriptions_resource.add_resource("{subscription_id}")
partner_subscription_id_resource.add_method("GET",
    apigateway.LambdaIntegration(self.lambda_functions['subscription-manager']),
    authorization_type=apigateway.AuthorizationType.NONE
)

# DELETE /partner/subscriptions/{subscription_id} - Cancel
partner_subscription_id_resource.add_method("DELETE",
    apigateway.LambdaIntegration(self.lambda_functions['subscription-manager']),
    authorization_type=apigateway.AuthorizationType.NONE
)

# PUT /partner/subscriptions/{subscription_id}/pause - Pause
partner_pause_resource = partner_subscription_id_resource.add_resource("pause")
partner_pause_resource.add_method("PUT",
    apigateway.LambdaIntegration(self.lambda_functions['subscription-manager']),
    authorization_type=apigateway.AuthorizationType.NONE
)

# PUT /partner/subscriptions/{subscription_id}/resume - Resume
partner_resume_resource = partner_subscription_id_resource.add_resource("resume")
partner_resume_resource.add_method("PUT",
    apigateway.LambdaIntegration(self.lambda_functions['subscription-manager']),
    authorization_type=apigateway.AuthorizationType.NONE
)
```

---

### **Phase 4: Strategy Executor Update** (1 day)

**File**: `options-strategy-platform/lambda_functions/strategy_execution/strategy_executor.py`

```python
def get_active_subscriptions(user_id: str, table) -> List[Dict]:
    """
    Get active subscriptions for user
    ONLY returns ACTIVE subscriptions (excludes PAUSED, CANCELLED, EXPIRED)
    """
    response = table.query(
        KeyConditionExpression='user_id = :user_id AND begins_with(sort_key, :prefix)',
        FilterExpression='#status = :active_status',  # Add filter
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':user_id': user_id,
            ':prefix': 'SUBSCRIPTION#',
            ':active_status': 'ACTIVE'  # Only ACTIVE subscriptions
        }
    )

    return response.get('Items', [])
```

**Key Change**: Add `FilterExpression='#status = :active_status'` to skip PAUSED/CANCELLED subscriptions during execution.

---

### **Phase 5: DynamoDB GSI (if needed)** (1 day)

**Check if GSI exists for Partner queries**:

```python
# PartnerSubscriptions GSI
{
    "IndexName": "PartnerSubscriptions",
    "Keys": {
        "PartitionKey": "partner_id",
        "SortKey": "user_id"
    },
    "ProjectionType": "ALL"
}

# SubscriptionIndex GSI (for lookup by subscription_id)
{
    "IndexName": "SubscriptionIndex",
    "Keys": {
        "PartitionKey": "subscription_id"
    },
    "ProjectionType": "ALL"
}
```

If these don't exist, add to CDK stack:

```python
# In options_trading_stack.py, add to main table
options_basket_table.add_global_secondary_index(
    index_name="PartnerSubscriptions",
    partition_key=dynamodb.Attribute(name="partner_id", type=dynamodb.AttributeType.STRING),
    sort_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
    projection_type=dynamodb.ProjectionType.ALL
)

options_basket_table.add_global_secondary_index(
    index_name="SubscriptionIndex",
    partition_key=dynamodb.Attribute(name="subscription_id", type=dynamodb.AttributeType.STRING),
    projection_type=dynamodb.ProjectionType.ALL
)
```

**NOTE**: DynamoDB allows only ONE GSI creation per deployment. Deploy them separately or manually.

---

### **Phase 6: OpenAPI Specification Update** (1 day)

Update `docs/marketplace/partner-api-openapi.json` and `.yaml` with new endpoints.

See detailed OpenAPI spec in next section.

---

### **Phase 7: Documentation Update** (1 day)

Update all partner documentation:
1. `PARTNER_API_DOCUMENTATION.md` - Add new endpoints with examples
2. `PARTNER_API_QUICK_REFERENCE.md` - Add quick reference
3. `MARKETPLACE_ARCHITECTURE_FOR_PARTNERS.md` - Update architecture diagrams
4. `PARTNER_INTEGRATION_INDEX.md` - Update feature matrix

---

### **Phase 8: Frontend Implementation** (3-4 days)

#### **Step 8.1: Subscription Management Service**

**File**: `frontend/src/services/subscriptionService.ts`

```typescript
export interface Subscription {
  subscription_id: string;
  template_basket_id: string;
  template_name?: string;
  status: 'ACTIVE' | 'PAUSED' | 'CANCELLED' | 'EXPIRED';
  subscribed_at: string;
  paused_at?: string;
  resumed_at?: string;
  cancelled_at?: string;
  subscription_price: number;
  partner_commission?: number;
  partner_id?: string;
  broker_account_id: string;
  custom_lot_multiplier: number;
  next_billing_date: string;
  auto_renew: boolean;
}

class SubscriptionService {
  private apiUrl: string;

  constructor() {
    this.apiUrl = process.env.REACT_APP_OPTIONS_API_URL_DEV || '';
  }

  // Get all user subscriptions
  async getUserSubscriptions(token: string): Promise<Subscription[]> {
    const response = await fetch(`${this.apiUrl}/options/user/subscriptions`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error('Failed to fetch subscriptions');
    }

    const data = await response.json();
    return data.subscriptions || [];
  }

  // Get single subscription details
  async getSubscriptionDetails(token: string, subscriptionId: string): Promise<Subscription> {
    const response = await fetch(
      `${this.apiUrl}/options/user/subscriptions/${subscriptionId}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch subscription details');
    }

    const data = await response.json();
    return data.subscription;
  }

  // Pause subscription
  async pauseSubscription(token: string, subscriptionId: string): Promise<void> {
    const response = await fetch(
      `${this.apiUrl}/options/user/subscriptions/${subscriptionId}/pause`,
      {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to pause subscription');
    }
  }

  // Resume subscription
  async resumeSubscription(token: string, subscriptionId: string): Promise<void> {
    const response = await fetch(
      `${this.apiUrl}/options/user/subscriptions/${subscriptionId}/resume`,
      {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to resume subscription');
    }
  }

  // Cancel subscription
  async cancelSubscription(token: string, subscriptionId: string): Promise<void> {
    const response = await fetch(
      `${this.apiUrl}/options/user/subscriptions/${subscriptionId}`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to cancel subscription');
    }
  }
}

export default new SubscriptionService();
```

#### **Step 8.2: Subscriptions Page Component**

**File**: `frontend/src/pages/SubscriptionsPage.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import subscriptionService, { Subscription } from '../services/subscriptionService';
import { Card, CardHeader, CardContent } from '../components/ui/Card';
import { Play, Pause, X, CheckCircle, AlertCircle } from 'lucide-react';

const SubscriptionsPage: React.FC = () => {
  const { token } = useAuth();
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    loadSubscriptions();
  }, []);

  const loadSubscriptions = async () => {
    if (!token) return;

    setLoading(true);
    try {
      const data = await subscriptionService.getUserSubscriptions(token);
      setSubscriptions(data);
    } catch (error) {
      console.error('Failed to load subscriptions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePause = async (subscriptionId: string) => {
    if (!token) return;

    setActionLoading(subscriptionId);
    try {
      await subscriptionService.pauseSubscription(token, subscriptionId);
      await loadSubscriptions();
    } catch (error) {
      console.error('Failed to pause subscription:', error);
      alert('Failed to pause subscription');
    } finally {
      setActionLoading(null);
    }
  };

  const handleResume = async (subscriptionId: string) => {
    if (!token) return;

    setActionLoading(subscriptionId);
    try {
      await subscriptionService.resumeSubscription(token, subscriptionId);
      await loadSubscriptions();
    } catch (error) {
      console.error('Failed to resume subscription:', error);
      alert('Failed to resume subscription');
    } finally {
      setActionLoading(null);
    }
  };

  const handleCancel = async (subscriptionId: string) => {
    if (!token) return;

    const confirmed = window.confirm(
      'Are you sure you want to cancel this subscription? This action cannot be undone.'
    );

    if (!confirmed) return;

    setActionLoading(subscriptionId);
    try {
      await subscriptionService.cancelSubscription(token, subscriptionId);
      await loadSubscriptions();
    } catch (error) {
      console.error('Failed to cancel subscription:', error);
      alert('Failed to cancel subscription');
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      ACTIVE: { color: 'bg-green-100 text-green-800', icon: CheckCircle },
      PAUSED: { color: 'bg-yellow-100 text-yellow-800', icon: Pause },
      CANCELLED: { color: 'bg-red-100 text-red-800', icon: X },
      EXPIRED: { color: 'bg-gray-100 text-gray-800', icon: AlertCircle }
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.ACTIVE;
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="w-3 h-3 mr-1" />
        {status}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">My Subscriptions</h1>
        <div className="text-center py-12">Loading subscriptions...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">My Subscriptions</h1>
        <div className="text-sm text-gray-600">
          {subscriptions.length} {subscriptions.length === 1 ? 'subscription' : 'subscriptions'}
        </div>
      </div>

      {subscriptions.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-500">You don't have any subscriptions yet.</p>
            <p className="text-sm text-gray-400 mt-2">
              Browse the marketplace to subscribe to strategies.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6">
          {subscriptions.map((subscription) => (
            <Card key={subscription.subscription_id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-lg font-semibold">
                      {subscription.template_name || 'Strategy Template'}
                    </h3>
                    <p className="text-sm text-gray-500 mt-1">
                      Subscribed on {new Date(subscription.subscribed_at).toLocaleDateString()}
                    </p>
                  </div>
                  {getStatusBadge(subscription.status)}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Price</span>
                    <p className="font-semibold">₹{subscription.subscription_price}/month</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Lot Multiplier</span>
                    <p className="font-semibold">{subscription.custom_lot_multiplier}x</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Next Billing</span>
                    <p className="font-semibold">
                      {new Date(subscription.next_billing_date).toLocaleDateString()}
                    </p>
                  </div>
                  <div>
                    <span className="text-gray-500">Auto Renew</span>
                    <p className="font-semibold">
                      {subscription.auto_renew ? 'Yes' : 'No'}
                    </p>
                  </div>
                </div>

                <div className="flex gap-3 pt-2">
                  {subscription.status === 'ACTIVE' && (
                    <>
                      <button
                        onClick={() => handlePause(subscription.subscription_id)}
                        disabled={actionLoading === subscription.subscription_id}
                        className="flex items-center gap-2 px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 disabled:opacity-50"
                      >
                        <Pause className="w-4 h-4" />
                        {actionLoading === subscription.subscription_id ? 'Pausing...' : 'Pause'}
                      </button>
                      <button
                        onClick={() => handleCancel(subscription.subscription_id)}
                        disabled={actionLoading === subscription.subscription_id}
                        className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50"
                      >
                        <X className="w-4 h-4" />
                        {actionLoading === subscription.subscription_id ? 'Cancelling...' : 'Cancel'}
                      </button>
                    </>
                  )}

                  {subscription.status === 'PAUSED' && (
                    <>
                      <button
                        onClick={() => handleResume(subscription.subscription_id)}
                        disabled={actionLoading === subscription.subscription_id}
                        className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50"
                      >
                        <Play className="w-4 h-4" />
                        {actionLoading === subscription.subscription_id ? 'Resuming...' : 'Resume'}
                      </button>
                      <button
                        onClick={() => handleCancel(subscription.subscription_id)}
                        disabled={actionLoading === subscription.subscription_id}
                        className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50"
                      >
                        <X className="w-4 h-4" />
                        {actionLoading === subscription.subscription_id ? 'Cancelling...' : 'Cancel'}
                      </button>
                    </>
                  )}

                  {subscription.status === 'CANCELLED' && (
                    <p className="text-sm text-gray-500">
                      Cancelled on {new Date(subscription.cancelled_at!).toLocaleDateString()}
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default SubscriptionsPage;
```

---

## 📅 Implementation Timeline

| Phase | Duration | Tasks | Team |
|-------|----------|-------|------|
| **Phase 1** | 2-3 days | QuantLeap user endpoints (pause, resume, get details) | Backend |
| **Phase 2** | 2-3 days | Partner API endpoints (list, cancel, pause, resume) | Backend |
| **Phase 3** | 1 day | CDK stack updates (API Gateway routes) | DevOps |
| **Phase 4** | 1 day | Strategy executor update (filter PAUSED) | Backend |
| **Phase 5** | 1 day | DynamoDB GSI (if needed) | DevOps |
| **Phase 6** | 1 day | OpenAPI specification update | Backend |
| **Phase 7** | 1 day | Documentation update | Documentation |
| **Phase 8** | 3-4 days | Frontend implementation (React components) | Frontend |
| **Testing** | 2-3 days | End-to-end testing, QA | QA Team |
| **Deployment** | 1 day | Production deployment | DevOps |

**Total Estimated Time**: 14-18 days (2.5-3.5 weeks)

---

## ✅ Testing Checklist

### **Unit Tests**
- [ ] Test pause_subscription() function
- [ ] Test resume_subscription() function
- [ ] Test status transition validation
- [ ] Test partner ownership validation
- [ ] Test status history tracking

### **Integration Tests**
- [ ] Test QuantLeap user pause/resume flow
- [ ] Test Partner API pause/resume flow
- [ ] Test strategy executor skips PAUSED subscriptions
- [ ] Test billing continues/stops for PAUSED (business rule)

### **End-to-End Tests**
- [ ] User subscribes → pauses → resumes → cancels
- [ ] Partner subscribes user → partner pauses → partner resumes → partner cancels
- [ ] Verify executions stop when paused
- [ ] Verify executions resume when resumed
- [ ] Verify subscriber count updates correctly

### **Security Tests**
- [ ] Partner cannot pause/cancel other partner's subscriptions
- [ ] User cannot pause/cancel other user's subscriptions
- [ ] Invalid status transitions return 400 error

---

## 📊 Success Metrics

- [ ] All 6 Partner API endpoints deployed and functional
- [ ] All 3 QuantLeap user endpoints deployed and functional
- [ ] Strategy executor correctly filters PAUSED subscriptions
- [ ] Frontend UI shows all subscription statuses correctly
- [ ] < 500ms response time for subscription operations
- [ ] Zero unauthorized access to other users' subscriptions
- [ ] 100% status transition validation accuracy

---

## 🚀 Deployment Plan

### **Development Environment**
1. Deploy backend Lambda updates
2. Deploy CDK stack updates (API Gateway routes)
3. Test all endpoints with Postman
4. Deploy frontend updates
5. End-to-end testing

### **Staging Environment**
1. Repeat dev deployment steps
2. Load testing (100 concurrent subscription operations)
3. Partner integration testing with test API keys

### **Production Environment**
1. Database backup before deployment
2. Deploy backend Lambda (blue-green deployment)
3. Deploy CDK stack (incremental update)
4. Monitor CloudWatch for errors
5. Deploy frontend (gradual rollout)
6. Partner communication (API updates available)

---

## 📞 Support Plan

### **Partner Communication**
- Email all partners 1 week before deployment
- Provide updated OpenAPI spec
- Offer integration support calls
- Create migration guide for existing integrations

### **User Communication**
- In-app notification about new pause/resume features
- Help center article with screenshots
- Email to active subscribers

---

This implementation plan provides complete subscription management for both QuantLeap users and Partner users with pause/resume/cancel functionality!
