"""
Position Manager Lambda
Handles position queries and square-off operations
Endpoints:
  GET    /trading/positions              - Get all positions
  GET    /trading/positions/{id}         - Get position details
  POST   /trading/positions/{id}/square-off - Square off position
"""

import json
import boto3
from botocore.exceptions import ClientError
import uuid
from datetime import datetime, timezone, date
from typing import Dict, Any, Optional, List
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
from shared_utils.logger import setup_logger, log_lambda_event, log_user_action
logger = setup_logger(__name__)

# Import trading strategies
from trading import (
    get_trading_strategy, OrderParams, OrderResponse, Position,
    OrderType, TransactionType, TradingMode, ProductType, OrderStatus
)

# CORS headers for all responses
CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
}


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda handler for position management operations.
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

        # Get HTTP method and path
        http_method = event['httpMethod']
        path = event.get('path', '')
        path_parameters = event.get('pathParameters') or {}
        position_id = path_parameters.get('position_id')

        logger.info("Processing position request", extra={
            "user_id": user_id,
            "http_method": http_method,
            "path": path
        })

        # Initialize DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name=os.environ['REGION'])
        trading_table = dynamodb.Table(os.environ['TRADING_CONFIGURATIONS_TABLE'])

        # Route based on HTTP method and path
        if http_method == 'GET' and not position_id:
            return handle_list_positions(event, user_id, trading_table)
        elif http_method == 'GET' and position_id:
            return handle_get_position(event, user_id, position_id, trading_table)
        elif http_method == 'POST' and 'square-off' in path:
            return handle_square_off(event, user_id, position_id, trading_table)
        else:
            return create_response(405, {'error': 'Method not allowed'})

    except Exception as e:
        logger.error("Unexpected error in position handler", extra={"error": str(e)})
        return create_response(500, {'error': 'Internal server error', 'message': str(e)})


def handle_list_positions(event: Dict, user_id: str, table) -> Dict:
    """
    Get all positions for the user.
    Aggregates positions from both paper and live trading modes.

    Query parameters:
    - trading_mode: Filter by PAPER or LIVE
    - broker_id: Filter by specific broker
    - status: Filter by OPEN or CLOSED
    """
    try:
        params = event.get('queryStringParameters') or {}
        trading_mode_filter = params.get('trading_mode')
        broker_filter = params.get('broker_id')
        status_filter = params.get('status', 'OPEN')  # Default to open positions

        # Get today's date for position key prefix
        today = date.today().isoformat()

        # Query positions from DynamoDB
        # Position sort key format: POSITION#{broker_id}#{symbol}#{date}
        response = table.query(
            KeyConditionExpression='user_id = :uid AND begins_with(sort_key, :prefix)',
            ExpressionAttributeValues={
                ':uid': user_id,
                ':prefix': 'POSITION#'
            }
        )

        positions = response.get('Items', [])

        # Apply filters
        if trading_mode_filter:
            positions = [p for p in positions if p.get('trading_mode') == trading_mode_filter]
        if broker_filter:
            positions = [p for p in positions if p.get('broker_id') == broker_filter]
        if status_filter:
            positions = [p for p in positions if p.get('status', 'OPEN') == status_filter]

        # Also fetch live positions from brokers
        live_positions = []
        if not trading_mode_filter or trading_mode_filter == 'LIVE':
            live_positions = fetch_live_positions(user_id, broker_filter)

        # Merge stored and live positions
        all_positions = merge_positions(positions, live_positions)

        # Format response
        formatted_positions = []
        total_pnl = 0
        total_day_pnl = 0

        for pos in all_positions:
            pnl = float(pos.get('pnl', 0))
            day_pnl = float(pos.get('day_change', 0))
            total_pnl += pnl
            total_day_pnl += day_pnl

            formatted_positions.append({
                'position_id': pos.get('position_id'),
                'symbol': pos.get('symbol'),
                'exchange': pos.get('exchange'),
                'product_type': pos.get('product_type'),
                'quantity': pos.get('quantity', 0),
                'buy_quantity': pos.get('buy_quantity', 0),
                'sell_quantity': pos.get('sell_quantity', 0),
                'average_buy_price': float(pos.get('average_buy_price', 0)),
                'average_sell_price': float(pos.get('average_sell_price', 0)),
                'last_price': float(pos.get('last_price', 0)),
                'pnl': pnl,
                'pnl_percentage': float(pos.get('pnl_percentage', 0)),
                'day_change': day_pnl,
                'value': float(pos.get('value', 0)),
                'trading_mode': pos.get('trading_mode', 'PAPER'),
                'broker_id': pos.get('broker_id'),
                'client_id': pos.get('client_id'),
                'strategy_id': pos.get('strategy_id'),
                'basket_id': pos.get('basket_id'),
                'status': pos.get('status', 'OPEN'),
                'opened_at': pos.get('opened_at'),
                'updated_at': pos.get('updated_at'),
            })

        return create_response(200, {
            'success': True,
            'positions': formatted_positions,
            'count': len(formatted_positions),
            'summary': {
                'total_pnl': round(total_pnl, 2),
                'total_day_pnl': round(total_day_pnl, 2),
                'open_positions': len([p for p in formatted_positions if p['status'] == 'OPEN'])
            }
        })

    except Exception as e:
        logger.error("Error listing positions", extra={"error": str(e)})
        return create_response(500, {'error': 'Failed to list positions', 'message': str(e)})


