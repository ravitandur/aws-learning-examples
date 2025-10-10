"""
Marketplace Manager Lambda
Handles marketplace template creation, updates, and browsing

Routes:
- Admin: Create/update marketplace config for baskets
- Public: Browse marketplace templates
- Partner API: External broker marketplace integration
"""

import json
import boto3
from datetime import datetime, timezone
from typing import Dict, Any, List
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


# Custom JSON encoder to handle Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Marketplace Manager Handler
    Handles both admin template management and public marketplace browsing
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

        # Route based on path and method
        if '/admin/marketplace' in path:
            # Admin-only routes (require authentication)
            return handle_admin_marketplace_request(event, trading_configurations_table)
        elif '/marketplace/templates' in path:
            # Public/Partner marketplace browsing
            return handle_public_marketplace_request(event, trading_configurations_table)
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
        logger.error("Unexpected error in marketplace handler", extra={"error": str(e)})
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


def handle_admin_marketplace_request(event, table):
    """Handle admin-only marketplace template management"""

    # Verify admin permissions
    user_id, is_admin = verify_admin_access(event)
    if not is_admin:
        return {
            'statusCode': 403,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Forbidden',
                'message': 'Admin access required'
            })
        }

    http_method = event['httpMethod']
    path_parameters = event.get('pathParameters') or {}
    basket_id = path_parameters.get('basket_id')

    # Route admin operations
    if http_method == 'POST' and basket_id:
        # Enable marketplace for basket
        return enable_marketplace_for_basket(user_id, basket_id, event, table)
    elif http_method == 'PUT' and basket_id:
        # Update marketplace configuration
        return update_marketplace_config(user_id, basket_id, event, table)
    elif http_method == 'DELETE' and basket_id:
        # Disable marketplace for basket
        return disable_marketplace_for_basket(user_id, basket_id, table)
    elif http_method == 'GET':
        # List admin's marketplace templates
        return list_admin_templates(user_id, table)
    else:
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Method not allowed'})
        }


def handle_public_marketplace_request(event, table):
    """Handle public marketplace browsing (and partner API access)"""

    http_method = event['httpMethod']
    path_parameters = event.get('pathParameters') or {}
    query_params = event.get('queryStringParameters') or {}
    template_id = path_parameters.get('template_id')

    if http_method == 'GET' and not template_id:
        # Browse marketplace templates
        return browse_marketplace_templates(query_params, table)
    elif http_method == 'GET' and template_id:
        # Get template details
        return get_template_details(template_id, table)
    else:
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Method not allowed'})
        }


def verify_admin_access(event) -> tuple:
    """Verify user is authenticated and belongs to Admins group"""

    if 'requestContext' not in event or 'authorizer' not in event['requestContext']:
        return None, False

    claims = event['requestContext']['authorizer'].get('claims', {})
    user_id = claims.get('sub') or claims.get('cognito:username')

    if not user_id:
        return None, False

    # Check Cognito groups
    groups = claims.get('cognito:groups', '')
    if isinstance(groups, str):
        groups = groups.split(',')

    is_admin = 'Admins' in groups

    return user_id, is_admin


def enable_marketplace_for_basket(admin_user_id, basket_id, event, table):
    """
    Enable marketplace for an admin's basket
    Adds marketplace_config to existing basket
    """

    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})

        # Verify basket exists and is owned by admin
        basket_response = table.get_item(
            Key={
                'user_id': admin_user_id,
                'sort_key': f'BASKET#{basket_id}'
            }
        )

        if 'Item' not in basket_response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Basket not found'})
            }

        basket = basket_response['Item']

        # Extract marketplace configuration
        marketplace_config = {
            'is_template': True,
            'visibility': body.get('visibility', 'PUBLIC').upper(),
            'pricing': body.get('pricing', {
                'type': 'FREE',
                'monthly_fee': 0
            }),
            'difficulty_level': body.get('difficulty_level', 'INTERMEDIATE').upper(),
            'tags': body.get('tags', []),
            'performance_published': body.get('performance_published', True)
        }

        # Validate visibility
        if marketplace_config['visibility'] not in ['PUBLIC', 'PRIVATE']:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Invalid visibility',
                    'message': 'Must be PUBLIC or PRIVATE'
                })
            }

        # Validate pricing type
        if marketplace_config['pricing']['type'] not in ['FREE', 'PAID', 'FREEMIUM']:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Invalid pricing type',
                    'message': 'Must be FREE, PAID, or FREEMIUM'
                })
            }

        # Create marketplace category for GSI3
        category = basket.get('category', 'GENERAL').upper()
        marketplace_category = f"MARKETPLACE#{category}"

        # Initialize subscriber count
        subscriber_count = Decimal('0')

        # Update basket with marketplace configuration
        now = datetime.now(timezone.utc).isoformat()

        response = table.update_item(
            Key={
                'user_id': admin_user_id,
                'sort_key': f'BASKET#{basket_id}'
            },
            UpdateExpression='''
                SET marketplace_config = :config,
                    marketplace_category = :marketplace_category,
                    subscriber_count = :subscriber_count,
                    published_at = :published_at,
                    updated_at = :updated_at
            ''',
            ExpressionAttributeValues={
                ':config': marketplace_config,
                ':marketplace_category': marketplace_category,
                ':subscriber_count': subscriber_count,
                ':published_at': now,
                ':updated_at': now
            },
            ReturnValues='ALL_NEW'
        )

        updated_basket = response['Attributes']

        logger.info("Marketplace enabled for basket", extra={
            "admin_user_id": admin_user_id,
            "basket_id": basket_id,
            "marketplace_category": marketplace_category
        })

        log_user_action(logger, admin_user_id, "marketplace_template_created", {
            "basket_id": basket_id,
            "category": category
        })

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Marketplace enabled successfully',
                'basket': updated_basket
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        logger.error("Failed to enable marketplace", extra={
            "error": str(e),
            "admin_user_id": admin_user_id,
            "basket_id": basket_id
        })
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to enable marketplace',
                'message': str(e)
            })
        }


