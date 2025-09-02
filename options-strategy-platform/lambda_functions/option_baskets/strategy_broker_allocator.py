import json
import boto3
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
import os
from decimal import Decimal

# Custom JSON encoder for Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

# Import shared logger
try:
    from shared_utils.logger import setup_logger, log_user_action
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Strategy-Broker Allocation Manager
    KEY INNOVATION: Allows each strategy to have different broker configurations
    
    Endpoints:
    - GET /options/strategies/{strategy_id}/brokers
    - POST /options/strategies/{strategy_id}/brokers
    - PUT /options/strategies/{strategy_id}/brokers/{allocation_id}
    - DELETE /options/strategies/{strategy_id}/brokers/{allocation_id}
    """
    
    try:
        # Get user ID from authorization context
        user_id = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            claims = event['requestContext']['authorizer'].get('claims', {})
            user_id = claims.get('sub') or claims.get('cognito:username')
        
        if not user_id:
            return create_error_response(401, 'Unauthorized', 'User ID not found')
        
        # Get request parameters
        http_method = event['httpMethod']
        path_parameters = event.get('pathParameters') or {}
        strategy_id = path_parameters.get('strategy_id')
        allocation_id = path_parameters.get('allocation_id')
        
        if not strategy_id:
            return create_error_response(400, 'Missing strategy_id', 'Strategy ID is required')
        
        # Initialize DynamoDB clients
        dynamodb = boto3.resource('dynamodb', region_name=os.environ['REGION'])
        allocations_table = dynamodb.Table(os.environ['STRATEGY_BROKER_ALLOCATIONS_TABLE'])
        strategies_table = dynamodb.Table(os.environ['STRATEGIES_TABLE'])
        brokers_table = dynamodb.Table(os.environ['BROKER_ACCOUNTS_TABLE'])
        
        # Route based on HTTP method
        if http_method == 'GET' and not allocation_id:
            return handle_list_strategy_allocations(user_id, strategy_id, allocations_table)
        elif http_method == 'POST':
            return handle_create_allocation(event, user_id, strategy_id, allocations_table, brokers_table)
        elif http_method == 'PUT' and allocation_id:
            return handle_update_allocation(event, user_id, strategy_id, allocation_id, allocations_table)
        elif http_method == 'DELETE' and allocation_id:
            return handle_delete_allocation(user_id, strategy_id, allocation_id, allocations_table)
        else:
            return create_error_response(405, 'Method not allowed')
            
    except Exception as e:
        logger.error(f"Unexpected error in strategy broker allocator: {str(e)}")
        return create_error_response(500, 'Internal server error', str(e))


def handle_list_strategy_allocations(user_id: str, strategy_id: str, table) -> Dict[str, Any]:
    """Get all broker allocations for a specific strategy"""
    
    try:
        # Query allocations by strategy using GSI
        response = table.query(
            IndexName='AllocationsByStrategy',
            KeyConditionExpression='strategy_id = :strategy_id',
            ExpressionAttributeValues={
                ':strategy_id': strategy_id
            },
            ScanIndexForward=True  # Sort by priority ascending
        )
        
        allocations = response['Items']
        
        # Filter to only user's allocations (security check)
        user_allocations = [alloc for alloc in allocations if alloc.get('user_id') == user_id]
        
        # Calculate total lots per execution
        total_lots = sum(alloc.get('lots_per_execution', 0) for alloc in user_allocations)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'data': {
                    'strategy_id': strategy_id,
                    'allocations': user_allocations,
                    'total_allocations': len(user_allocations),
                    'total_lots_per_execution': total_lots
                },
                'message': f'Retrieved {len(user_allocations)} broker allocations for strategy'
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        logger.error(f"Failed to list strategy allocations: {str(e)}")
        return create_error_response(500, 'Failed to retrieve allocations', str(e))


def handle_create_allocation(event, user_id: str, strategy_id: str, allocations_table, brokers_table) -> Dict[str, Any]:
    """
    Create new broker allocation for strategy
    KEY FEATURE: Each strategy can have different broker configurations
    """
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Extract allocation data
        client_id = body.get('client_id', '').strip()
        lots_per_execution = int(body.get('lots_per_execution', 1))
        priority = int(body.get('priority', 1))
        allocation_percentage = body.get('allocation_percentage')  # Optional alternative to fixed lots
        
        # Risk limits configuration
        risk_limits = body.get('risk_limits', {})
        max_daily_trades = risk_limits.get('max_daily_trades', 10)
        max_daily_loss = Decimal(str(risk_limits.get('max_daily_loss', 50000)))
        max_position_value = Decimal(str(risk_limits.get('max_position_value', 500000)))
        max_margin_utilization = min(100, max(10, risk_limits.get('max_margin_utilization', 70)))
        
        # Execution preferences
        execution_config = body.get('execution_config', {})
        execution_delay_ms = execution_config.get('execution_delay_ms', 0)
        prefer_for_entries = execution_config.get('prefer_for_entries', True)
        prefer_for_exits = execution_config.get('prefer_for_exits', True)
        
        # Validate required fields
        if not client_id or lots_per_execution <= 0 or priority <= 0:
            return create_error_response(
                400, 
                'Invalid allocation data',
                'client_id, lots_per_execution, and priority are required'
            )
        
        # Verify broker account exists and belongs to user
        try:
            broker_response = brokers_table.get_item(
                Key={
                    'user_id': user_id,
                    'client_id': client_id
                }
            )
            
            if 'Item' not in broker_response:
                return create_error_response(
                    404,
                    'Broker account not found',
                    f'Broker account {client_id} does not exist or does not belong to user'
                )
                
            broker_account = broker_response['Item']
            
        except Exception as e:
            return create_error_response(500, 'Failed to validate broker account', str(e))
        
        # Check for duplicate allocation (same strategy + broker + user)
        existing_check = allocations_table.query(
            IndexName='AllocationsByStrategy',
            KeyConditionExpression='strategy_id = :strategy_id',
            FilterExpression='user_id = :user_id AND client_id = :client_id',
            ExpressionAttributeValues={
                ':strategy_id': strategy_id,
                ':user_id': user_id,
                ':client_id': client_id
            }
        )
        
        if existing_check['Items']:
            return create_error_response(
                400,
                'Duplicate allocation',
                f'Strategy {strategy_id} already has allocation for broker {client_id}'
            )
        
        # Generate allocation ID and timestamp
        allocation_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc).isoformat()
        
        # Create allocation item
        allocation_item = {
            'user_id': user_id,
            'allocation_id': allocation_id,
            'strategy_id': strategy_id,
            'client_id': client_id,
            'broker_name': broker_account.get('broker_name', '').upper(),
            
            # Allocation Configuration
            'lots_per_execution': lots_per_execution,
            'priority': priority,
            'allocation_percentage': Decimal(str(allocation_percentage)) if allocation_percentage else None,
            
            # Risk Limits for this Strategy-Broker combination
            'risk_limits': {
                'max_daily_trades': max_daily_trades,
                'max_daily_loss': max_daily_loss,
                'max_position_value': max_position_value,
                'max_margin_utilization': max_margin_utilization
            },
            
            # Execution Configuration
            'execution_config': {
                'execution_delay_ms': execution_delay_ms,
                'prefer_for_entries': prefer_for_entries,
                'prefer_for_exits': prefer_for_exits,
                'enable_auto_rebalance': execution_config.get('enable_auto_rebalance', False)
            },
            
            # Performance Tracking
            'performance_metrics': {
                'total_trades_executed': 0,
                'success_rate': Decimal('100'),
                'average_execution_time': Decimal('0'),
                'total_pnl': Decimal('0')
            },
            
            # Status
            'status': 'ACTIVE',
            'created_at': current_time,
            'updated_at': current_time,
            'last_used': None
        }
        
        # Store allocation in DynamoDB
        allocations_table.put_item(Item=allocation_item)
        
        log_user_action(logger, user_id, "strategy_broker_allocation_created", {
            "strategy_id": strategy_id,
            "client_id": client_id,
            "lots_per_execution": lots_per_execution,
            "priority": priority
        })
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'data': allocation_item,
                'message': 'Strategy broker allocation created successfully'
            }, cls=DecimalEncoder)
        }
        
    except json.JSONDecodeError:
        return create_error_response(400, 'Invalid JSON in request body')
    except Exception as e:
        logger.error(f"Failed to create strategy broker allocation: {str(e)}")
        return create_error_response(500, 'Failed to create allocation', str(e))


def handle_update_allocation(event, user_id: str, strategy_id: str, allocation_id: str, table) -> Dict[str, Any]:
    """Update existing strategy broker allocation"""
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Verify allocation exists and belongs to user
        response = table.get_item(
            Key={
                'user_id': user_id,
                'allocation_id': allocation_id
            }
        )
        
        if 'Item' not in response:
            return create_error_response(404, 'Allocation not found')
        
        allocation = response['Item']
        
        # Verify this allocation belongs to the specified strategy
        if allocation.get('strategy_id') != strategy_id:
            return create_error_response(400, 'Allocation does not belong to specified strategy')
        
        # Build update expression
        current_time = datetime.now(timezone.utc).isoformat()
        update_expression_parts = []
        expression_attribute_values = {}
        
        # Update allowed fields
        updatable_fields = [
            'lots_per_execution', 'priority', 'allocation_percentage', 'status'
        ]
        
        for field in updatable_fields:
            if field in body and body[field] is not None:
                if field == 'allocation_percentage':
                    update_expression_parts.append(f'{field} = :{field}')
                    expression_attribute_values[f':{field}'] = Decimal(str(body[field]))
                else:
                    update_expression_parts.append(f'{field} = :{field}')
                    expression_attribute_values[f':{field}'] = body[field]
        
        # Update nested configurations if provided
        if 'risk_limits' in body:
            risk_limits = body['risk_limits']
            for key, value in risk_limits.items():
                if key in ['max_daily_loss', 'max_position_value']:
                    update_expression_parts.append(f'risk_limits.{key} = :risk_{key}')
                    expression_attribute_values[f':risk_{key}'] = Decimal(str(value))
                else:
                    update_expression_parts.append(f'risk_limits.{key} = :risk_{key}')
                    expression_attribute_values[f':risk_{key}'] = value
        
        if 'execution_config' in body:
            exec_config = body['execution_config']
            for key, value in exec_config.items():
                update_expression_parts.append(f'execution_config.{key} = :exec_{key}')
                expression_attribute_values[f':exec_{key}'] = value
        
        # Always update timestamp
        update_expression_parts.append('updated_at = :updated_at')
        expression_attribute_values[':updated_at'] = current_time
        
        if update_expression_parts:
            table.update_item(
                Key={
                    'user_id': user_id,
                    'allocation_id': allocation_id
                },
                UpdateExpression='SET ' + ', '.join(update_expression_parts),
                ExpressionAttributeValues=expression_attribute_values
            )
        
        log_user_action(logger, user_id, "strategy_broker_allocation_updated", {
            "strategy_id": strategy_id,
            "allocation_id": allocation_id
        })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'message': 'Strategy broker allocation updated successfully',
                'allocation_id': allocation_id
            })
        }
        
    except Exception as e:
        logger.error(f"Failed to update strategy broker allocation: {str(e)}")
        return create_error_response(500, 'Failed to update allocation', str(e))


def handle_delete_allocation(user_id: str, strategy_id: str, allocation_id: str, table) -> Dict[str, Any]:
    """Delete strategy broker allocation"""
    
    try:
        # Verify allocation exists and belongs to user
        response = table.get_item(
            Key={
                'user_id': user_id,
                'allocation_id': allocation_id
            }
        )
        
        if 'Item' not in response:
            return create_error_response(404, 'Allocation not found')
        
        allocation = response['Item']
        
        # Verify this allocation belongs to the specified strategy
        if allocation.get('strategy_id') != strategy_id:
            return create_error_response(400, 'Allocation does not belong to specified strategy')
        
        # Check if allocation is currently being used (has active positions)
        # This would require checking position tracker table
        # For now, we'll allow deletion
        
        # Delete the allocation
        table.delete_item(
            Key={
                'user_id': user_id,
                'allocation_id': allocation_id
            }
        )
        
        log_user_action(logger, user_id, "strategy_broker_allocation_deleted", {
            "strategy_id": strategy_id,
            "allocation_id": allocation_id,
            "client_id": allocation.get('client_id')
        })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'message': 'Strategy broker allocation deleted successfully',
                'allocation_id': allocation_id
            })
        }
        
    except Exception as e:
        logger.error(f"Failed to delete strategy broker allocation: {str(e)}")
        return create_error_response(500, 'Failed to delete allocation', str(e))


def create_error_response(status_code: int, error: str, message: str = None) -> Dict[str, Any]:
    """Helper function to create consistent error responses"""
    
    response_body = {'error': error}
    if message:
        response_body['message'] = message
    
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(response_body)
    }