def handle_get_position(event: Dict, user_id: str, position_id: str, table) -> Dict:
    """Get details of a specific position."""
    try:
        # Query for position by position_id
        # Position ID format might be embedded in sort_key
        response = table.query(
            KeyConditionExpression='user_id = :uid AND begins_with(sort_key, :prefix)',
            FilterExpression='position_id = :pid',
            ExpressionAttributeValues={
                ':uid': user_id,
                ':prefix': 'POSITION#',
                ':pid': position_id
            }
        )

        positions = response.get('Items', [])
        if not positions:
            return create_response(404, {'error': 'Position not found'})

        pos = positions[0]

        formatted_position = {
            'position_id': pos.get('position_id'),
            'symbol': pos.get('symbol'),
            'exchange': pos.get('exchange'),
            'product_type': pos.get('product_type'),
            'quantity': pos.get('quantity', 0),
            'buy_quantity': pos.get('buy_quantity', 0),
            'sell_quantity': pos.get('sell_quantity', 0),
            'average_buy_price': float(pos.get('average_buy_price', 0)),
            'average_sell_price': float(pos.get('average_sell_price', 0)),
            'last_price': float(pos.get('last_price', 0)),
            'pnl': float(pos.get('pnl', 0)),
            'pnl_percentage': float(pos.get('pnl_percentage', 0)),
            'day_change': float(pos.get('day_change', 0)),
            'value': float(pos.get('value', 0)),
            'trading_mode': pos.get('trading_mode', 'PAPER'),
            'broker_id': pos.get('broker_id'),
            'client_id': pos.get('client_id'),
            'strategy_id': pos.get('strategy_id'),
            'basket_id': pos.get('basket_id'),
            'status': pos.get('status', 'OPEN'),
            'opened_at': pos.get('opened_at'),
            'closed_at': pos.get('closed_at'),
            'updated_at': pos.get('updated_at'),
        }

        return create_response(200, {
            'success': True,
            'position': formatted_position
        })

    except Exception as e:
        logger.error("Error getting position", extra={"error": str(e), "position_id": position_id})
        return create_response(500, {'error': 'Failed to get position', 'message': str(e)})


