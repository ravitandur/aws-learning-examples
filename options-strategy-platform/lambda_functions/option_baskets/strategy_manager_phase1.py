import json
import boto3
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
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
    Phase 1 Lambda function to manage strategies using hybrid architecture
    Handles CRUD operations for strategies and legs using single table design
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
        strategy_id = path_parameters.get('strategy_id')
        
        logger.info("Processing strategy request", extra={
            "user_id": user_id, 
            "http_method": http_method,
            "basket_id": basket_id,
            "strategy_id": strategy_id
        })
        
        # Initialize AWS clients for hybrid architecture
        dynamodb = boto3.resource('dynamodb', region_name=os.environ['REGION'])
        trading_configurations_table = dynamodb.Table(os.environ['TRADING_CONFIGURATIONS_TABLE'])
        
        # Route based on HTTP method and parameters
        if http_method == 'POST' and basket_id:
            return handle_create_strategy(event, user_id, basket_id, trading_configurations_table)
        elif http_method == 'GET' and basket_id and not strategy_id:
            return handle_list_strategies(event, user_id, basket_id, trading_configurations_table)
        elif http_method == 'GET' and strategy_id:
            return handle_get_strategy(event, user_id, strategy_id, trading_configurations_table)
        elif http_method == 'PUT' and strategy_id:
            return handle_update_strategy(event, user_id, strategy_id, trading_configurations_table)
        elif http_method == 'DELETE' and strategy_id:
            return handle_delete_strategy(event, user_id, strategy_id, trading_configurations_table)
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
        logger.error("Unexpected error in strategy handler", extra={"error": str(e)})
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


def handle_create_strategy(event, user_id, basket_id, table):
    """Create a new strategy with legs using single table design"""
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Extract strategy data from user request
        strategy_name = body.get('name', '').strip()
        description = body.get('description', '').strip()
        underlying = body.get('underlying', '').upper()  # NIFTY, BANKNIFTY, etc.
        product = body.get('product', '').upper()  # NRML or MIS
        entry_time = body.get('entry_time', '09:30')  # "09:30" format
        exit_time = body.get('exit_time', '15:20')   # "15:20" format
        entry_days = body.get('entry_days', ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY'])
        exit_days = body.get('exit_days', ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY'])
        legs = body.get('legs', [])  # List of leg configurations
        
        # Validate required fields
        if not strategy_name or not underlying or not product or not legs:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing required fields',
                    'message': 'strategy_name, underlying, product, and legs are required'
                })
            }
        
        # Validate product field (user requirement)
        if product not in ['NRML', 'MIS']:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Invalid product',
                    'message': 'Product must be NRML (positional) or MIS (intraday)'
                })
            }
        
        # Validate underlying (user requirement)
        valid_underlyings = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX']
        if underlying not in valid_underlyings:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Invalid underlying',
                    'message': f'Underlying must be one of: {", ".join(valid_underlyings)}'
                })
            }
        
        # Check if basket exists
        basket_response = table.get_item(
            Key={
                'user_id': user_id,
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
                'body': json.dumps({
                    'error': 'Basket not found'
                })
            }
        
        # Generate strategy ID and current timestamp
        strategy_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc).isoformat()
        
        # Phase 1: Single table structure for strategy
        strategy_item = {
            # Single table structure
            'user_id': user_id,  # Partition key
            'sort_key': f"STRATEGY#{strategy_id}",  # Sort key
            
            # Basic Information
            'strategy_id': strategy_id,
            'basket_id': basket_id,
            'strategy_name': strategy_name,
            'description': description,
            
            # Trading Configuration (User-specified requirements)
            'underlying': underlying,  # NIFTY, BANKNIFTY, etc.
            'product': product,  # NRML (positional) or MIS (intraday) 
            'is_intra_day': (product == 'MIS'),  # Derived from product
            
            # Timing Configuration
            'entry_time': entry_time,
            'exit_time': exit_time,
            'entry_days': entry_days,
            'exit_days': exit_days,
            
            # Leg Information
            'leg_count': len(legs),
            'legs': legs,  # Store legs inline for Phase 1 simplicity
            
            # Performance Metrics (initialized)
            'total_return': Decimal('0'),
            'success_rate': Decimal('0'),
            'execution_count': 0,
            'last_execution_date': None,
            
            # Status & Metadata
            'status': 'ACTIVE',
            'created_at': current_time,
            'updated_at': current_time,
            'version': 1,
            
            # Single table entity type identifier
            'entity_type': 'STRATEGY',
            
            # GSI attributes for strategy-specific queries
            'strategy_id': strategy_id,  # For GSI1 (AllocationsByStrategy)
            'entity_type_priority': f"STRATEGY#{strategy_name}",  # For GSI1 sorting
            
            # GSI attributes for execution schedule (CRITICAL FOR PERFORMANCE)
            'execution_schedule_key': f"ENTRY#{entry_time}#{strategy_id}",  # For GSI2 entry queries
        }
        
        # Store strategy in single table
        table.put_item(Item=strategy_item)
        
        # Update basket strategy count
        table.update_item(
            Key={
                'user_id': user_id,
                'sort_key': f'BASKET#{basket_id}'
            },
            UpdateExpression='SET strategy_count = strategy_count + :one, active_strategy_count = active_strategy_count + :one',
            ExpressionAttributeValues={':one': 1}
        )
        
        log_user_action(logger, user_id, "strategy_created", {
            "strategy_id": strategy_id,
            "basket_id": basket_id, 
            "name": strategy_name,
            "underlying": underlying,
            "leg_count": len(legs)
        })
        
        # Return response without sensitive data
        response_item = {k: v for k, v in strategy_item.items()}
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'data': response_item,
                'message': 'Strategy created successfully'
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
        logger.error("Failed to create strategy", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to create strategy',
                'message': str(e)
            })
        }


