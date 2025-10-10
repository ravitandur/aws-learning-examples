"""
Subscription Manager Lambda
Handles user subscriptions to marketplace templates and partner API subscriptions

Routes:
- User: Subscribe/manage subscriptions to marketplace templates
- Partner API: External broker subscription creation with auto-linking
"""

import json
import boto3
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple
import os
import sys
from decimal import Decimal

# Add paths for imports
sys.path.append('/opt/python')
sys.path.append('/var/task')
sys.path.append('/var/task/option_baskets')

# Import shared logger
from shared_utils.logger import setup_logger, log_lambda_event, log_user_action
logger = setup_logger(__name__)

# Import partner auth middleware
from partner_auth_middleware import validate_partner_request


# Custom JSON encoder to handle Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Subscription Manager Handler
    Handles both user subscriptions and partner API subscriptions
    """

    log_lambda_event(logger, event, context)

    try:
        # Get HTTP method and path
        http_method = event['httpMethod']
        path = event.get('path', '')
        path_parameters = event.get('pathParameters') or {}

        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb', region_name=os.environ['REGION'])
        trading_configurations_table = dynamodb.Table(os.environ['TRADING_CONFIGURATIONS_TABLE'])
        broker_accounts_table = dynamodb.Table(os.environ['BROKER_ACCOUNTS_TABLE'])

        # Route based on path
        if '/partner/marketplace/subscribe' in path:
            # Partner API subscription (requires partner authentication)
            return handle_partner_api_subscription(event, trading_configurations_table, broker_accounts_table)
        elif '/partner/subscriptions' in path:
            # Partner API subscription management (list, get, cancel, pause, resume)
            return handle_partner_subscription_management(event, trading_configurations_table)
        elif '/marketplace/subscribe' in path:
            # User direct subscription
            return handle_user_subscription(event, trading_configurations_table, broker_accounts_table)
        elif '/user/subscriptions' in path:
            # User subscription management
            return handle_user_subscription_management(event, trading_configurations_table)
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Not found'})
            }

    except Exception as e:
        logger.error("Unexpected error in subscription handler", extra={"error": str(e)})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }


def handle_partner_api_subscription(event, trading_table, broker_table):
    """
    Partner API subscription endpoint
    External brokers (Zebu, etc.) subscribe their users to marketplace templates
    """

    # Validate partner authentication
    validation = validate_partner_request(event, 'marketplace:subscribe')
    if not validation['authenticated']:
        return {
            'statusCode': validation['status_code'],
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': validation['error']})
        }

    partner_context = validation['partner_context']

    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})

        # Extract subscription parameters
        template_id = body.get('template_id', '').strip()
        user_email = body.get('user_email', '').strip()
        broker_client_id = body.get('broker_client_id', '').strip()
        auto_link_broker = body.get('auto_link_broker', True)
        lot_multiplier = float(body.get('lot_multiplier', 1.0))
        metadata = body.get('metadata', {})

        # Validate required fields
        if not template_id or not user_email or not broker_client_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing required fields',
                    'message': 'template_id, user_email, and broker_client_id are required'
                })
            }

        # Fetch template to verify it exists and is PUBLIC
        template = get_template_by_id(template_id, trading_table)
        if not template:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Template not found'})
            }

        if template.get('marketplace_config', {}).get('visibility') != 'PUBLIC':
            return {
                'statusCode': 403,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Template is not public'})
            }

        # Get or create user account
        user_id, is_new_user = get_or_create_user_for_partner(
            user_email,
            partner_context,
            broker_table
        )

        # Create subscription
        subscription = create_subscription(
            user_id=user_id,
            template_id=template_id,
            template_owner_id=template.get('user_id'),
            partner_context=partner_context,
            pricing=template.get('marketplace_config', {}).get('pricing', {}),
            trading_table=trading_table
        )

        # Auto-create broker allocation if requested
        broker_allocation = None
        if auto_link_broker:
            broker_allocation = create_auto_broker_allocation(
                user_id=user_id,
                template_id=template_id,
                broker_client_id=broker_client_id,
                broker_id=partner_context.get('broker_id'),
                lot_multiplier=lot_multiplier,
                trading_table=trading_table
            )

        # Increment template subscriber count
        increment_template_subscriber_count(template_id, template.get('user_id'), trading_table)

        # Update partner metrics
        update_partner_metrics(partner_context['api_key_id'], trading_table)

        logger.info("Partner API subscription created", extra={
            "partner_id": partner_context['partner_id'],
            "user_id": user_id,
            "template_id": template_id,
            "subscription_id": subscription['subscription_id']
        })

        # Calculate revenue share
        pricing = template.get('marketplace_config', {}).get('pricing', {})
        monthly_fee = pricing.get('monthly_fee', 0)
        revenue_share = partner_context.get('revenue_share', {})
        partner_commission = monthly_fee * revenue_share.get('partner_percentage', 30) / 100
        platform_fee = monthly_fee * revenue_share.get('platform_percentage', 70) / 100

        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Subscription created successfully',
                'subscription_id': subscription['subscription_id'],
                'user_id': user_id,
                'is_new_user': is_new_user,
                'template_id': template_id,
                'status': subscription['status'],
                'broker_allocation': {
                    'allocation_id': broker_allocation['allocation_id'] if broker_allocation else None,
                    'client_id': broker_client_id,
                    'broker_id': partner_context.get('broker_id'),
                    'lot_multiplier': lot_multiplier,
                    'status': 'ACTIVE' if broker_allocation else None
                } if broker_allocation else None,
                'next_billing_date': subscription.get('next_billing_date'),
                'revenue_share': {
                    'partner_commission': float(partner_commission),
                    'platform_fee': float(platform_fee),
                    'currency': 'INR'
                }
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        logger.error("Partner API subscription failed", extra={
            "error": str(e),
            "partner_id": partner_context.get('partner_id')
        })
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to create subscription',
                'message': str(e)
            })
        }


def handle_partner_subscription_management(event, trading_table):
    """
    Partner API subscription management
    Handles list, get, cancel, pause, resume for partner subscriptions
    """

    # Validate partner authentication
    validation = validate_partner_request(event, 'marketplace:read')
    if not validation['authenticated']:
        return {
            'statusCode': validation['status_code'],
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': validation['error']})
        }

    partner_context = validation['partner_context']
    partner_id = partner_context['partner_id']

    http_method = event['httpMethod']
    path = event.get('path', '')
    path_parameters = event.get('pathParameters') or {}
    subscription_id = path_parameters.get('subscription_id')
    query_params = event.get('queryStringParameters') or {}

    try:
        if http_method == 'GET' and not subscription_id:
            # GET /partner/subscriptions - List all partner subscriptions
            return list_partner_subscriptions(partner_id, query_params, trading_table)
        elif http_method == 'GET' and subscription_id:
            # GET /partner/subscriptions/{id} - Get subscription details
            return get_partner_subscription_details(partner_id, subscription_id, trading_table)
        elif http_method == 'PUT' and subscription_id and path.endswith('/pause'):
            # PUT /partner/subscriptions/{id}/pause - Pause subscription
            return pause_partner_subscription(partner_id, subscription_id, trading_table)
        elif http_method == 'PUT' and subscription_id and path.endswith('/resume'):
            # PUT /partner/subscriptions/{id}/resume - Resume subscription
            return resume_partner_subscription(partner_id, subscription_id, trading_table)
        elif http_method == 'DELETE' and subscription_id:
            # DELETE /partner/subscriptions/{id} - Cancel subscription
            return cancel_partner_subscription(partner_id, subscription_id, trading_table)
        else:
            return {
                'statusCode': 405,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Method not allowed'})
            }

    except Exception as e:
        logger.error("Partner subscription management failed", extra={
            "error": str(e),
            "partner_id": partner_id
        })
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to manage subscription',
                'message': str(e)
            })
        }


def handle_user_subscription(event, trading_table, broker_table):
    """
    User direct subscription (from your platform's frontend)
    """

    # Get user ID from Cognito authorizer
    user_id = None
    if 'requestContext' in event and 'authorizer' in event['requestContext']:
        claims = event['requestContext']['authorizer'].get('claims', {})
        user_id = claims.get('sub') or claims.get('cognito:username')

    if not user_id:
        return {
            'statusCode': 401,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Unauthorized',
                'message': 'User ID not found in request context'
            })
        }

    try:
        path_parameters = event.get('pathParameters') or {}
        template_id = path_parameters.get('template_id')

        if not template_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'template_id is required'})
            }

        # Fetch template
        template = get_template_by_id(template_id, trading_table)
        if not template:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Template not found'})
            }

        if template.get('marketplace_config', {}).get('visibility') != 'PUBLIC':
            return {
                'statusCode': 403,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Template is not public'})
            }

        # Check if user already subscribed
        existing_subscription = check_existing_subscription(user_id, template_id, trading_table)
        if existing_subscription:
            return {
                'statusCode': 409,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Already subscribed',
                    'message': 'You are already subscribed to this template',
                    'subscription_id': existing_subscription.get('subscription_id')
                })
            }

        # Create subscription (no partner attribution for direct subscriptions)
        subscription = create_subscription(
            user_id=user_id,
            template_id=template_id,
            template_owner_id=template.get('user_id'),
            partner_context=None,
            pricing=template.get('marketplace_config', {}).get('pricing', {}),
            trading_table=trading_table
        )

        # Increment template subscriber count
        increment_template_subscriber_count(template_id, template.get('user_id'), trading_table)

        logger.info("User subscription created", extra={
            "user_id": user_id,
            "template_id": template_id,
            "subscription_id": subscription['subscription_id']
        })

        log_user_action(logger, user_id, "template_subscribed", {
            "template_id": template_id,
            "subscription_id": subscription['subscription_id']
        })

        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Subscription created successfully',
                'subscription': subscription,
                'next_step': 'Create broker allocation to start execution'
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        logger.error("User subscription failed", extra={
            "error": str(e),
            "user_id": user_id
        })
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to create subscription',
                'message': str(e)
            })
        }


def handle_user_subscription_management(event, trading_table):
    """
    Manage user subscriptions (list, update, cancel)
    """

    # Get user ID from Cognito authorizer
    user_id = None
    if 'requestContext' in event and 'authorizer' in event['requestContext']:
        claims = event['requestContext']['authorizer'].get('claims', {})
        user_id = claims.get('sub') or claims.get('cognito:username')

    if not user_id:
        return {
            'statusCode': 401,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Unauthorized'})
        }

    http_method = event['httpMethod']
    path = event.get('path', '')
    path_parameters = event.get('pathParameters') or {}
    subscription_id = path_parameters.get('subscription_id')

    try:
        if http_method == 'GET' and not subscription_id:
            # List user's subscriptions
            return list_user_subscriptions(user_id, trading_table)
        elif http_method == 'GET' and subscription_id:
            # Get specific subscription details
            return get_subscription_details(user_id, subscription_id, trading_table)
        elif http_method == 'PUT' and subscription_id and path.endswith('/pause'):
            # Pause subscription
            return pause_subscription(user_id, subscription_id, trading_table)
        elif http_method == 'PUT' and subscription_id and path.endswith('/resume'):
            # Resume subscription
            return resume_subscription(user_id, subscription_id, trading_table)
        elif http_method == 'PUT' and subscription_id:
            # Update subscription (e.g., change lot multiplier)
            return update_subscription(user_id, subscription_id, event, trading_table)
        elif http_method == 'DELETE' and subscription_id:
            # Cancel subscription
            return cancel_subscription(user_id, subscription_id, trading_table)
        else:
            return {
                'statusCode': 405,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Method not allowed'})
            }

    except Exception as e:
        logger.error("Subscription management failed", extra={
            "error": str(e),
            "user_id": user_id
        })
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to manage subscription',
                'message': str(e)
            })
        }


# Helper Functions

def get_template_by_id(template_id: str, table) -> Optional[Dict]:
    """Fetch marketplace template by basket_id"""

    try:
        # Scan for template (can be optimized with additional GSI if needed)
        response = table.scan(
            FilterExpression='basket_id = :basket_id AND attribute_exists(marketplace_config)',
            ExpressionAttributeValues={
                ':basket_id': template_id
            },
            Limit=1
        )

        items = response.get('Items', [])
        return items[0] if items else None

    except Exception as e:
        logger.error("Failed to fetch template", extra={"error": str(e), "template_id": template_id})
        return None


def get_or_create_user_for_partner(user_email: str, partner_context: Dict, broker_table) -> Tuple[str, bool]:
    """
    Get existing user by email or create new user account
    Returns (user_id, is_new_user)
    """

    try:
        # Query user_profiles table by email (would need GSI on email)
        # For now, create new user with email as identifier
        # In production, integrate with Cognito user pool

        # Check if user exists (simplified - use Cognito in production)
        user_id = f"partner-user-{user_email.replace('@', '-at-').replace('.', '-')}"
        is_new_user = True

        # In production, you would:
        # 1. Check Cognito user pool for email
        # 2. Create Cognito user if doesn't exist
        # 3. Link to broker account

        logger.info("User resolved for partner", extra={
            "user_id": user_id,
            "user_email": user_email,
            "partner_id": partner_context.get('partner_id'),
            "is_new_user": is_new_user
        })

        return user_id, is_new_user

    except Exception as e:
        logger.error("Failed to get/create user", extra={"error": str(e), "user_email": user_email})
        raise


def create_subscription(
    user_id: str,
    template_id: str,
    template_owner_id: str,
    partner_context: Optional[Dict],
    pricing: Dict,
    trading_table
) -> Dict:
    """Create marketplace subscription entity"""

    try:
        subscription_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Determine subscription status based on pricing
        pricing_type = pricing.get('type', 'FREE')
        if pricing_type == 'FREE':
            status = 'ACTIVE'
            trial_ends_at = None
            next_billing_date = None
        else:
            # Paid subscription starts with trial
            status = 'TRIAL'
            trial_ends_at = (now + timedelta(days=pricing.get('trial_days', 7))).isoformat()
            next_billing_date = (now + timedelta(days=30)).isoformat()

        # Create subscription_status_date for GSI4 (UserSubscriptions)
        subscription_status_date = f"{status}#{now.strftime('%Y-%m-%d')}"

        subscription_item = {
            'user_id': user_id,
            'sort_key': f'SUBSCRIPTION#{subscription_id}',
            'entity_type': 'MARKETPLACE_SUBSCRIPTION',

            'subscription_id': subscription_id,
            'template_basket_id': template_id,
            'template_owner_id': template_owner_id,

            # For GSI4: UserSubscriptions
            'subscription_status_date': subscription_status_date,

            # Partner attribution (if applicable)
            'partner_api_key_id': partner_context.get('api_key_id') if partner_context else None,
            'partner_id': partner_context.get('partner_id') if partner_context else None,
            'partner_commission_eligible': True if partner_context else False,

            # Subscription details
            'status': status,
            'subscription_date': now.isoformat(),
            'trial_ends_at': trial_ends_at,
            'next_billing_date': next_billing_date,

            'pricing': {
                'type': pricing_type,
                'monthly_fee': pricing.get('monthly_fee', 0),
                'billing_cycle': 'MONTHLY'
            },

            # Performance tracking (initialize)
            'performance_tracking': {
                'total_pnl': Decimal('0'),
                'roi_percentage': Decimal('0'),
                'trades_executed': 0,
                'last_execution': None
            },

            # Revenue share tracking (if partner)
            'revenue_share_tracking': {
                'total_fees_paid': Decimal('0'),
                'platform_share': Decimal('0'),
                'partner_share': Decimal('0'),
                'last_settlement_date': None
            } if partner_context else None,

            'created_at': now.isoformat(),
            'updated_at': now.isoformat()
        }

        # Store subscription
        trading_table.put_item(
            Item=subscription_item,
            ConditionExpression='attribute_not_exists(user_id) AND attribute_not_exists(sort_key)'
        )

        logger.info("Subscription created", extra={
            "user_id": user_id,
            "subscription_id": subscription_id,
            "template_id": template_id
        })

        return subscription_item

    except Exception as e:
        logger.error("Failed to create subscription", extra={"error": str(e), "user_id": user_id})
        raise


def create_auto_broker_allocation(
    user_id: str,
    template_id: str,
    broker_client_id: str,
    broker_id: str,
    lot_multiplier: float,
    trading_table
) -> Optional[Dict]:
    """
    Auto-create broker allocation for subscribed basket
    This enables execution with user's broker
    """

    try:
        allocation_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # Create broker allocation entity
        # IMPORTANT: basket_id points to ADMIN's basket (template_id)
        allocation_item = {
            'user_id': user_id,
            'sort_key': f'BROKER_ALLOCATION#{template_id}#{allocation_id}',
            'entity_type': 'BROKER_ALLOCATION',

            'allocation_id': allocation_id,
            'basket_id': template_id,  # Points to admin's template basket!

            # User's broker configuration
            'client_id': broker_client_id,
            'broker_id': broker_id,
            'lot_multiplier': Decimal(str(lot_multiplier)),
            'priority': 1,
            'max_lots_per_order': 100,
            'risk_limit_per_trade': Decimal('10000'),

            # For GSI1: AllocationsByBasket
            'entity_type_priority': f'BROKER_ALLOCATION#001',

            'created_at': now,
            'updated_at': now
        }

        trading_table.put_item(Item=allocation_item)

        logger.info("Auto broker allocation created", extra={
            "user_id": user_id,
            "template_id": template_id,
            "allocation_id": allocation_id,
            "broker_id": broker_id
        })

        return allocation_item

    except Exception as e:
        logger.error("Failed to create auto broker allocation", extra={
            "error": str(e),
            "user_id": user_id,
            "template_id": template_id
        })
        # Don't fail subscription creation if allocation fails
        return None


def check_existing_subscription(user_id: str, template_id: str, table) -> Optional[Dict]:
    """Check if user already has active subscription to template"""

    try:
        # Query user's subscriptions
        response = table.query(
            KeyConditionExpression='user_id = :user_id AND begins_with(sort_key, :prefix)',
            FilterExpression='template_basket_id = :template_id AND #status IN (:active, :trial)',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':user_id': user_id,
                ':prefix': 'SUBSCRIPTION#',
                ':template_id': template_id,
                ':active': 'ACTIVE',
                ':trial': 'TRIAL'
            }
        )

        items = response.get('Items', [])
        return items[0] if items else None

    except Exception as e:
        logger.error("Failed to check existing subscription", extra={
            "error": str(e),
            "user_id": user_id,
            "template_id": template_id
        })
        return None


def increment_template_subscriber_count(template_id: str, template_owner_id: str, table):
    """Increment subscriber_count on template basket"""

    try:
        table.update_item(
            Key={
                'user_id': template_owner_id,
                'sort_key': f'BASKET#{template_id}'
            },
            UpdateExpression='ADD subscriber_count :inc',
            ExpressionAttributeValues={':inc': 1}
        )

        logger.debug("Template subscriber count incremented", extra={
            "template_id": template_id
        })

    except Exception as e:
        logger.warning("Failed to increment subscriber count", extra={
            "error": str(e),
            "template_id": template_id
        })
        # Don't fail subscription if count update fails


def update_partner_metrics(api_key_id: str, table):
    """Update partner API key metrics"""

    try:
        table.update_item(
            Key={
                'user_id': 'PARTNER',
                'sort_key': f'PARTNER_API_KEY#{api_key_id}'
            },
            UpdateExpression='ADD metrics.total_subscriptions :inc, metrics.active_users :inc',
            ExpressionAttributeValues={':inc': 1}
        )

        logger.debug("Partner metrics updated", extra={"api_key_id": api_key_id})

    except Exception as e:
        logger.warning("Failed to update partner metrics", extra={
            "error": str(e),
            "api_key_id": api_key_id
        })


def list_user_subscriptions(user_id: str, table):
    """List all user's subscriptions"""

    try:
        # Query GSI4: UserSubscriptions
        response = table.query(
            IndexName='UserSubscriptions',
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id}
        )

        subscriptions = response.get('Items', [])

        # Enrich with template information
        for sub in subscriptions:
            template_id = sub.get('template_basket_id')
            if template_id:
                template = get_template_by_id(template_id, table)
                if template:
                    sub['template_name'] = template.get('name')
                    sub['template_category'] = template.get('category')

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'subscriptions': subscriptions,
                'count': len(subscriptions)
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        logger.error("Failed to list subscriptions", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to list subscriptions',
                'message': str(e)
            })
        }


