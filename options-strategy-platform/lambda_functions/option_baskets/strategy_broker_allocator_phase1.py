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
    Phase 1 Revolutionary Feature: Leg-Level Broker Allocation
    Allows each leg of a strategy to be executed across different brokers with custom lot sizes
    This is the core innovation that sets this platform apart from all existing solutions
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
        strategy_id = path_parameters.get('strategy_id')
        allocation_id = path_parameters.get('allocation_id')
        leg_id = path_parameters.get('leg_id')
        
        logger.info("Processing leg broker allocation request", extra={
            "user_id": user_id, 
            "http_method": http_method,
            "strategy_id": strategy_id,
            "allocation_id": allocation_id,
            "leg_id": leg_id
        })
        
        # Initialize AWS clients for hybrid architecture
        dynamodb = boto3.resource('dynamodb', region_name=os.environ['REGION'])
        trading_configurations_table = dynamodb.Table(os.environ['TRADING_CONFIGURATIONS_TABLE'])
        
        # Route based on HTTP method and parameters
        if http_method == 'POST' and strategy_id:
            return handle_create_leg_allocation(event, user_id, strategy_id, trading_configurations_table)
        elif http_method == 'GET' and strategy_id and not allocation_id:
            return handle_list_leg_allocations(event, user_id, strategy_id, trading_configurations_table)
        elif http_method == 'GET' and allocation_id:
            return handle_get_leg_allocation(event, user_id, strategy_id, allocation_id, trading_configurations_table)
        elif http_method == 'PUT' and allocation_id:
            return handle_update_leg_allocation(event, user_id, strategy_id, allocation_id, trading_configurations_table)
        elif http_method == 'DELETE' and allocation_id:
            return handle_delete_leg_allocation(event, user_id, strategy_id, allocation_id, trading_configurations_table)
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
        logger.error("Unexpected error in leg allocation handler", extra={"error": str(e)})
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


def handle_create_leg_allocation(event, user_id, strategy_id, table):
    """
    REVOLUTIONARY FEATURE: Create leg-level broker allocation
    Allows each leg of a strategy to use different brokers with custom lot sizes
    """
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Extract leg allocation data
        leg_id = body.get('leg_id', '').strip()
        client_id = body.get('client_id', '').strip()  # Broker account client ID
        lot_size = body.get('lot_size', 1)
        priority = body.get('priority', 1)  # Execution priority (1 = highest)
        max_lots_per_order = body.get('max_lots_per_order', lot_size)
        risk_limit_per_trade = Decimal(str(body.get('risk_limit_per_trade', 10000)))
        
        # Validate required fields
        if not leg_id or not client_id or lot_size <= 0:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing required fields',
                    'message': 'leg_id, client_id, and lot_size are required'
                })
            }
        
        # Check if strategy exists and user owns it
        strategy_response = table.get_item(
            Key={
                'user_id': user_id,
                'sort_key': f'STRATEGY#{strategy_id}'
            }
        )
        
        if 'Item' not in strategy_response:
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
        
        # Verify broker account exists using cross-stack integration
        broker_accounts_table = dynamodb.Table(os.environ['BROKER_ACCOUNTS_TABLE'])
        broker_response = broker_accounts_table.get_item(
            Key={
                'user_id': user_id,
                'client_id': client_id
            }
        )
        
        if 'Item' not in broker_response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Broker account not found',
                    'message': f'Client ID {client_id} not found in your broker accounts'
                })
            }
        
        broker_account = broker_response['Item']
        broker_name = broker_account.get('broker_name')
        
        # Generate allocation ID and current timestamp
        allocation_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc).isoformat()
        
        # Phase 1: Single table structure for leg broker allocation
        allocation_item = {
            # Single table structure
            'user_id': user_id,  # Partition key
            'sort_key': f"LEG_ALLOCATION#{allocation_id}",  # Sort key
            
            # Allocation Information
            'allocation_id': allocation_id,
            'strategy_id': strategy_id,
            'leg_id': leg_id,
            
            # Broker Configuration
            'client_id': client_id,
            'broker_name': broker_name,
            'lot_size': lot_size,
            'priority': priority,  # 1 = highest priority (executed first)
            'max_lots_per_order': max_lots_per_order,
            
            # Risk Management
            'risk_limit_per_trade': risk_limit_per_trade,
            'max_daily_trades': body.get('max_daily_trades', 10),
            'stop_loss_percentage': Decimal(str(body.get('stop_loss_percentage', 0.05))),
            
            # Execution Statistics (initialized)
            'total_executions': 0,
            'successful_executions': 0,
            'total_pnl': Decimal('0'),
            'avg_execution_time_ms': 0,
            'last_execution_date': None,
            
            # Status & Metadata
            'status': 'ACTIVE',
            'created_at': current_time,
            'updated_at': current_time,
            'version': 1,
            
            # Single table entity type identifier
            'entity_type': 'LEG_ALLOCATION',
            
            # GSI attributes for strategy-specific queries (CRITICAL FOR EXECUTION ENGINE)
            'entity_type_priority': f"LEG_ALLOCATION#{priority:02d}#{allocation_id}",  # For GSI1 sorting by priority
        }
        
        # Store leg allocation in single table
        table.put_item(Item=allocation_item)
        
        log_user_action(logger, user_id, "leg_allocation_created", {
            "allocation_id": allocation_id,
            "strategy_id": strategy_id,
            "leg_id": leg_id,
            "client_id": client_id,
            "broker_name": broker_name,
            "lot_size": lot_size
        })
        
        # Return response without sensitive data
        response_item = {k: v for k, v in allocation_item.items()}
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'data': response_item,
                'message': 'Leg broker allocation created successfully'
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
        logger.error("Failed to create leg allocation", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to create leg allocation',
                'message': str(e)
            })
        }