def update_marketplace_config(admin_user_id, basket_id, event, table):
    """Update marketplace configuration (preserves basket/strategy config)"""

    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})

        # Build update expression for allowed marketplace fields
        update_parts = []
        expr_values = {}

        if 'visibility' in body:
            update_parts.append('marketplace_config.visibility = :visibility')
            expr_values[':visibility'] = body['visibility'].upper()

        if 'pricing' in body:
            update_parts.append('marketplace_config.pricing = :pricing')
            expr_values[':pricing'] = body['pricing']

        if 'tags' in body:
            update_parts.append('marketplace_config.tags = :tags')
            expr_values[':tags'] = body['tags']

        if 'performance_published' in body:
            update_parts.append('marketplace_config.performance_published = :perf_pub')
            expr_values[':perf_pub'] = body['performance_published']

        if not update_parts:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'No updates provided'})
            }

        update_parts.append('updated_at = :updated_at')
        expr_values[':updated_at'] = datetime.now(timezone.utc).isoformat()

        update_expr = 'SET ' + ', '.join(update_parts)

        response = table.update_item(
            Key={
                'user_id': admin_user_id,
                'sort_key': f'BASKET#{basket_id}'
            },
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
            ConditionExpression='attribute_exists(marketplace_config)',
            ReturnValues='ALL_NEW'
        )

        updated_basket = response['Attributes']

        logger.info("Marketplace config updated", extra={
            "admin_user_id": admin_user_id,
            "basket_id": basket_id
        })

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Marketplace configuration updated',
                'basket': updated_basket
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        logger.error("Failed to update marketplace config", extra={
            "error": str(e),
            "admin_user_id": admin_user_id,
            "basket_id": basket_id
        })
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to update marketplace config',
                'message': str(e)
            })
        }


def disable_marketplace_for_basket(admin_user_id, basket_id, table):
    """Disable marketplace (set visibility to PRIVATE)"""

    try:
        response = table.update_item(
            Key={
                'user_id': admin_user_id,
                'sort_key': f'BASKET#{basket_id}'
            },
            UpdateExpression='SET marketplace_config.visibility = :visibility, updated_at = :updated_at',
            ExpressionAttributeValues={
                ':visibility': 'PRIVATE',
                ':updated_at': datetime.now(timezone.utc).isoformat()
            },
            ReturnValues='ALL_NEW'
        )

        logger.info("Marketplace disabled for basket", extra={
            "admin_user_id": admin_user_id,
            "basket_id": basket_id
        })

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Marketplace disabled (set to PRIVATE)',
                'basket_id': basket_id
            })
        }

    except Exception as e:
        logger.error("Failed to disable marketplace", extra={
            "error": str(e),
            "admin_user_id": admin_user_id,
            "basket_id": basket_id
        })
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to disable marketplace',
                'message': str(e)
            })
        }


def list_admin_templates(admin_user_id, table):
    """List all marketplace templates created by admin"""

    try:
        # Query admin's baskets with marketplace enabled
        response = table.query(
            KeyConditionExpression='user_id = :user_id AND begins_with(sort_key, :prefix)',
            FilterExpression='attribute_exists(marketplace_config)',
            ExpressionAttributeValues={
                ':user_id': admin_user_id,
                ':prefix': 'BASKET#'
            }
        )

        templates = response.get('Items', [])

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'templates': templates,
                'count': len(templates)
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        logger.error("Failed to list admin templates", extra={
            "error": str(e),
            "admin_user_id": admin_user_id
        })
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to list templates',
                'message': str(e)
            })
        }