def get_subscription_details(user_id: str, subscription_id: str, table):
    """Get detailed subscription information"""

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
                'body': json.dumps({'error': 'Subscription not found'})
            }

        subscription = response['Item']

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(subscription, cls=DecimalEncoder)
        }

    except Exception as e:
        logger.error("Failed to get subscription details", extra={
            "error": str(e),
            "user_id": user_id,
            "subscription_id": subscription_id
        })
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to get subscription',
                'message': str(e)
            })
        }


def update_subscription(user_id: str, subscription_id: str, event, table):
    """Update subscription (placeholder for future features)"""

    # Future: Allow updating lot_multiplier via broker allocation update
    return {
        'statusCode': 501,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': 'Not implemented',
            'message': 'Update subscription via broker allocation endpoint'
        })
    }


def cancel_subscription(user_id: str, subscription_id: str, table):
    """Cancel user subscription"""

    try:
        now = datetime.now(timezone.utc).isoformat()

        # Update subscription status to CANCELLED
        response = table.update_item(
            Key={
                'user_id': user_id,
                'sort_key': f'SUBSCRIPTION#{subscription_id}'
            },
            UpdateExpression='SET #status = :status, cancelled_at = :cancelled_at, subscription_status_date = :status_date',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'CANCELLED',
                ':cancelled_at': now,
                ':status_date': f'CANCELLED#{datetime.now(timezone.utc).strftime("%Y-%m-%d")}'
            },
            ReturnValues='ALL_NEW'
        )

        subscription = response['Attributes']
        template_id = subscription.get('template_basket_id')
        template_owner_id = subscription.get('template_owner_id')

        # Decrement template subscriber count
        if template_id and template_owner_id:
            table.update_item(
                Key={
                    'user_id': template_owner_id,
                    'sort_key': f'BASKET#{template_id}'
                },
                UpdateExpression='ADD subscriber_count :dec',
                ExpressionAttributeValues={':dec': -1}
            )

        logger.info("Subscription cancelled", extra={
            "user_id": user_id,
            "subscription_id": subscription_id
        })

        log_user_action(logger, user_id, "subscription_cancelled", {
            "subscription_id": subscription_id,
            "template_id": template_id
        })

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Subscription cancelled successfully',
                'subscription_id': subscription_id,
                'status': 'CANCELLED',
                'cancelled_at': now
            })
        }

    except Exception as e:
        logger.error("Failed to cancel subscription", extra={
            "error": str(e),
            "user_id": user_id,
            "subscription_id": subscription_id
        })
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to cancel subscription',
                'message': str(e)
            })
        }


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
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Subscription not found'})
            }

        subscription = response['Item']
        current_status = subscription.get('status')

        # Validate status transition
        if current_status != 'ACTIVE':
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
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
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to pause subscription',
                'message': str(e)
            })
        }


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
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Subscription not found'})
            }

        subscription = response['Item']
        current_status = subscription.get('status')

        # Validate status transition
        if current_status != 'PAUSED':
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
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
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to resume subscription',
                'message': str(e)
            })
        }