def handle_square_off(event: Dict, user_id: str, position_id: str, table) -> Dict:
    """
    Square off a position by placing opposite trade.

    Request body:
    {
        "quantity": null,  // Optional, defaults to full position
        "order_type": "MARKET"  // Optional, defaults to MARKET
    }
    """
    try:
        body = json.loads(event.get('body', '{}'))

        # Get position
        response = table.query(
            KeyConditionExpression='user_id = :uid AND begins_with(sort_key, :prefix)',
            FilterExpression='position_id = :pid',
            ExpressionAttributeValues={
                ':uid': user_id,
                ':prefix': 'POSITION#',
                ':pid': position_id
            }
        )

        positions = response.get('Items', [])
        if not positions:
            return create_response(404, {'error': 'Position not found'})

        pos = positions[0]

        # Validate position is open
        if pos.get('status') == 'CLOSED':
            return create_response(400, {'error': 'Position already closed'})

        quantity = pos.get('quantity', 0)
        if quantity == 0:
            return create_response(400, {'error': 'No quantity to square off'})

        # Determine square-off quantity
        sq_quantity = body.get('quantity')
        if sq_quantity:
            sq_quantity = abs(int(sq_quantity))
            if sq_quantity > abs(quantity):
                return create_response(400, {'error': 'Square-off quantity exceeds position quantity'})
        else:
            sq_quantity = abs(quantity)

        # Determine transaction type (opposite of position direction)
        if quantity > 0:
            transaction_type = TransactionType.SELL
        else:
            transaction_type = TransactionType.BUY

        # Get trading strategy
        trading_mode = TradingMode[pos.get('trading_mode', 'PAPER')]
        broker_name = pos.get('broker_id', 'paper')
        strategy = get_trading_strategy(broker_name, trading_mode)

        # Connect to broker
        if trading_mode == TradingMode.LIVE:
            credentials = get_broker_credentials(user_id, pos.get('client_id'), broker_name)
            if not credentials:
                return create_response(400, {'error': 'Broker credentials not found'})
            strategy.connect(credentials)
        else:
            strategy.connect({})

        # Build square-off order
        order_type_str = body.get('order_type', 'MARKET').upper()
        order_type = OrderType[order_type_str.replace('-', '_')]

        order_params = OrderParams(
            symbol=pos.get('symbol'),
            exchange=pos.get('exchange'),
            transaction_type=transaction_type,
            order_type=order_type,
            quantity=sq_quantity,
            price=float(body.get('price', 0)) if order_type == OrderType.LIMIT else None,
            product_type=ProductType[pos.get('product_type', 'NRML')],
            strategy_id=pos.get('strategy_id'),
            basket_id=pos.get('basket_id'),
            execution_type='EXIT',
            tag=f"SQ_{position_id[:8]}"
        )

        # Place square-off order
        order_response = strategy.place_order(order_params)

        if not order_response.success:
            return create_response(400, {
                'error': 'Square-off order failed',
                'message': order_response.message
            })

        # Update position status if fully squared off
        now_iso = datetime.now(timezone.utc).isoformat()
        remaining_quantity = abs(quantity) - sq_quantity

        if remaining_quantity == 0:
            # Position fully closed
            table.update_item(
                Key={
                    'user_id': user_id,
                    'sort_key': pos.get('sort_key')
                },
                UpdateExpression="SET #status = :status, quantity = :qty, closed_at = :closed, updated_at = :updated",
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'CLOSED',
                    ':qty': 0,
                    ':closed': now_iso,
                    ':updated': now_iso
                }
            )
        else:
            # Partial square-off
            new_quantity = remaining_quantity if quantity > 0 else -remaining_quantity
            table.update_item(
                Key={
                    'user_id': user_id,
                    'sort_key': pos.get('sort_key')
                },
                UpdateExpression="SET quantity = :qty, updated_at = :updated",
                ExpressionAttributeValues={
                    ':qty': new_quantity,
                    ':updated': now_iso
                }
            )

        # Store the square-off order
        store_square_off_order(user_id, pos, order_response, sq_quantity, table)

        log_user_action(logger, user_id, "square_off_position", {
            "position_id": position_id,
            "quantity": sq_quantity,
            "symbol": pos.get('symbol')
        })

        return create_response(200, {
            'success': True,
            'message': 'Position square-off order placed',
            'order': {
                'order_id': order_response.order_id,
                'broker_order_id': order_response.broker_order_id,
                'status': order_response.status.value,
                'quantity': sq_quantity
            },
            'remaining_quantity': remaining_quantity if quantity > 0 else -remaining_quantity
        })

    except Exception as e:
        logger.error("Error squaring off position", extra={"error": str(e), "position_id": position_id})
        return create_response(500, {'error': 'Failed to square off position', 'message': str(e)})


