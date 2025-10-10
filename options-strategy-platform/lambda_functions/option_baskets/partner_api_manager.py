"""
Partner API Key Management Lambda
Handles CRUD operations for broker partner API keys (B2B2C integration)

Admin-only endpoints for creating and managing external broker partnerships
"""

import json
import boto3
import uuid
import secrets
import bcrypt
from datetime import datetime, timezone
from typing import Dict, Any
import os
import sys
from decimal import Decimal

# Add paths for imports
sys.path.append('/opt/python')
sys.path.append('/var/task')
sys.path.append('/var/task/option_baskets')

# Import shared logger
from shared_utils.logger import setup_logger, log_lambda_event, log_user_action, log_api_response
logger = setup_logger(__name__)


# Custom JSON encoder to handle Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Partner API Key Management Handler
    Admin-only operations for managing broker partner integrations
    """

    log_lambda_event(logger, event, context)

    try:
        # Get user ID and verify admin permissions
        user_id = None
        is_admin = False

        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            claims = event['requestContext']['authorizer'].get('claims', {})
            user_id = claims.get('sub') or claims.get('cognito:username')

            # Check if user belongs to Admins Cognito group
            groups = claims.get('cognito:groups', '')
            if isinstance(groups, str):
                groups = groups.split(',')
            is_admin = 'Admins' in groups

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

        if not is_admin:
            return {
                'statusCode': 403,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Forbidden',
                    'message': 'Admin access required for partner API management'
                })
            }

        # Get HTTP method and path parameters
        http_method = event['httpMethod']
        path_parameters = event.get('pathParameters') or {}
        api_key_id = path_parameters.get('api_key_id')

        logger.info("Processing partner API key request", extra={
            "admin_user_id": user_id,
            "http_method": http_method,
            "api_key_id": api_key_id
        })

        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb', region_name=os.environ['REGION'])
        trading_configurations_table = dynamodb.Table(os.environ['TRADING_CONFIGURATIONS_TABLE'])

        # Route based on HTTP method
        if http_method == 'POST':
            return handle_create_partner_api_key(event, user_id, trading_configurations_table)
        elif http_method == 'GET' and not api_key_id:
            return handle_list_partner_api_keys(event, user_id, trading_configurations_table)
        elif http_method == 'GET' and api_key_id:
            return handle_get_partner_api_key(event, user_id, api_key_id, trading_configurations_table)
        elif http_method == 'PUT' and api_key_id:
            return handle_update_partner_api_key(event, user_id, api_key_id, trading_configurations_table)
        elif http_method == 'DELETE' and api_key_id:
            return handle_delete_partner_api_key(event, user_id, api_key_id, trading_configurations_table)
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
        logger.error("Unexpected error in partner API key handler", extra={"error": str(e)})
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


def handle_create_partner_api_key(event, admin_user_id, table):
    """
    Create new partner API key for external broker
    Returns API key and secret (secret shown only once!)
    """

    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})

        # Extract partner information
        partner_id = body.get('partner_id', '').upper().strip()
        partner_name = body.get('partner_name', '').strip()
        partner_type = body.get('partner_type', 'BROKER').upper()
        broker_id = body.get('broker_id', '').upper().strip()  # Links to broker_configs.py

        # Validate required fields
        if not partner_id or not partner_name:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing required fields',
                    'message': 'partner_id and partner_name are required'
                })
            }

        # Validate partner type
        valid_types = ['BROKER', 'PLATFORM', 'AFFILIATE']
        if partner_type not in valid_types:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Invalid partner_type',
                    'message': f'Must be one of: {", ".join(valid_types)}'
                })
            }

        # Generate API key and secret
        api_key_id = str(uuid.uuid4())
        api_key = f"pk_{partner_id.lower()}_live_{secrets.token_urlsafe(32)}"
        api_secret = f"sk_{partner_id.lower()}_live_{secrets.token_urlsafe(48)}"

        # Hash the secret (never store plain text)
        api_secret_hash = bcrypt.hashpw(api_secret.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Get configuration from request body
        permissions = body.get('permissions', ['marketplace:read', 'marketplace:subscribe', 'user:link_account'])
        rate_limits = body.get('rate_limits', {
            'requests_per_minute': 100,
            'requests_per_day': 10000
        })
        branding = body.get('branding', {
            'show_platform_branding': False,
            'custom_logo_url': '',
            'custom_color_scheme': ''
        })
        revenue_share = body.get('revenue_share', {
            'platform_percentage': 70,
            'partner_percentage': 30,
            'settlement_frequency': 'MONTHLY'
        })

        # Validate revenue share percentages
        if revenue_share['platform_percentage'] + revenue_share['partner_percentage'] != 100:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Invalid revenue share',
                    'message': 'Platform and partner percentages must sum to 100'
                })
            }

        # Create timestamp
        now = datetime.now(timezone.utc).isoformat()

        # Create partner API key entity
        partner_api_key_item = {
            'user_id': 'PARTNER',  # Special partition key for partner entities
            'sort_key': f'PARTNER_API_KEY#{api_key_id}',
            'entity_type': 'PARTNER_API_KEY',

            'api_key_id': api_key_id,
            'api_key': api_key,
            'api_secret_hash': api_secret_hash,

            # Partner information
            'partner_id': partner_id,
            'partner_name': partner_name,
            'partner_type': partner_type,
            'broker_id': broker_id if partner_type == 'BROKER' else None,

            # Access control
            'status': 'ACTIVE',
            'permissions': permissions,

            # Rate limiting
            'rate_limits': rate_limits,

            # White-label config
            'branding': branding,

            # Revenue sharing
            'revenue_share': revenue_share,

            # Analytics (initialize to zero)
            'metrics': {
                'total_subscriptions': 0,
                'total_revenue_generated': Decimal('0'),
                'active_users': 0
            },

            # Audit
            'created_at': now,
            'created_by_admin': admin_user_id,
            'last_used_at': None
        }

        # Check if partner_id already exists
        existing_check = table.query(
            IndexName='MarketplaceDiscovery',  # Using existing GSI to scan
            FilterExpression='partner_id = :pid',
            ExpressionAttributeValues={':pid': partner_id}
        )

        if existing_check.get('Items'):
            return {
                'statusCode': 409,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Partner already exists',
                    'message': f'Partner ID {partner_id} is already registered'
                })
            }

        # Store in DynamoDB
        table.put_item(
            Item=partner_api_key_item,
            ConditionExpression='attribute_not_exists(user_id) AND attribute_not_exists(sort_key)'
        )

        logger.info("Partner API key created", extra={
            "admin_user_id": admin_user_id,
            "partner_id": partner_id,
            "api_key_id": api_key_id
        })

        log_user_action(logger, admin_user_id, "partner_api_key_created", {
            "partner_id": partner_id,
            "api_key_id": api_key_id
        })

        # Return response with API key and secret
        # IMPORTANT: Secret is returned ONLY this one time!
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Partner API key created successfully',
                'api_key_id': api_key_id,
                'api_key': api_key,
                'api_secret': api_secret,  # Shown only once!
                'partner_id': partner_id,
                'partner_name': partner_name,
                'status': 'ACTIVE',
                'warning': '⚠️ IMPORTANT: Store the API secret securely. It will not be shown again!',
                'created_at': now
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        logger.error("Failed to create partner API key", extra={"error": str(e), "admin_user_id": admin_user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to create partner API key',
                'message': str(e)
            })
        }


def handle_list_partner_api_keys(event, admin_user_id, table):
    """List all partner API keys (without secrets)"""

    try:
        # Query all partner API keys
        response = table.query(
            KeyConditionExpression='user_id = :user_id AND begins_with(sort_key, :prefix)',
            ExpressionAttributeValues={
                ':user_id': 'PARTNER',
                ':prefix': 'PARTNER_API_KEY#'
            }
        )

        partners = response.get('Items', [])

        # Remove sensitive data (api_secret_hash)
        for partner in partners:
            if 'api_secret_hash' in partner:
                del partner['api_secret_hash']

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'partners': partners,
                'count': len(partners)
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        logger.error("Failed to list partner API keys", extra={"error": str(e)})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to list partner API keys',
                'message': str(e)
            })
        }


def handle_get_partner_api_key(event, admin_user_id, api_key_id, table):
    """Get specific partner API key details (without secret)"""

    try:
        response = table.get_item(
            Key={
                'user_id': 'PARTNER',
                'sort_key': f'PARTNER_API_KEY#{api_key_id}'
            }
        )

        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Partner API key not found'})
            }

        partner = response['Item']

        # Remove sensitive data
        if 'api_secret_hash' in partner:
            del partner['api_secret_hash']

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(partner, cls=DecimalEncoder)
        }

    except Exception as e:
        logger.error("Failed to get partner API key", extra={"error": str(e), "api_key_id": api_key_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to get partner API key',
                'message': str(e)
            })
        }


def handle_update_partner_api_key(event, admin_user_id, api_key_id, table):
    """Update partner API key configuration (cannot change secret)"""

    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})

        # Build update expression
        update_expr_parts = []
        expr_attr_values = {}
        expr_attr_names = {}

        # Allowed updates
        if 'status' in body:
            update_expr_parts.append('#status = :status')
            expr_attr_names['#status'] = 'status'
            expr_attr_values[':status'] = body['status']

        if 'rate_limits' in body:
            update_expr_parts.append('rate_limits = :rate_limits')
            expr_attr_values[':rate_limits'] = body['rate_limits']

        if 'branding' in body:
            update_expr_parts.append('branding = :branding')
            expr_attr_values[':branding'] = body['branding']

        if 'revenue_share' in body:
            # Validate percentages
            if body['revenue_share']['platform_percentage'] + body['revenue_share']['partner_percentage'] != 100:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'Invalid revenue share',
                        'message': 'Percentages must sum to 100'
                    })
                }
            update_expr_parts.append('revenue_share = :revenue_share')
            expr_attr_values[':revenue_share'] = body['revenue_share']

        if not update_expr_parts:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'No updates provided',
                    'message': 'Provide at least one field to update'
                })
            }

        # Add updated_at timestamp
        update_expr_parts.append('updated_at = :updated_at')
        expr_attr_values[':updated_at'] = datetime.now(timezone.utc).isoformat()

        # Execute update
        update_expr = 'SET ' + ', '.join(update_expr_parts)

        response = table.update_item(
            Key={
                'user_id': 'PARTNER',
                'sort_key': f'PARTNER_API_KEY#{api_key_id}'
            },
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_attr_values,
            ExpressionAttributeNames=expr_attr_names if expr_attr_names else None,
            ReturnValues='ALL_NEW'
        )

        updated_item = response['Attributes']

        # Remove sensitive data
        if 'api_secret_hash' in updated_item:
            del updated_item['api_secret_hash']

        logger.info("Partner API key updated", extra={
            "admin_user_id": admin_user_id,
            "api_key_id": api_key_id
        })

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Partner API key updated successfully',
                'partner': updated_item
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        logger.error("Failed to update partner API key", extra={"error": str(e), "api_key_id": api_key_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to update partner API key',
                'message': str(e)
            })
        }


def handle_delete_partner_api_key(event, admin_user_id, api_key_id, table):
    """Delete (revoke) partner API key"""

    try:
        # Instead of deleting, mark as REVOKED for audit trail
        response = table.update_item(
            Key={
                'user_id': 'PARTNER',
                'sort_key': f'PARTNER_API_KEY#{api_key_id}'
            },
            UpdateExpression='SET #status = :status, revoked_at = :revoked_at, revoked_by_admin = :admin',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'REVOKED',
                ':revoked_at': datetime.now(timezone.utc).isoformat(),
                ':admin': admin_user_id
            },
            ReturnValues='ALL_NEW'
        )

        logger.info("Partner API key revoked", extra={
            "admin_user_id": admin_user_id,
            "api_key_id": api_key_id
        })

        log_user_action(logger, admin_user_id, "partner_api_key_revoked", {
            "api_key_id": api_key_id
        })

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Partner API key revoked successfully',
                'api_key_id': api_key_id,
                'status': 'REVOKED'
            })
        }

    except Exception as e:
        logger.error("Failed to revoke partner API key", extra={"error": str(e), "api_key_id": api_key_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to revoke partner API key',
                'message': str(e)
            })
        }
