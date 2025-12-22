"""
Order Manager Lambda
Handles order CRUD operations and broker order placement
Endpoints:
  POST   /trading/orders           - Place order
  GET    /trading/orders           - List orders (with filters)
  GET    /trading/orders/{id}      - Get order details
  PUT    /trading/orders/{id}      - Modify order
  DELETE /trading/orders/{id}      - Cancel order
"""

import json
import boto3
from botocore.exceptions import ClientError
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
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
sys.path.append('/var/task')
sys.path.append('/var/task/option_baskets')

# Import shared logger
from shared_utils.logger import setup_logger, log_lambda_event, log_user_action, log_api_response
logger = setup_logger(__name__)

# Import trading strategies
from trading import (
    get_trading_strategy, OrderParams, OrderResponse, OrderStatus,
    OrderType, TransactionType, TradingMode, ProductType
)

# CORS headers for all responses
CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
}


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda handler for order management operations.
    """
    log_lambda_event(logger, event, context)

    try:
        # Handle OPTIONS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': ''}

        # Get user ID from Cognito authorizer
        user_id = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            claims = event['requestContext']['authorizer'].get('claims', {})
            user_id = claims.get('sub') or claims.get('cognito:username')

        if not user_id:
            return create_response(401, {'error': 'Unauthorized', 'message': 'User ID not found'})

        # Get HTTP method and path parameters
        http_method = event['httpMethod']
        path_parameters = event.get('pathParameters') or {}
        order_id = path_parameters.get('order_id')

        logger.info("Processing order request", extra={
            "user_id": user_id,
            "http_method": http_method,
            "order_id": order_id
        })

        # Initialize DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name=os.environ['REGION'])
        trading_table = dynamodb.Table(os.environ['TRADING_CONFIGURATIONS_TABLE'])

        # Route based on HTTP method
        if http_method == 'POST':
            return handle_place_order(event, user_id, trading_table)
        elif http_method == 'GET' and not order_id:
            return handle_list_orders(event, user_id, trading_table)
        elif http_method == 'GET' and order_id:
            return handle_get_order(event, user_id, order_id, trading_table)
        elif http_method == 'PUT' and order_id:
            return handle_modify_order(event, user_id, order_id, trading_table)
        elif http_method == 'DELETE' and order_id:
            return handle_cancel_order(event, user_id, order_id, trading_table)
        else:
            return create_response(405, {'error': 'Method not allowed'})

    except Exception as e:
        logger.error("Unexpected error in order handler", extra={"error": str(e)})
        return create_response(500, {'error': 'Internal server error', 'message': str(e)})


def handle_place_order(event: Dict, user_id: str, table) -> Dict:
    """
    Place a new order.

    Request body:
    {
        "symbol": "NIFTY24DEC19500CE",
        "exchange": "NFO",
        "transaction_type": "BUY",
        "order_type": "MARKET",
        "quantity": 50,
        "price": null,
        "trigger_price": null,
        "product_type": "NRML",
        "trading_mode": "PAPER",
        "broker_id": "zerodha",
        "client_id": "ABC123",
        "strategy_id": "optional-strategy-id",
        "basket_id": "optional-basket-id",
        "execution_type": "ENTRY"
    }
    """
    try:
        body = json.loads(event.get('body', '{}'))

        # Validate required fields
        required_fields = ['symbol', 'exchange', 'transaction_type', 'order_type', 'quantity']
        for field in required_fields:
            if field not in body:
                return create_response(400, {'error': f'Missing required field: {field}'})

        # Parse order parameters
        trading_mode = TradingMode[body.get('trading_mode', 'PAPER').upper()]
        broker_name = body.get('broker_id', 'paper')

        # Build OrderParams
        order_params = OrderParams(
            symbol=body['symbol'],
            exchange=body['exchange'],
            transaction_type=TransactionType[body['transaction_type'].upper()],
            order_type=OrderType[body['order_type'].upper().replace('-', '_')],
            quantity=int(body['quantity']),
            price=float(body['price']) if body.get('price') else None,
            trigger_price=float(body['trigger_price']) if body.get('trigger_price') else None,
            product_type=ProductType[body.get('product_type', 'NRML').upper()],
            strategy_id=body.get('strategy_id'),
            basket_id=body.get('basket_id'),
            leg_id=body.get('leg_id'),
            execution_type=body.get('execution_type', 'MANUAL'),
            tag=body.get('tag')
        )

        # Get appropriate trading strategy
        strategy = get_trading_strategy(broker_name, trading_mode)

        # Connect to broker (for paper trading, uses defaults; for live, needs credentials)
        if trading_mode == TradingMode.LIVE:
            # Get broker credentials from Secrets Manager
            credentials = get_broker_credentials(user_id, body.get('client_id'), broker_name)
            if not credentials:
                return create_response(400, {'error': 'Broker credentials not found'})
            connected = strategy.connect(credentials)
        else:
            # Paper trading - connect with default settings
            connected = strategy.connect({'initial_balance': 1000000})

        if not connected:
            return create_response(500, {'error': 'Failed to connect to broker'})

        # Place the order
        response = strategy.place_order(order_params)

        if not response.success:
            return create_response(400, {
                'error': 'Order placement failed',
                'message': response.message
            })

        # Generate internal order ID
        internal_order_id = f"ORD_{uuid.uuid4().hex[:12].upper()}"
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        # Build order status key for GSI6: OrdersByStatus
        # Format: {status}#{timestamp}
        order_status_key = f"{response.status.value}#{now_iso}"

        # Store order in DynamoDB
        order_item = {
            'user_id': user_id,
            'sort_key': f'ORDER#{internal_order_id}',
            'order_id': internal_order_id,
            'broker_order_id': response.broker_order_id,
            'entity_type': 'ORDER',

            # Order details
            'symbol': order_params.symbol,
            'exchange': order_params.exchange,
            'transaction_type': order_params.transaction_type.value,
            'order_type': order_params.order_type.value,
            'quantity': order_params.quantity,
            'price': Decimal(str(order_params.price)) if order_params.price else None,
            'trigger_price': Decimal(str(order_params.trigger_price)) if order_params.trigger_price else None,
            'product_type': order_params.product_type.value,

            # Status tracking
            'status': response.status.value,
            'order_status_key': order_status_key,  # For GSI6
            'filled_quantity': 0,
            'fill_price': None,
            'rejection_reason': None,

            # Broker and mode
            'broker_id': broker_name,
            'client_id': body.get('client_id'),
            'trading_mode': trading_mode.value,

            # Strategy linking
            'strategy_id': order_params.strategy_id,
            'basket_id': order_params.basket_id,
            'leg_id': order_params.leg_id,
            'execution_type': order_params.execution_type,

            # Timestamps
            'placed_at': now_iso,
            'updated_at': now_iso,
            'created_at': now_iso,
        }

        # Remove None values
        order_item = {k: v for k, v in order_item.items() if v is not None}

        table.put_item(Item=order_item)

        log_user_action(logger, user_id, "place_order", {
            "order_id": internal_order_id,
            "symbol": order_params.symbol,
            "trading_mode": trading_mode.value
        })

        return create_response(201, {
            'success': True,
            'order': {
                'order_id': internal_order_id,
                'broker_order_id': response.broker_order_id,
                'status': response.status.value,
                'message': response.message,
                'placed_at': now_iso
            }
        })

    except KeyError as e:
        return create_response(400, {'error': f'Invalid enum value: {e}'})
    except Exception as e:
        logger.error("Error placing order", extra={"error": str(e)})
        return create_response(500, {'error': 'Failed to place order', 'message': str(e)})


def handle_list_orders(event: Dict, user_id: str, table) -> Dict:
    """
    List orders with optional filtering.

    Query parameters:
    - status: Filter by order status (OPEN, FILLED, CANCELLED, etc.)
    - trading_mode: Filter by PAPER or LIVE
    - symbol: Filter by trading symbol
    - from_date: ISO date string for date range
    - to_date: ISO date string for date range
    """
    try:
        params = event.get('queryStringParameters') or {}
        status_filter = params.get('status')
        trading_mode_filter = params.get('trading_mode')
        symbol_filter = params.get('symbol')

        # Query using GSI6 if filtering by status, otherwise main table
        if status_filter:
            # Use OrdersByStatus GSI
            response = table.query(
                IndexName='OrdersByStatus',
                KeyConditionExpression='user_id = :uid AND begins_with(order_status_key, :status)',
                ExpressionAttributeValues={
                    ':uid': user_id,
                    ':status': status_filter
                },
                ScanIndexForward=False  # Most recent first
            )
        else:
            # Query main table for all orders
            response = table.query(
                KeyConditionExpression='user_id = :uid AND begins_with(sort_key, :prefix)',
                ExpressionAttributeValues={
                    ':uid': user_id,
                    ':prefix': 'ORDER#'
                },
                ScanIndexForward=False
            )

        orders = response.get('Items', [])

        # Apply additional filters
        if trading_mode_filter:
            orders = [o for o in orders if o.get('trading_mode') == trading_mode_filter]
        if symbol_filter:
            orders = [o for o in orders if o.get('symbol') == symbol_filter]

        # Format response
        formatted_orders = []
        for order in orders:
            formatted_orders.append({
                'order_id': order.get('order_id'),
                'broker_order_id': order.get('broker_order_id'),
                'symbol': order.get('symbol'),
                'exchange': order.get('exchange'),
                'transaction_type': order.get('transaction_type'),
                'order_type': order.get('order_type'),
                'quantity': order.get('quantity'),
                'price': float(order['price']) if order.get('price') else None,
                'trigger_price': float(order['trigger_price']) if order.get('trigger_price') else None,
                'status': order.get('status'),
                'filled_quantity': order.get('filled_quantity', 0),
                'fill_price': float(order['fill_price']) if order.get('fill_price') else None,
                'trading_mode': order.get('trading_mode'),
                'broker_id': order.get('broker_id'),
                'strategy_id': order.get('strategy_id'),
                'basket_id': order.get('basket_id'),
                'execution_type': order.get('execution_type'),
                'placed_at': order.get('placed_at'),
                'updated_at': order.get('updated_at'),
            })

        return create_response(200, {
            'success': True,
            'orders': formatted_orders,
            'count': len(formatted_orders)
        })

    except Exception as e:
        logger.error("Error listing orders", extra={"error": str(e)})
        return create_response(500, {'error': 'Failed to list orders', 'message': str(e)})


def handle_get_order(event: Dict, user_id: str, order_id: str, table) -> Dict:
    """Get details of a specific order."""
    try:
        # Get order from DynamoDB
        response = table.get_item(
            Key={
                'user_id': user_id,
                'sort_key': f'ORDER#{order_id}'
            }
        )

        order = response.get('Item')
        if not order:
            return create_response(404, {'error': 'Order not found'})

        # Format response
        formatted_order = {
            'order_id': order.get('order_id'),
            'broker_order_id': order.get('broker_order_id'),
            'symbol': order.get('symbol'),
            'exchange': order.get('exchange'),
            'transaction_type': order.get('transaction_type'),
            'order_type': order.get('order_type'),
            'quantity': order.get('quantity'),
            'price': float(order['price']) if order.get('price') else None,
            'trigger_price': float(order['trigger_price']) if order.get('trigger_price') else None,
            'product_type': order.get('product_type'),
            'status': order.get('status'),
            'filled_quantity': order.get('filled_quantity', 0),
            'fill_price': float(order['fill_price']) if order.get('fill_price') else None,
            'rejection_reason': order.get('rejection_reason'),
            'trading_mode': order.get('trading_mode'),
            'broker_id': order.get('broker_id'),
            'client_id': order.get('client_id'),
            'strategy_id': order.get('strategy_id'),
            'basket_id': order.get('basket_id'),
            'leg_id': order.get('leg_id'),
            'execution_type': order.get('execution_type'),
            'placed_at': order.get('placed_at'),
            'updated_at': order.get('updated_at'),
        }

        return create_response(200, {
            'success': True,
            'order': formatted_order
        })

    except Exception as e:
        logger.error("Error getting order", extra={"error": str(e), "order_id": order_id})
        return create_response(500, {'error': 'Failed to get order', 'message': str(e)})


def handle_modify_order(event: Dict, user_id: str, order_id: str, table) -> Dict:
    """
    Modify an existing order.

    Request body:
    {
        "quantity": 100,
        "price": 150.5,
        "trigger_price": 145.0,
        "order_type": "LIMIT"
    }
    """
    try:
        body = json.loads(event.get('body', '{}'))

        # Get existing order
        response = table.get_item(
            Key={
                'user_id': user_id,
                'sort_key': f'ORDER#{order_id}'
            }
        )

        order = response.get('Item')
        if not order:
            return create_response(404, {'error': 'Order not found'})

        # Can only modify open orders
        if order.get('status') not in ['OPEN', 'PENDING', 'PLACED']:
            return create_response(400, {
                'error': 'Cannot modify order',
                'message': f"Order is in {order.get('status')} status"
            })

        # Get trading strategy and modify order
        trading_mode = TradingMode[order.get('trading_mode', 'PAPER')]
        broker_name = order.get('broker_id', 'paper')
        strategy = get_trading_strategy(broker_name, trading_mode)

        # Connect to broker
        if trading_mode == TradingMode.LIVE:
            credentials = get_broker_credentials(user_id, order.get('client_id'), broker_name)
            if not credentials:
                return create_response(400, {'error': 'Broker credentials not found'})
            strategy.connect(credentials)
        else:
            strategy.connect({})

        # Modify order with broker
        modifications = {}
        if 'quantity' in body:
            modifications['quantity'] = int(body['quantity'])
        if 'price' in body:
            modifications['price'] = float(body['price'])
        if 'trigger_price' in body:
            modifications['trigger_price'] = float(body['trigger_price'])
        if 'order_type' in body:
            modifications['order_type'] = OrderType[body['order_type'].upper().replace('-', '_')]

        broker_order_id = order.get('broker_order_id', order_id)
        modify_response = strategy.modify_order(broker_order_id, modifications)

        if not modify_response.success:
            return create_response(400, {
                'error': 'Order modification failed',
                'message': modify_response.message
            })

        # Update DynamoDB
        now_iso = datetime.now(timezone.utc).isoformat()
        update_expression = "SET updated_at = :updated"
        expression_values = {':updated': now_iso}

        if 'quantity' in body:
            update_expression += ", quantity = :qty"
            expression_values[':qty'] = int(body['quantity'])
        if 'price' in body:
            update_expression += ", price = :price"
            expression_values[':price'] = Decimal(str(body['price']))
        if 'trigger_price' in body:
            update_expression += ", trigger_price = :trig"
            expression_values[':trig'] = Decimal(str(body['trigger_price']))

        table.update_item(
            Key={
                'user_id': user_id,
                'sort_key': f'ORDER#{order_id}'
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )

        log_user_action(logger, user_id, "modify_order", {
            "order_id": order_id,
            "modifications": modifications
        })

        return create_response(200, {
            'success': True,
            'message': 'Order modified successfully',
            'order_id': order_id
        })

    except Exception as e:
        logger.error("Error modifying order", extra={"error": str(e), "order_id": order_id})
        return create_response(500, {'error': 'Failed to modify order', 'message': str(e)})


def handle_cancel_order(event: Dict, user_id: str, order_id: str, table) -> Dict:
    """Cancel an order."""
    try:
        # Get existing order
        response = table.get_item(
            Key={
                'user_id': user_id,
                'sort_key': f'ORDER#{order_id}'
            }
        )

        order = response.get('Item')
        if not order:
            return create_response(404, {'error': 'Order not found'})

        # Can only cancel open orders
        if order.get('status') not in ['OPEN', 'PENDING', 'PLACED']:
            return create_response(400, {
                'error': 'Cannot cancel order',
                'message': f"Order is in {order.get('status')} status"
            })

        # Get trading strategy and cancel order
        trading_mode = TradingMode[order.get('trading_mode', 'PAPER')]
        broker_name = order.get('broker_id', 'paper')
        strategy = get_trading_strategy(broker_name, trading_mode)

        # Connect to broker
        if trading_mode == TradingMode.LIVE:
            credentials = get_broker_credentials(user_id, order.get('client_id'), broker_name)
            if not credentials:
                return create_response(400, {'error': 'Broker credentials not found'})
            strategy.connect(credentials)
        else:
            strategy.connect({})

        # Cancel order with broker
        broker_order_id = order.get('broker_order_id', order_id)
        cancelled = strategy.cancel_order(broker_order_id)

        if not cancelled:
            return create_response(400, {'error': 'Order cancellation failed'})

        # Update DynamoDB
        now_iso = datetime.now(timezone.utc).isoformat()
        new_status = 'CANCELLED'
        order_status_key = f"{new_status}#{now_iso}"

        table.update_item(
            Key={
                'user_id': user_id,
                'sort_key': f'ORDER#{order_id}'
            },
            UpdateExpression="SET #status = :status, order_status_key = :status_key, updated_at = :updated",
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': new_status,
                ':status_key': order_status_key,
                ':updated': now_iso
            }
        )

        log_user_action(logger, user_id, "cancel_order", {"order_id": order_id})

        return create_response(200, {
            'success': True,
            'message': 'Order cancelled successfully',
            'order_id': order_id
        })

    except Exception as e:
        logger.error("Error cancelling order", extra={"error": str(e), "order_id": order_id})
        return create_response(500, {'error': 'Failed to cancel order', 'message': str(e)})


def get_broker_credentials(user_id: str, client_id: str, broker_name: str) -> Optional[Dict]:
    """
    Get broker credentials from Secrets Manager.
    """
    try:
        secrets_client = boto3.client('secretsmanager', region_name=os.environ['REGION'])
        env = os.environ.get('ENVIRONMENT', 'dev')

        # Try OAuth tokens first (for daily sessions)
        oauth_secret_name = f"ql-{broker_name}-oauth-tokens-{env}-{user_id}-{client_id}"
        try:
            oauth_response = secrets_client.get_secret_value(SecretId=oauth_secret_name)
            oauth_data = json.loads(oauth_response['SecretString'])
            if oauth_data.get('access_token'):
                return {
                    'api_key': oauth_data.get('api_key'),
                    'access_token': oauth_data.get('access_token'),
                    'user_id': oauth_data.get('user_id', client_id)
                }
        except ClientError:
            pass  # Try API credentials next

        # Fall back to API credentials
        api_secret_name = f"ql-{broker_name}-api-credentials-{env}-{user_id}-{client_id}"
        api_response = secrets_client.get_secret_value(SecretId=api_secret_name)
        api_data = json.loads(api_response['SecretString'])

        return {
            'api_key': api_data.get('api_key'),
            'api_secret': api_data.get('api_secret'),
            'user_id': client_id
        }

    except ClientError as e:
        logger.error("Failed to get broker credentials", extra={
            "error": str(e),
            "broker": broker_name
        })
        return None


def create_response(status_code: int, body: Dict) -> Dict:
    """Create standardized API response."""
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': json.dumps(body, cls=DecimalEncoder)
    }