# Partner API Subscription Management Functions

def list_partner_subscriptions(partner_id: str, query_params: Dict, table):
    """List all subscriptions created by this partner"""
    try:
        user_email = query_params.get('user_email')

        # Query subscriptions by partner_id
        # Note: This requires a GSI on partner_id
        # For now, we'll scan with filter (optimize with GSI in production)
        if user_email:
            # Filter by specific user
            response = table.query(
                KeyConditionExpression='user_id = :user_id AND begins_with(sort_key, :prefix)',
                FilterExpression='partner_id = :partner_id',
                ExpressionAttributeValues={
                    ':user_id': user_email,
                    ':prefix': 'SUBSCRIPTION#',
                    ':partner_id': partner_id
                }
            )
        else:
            # Get all partner subscriptions (scan with filter - optimize with GSI)
            response = table.scan(
                FilterExpression='partner_id = :partner_id AND begins_with(sort_key, :prefix)',
                ExpressionAttributeValues={
                    ':partner_id': partner_id,
                    ':prefix': 'SUBSCRIPTION#'
                }
            )

        subscriptions = response.get('Items', [])

        logger.info("Partner subscriptions listed", extra={
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
                'partner_id': partner_id,
                'filtered_by': user_email if user_email else None
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        logger.error("Failed to list partner subscriptions", extra={
            "error": str(e),
            "partner_id": partner_id
        })
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to list subscriptions',
                'message': str(e)
            })
        }


