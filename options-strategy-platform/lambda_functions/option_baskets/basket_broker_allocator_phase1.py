import json
import boto3
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
import os
import sys
from decimal import Decimal

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('REGION', 'ap-south-1'))

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
    Industry Best Practice: Basket-Level Broker Allocation
    Users allocate entire baskets to brokers with lot multipliers
    All strategies within basket inherit the same allocation
    This follows the required user workflow: Create basket → Add strategies → Allocate to brokers
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
        allocation_id = path_parameters.get('allocation_id')
        
        logger.info("Processing basket broker allocation request", extra={
            "user_id": user_id, 
            "http_method": http_method,
            "basket_id": basket_id,
            "allocation_id": allocation_id
        })
        
        # Initialize AWS clients for hybrid architecture
        dynamodb = boto3.resource('dynamodb', region_name=os.environ['REGION'])
        trading_configurations_table = dynamodb.Table(os.environ['TRADING_CONFIGURATIONS_TABLE'])
        
        # Route based on HTTP method and parameters
        if http_method == 'POST' and basket_id:
            return handle_create_basket_allocation(event, user_id, basket_id, trading_configurations_table)
        elif http_method == 'GET' and basket_id and not allocation_id:
            return handle_list_basket_allocations(event, user_id, basket_id, trading_configurations_table)
        elif http_method == 'GET' and basket_id and allocation_id:
            return handle_get_basket_allocation(event, user_id, basket_id, allocation_id, trading_configurations_table)
        elif http_method == 'PUT' and basket_id and allocation_id:
            return handle_update_basket_allocation(event, user_id, basket_id, allocation_id, trading_configurations_table)
        elif http_method == 'DELETE' and basket_id and allocation_id:
            return handle_delete_basket_allocation(event, user_id, basket_id, allocation_id, trading_configurations_table)
        elif http_method == 'GET' and basket_id and path_parameters.get('summary'):
            return handle_get_basket_allocation_summary(event, user_id, basket_id, trading_configurations_table)
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
        logger.error("Unexpected error in basket allocation handler", extra={"error": str(e)})
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


def handle_create_basket_allocation(event, user_id, basket_id, table):
    """
    ✅ INDUSTRY BEST PRACTICE: Create basket-level broker allocation
    All strategies in basket inherit this allocation during execution
    Formula: final_lots = leg.lots × basket_lot_multiplier
    """
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Handle both single allocation and batch allocation
        allocations_data = body.get('allocations', [])
        if not allocations_data:
            # Single allocation format for backward compatibility
            allocations_data = [body]
        
        # Validate basket exists and user owns it
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
        
        basket = basket_response['Item']
        basket_strategies = basket.get('strategies', [])
        
        # Verify broker accounts exist using cross-stack integration
        broker_accounts_table = dynamodb.Table(os.environ['BROKER_ACCOUNTS_TABLE'])
        created_allocations = []
        
        for allocation_data in allocations_data:
            # Extract basket-level broker allocation data
            client_id = allocation_data.get('client_id', '').strip()
            broker_id = allocation_data.get('broker_id', '').strip()
            lot_multiplier = allocation_data.get('lot_multiplier', 1.0)
            priority = allocation_data.get('priority', 1)
            max_lots_per_order = allocation_data.get('max_lots_per_order', 100)
            risk_limit_per_trade = Decimal(str(allocation_data.get('risk_limit_per_trade', 10000)))
            
            # Validate required fields
            if not client_id:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'Missing required fields',
                        'message': 'client_id is required'
                    })
                }
            
            # Validate lot_multiplier
            try:
                lot_multiplier = float(lot_multiplier)
                if lot_multiplier <= 0:
                    raise ValueError("lot_multiplier must be positive")
                if lot_multiplier > 10.0:
                    raise ValueError("lot_multiplier cannot exceed 10.0")
            except (ValueError, TypeError) as e:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'Invalid lot_multiplier',
                        'message': 'lot_multiplier must be a positive number between 0.1 and 10.0'
                    })
                }
            
            # Verify broker account exists
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
            
            # Generate allocation ID and timestamp
            allocation_id = str(uuid.uuid4())
            current_time = datetime.now(timezone.utc).isoformat()
            
            # ✅ BASKET-LEVEL ALLOCATION: Single table structure
            allocation_item = {
                # Single table structure
                'user_id': user_id,  # Partition key
                'sort_key': f"BASKET_ALLOCATION#{allocation_id}",  # Changed from BROKER_ALLOCATION
                
                # Allocation Information
                'allocation_id': allocation_id,
                'basket_id': basket_id,  # ✅ KEY CHANGE: basket_id instead of strategy_id
                'strategies_count': len(basket_strategies),  # Number of strategies that inherit this allocation
                
                # ✅ BASKET-LEVEL: Lot Multiplier applies to ALL strategies in basket
                'lot_multiplier': lot_multiplier,
                
                # Broker Configuration
                'client_id': client_id,
                'broker_id': broker_id or broker_name,
                'broker_name': broker_name,
                'priority': priority,
                'max_lots_per_order': max_lots_per_order,
                
                # Risk Management
                'risk_limit_per_trade': risk_limit_per_trade,
                'max_daily_trades': allocation_data.get('max_daily_trades', 10),
                'stop_loss_percentage': Decimal(str(allocation_data.get('stop_loss_percentage', 0.05))),
                
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
                'entity_type': 'BASKET_ALLOCATION',  # Changed from BROKER_ALLOCATION
                
                # GSI attributes for basket-specific queries (CRITICAL FOR EXECUTION ENGINE)
                'entity_type_priority': f"BASKET_ALLOCATION#{priority:02d}#{allocation_id}",
            }
            
            # Store basket-level allocation in single table
            table.put_item(Item=allocation_item)
            created_allocations.append(allocation_item)
            
            logger.info(f"✅ Basket allocation created: {basket_id} → {broker_name} ({lot_multiplier}x multiplier)")
            logger.info(f"📊 ALL {len(basket_strategies)} strategies inherit this allocation")
        
        # Log user action
        log_user_action(logger, user_id, "basket_broker_allocation_created", {
            "basket_id": basket_id,
            "allocations_created": len(created_allocations),
            "strategies_affected": len(basket_strategies),
            "lot_multipliers": [a['lot_multiplier'] for a in created_allocations]
        })
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'data': created_allocations,
                'message': f'Created {len(created_allocations)} basket allocations affecting {len(basket_strategies)} strategies'
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
        logger.error("Failed to create basket allocation", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to create basket allocation',
                'message': str(e)
            })
        }