def handle_list_leg_allocations(event, user_id, strategy_id, table):
    """Get all leg allocations for a strategy using GSI query (ULTRA-FAST)"""
    
    try:
        # Verify strategy exists and user owns it
        strategy_response = table.get_item(
            Key={
                'user_id': user_id,
                'sort_key': f'STRATEGY#{strategy_id}'
            }
        )
        
        if 'Item' not in strategy_response:
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
        
        # Query allocations using GSI1 for strategy-specific queries (PERFORMANCE CRITICAL)
        response = table.query(
            IndexName='AllocationsByStrategy',
            KeyConditionExpression='strategy_id = :strategy_id AND begins_with(entity_type_priority, :allocation_prefix)',
            ExpressionAttributeValues={
                ':strategy_id': strategy_id,
                ':allocation_prefix': 'LEG_ALLOCATION#'
            },
            ScanIndexForward=True  # Sort by priority (ascending, so 01, 02, 03...)
        )
        
        allocations = response['Items']
        
        # Group by leg_id for better organization
        allocations_by_leg = {}
        for allocation in allocations:
            leg_id = allocation.get('leg_id')
            if leg_id not in allocations_by_leg:
                allocations_by_leg[leg_id] = []
            allocations_by_leg[leg_id].append(allocation)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'data': {
                    'allocations': allocations,
                    'allocations_by_leg': allocations_by_leg
                },
                'count': len(allocations),
                'strategy_id': strategy_id,
                'message': f'Retrieved {len(allocations)} leg allocations'
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        logger.error("Failed to retrieve leg allocations", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to retrieve leg allocations',
                'message': str(e)
            })
        }


def handle_get_leg_allocation(event, user_id, strategy_id, allocation_id, table):
    """Get specific leg allocation details"""
    
    try:
        response = table.get_item(
            Key={
                'user_id': user_id,
                'sort_key': f'LEG_ALLOCATION#{allocation_id}'
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
                    'error': 'Leg allocation not found'
                })
            }
        
        allocation = response['Item']
        
        # Verify it belongs to the specified strategy
        if allocation.get('strategy_id') != strategy_id:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Leg allocation not found for this strategy'
                })
            }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'data': allocation,
                'message': 'Leg allocation retrieved successfully'
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        logger.error("Failed to retrieve leg allocation", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to retrieve leg allocation',
                'message': str(e)
            })
        }