def get_partner_subscription_details(partner_id: str, subscription_id: str, table):
    """Get subscription details with partner ownership validation"""
    try:
        # Query by subscription_id to find the subscription
        # Note: Requires GSI on subscription_id (optimize in production)
        response = table.scan(
            FilterExpression='subscription_id = :sub_id',
            ExpressionAttributeValues={':sub_id': subscription_id},
            Limit=1
        )

        if not response.get('Items'):
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Subscription not found'})
            }

        subscription = response['Items'][0]
        subscription_partner_id = subscription.get('partner_id')

        # Validate partner ownership
        if subscription_partner_id != partner_id:
            return {
                'statusCode': 403,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Forbidden',
                    'message': 'This subscription does not belong to your partner account'
                })
            }

        logger.info("Partner subscription details retrieved", extra={
            "partner_id": partner_id,
            "subscription_id": subscription_id
        })

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'subscription': subscription
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        logger.error("Failed to get partner subscription details", extra={
            "error": str(e),
            "partner_id": partner_id,
            "subscription_id": subscription_id
        })
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to get subscription details',
                'message': str(e)
            })
        }


def pause_partner_subscription(partner_id: str, subscription_id: str, table):
    """Pause subscription on behalf of partner user"""
    try:
        # Get subscription and validate partner ownership
        response = table.scan(
            FilterExpression='subscription_id = :sub_id',
            ExpressionAttributeValues={':sub_id': subscription_id},
            Limit=1
        )

        if not response.get('Items'):
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Subscription not found'})
            }

        subscription = response['Items'][0]
        subscription_partner_id = subscription.get('partner_id')

        # Validate partner ownership
        if subscription_partner_id != partner_id:
            return {
                'statusCode': 403,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Forbidden',
                    'message': 'This subscription does not belong to your partner account'
                })
            }

        user_id = subscription.get('user_id')

        # Use existing pause_subscription function
        return pause_subscription(user_id, subscription_id, table)

    except Exception as e:
        logger.error("Failed to pause partner subscription", extra={
            "error": str(e),
            "partner_id": partner_id,
            "subscription_id": subscription_id
        })
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to pause subscription',
                'message': str(e)
            })
        }