def handle_list_strategies(event, user_id, basket_id, table):
    """Get all strategies for a basket using single table query"""
    
    try:
        # First verify basket exists and user owns it
        basket_response = table.get_item(
            Key={
                'user_id': user_id,
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
                'body': json.dumps({
                    'error': 'Basket not found'
                })
            }
        
        # Query all strategies for the user using sort key pattern
        response = table.query(
            KeyConditionExpression='user_id = :user_id AND begins_with(sort_key, :strategy_prefix)',
            ExpressionAttributeValues={
                ':user_id': user_id,
                ':strategy_prefix': 'STRATEGY#'
            },
            # Filter by basket_id
            FilterExpression='basket_id = :basket_id',
            ExpressionAttributeValues={
                **response.get('ExpressionAttributeValues', {}),
                ':basket_id': basket_id
            }
        )
        
        strategies = response['Items']
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'data': strategies,
                'count': len(strategies),
                'basket_id': basket_id,
                'message': f'Retrieved {len(strategies)} strategies'
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        logger.error("Failed to retrieve strategies", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to retrieve strategies',
                'message': str(e)
            })
        }


def handle_get_strategy(event, user_id, strategy_id, table):
    """Get specific strategy details using single table structure"""
    
    try:
        response = table.get_item(
            Key={
                'user_id': user_id,
                'sort_key': f'STRATEGY#{strategy_id}'
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
                    'error': 'Strategy not found'
                })
            }
        
        strategy = response['Item']
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'data': strategy,
                'message': 'Strategy retrieved successfully'
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        logger.error("Failed to retrieve strategy", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to retrieve strategy',
                'message': str(e)
            })
        }


def handle_update_strategy(event, user_id, strategy_id, table):
    """Update an existing strategy using single table structure"""
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Check if strategy exists
        response = table.get_item(
            Key={
                'user_id': user_id,
                'sort_key': f'STRATEGY#{strategy_id}'
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
                    'error': 'Strategy not found'
                })
            }
        
        # Update allowed fields
        current_time = datetime.now(timezone.utc).isoformat()
        update_expression_parts = []
        expression_attribute_values = {}
        
        # Only allow updates to specific fields (no underlying or product changes in Phase 1)
        updatable_fields = ['strategy_name', 'description', 'entry_time', 'exit_time', 'entry_days', 'exit_days', 'legs', 'status']
        
        for field in updatable_fields:
            if field in body:
                update_expression_parts.append(f'{field} = :{field}')
                expression_attribute_values[f':{field}'] = body[field]
                
                # Update derived fields
                if field == 'legs':
                    update_expression_parts.append('leg_count = :leg_count')
                    expression_attribute_values[':leg_count'] = len(body[field])
        
        # Always update the updated_at timestamp and increment version
        update_expression_parts.extend(['updated_at = :updated_at', 'version = version + :one'])
        expression_attribute_values[':updated_at'] = current_time
        expression_attribute_values[':one'] = 1
        
        if update_expression_parts:
            table.update_item(
                Key={
                    'user_id': user_id,
                    'sort_key': f'STRATEGY#{strategy_id}'
                },
                UpdateExpression='SET ' + ', '.join(update_expression_parts),
                ExpressionAttributeValues=expression_attribute_values
            )
        
        log_user_action(logger, user_id, "strategy_updated", {"strategy_id": strategy_id})
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'message': 'Strategy updated successfully',
                'strategy_id': strategy_id
            })
        }
        
    except Exception as e:
        logger.error("Failed to update strategy", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to update strategy',
                'message': str(e)
            })
        }


def handle_delete_strategy(event, user_id, strategy_id, table):
    """Delete a strategy using single table structure"""
    
    try:
        # Check if strategy exists and user owns it
        response = table.get_item(
            Key={
                'user_id': user_id,
                'sort_key': f'STRATEGY#{strategy_id}'
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
                    'error': 'Strategy not found'
                })
            }
        
        strategy = response['Item']
        basket_id = strategy.get('basket_id')
        
        # Check if strategy has active positions (future enhancement)
        # For now, allow deletion
        
        # Delete the strategy
        table.delete_item(
            Key={
                'user_id': user_id,
                'sort_key': f'STRATEGY#{strategy_id}'
            }
        )
        
        # Update basket strategy counts if basket_id exists
        if basket_id:
            table.update_item(
                Key={
                    'user_id': user_id,
                    'sort_key': f'BASKET#{basket_id}'
                },
                UpdateExpression='SET strategy_count = strategy_count - :one, active_strategy_count = active_strategy_count - :one',
                ExpressionAttributeValues={':one': 1}
            )
        
        log_user_action(logger, user_id, "strategy_deleted", {"strategy_id": strategy_id})
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'message': 'Strategy deleted successfully',
                'strategy_id': strategy_id
            })
        }
        
    except Exception as e:
        logger.error("Failed to delete strategy", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to delete strategy',
                'message': str(e)
            })
        }