def browse_marketplace_templates(query_params, table):
    """
    Browse public marketplace templates
    Supports filtering by category, difficulty, performance
    """

    try:
        # Extract query parameters
        category = query_params.get('category')
        difficulty = query_params.get('difficulty')
        min_performance = query_params.get('min_performance')
        limit = min(int(query_params.get('limit', 50)), 50)  # Max 50

        # Query GSI3: MarketplaceDiscovery
        if category:
            # Category-specific query
            marketplace_category = f"MARKETPLACE#{category.upper()}"

            response = table.query(
                IndexName='MarketplaceDiscovery',
                KeyConditionExpression='marketplace_category = :cat',
                FilterExpression='marketplace_config.visibility = :visibility',
                ExpressionAttributeValues={
                    ':cat': marketplace_category,
                    ':visibility': 'PUBLIC'
                },
                ScanIndexForward=False,  # Highest subscriber_count first
                Limit=limit
            )
        else:
            # Scan all categories (less efficient, use sparingly)
            response = table.scan(
                FilterExpression='attribute_exists(marketplace_config) AND marketplace_config.visibility = :visibility',
                ExpressionAttributeValues={
                    ':visibility': 'PUBLIC'
                },
                Limit=limit
            )

        templates = response.get('Items', [])

        # Apply additional filters
        if difficulty:
            templates = [
                t for t in templates
                if t.get('marketplace_config', {}).get('difficulty_level') == difficulty.upper()
            ]

        if min_performance:
            min_perf = float(min_performance)
            templates = [
                t for t in templates
                if t.get('performance_metrics', {}).get('total_return', 0) >= min_perf
            ]

        # Sanitize templates (remove sensitive admin data)
        sanitized_templates = []
        for template in templates:
            sanitized = {
                'template_id': template.get('basket_id'),
                'name': template.get('name'),
                'description': template.get('description'),
                'category': template.get('category'),
                'difficulty_level': template.get('marketplace_config', {}).get('difficulty_level'),
                'pricing': template.get('marketplace_config', {}).get('pricing'),
                'subscriber_count': template.get('subscriber_count', 0),
                'tags': template.get('marketplace_config', {}).get('tags', []),
                'performance_metrics': template.get('performance_metrics', {}),
                'created_at': template.get('published_at')
            }
            sanitized_templates.append(sanitized)

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'templates': sanitized_templates,
                'count': len(sanitized_templates)
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        logger.error("Failed to browse marketplace", extra={"error": str(e)})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to browse marketplace',
                'message': str(e)
            })
        }


def get_template_details(template_id, table):
    """Get detailed information about a marketplace template"""

    try:
        # We need to find the template by basket_id
        # Since we don't know the user_id (admin), we need to scan or use GSI
        # For now, scan with filter (can be optimized with additional GSI if needed)

        response = table.scan(
            FilterExpression='basket_id = :basket_id AND attribute_exists(marketplace_config) AND marketplace_config.visibility = :visibility',
            ExpressionAttributeValues={
                ':basket_id': template_id,
                ':visibility': 'PUBLIC'
            },
            Limit=1
        )

        items = response.get('Items', [])
        if not items:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Template not found'})
            }

        template = items[0]
        admin_user_id = template.get('user_id')

        # Fetch strategies for this basket
        strategies_response = table.query(
            KeyConditionExpression='user_id = :user_id AND begins_with(sort_key, :prefix)',
            FilterExpression='basket_id = :basket_id',
            ExpressionAttributeValues={
                ':user_id': admin_user_id,
                ':prefix': 'STRATEGY#',
                ':basket_id': template_id
            }
        )

        strategies = strategies_response.get('Items', [])

        # Build detailed response (sanitize sensitive data)
        response_data = {
            'template_id': template.get('basket_id'),
            'template_owner_id': admin_user_id,  # Needed for subscription
            'name': template.get('name'),
            'description': template.get('description'),
            'category': template.get('category'),
            'marketplace_config': template.get('marketplace_config'),
            'subscriber_count': template.get('subscriber_count', 0),
            'performance_metrics': template.get('performance_metrics', {}),
            'strategies': [
                {
                    'strategy_id': s.get('strategy_id'),
                    'name': s.get('name'),
                    'strategy_type': s.get('strategy_type'),
                    'underlying': s.get('underlying'),
                    'legs': s.get('legs', []),
                    'entry_time': s.get('entry_time'),
                    'exit_time': s.get('exit_time'),
                    'risk_management': s.get('risk_management')
                }
                for s in strategies
            ],
            'published_at': template.get('published_at')
        }

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_data, cls=DecimalEncoder)
        }

    except Exception as e:
        logger.error("Failed to get template details", extra={
            "error": str(e),
            "template_id": template_id
        })
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to get template details',
                'message': str(e)
            })
        }