def fetch_live_positions(user_id: str, broker_filter: Optional[str] = None) -> List[Dict]:
    """
    Fetch live positions from connected brokers.
    """
    try:
        live_positions = []

        # Get user's broker accounts from DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name=os.environ['REGION'])
        broker_table = dynamodb.Table(os.environ['BROKER_ACCOUNTS_TABLE'])

        response = broker_table.query(
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user_id}
        )

        broker_accounts = response.get('Items', [])

        for account in broker_accounts:
            broker_name = account.get('broker_name', '').lower()

            # Apply broker filter
            if broker_filter and broker_name != broker_filter.lower():
                continue

            # Only process enabled accounts
            if account.get('account_status') != 'enabled':
                continue

            try:
                # Get broker credentials
                credentials = get_broker_credentials(user_id, account.get('client_id'), broker_name)
                if not credentials:
                    continue

                # Get trading strategy and fetch positions
                strategy = get_trading_strategy(broker_name, TradingMode.LIVE)
                if strategy.connect(credentials):
                    positions = strategy.get_positions()

                    for pos in positions:
                        live_positions.append({
                            'position_id': f"LIVE_{broker_name}_{pos.symbol}",
                            'symbol': pos.symbol,
                            'exchange': pos.exchange,
                            'product_type': pos.product_type.value,
                            'quantity': pos.quantity,
                            'buy_quantity': pos.buy_quantity,
                            'sell_quantity': pos.sell_quantity,
                            'average_buy_price': pos.average_buy_price,
                            'average_sell_price': pos.average_sell_price,
                            'last_price': pos.last_price,
                            'pnl': pos.pnl,
                            'pnl_percentage': pos.pnl_percentage,
                            'day_change': pos.day_change,
                            'value': pos.value,
                            'trading_mode': 'LIVE',
                            'broker_id': broker_name,
                            'client_id': account.get('client_id'),
                            'status': 'OPEN' if pos.quantity != 0 else 'CLOSED',
                        })

                    strategy.disconnect()

            except Exception as e:
                logger.warning(f"Failed to fetch positions from {broker_name}", extra={"error": str(e)})
                continue

        return live_positions

    except Exception as e:
        logger.error("Error fetching live positions", extra={"error": str(e)})
        return []


def merge_positions(stored: List[Dict], live: List[Dict]) -> List[Dict]:
    """
    Merge stored and live positions, preferring live data for accuracy.
    """
    # Create lookup for stored positions
    stored_map = {}
    for pos in stored:
        key = f"{pos.get('broker_id')}_{pos.get('symbol')}"
        stored_map[key] = pos

    # Merge with live positions
    merged = []
    live_keys = set()

    for pos in live:
        key = f"{pos.get('broker_id')}_{pos.get('symbol')}"
        live_keys.add(key)

        # Merge with stored data if exists
        if key in stored_map:
            stored_pos = stored_map[key]
            # Preserve strategy/basket links from stored
            pos['strategy_id'] = stored_pos.get('strategy_id')
            pos['basket_id'] = stored_pos.get('basket_id')
            pos['opened_at'] = stored_pos.get('opened_at')

        merged.append(pos)

    # Add paper positions (not in live)
    for pos in stored:
        if pos.get('trading_mode') == 'PAPER':
            merged.append(pos)
        else:
            key = f"{pos.get('broker_id')}_{pos.get('symbol')}"
            if key not in live_keys and pos.get('status') != 'CLOSED':
                # Stored live position not returned from broker (might be fully closed)
                pos['status'] = 'CLOSED'
                merged.append(pos)

    return merged


def store_square_off_order(user_id: str, position: Dict, order_response: OrderResponse,
                           quantity: int, table) -> None:
    """Store the square-off order in DynamoDB."""
    try:
        order_id = f"ORD_{uuid.uuid4().hex[:12].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        order_item = {
            'user_id': user_id,
            'sort_key': f'ORDER#{order_id}',
            'order_id': order_id,
            'broker_order_id': order_response.broker_order_id,
            'entity_type': 'ORDER',
            'symbol': position.get('symbol'),
            'exchange': position.get('exchange'),
            'transaction_type': 'SELL' if position.get('quantity', 0) > 0 else 'BUY',
            'order_type': 'MARKET',
            'quantity': quantity,
            'status': order_response.status.value,
            'order_status_key': f"{order_response.status.value}#{now_iso}",
            'broker_id': position.get('broker_id'),
            'client_id': position.get('client_id'),
            'trading_mode': position.get('trading_mode'),
            'strategy_id': position.get('strategy_id'),
            'basket_id': position.get('basket_id'),
            'execution_type': 'EXIT',
            'placed_at': now_iso,
            'created_at': now_iso,
            'updated_at': now_iso,
        }

        order_item = {k: v for k, v in order_item.items() if v is not None}
        table.put_item(Item=order_item)

    except Exception as e:
        logger.error("Error storing square-off order", extra={"error": str(e)})


def get_broker_credentials(user_id: str, client_id: str, broker_name: str) -> Optional[Dict]:
    """Get broker credentials from Secrets Manager."""
    try:
        secrets_client = boto3.client('secretsmanager', region_name=os.environ['REGION'])
        env = os.environ.get('ENVIRONMENT', 'dev')

        # Try OAuth tokens first
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
            pass

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
        logger.error("Failed to get broker credentials", extra={"error": str(e), "broker": broker_name})
        return None


def create_response(status_code: int, body: Dict) -> Dict:
    """Create standardized API response."""
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': json.dumps(body, cls=DecimalEncoder)
    }