def resume_partner_subscription(partner_id: str, subscription_id: str, table):
    """Resume subscription on behalf of partner user"""
    try:
        # Get subscription and validate partner ownership
        response = table.scan(
            FilterExpression='subscription_id = :sub_id',
            ExpressionAttributeValues={':sub_id': subscription_id},
            Limit=1
        )

        if not response.get('Items'):
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Subscription not found'})
            }

        subscription = response['Items'][0]
        subscription_partner_id = subscription.get('partner_id')

        # Validate partner ownership
        if subscription_partner_id != partner_id:
            return {
                'statusCode': 403,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Forbidden',
                    'message': 'This subscription does not belong to your partner account'
                })
            }

        user_id = subscription.get('user_id')

        # Use existing resume_subscription function
        return resume_subscription(user_id, subscription_id, table)

    except Exception as e:
        logger.error("Failed to resume partner subscription", extra={
            "error": str(e),
            "partner_id": partner_id,
            "subscription_id": subscription_id
        })
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to resume subscription',
                'message': str(e)
            })
        }


def cancel_partner_subscription(partner_id: str, subscription_id: str, table):
    """Cancel subscription on behalf of partner user"""
    try:
        # Get subscription and validate partner ownership
        response = table.scan(
            FilterExpression='subscription_id = :sub_id',
            ExpressionAttributeValues={':sub_id': subscription_id},
            Limit=1
        )

        if not response.get('Items'):
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Subscription not found'})
            }

        subscription = response['Items'][0]
        subscription_partner_id = subscription.get('partner_id')

        # Validate partner ownership
        if subscription_partner_id != partner_id:
            return {
                'statusCode': 403,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
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
            "partner_id": partner_id,
            "subscription_id": subscription_id
        })
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to cancel subscription',
                'message': str(e)
            })
        }