def handle_update_leg_allocation(event, user_id, strategy_id, allocation_id, table):
    """Update leg allocation (lot sizes, priorities, risk limits)"""
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Check if allocation exists
        response = table.get_item(
            Key={
                'user_id': user_id,
                'sort_key': f'LEG_ALLOCATION#{allocation_id}'
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
                    'error': 'Leg allocation not found'
                })
            }
        
        allocation = response['Item']
        
        # Verify it belongs to the specified strategy
        if allocation.get('strategy_id') != strategy_id:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Leg allocation not found for this strategy'
                })
            }
        
        # Update allowed fields
        current_time = datetime.now(timezone.utc).isoformat()
        update_expression_parts = []
        expression_attribute_values = {}
        
        # Allow updates to operational parameters
        updatable_fields = ['lot_size', 'priority', 'max_lots_per_order', 'risk_limit_per_trade', 
                           'max_daily_trades', 'stop_loss_percentage', 'status']
        
        for field in updatable_fields:
            if field in body:
                update_expression_parts.append(f'{field} = :{field}')
                expression_attribute_values[f':{field}'] = body[field]
                
                # Update GSI attribute if priority changes
                if field == 'priority':
                    new_priority = body[field]
                    update_expression_parts.append('entity_type_priority = :entity_type_priority')
                    expression_attribute_values[':entity_type_priority'] = f"LEG_ALLOCATION#{new_priority:02d}#{allocation_id}"
        
        # Always update the updated_at timestamp and increment version
        update_expression_parts.extend(['updated_at = :updated_at', 'version = version + :one'])
        expression_attribute_values[':updated_at'] = current_time
        expression_attribute_values[':one'] = 1
        
        if update_expression_parts:
            table.update_item(
                Key={
                    'user_id': user_id,
                    'sort_key': f'LEG_ALLOCATION#{allocation_id}'
                },
                UpdateExpression='SET ' + ', '.join(update_expression_parts),
                ExpressionAttributeValues=expression_attribute_values
            )
        
        log_user_action(logger, user_id, "leg_allocation_updated", {
            "allocation_id": allocation_id,
            "strategy_id": strategy_id
        })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'message': 'Leg allocation updated successfully',
                'allocation_id': allocation_id
            })
        }
        
    except Exception as e:
        logger.error("Failed to update leg allocation", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to update leg allocation',
                'message': str(e)
            })
        }


def handle_delete_leg_allocation(event, user_id, strategy_id, allocation_id, table):
    """Delete a leg allocation"""
    
    try:
        # Check if allocation exists and user owns it
        response = table.get_item(
            Key={
                'user_id': user_id,
                'sort_key': f'LEG_ALLOCATION#{allocation_id}'
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
                    'error': 'Leg allocation not found'
                })
            }
        
        allocation = response['Item']
        
        # Verify it belongs to the specified strategy
        if allocation.get('strategy_id') != strategy_id:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Leg allocation not found for this strategy'
                })
            }
        
        # Check if allocation has active positions (future enhancement)
        # For now, allow deletion
        
        # Delete the allocation
        table.delete_item(
            Key={
                'user_id': user_id,
                'sort_key': f'LEG_ALLOCATION#{allocation_id}'
            }
        )
        
        log_user_action(logger, user_id, "leg_allocation_deleted", {
            "allocation_id": allocation_id,
            "strategy_id": strategy_id
        })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'message': 'Leg allocation deleted successfully',
                'allocation_id': allocation_id
            })
        }
        
    except Exception as e:
        logger.error("Failed to delete leg allocation", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to delete leg allocation',
                'message': str(e)
            })
        }