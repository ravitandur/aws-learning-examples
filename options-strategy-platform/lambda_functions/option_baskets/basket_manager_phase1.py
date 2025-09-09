import json
import boto3
from botocore.exceptions import ClientError
import uuid
from datetime import datetime, timezone
from typing import Dict, Any
import os
import sys
from decimal import Decimal

# Custom JSON encoder to handle Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

# Add paths for imports
sys.path.append('/opt/python')
sys.path.append('/var/task')  # Add current directory to path
sys.path.append('/var/task/option_baskets')  # Add option_baskets directory to path

# Import shared logger directly
from shared_utils.logger import setup_logger, log_lambda_event, log_user_action, log_api_response
logger = setup_logger(__name__)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Phase 1 Lambda function to manage options baskets using hybrid architecture
    Handles CRUD operations using single table design for operational data
    """
    
    # Log the incoming Lambda event (sanitized)
    log_lambda_event(logger, event, context)
    
    try:
        # Get user ID from Cognito authorizer context
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
        
        # Get HTTP method and path parameters
        http_method = event['httpMethod']
        path_parameters = event.get('pathParameters') or {}
        basket_id = path_parameters.get('basket_id')
        
        logger.info("Processing basket request", extra={"user_id": user_id, "http_method": http_method})
        
        # Initialize AWS clients for hybrid architecture
        dynamodb = boto3.resource('dynamodb', region_name=os.environ['REGION'])
        trading_configurations_table = dynamodb.Table(os.environ['TRADING_CONFIGURATIONS_TABLE'])
        
        # Route based on HTTP method
        if http_method == 'POST':
            return handle_create_basket(event, user_id, trading_configurations_table)
        elif http_method == 'GET' and not basket_id:
            return handle_list_baskets(event, user_id, trading_configurations_table)
        elif http_method == 'GET' and basket_id:
            return handle_get_basket(event, user_id, basket_id, trading_configurations_table)
        elif http_method == 'PUT' and basket_id:
            return handle_update_basket(event, user_id, basket_id, trading_configurations_table)
        elif http_method == 'DELETE' and basket_id:
            return handle_delete_basket(event, user_id, basket_id, trading_configurations_table)
        else:
            return {
                'statusCode': 405,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Method not allowed'
                })
            }
            
    except Exception as e:
        logger.error("Unexpected error in basket handler", extra={"error": str(e)})
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


def handle_create_basket(event, user_id, table):
    """Create a new options basket using single table design"""
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Extract basket data
        basket_name = body.get('name', '').strip()
        description = body.get('description', '').strip()
        category = body.get('category', 'CONSERVATIVE').upper()
        initial_capital = Decimal(str(body.get('initial_capital', 100000)))
        
        # Validate required fields
        if not basket_name or initial_capital <= 0:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing required fields',
                    'message': 'name and initial_capital are required'
                })
            }
        
        # Validate category
        valid_categories = ['CONSERVATIVE', 'AGGRESSIVE', 'HEDGED', 'INCOME', 'MOMENTUM']
        if category not in valid_categories:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Invalid category',
                    'message': f'Category must be one of: {", ".join(valid_categories)}'
                })
            }
        
        # Generate basket ID and current timestamp
        basket_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc).isoformat()
        
        # Phase 1: Single table structure for basket
        basket_item = {
            # Single table structure
            'user_id': user_id,  # Partition key
            'sort_key': f"BASKET#{basket_id}",  # Sort key
            
            # Basic Information
            'basket_id': basket_id,
            'basket_name': basket_name,
            'description': description,
            'category': category,
            
            # Phase 1: Only user-created baskets
            'created_by_type': 'USER',  # vs ADMIN for marketplace (future)
            'creator_user_id': user_id,
            
            # Financial Configuration
            'initial_capital': initial_capital,
            'current_capital': initial_capital,  # Initially same as initial
            
            
            # Performance Metrics (initialized)
            'total_return': Decimal('0'),
            'sharpe_ratio': Decimal('0'), 
            'max_drawdown': Decimal('0'),
            'win_rate': Decimal('0'),
            
            # Status & Metadata
            'status': 'ACTIVE',
            'execution_mode': body.get('execution_mode', 'PAPER'),
            'created_at': current_time,
            'updated_at': current_time,
            'version': 1,
            
            # Single table entity type identifier
            'entity_type': 'BASKET'
        }
        
        # Store basket in single table with uniqueness constraint
        # Use conditional expression to prevent duplicate basket names per user
        try:
            # First check for existing baskets with same name
            existing_check = table.query(
                KeyConditionExpression='user_id = :user_id AND begins_with(sort_key, :basket_prefix)',
                FilterExpression='basket_name = :basket_name',
                ExpressionAttributeValues={
                    ':user_id': user_id,
                    ':basket_prefix': 'BASKET#',
                    ':basket_name': basket_name
                },
                Select='COUNT'
            )
            
            if existing_check['Count'] > 0:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'Basket name already exists',
                        'message': f'A basket with the name "{basket_name}" already exists. Please choose a different name.'
                    })
                }
            
            # Put item with additional condition to ensure no race condition
            table.put_item(Item=basket_item,
                ConditionExpression='attribute_not_exists(user_id) AND attribute_not_exists(sort_key)'
            )
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'Basket creation failed',
                        'message': 'A basket with this ID already exists (race condition detected)'
                    })
                }
            else:
                raise e
        
        log_user_action(logger, user_id, "basket_created", {
            "basket_id": basket_id, 
            "basket_name": basket_name,
            "initial_capital": float(initial_capital)
        })
        
        # Return response without sensitive data
        response_item = {k: v for k, v in basket_item.items()}
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'data': response_item,
                'message': 'Basket created successfully'
            }, cls=DecimalEncoder)
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Invalid JSON in request body'
            })
        }
    except Exception as e:
        logger.error("Failed to create basket", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to create basket',
                'message': str(e)
            })
        }


def handle_list_baskets(event, user_id, table):
    """Get all baskets for the user using single table query"""
    
    try:
        # Query all baskets for the user using sort key pattern
        response = table.query(
            KeyConditionExpression='user_id = :user_id AND begins_with(sort_key, :basket_prefix)',
            ExpressionAttributeValues={
                ':user_id': user_id,
                ':basket_prefix': 'BASKET#'
            }
        )
        
        baskets = response['Items']
        
        # Parse query parameters for filtering
        query_params = event.get('queryStringParameters') or {}
        category = query_params.get('category')
        
        # Apply category filter if specified
        if category:
            baskets = [basket for basket in baskets if basket.get('category') == category.upper()]
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'data': baskets,
                'count': len(baskets),
                'message': f'Retrieved {len(baskets)} baskets'
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        logger.error("Failed to retrieve baskets", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to retrieve baskets',
                'message': str(e)
            })
        }


def handle_get_basket(event, user_id, basket_id, table):
    """Get specific basket details using single table structure"""
    
    try:
        response = table.get_item(
            Key={
                'user_id': user_id,
                'sort_key': f'BASKET#{basket_id}'
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
                    'error': 'Basket not found'
                })
            }
        
        basket = response['Item']
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'data': basket,
                'message': 'Basket retrieved successfully'
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        logger.error("Failed to retrieve basket", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to retrieve basket',
                'message': str(e)
            })
        }


def handle_update_basket(event, user_id, basket_id, table):
    """Update an existing basket using single table structure"""
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Check if basket exists
        response = table.get_item(
            Key={
                'user_id': user_id,
                'sort_key': f'BASKET#{basket_id}'
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
                    'error': 'Basket not found'
                })
            }
        
        # Update allowed fields
        current_time = datetime.now(timezone.utc).isoformat()
        update_expression_parts = []
        expression_attribute_values = {}
        
        # Only allow updates to specific fields
        updatable_fields = ['basket_name', 'description', 'status']
        
        # Check for basket_name uniqueness if it's being updated
        if 'basket_name' in body:
            new_basket_name = body['basket_name'].strip()
            current_basket_name = response['Item'].get('basket_name')
            
            # Only check if the name is actually changing
            if new_basket_name != current_basket_name:
                existing_check = table.query(
                    KeyConditionExpression='user_id = :user_id AND begins_with(sort_key, :basket_prefix)',
                    FilterExpression='basket_name = :basket_name',
                    ExpressionAttributeValues={
                        ':user_id': user_id,
                        ':basket_prefix': 'BASKET#',
                        ':basket_name': new_basket_name
                    },
                    Select='COUNT'
                )
                
                if existing_check['Count'] > 0:
                    return {
                        'statusCode': 400,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({
                            'error': 'Basket name already exists',
                            'message': f'A basket with the name "{new_basket_name}" already exists. Please choose a different name.'
                        })
                    }
        
        for field in updatable_fields:
            if field in body:
                update_expression_parts.append(f'{field} = :{field}')
                expression_attribute_values[f':{field}'] = body[field]
        
        # Always update the updated_at timestamp and increment version
        update_expression_parts.extend(['updated_at = :updated_at', 'version = version + :one'])
        expression_attribute_values[':updated_at'] = current_time
        expression_attribute_values[':one'] = 1
        
        if update_expression_parts:
            table.update_item(
                Key={
                    'user_id': user_id,
                    'sort_key': f'BASKET#{basket_id}'
                },
                UpdateExpression='SET ' + ', '.join(update_expression_parts),
                ExpressionAttributeValues=expression_attribute_values
            )
        
        log_user_action(logger, user_id, "basket_updated", {"basket_id": basket_id})
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'message': 'Basket updated successfully',
                'basket_id': basket_id
            })
        }
        
    except Exception as e:
        logger.error("Failed to update basket", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to update basket',
                'message': str(e)
            })
        }


def handle_delete_basket(event, user_id, basket_id, table):
    """Delete a basket using single table structure"""
    
    try:
        # Check if basket exists and user owns it
        response = table.get_item(
            Key={
                'user_id': user_id,
                'sort_key': f'BASKET#{basket_id}'
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
                    'error': 'Basket not found'
                })
            }
        
        basket = response['Item']
        
        # Check if basket has active strategies by doing a count query
        strategies_count_response = table.query(
            KeyConditionExpression='user_id = :user_id AND begins_with(sort_key, :strategy_prefix)',
            FilterExpression='basket_id = :basket_id AND #status IN (:active, :pending)',
            ExpressionAttributeNames={
                '#status': 'status'  # Use expression attribute name for reserved keyword
            },
            ExpressionAttributeValues={
                ':user_id': user_id,
                ':strategy_prefix': 'STRATEGY#',
                ':basket_id': basket_id,
                ':active': 'ACTIVE',
                ':pending': 'PENDING'
            },
            Select='COUNT'  # Only return count, not the items
        )
        
        active_strategy_count = strategies_count_response.get('Count', 0)
        if active_strategy_count > 0:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Cannot delete basket with active strategies',
                    'message': f'Please delete {active_strategy_count} active/pending strategies first',
                    'active_strategy_count': active_strategy_count
                })
            }
        
        # Delete the basket
        table.delete_item(
            Key={
                'user_id': user_id,
                'sort_key': f'BASKET#{basket_id}'
            }
        )
        
        log_user_action(logger, user_id, "basket_deleted", {"basket_id": basket_id})
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'message': 'Basket deleted successfully',
                'basket_id': basket_id
            })
        }
        
    except Exception as e:
        logger.error("Failed to delete basket", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to delete basket',
                'message': str(e)
            })
        }