def handle_list_basket_allocations(event, user_id, basket_id, table):
    """Get all broker allocations for a basket using optimized GSI query"""
    
    try:
        # Verify basket exists and user owns it
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
        
        # Query allocations for this basket
        response = table.query(
            IndexName='AllocationsByBasket',  # GSI for basket-specific queries
            KeyConditionExpression='basket_id = :basket_id AND begins_with(entity_type_priority, :allocation_prefix)',
            ExpressionAttributeValues={
                ':basket_id': basket_id,
                ':allocation_prefix': 'BASKET_ALLOCATION#'
            },
            ScanIndexForward=True  # Sort by priority
        )
        
        allocations = response['Items']
        
        # Calculate summary statistics
        total_lot_multiplier = sum(float(allocation.get('lot_multiplier', 0)) for allocation in allocations)
        active_brokers = len([a for a in allocations if a.get('status') == 'ACTIVE'])
        
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
                    'total_brokers': len(allocations),
                    'active_brokers': active_brokers,
                    'total_lot_multiplier': total_lot_multiplier
                },
                'count': len(allocations),
                'basket_id': basket_id,
                'message': f'Retrieved {len(allocations)} basket allocations'
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        logger.error("Failed to retrieve basket allocations", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to retrieve basket allocations',
                'message': str(e)
            })
        }


def handle_get_basket_allocation(event, user_id, basket_id, allocation_id, table):
    """Get specific basket allocation details"""
    
    try:
        response = table.get_item(
            Key={
                'user_id': user_id,
                'sort_key': f'BASKET_ALLOCATION#{allocation_id}'
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
                    'error': 'Basket allocation not found'
                })
            }
        
        allocation = response['Item']
        
        # Verify it belongs to the specified basket
        if allocation.get('basket_id') != basket_id:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Basket allocation not found for this basket'
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
                'message': 'Basket allocation retrieved successfully'
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        logger.error("Failed to retrieve basket allocation", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to retrieve basket allocation',
                'message': str(e)
            })
        }


def handle_update_basket_allocation(event, user_id, basket_id, allocation_id, table):
    """Update basket allocation (lot multiplier, priorities, risk limits)"""
    
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
                'sort_key': f'BASKET_ALLOCATION#{allocation_id}'
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
                    'error': 'Basket allocation not found'
                })
            }
        
        allocation = response['Item']
        
        # Verify it belongs to the specified basket
        if allocation.get('basket_id') != basket_id:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Basket allocation not found for this basket'
                })
            }
        
        # Update allowed fields
        current_time = datetime.now(timezone.utc).isoformat()
        update_expression_parts = []
        expression_attribute_values = {}
        
        # Allow updates to operational parameters
        updatable_fields = ['lot_multiplier', 'priority', 'max_lots_per_order', 'risk_limit_per_trade', 
                           'max_daily_trades', 'stop_loss_percentage', 'status']
        
        for field in updatable_fields:
            if field in body:
                update_expression_parts.append(f'{field} = :{field}')
                expression_attribute_values[f':{field}'] = body[field]
                
                # Update GSI attribute if priority changes
                if field == 'priority':
                    new_priority = body[field]
                    update_expression_parts.append('entity_type_priority = :entity_type_priority')
                    expression_attribute_values[':entity_type_priority'] = f"BASKET_ALLOCATION#{new_priority:02d}#{allocation_id}"
        
        # Always update the updated_at timestamp and increment version
        update_expression_parts.extend(['updated_at = :updated_at', 'version = version + :one'])
        expression_attribute_values[':updated_at'] = current_time
        expression_attribute_values[':one'] = 1
        
        if update_expression_parts:
            table.update_item(
                Key={
                    'user_id': user_id,
                    'sort_key': f'BASKET_ALLOCATION#{allocation_id}'
                },
                UpdateExpression='SET ' + ', '.join(update_expression_parts),
                ExpressionAttributeValues=expression_attribute_values
            )
        
        log_user_action(logger, user_id, "basket_allocation_updated", {
            "allocation_id": allocation_id,
            "basket_id": basket_id,
            "updated_fields": list(body.keys())
        })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'message': 'Basket allocation updated successfully',
                'allocation_id': allocation_id
            })
        }
        
    except Exception as e:
        logger.error("Failed to update basket allocation", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to update basket allocation',
                'message': str(e)
            })
        }


def handle_delete_basket_allocation(event, user_id, basket_id, allocation_id, table):
    """Delete a basket allocation"""
    
    try:
        # Check if allocation exists and user owns it
        response = table.get_item(
            Key={
                'user_id': user_id,
                'sort_key': f'BASKET_ALLOCATION#{allocation_id}'
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
                    'error': 'Basket allocation not found'
                })
            }
        
        allocation = response['Item']
        
        # Verify it belongs to the specified basket
        if allocation.get('basket_id') != basket_id:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Basket allocation not found for this basket'
                })
            }
        
        # Delete the allocation
        table.delete_item(
            Key={
                'user_id': user_id,
                'sort_key': f'BASKET_ALLOCATION#{allocation_id}'
            }
        )
        
        log_user_action(logger, user_id, "basket_allocation_deleted", {
            "allocation_id": allocation_id,
            "basket_id": basket_id
        })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'message': 'Basket allocation deleted successfully',
                'allocation_id': allocation_id
            })
        }
        
    except Exception as e:
        logger.error("Failed to delete basket allocation", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to delete basket allocation',
                'message': str(e)
            })
        }


def handle_get_basket_allocation_summary(event, user_id, basket_id, table):
    """Get basket allocation summary with statistics"""
    
    try:
        # Query all allocations for this basket
        response = table.query(
            IndexName='AllocationsByBasket',
            KeyConditionExpression='basket_id = :basket_id AND begins_with(entity_type_priority, :allocation_prefix)',
            ExpressionAttributeValues={
                ':basket_id': basket_id,
                ':allocation_prefix': 'BASKET_ALLOCATION#'
            }
        )
        
        allocations = response['Items']
        
        # Calculate summary statistics
        total_allocations = len(allocations)
        active_allocations = len([a for a in allocations if a.get('status') == 'ACTIVE'])
        total_lot_multiplier = sum(float(a.get('lot_multiplier', 0)) for a in allocations if a.get('status') == 'ACTIVE')
        
        # Broker breakdown
        broker_map = {}
        for allocation in allocations:
            broker_id = allocation.get('broker_id', allocation.get('broker_name', 'unknown'))
            if broker_id not in broker_map:
                broker_map[broker_id] = {
                    'broker_id': broker_id,
                    'client_count': 0,
                    'total_multiplier': 0
                }
            
            broker_map[broker_id]['client_count'] += 1
            if allocation.get('status') == 'ACTIVE':
                broker_map[broker_id]['total_multiplier'] += float(allocation.get('lot_multiplier', 0))
        
        broker_breakdown = list(broker_map.values())
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'data': {
                    'totalAllocations': total_allocations,
                    'activeAllocations': active_allocations,
                    'totalLotMultiplier': total_lot_multiplier,
                    'brokerBreakdown': broker_breakdown
                },
                'message': 'Basket allocation summary retrieved successfully'
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        logger.error("Failed to get basket allocation summary", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to get basket allocation summary',
                'message': str(e)
            })
        }