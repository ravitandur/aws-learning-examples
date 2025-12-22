"""
Trading Execution Bridge
Connects the strategy execution engine with actual broker trading strategies

This bridge provides the interface between:
- Strategy Executor (strategy_executor_phase1.py)
- Broker Trading Strategies (Zerodha, Zebu, Paper)
- Order/Position Management
- WebSocket Broadcasting
"""

import json
import os
import uuid
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple

import boto3
from boto3.dynamodb.conditions import Key

# Import trading strategies
from .broker_trading_strategy import (
    BrokerTradingStrategy,
    OrderParams,
    OrderResponse,
    OrderType,
    TransactionType,
    OrderStatus,
    TradingMode,
    ProductType,
)
from . import get_trading_strategy

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class TradingExecutionBridge:
    """
    Bridge between strategy execution and broker trading APIs.

    Responsibilities:
    - Route orders to appropriate broker strategy
    - Store orders in DynamoDB
    - Track positions
    - Broadcast updates via WebSocket
    """

    def __init__(
        self,
        trading_table_name: Optional[str] = None,
        websocket_endpoint: Optional[str] = None,
        connections_table_name: Optional[str] = None
    ):
        """Initialize the trading execution bridge."""
        self.dynamodb = boto3.resource('dynamodb')

        self.trading_table_name = trading_table_name or os.environ.get('TRADING_CONFIGURATIONS_TABLE', '')
        self.trading_table = self.dynamodb.Table(self.trading_table_name) if self.trading_table_name else None

        self.websocket_endpoint = websocket_endpoint or os.environ.get('WEBSOCKET_ENDPOINT_URL', '')
        self.connections_table_name = connections_table_name or os.environ.get('WEBSOCKET_CONNECTIONS_TABLE', '')

        # Cache for broker strategies
        self._strategy_cache: Dict[str, BrokerTradingStrategy] = {}

    def _get_broker_strategy(
        self,
        broker_name: str,
        trading_mode: TradingMode,
        credentials: Optional[Dict[str, str]] = None
    ) -> BrokerTradingStrategy:
        """Get or create a broker strategy instance."""
        cache_key = f"{broker_name}_{trading_mode.value}"

        if cache_key not in self._strategy_cache:
            strategy = get_trading_strategy(broker_name, trading_mode)

            # Connect if credentials provided
            if credentials:
                strategy.connect(credentials)

            self._strategy_cache[cache_key] = strategy

        return self._strategy_cache[cache_key]

    def _generate_order_id(self) -> str:
        """Generate a unique order ID."""
        return f"ORD_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"

    def _convert_to_decimal(self, value: Any) -> Any:
        """Convert float to Decimal for DynamoDB."""
        if isinstance(value, float):
            return Decimal(str(value))
        if isinstance(value, dict):
            return {k: self._convert_to_decimal(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._convert_to_decimal(v) for v in value]
        return value

    async def execute_leg(
        self,
        user_id: str,
        strategy_id: str,
        basket_id: str,
        leg_data: Dict[str, Any],
        allocation: Dict[str, Any],
        trading_mode: TradingMode,
        execution_type: str = 'ENTRY',
        credentials: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute a single leg with a specific broker allocation.

        Args:
            user_id: User ID for the execution
            strategy_id: Strategy ID
            basket_id: Basket ID
            leg_data: Leg configuration (symbol, option_type, strike, etc.)
            allocation: Broker allocation (broker_name, client_id, lot_size)
            trading_mode: PAPER or LIVE
            execution_type: ENTRY or EXIT
            credentials: Optional broker credentials

        Returns:
            Execution result with order details
        """
        broker_name = allocation.get('broker_name', 'paper')
        client_id = allocation.get('client_id', 'unknown')
        lot_multiplier = float(allocation.get('lot_multiplier', 1.0))
        base_lots = int(leg_data.get('lots', 1))
        final_lots = int(base_lots * lot_multiplier)

        logger.info(f"Executing leg for user {user_id}: {final_lots} lots on {broker_name}")

        # Get broker strategy
        strategy = self._get_broker_strategy(broker_name, trading_mode, credentials)

        # Build order parameters
        order_id = self._generate_order_id()

        # Determine transaction type based on leg action and execution type
        leg_action = leg_data.get('action', 'BUY')
        if execution_type == 'EXIT':
            # Reverse the action for exit
            transaction_type = TransactionType.SELL if leg_action == 'BUY' else TransactionType.BUY
        else:
            transaction_type = TransactionType.BUY if leg_action == 'BUY' else TransactionType.SELL

        # Build symbol from leg data
        symbol = self._build_trading_symbol(leg_data)

        order_params = OrderParams(
            symbol=symbol,
            exchange=leg_data.get('exchange', 'NFO'),
            transaction_type=transaction_type,
            order_type=OrderType.MARKET,  # Use market orders for execution
            quantity=final_lots,
            product_type=ProductType.NRML,
            client_id=client_id,
        )

        # Place order via broker strategy
        try:
            order_response = strategy.place_order(order_params)

            # Build order record
            order_record = {
                'user_id': user_id,
                'sort_key': f'ORDER#{order_id}',
                'order_id': order_id,
                'broker_order_id': order_response.broker_order_id,
                'strategy_id': strategy_id,
                'basket_id': basket_id,
                'leg_id': leg_data.get('leg_id'),
                'broker_id': broker_name,
                'client_id': client_id,
                'symbol': symbol,
                'exchange': order_params.exchange,
                'transaction_type': transaction_type.value,
                'order_type': order_params.order_type.value,
                'quantity': final_lots,
                'base_lots': base_lots,
                'lot_multiplier': Decimal(str(lot_multiplier)),
                'product_type': order_params.product_type.value,
                'status': order_response.status.value,
                'trading_mode': trading_mode.value,
                'execution_type': execution_type,
                'filled_quantity': 0,
                'fill_price': None,
                'rejection_reason': order_response.message if order_response.status == OrderStatus.REJECTED else None,
                'order_status_key': f'{order_response.status.value}#{datetime.now(timezone.utc).isoformat()}',
                'placed_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'entity_type': 'ORDER',
            }

            # Store order in DynamoDB
            if self.trading_table:
                order_record_decimal = self._convert_to_decimal(order_record)
                self.trading_table.put_item(Item=order_record_decimal)

            # Broadcast order update via WebSocket
            await self._broadcast_order_update(user_id, order_record)

            return {
                'order_id': order_id,
                'broker_order_id': order_response.broker_order_id,
                'status': order_response.status.value,
                'message': order_response.message,
                'symbol': symbol,
                'quantity': final_lots,
                'broker_name': broker_name,
                'client_id': client_id,
                'execution_timestamp': datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Order execution failed: {e}")
            return {
                'order_id': order_id,
                'status': 'ERROR',
                'error': str(e),
                'symbol': symbol,
                'quantity': final_lots,
                'broker_name': broker_name,
                'client_id': client_id,
                'execution_timestamp': datetime.now(timezone.utc).isoformat(),
            }

    def execute_leg_sync(
        self,
        user_id: str,
        strategy_id: str,
        basket_id: str,
        leg_data: Dict[str, Any],
        allocation: Dict[str, Any],
        trading_mode: TradingMode,
        execution_type: str = 'ENTRY',
        credentials: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Synchronous version of execute_leg for Lambda compatibility.
        """
        broker_name = allocation.get('broker_name', 'paper')
        client_id = allocation.get('client_id', 'unknown')
        lot_multiplier = float(allocation.get('lot_multiplier', 1.0))
        base_lots = int(leg_data.get('lots', 1))
        final_lots = int(base_lots * lot_multiplier)

        logger.info(f"Executing leg (sync) for user {user_id}: {final_lots} lots on {broker_name}")

        # Get broker strategy
        strategy = self._get_broker_strategy(broker_name, trading_mode, credentials)

        # Build order parameters
        order_id = self._generate_order_id()

        # Determine transaction type
        leg_action = leg_data.get('action', 'BUY')
        if execution_type == 'EXIT':
            transaction_type = TransactionType.SELL if leg_action == 'BUY' else TransactionType.BUY
        else:
            transaction_type = TransactionType.BUY if leg_action == 'BUY' else TransactionType.SELL

        symbol = self._build_trading_symbol(leg_data)

        order_params = OrderParams(
            symbol=symbol,
            exchange=leg_data.get('exchange', 'NFO'),
            transaction_type=transaction_type,
            order_type=OrderType.MARKET,
            quantity=final_lots,
            product_type=ProductType.NRML,
            client_id=client_id,
        )

        try:
            order_response = strategy.place_order(order_params)

            order_record = {
                'user_id': user_id,
                'sort_key': f'ORDER#{order_id}',
                'order_id': order_id,
                'broker_order_id': order_response.broker_order_id,
                'strategy_id': strategy_id,
                'basket_id': basket_id,
                'leg_id': leg_data.get('leg_id'),
                'broker_id': broker_name,
                'client_id': client_id,
                'symbol': symbol,
                'exchange': order_params.exchange,
                'transaction_type': transaction_type.value,
                'order_type': order_params.order_type.value,
                'quantity': final_lots,
                'base_lots': base_lots,
                'lot_multiplier': Decimal(str(lot_multiplier)),
                'product_type': order_params.product_type.value,
                'status': order_response.status.value,
                'trading_mode': trading_mode.value,
                'execution_type': execution_type,
                'filled_quantity': 0,
                'fill_price': None,
                'rejection_reason': order_response.message if order_response.status == OrderStatus.REJECTED else None,
                'order_status_key': f'{order_response.status.value}#{datetime.now(timezone.utc).isoformat()}',
                'placed_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'entity_type': 'ORDER',
            }

            if self.trading_table:
                order_record_decimal = self._convert_to_decimal(order_record)
                self.trading_table.put_item(Item=order_record_decimal)

            return {
                'order_id': order_id,
                'broker_order_id': order_response.broker_order_id,
                'status': order_response.status.value,
                'message': order_response.message,
                'symbol': symbol,
                'quantity': final_lots,
                'broker_name': broker_name,
                'client_id': client_id,
                'execution_timestamp': datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Order execution failed: {e}")
            return {
                'order_id': order_id,
                'status': 'ERROR',
                'error': str(e),
                'symbol': symbol,
                'quantity': final_lots,
                'broker_name': broker_name,
                'client_id': client_id,
                'execution_timestamp': datetime.now(timezone.utc).isoformat(),
            }

    def execute_strategy(
        self,
        user_id: str,
        strategy: Dict[str, Any],
        allocations: List[Dict[str, Any]],
        trading_mode: TradingMode,
        execution_type: str = 'ENTRY',
        credentials_map: Optional[Dict[str, Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Execute all legs of a strategy with all broker allocations.

        Args:
            user_id: User ID
            strategy: Strategy data with legs
            allocations: List of broker allocations
            trading_mode: PAPER or LIVE
            execution_type: ENTRY or EXIT
            credentials_map: Map of broker_name -> credentials

        Returns:
            Execution results for all legs
        """
        strategy_id = strategy.get('strategy_id')
        basket_id = strategy.get('basket_id')
        strategy_name = strategy.get('strategy_name', 'Unknown')
        legs = strategy.get('legs', [])

        logger.info(f"Executing strategy {strategy_name} with {len(legs)} legs and {len(allocations)} allocations")

        execution_results = []
        total_orders = 0
        successful_orders = 0

        for allocation in allocations:
            broker_name = allocation.get('broker_name')
            credentials = credentials_map.get(broker_name) if credentials_map else None

            for leg in legs:
                result = self.execute_leg_sync(
                    user_id=user_id,
                    strategy_id=strategy_id,
                    basket_id=basket_id,
                    leg_data=leg,
                    allocation=allocation,
                    trading_mode=trading_mode,
                    execution_type=execution_type,
                    credentials=credentials,
                )

                execution_results.append(result)
                total_orders += 1

                if result.get('status') in ['PENDING', 'PLACED', 'OPEN', 'FILLED']:
                    successful_orders += 1

        return {
            'strategy_id': strategy_id,
            'strategy_name': strategy_name,
            'basket_id': basket_id,
            'execution_type': execution_type,
            'trading_mode': trading_mode.value,
            'total_orders': total_orders,
            'successful_orders': successful_orders,
            'failed_orders': total_orders - successful_orders,
            'leg_executions': execution_results,
            'execution_timestamp': datetime.now(timezone.utc).isoformat(),
        }

    def _build_trading_symbol(self, leg_data: Dict[str, Any]) -> str:
        """
        Build a trading symbol from leg data.
        Format: UNDERLYING + EXPIRY + STRIKE + OPTION_TYPE
        Example: NIFTY24DEC2140050CE
        """
        underlying = leg_data.get('underlying', leg_data.get('index', 'NIFTY'))
        expiry = leg_data.get('expiry_date', '')
        strike = leg_data.get('strike_price', leg_data.get('strike', ''))
        option_type = leg_data.get('option_type', 'CE')

        # If we have a pre-built symbol, use it
        if leg_data.get('symbol'):
            return leg_data['symbol']

        # Build symbol from components
        # Handle expiry format (DDMMMYY or YYYYMMDD)
        if expiry and len(expiry) == 10:  # YYYY-MM-DD format
            from datetime import datetime as dt
            exp_date = dt.strptime(expiry, '%Y-%m-%d')
            expiry_str = exp_date.strftime('%d%b%y').upper()
        else:
            expiry_str = expiry.upper() if expiry else ''

        return f"{underlying}{expiry_str}{strike}{option_type}"

    async def _broadcast_order_update(self, user_id: str, order: Dict[str, Any]) -> None:
        """Broadcast order update via WebSocket."""
        if not self.websocket_endpoint or not self.connections_table_name:
            return

        try:
            # Import broadcaster here to avoid circular imports
            from ..websocket.broadcaster import WebSocketBroadcaster

            broadcaster = WebSocketBroadcaster(
                connections_table_name=self.connections_table_name,
                endpoint_url=self.websocket_endpoint
            )

            broadcaster.broadcast_order_update(user_id, order)
        except Exception as e:
            logger.warning(f"Failed to broadcast order update: {e}")

    def update_position(
        self,
        user_id: str,
        order_id: str,
        filled_quantity: int,
        fill_price: float
    ) -> Optional[Dict[str, Any]]:
        """
        Update position based on order fill.
        Called when order status changes to FILLED or PARTIALLY_FILLED.
        """
        if not self.trading_table:
            return None

        # Get the order
        order_response = self.trading_table.get_item(
            Key={'user_id': user_id, 'sort_key': f'ORDER#{order_id}'}
        )

        if 'Item' not in order_response:
            logger.warning(f"Order {order_id} not found")
            return None

        order = order_response['Item']

        # Build position key
        broker_id = order.get('broker_id')
        symbol = order.get('symbol')
        today = datetime.now(timezone.utc).date().isoformat()
        position_id = f"{broker_id}#{symbol}#{today}"

        # Get or create position
        position_response = self.trading_table.get_item(
            Key={'user_id': user_id, 'sort_key': f'POSITION#{position_id}'}
        )

        existing_position = position_response.get('Item')

        if existing_position:
            # Update existing position
            transaction_type = order.get('transaction_type')
            if transaction_type == 'BUY':
                new_buy_qty = existing_position.get('buy_quantity', 0) + filled_quantity
                new_buy_value = (
                    existing_position.get('buy_quantity', 0) * float(existing_position.get('average_buy_price', 0)) +
                    filled_quantity * fill_price
                )
                new_avg_buy = new_buy_value / new_buy_qty if new_buy_qty > 0 else 0

                self.trading_table.update_item(
                    Key={'user_id': user_id, 'sort_key': f'POSITION#{position_id}'},
                    UpdateExpression='SET buy_quantity = :bq, average_buy_price = :abp, quantity = :q, updated_at = :ua',
                    ExpressionAttributeValues={
                        ':bq': new_buy_qty,
                        ':abp': Decimal(str(new_avg_buy)),
                        ':q': new_buy_qty - existing_position.get('sell_quantity', 0),
                        ':ua': datetime.now(timezone.utc).isoformat(),
                    }
                )
            else:  # SELL
                new_sell_qty = existing_position.get('sell_quantity', 0) + filled_quantity
                new_sell_value = (
                    existing_position.get('sell_quantity', 0) * float(existing_position.get('average_sell_price', 0)) +
                    filled_quantity * fill_price
                )
                new_avg_sell = new_sell_value / new_sell_qty if new_sell_qty > 0 else 0

                self.trading_table.update_item(
                    Key={'user_id': user_id, 'sort_key': f'POSITION#{position_id}'},
                    UpdateExpression='SET sell_quantity = :sq, average_sell_price = :asp, quantity = :q, updated_at = :ua',
                    ExpressionAttributeValues={
                        ':sq': new_sell_qty,
                        ':asp': Decimal(str(new_avg_sell)),
                        ':q': existing_position.get('buy_quantity', 0) - new_sell_qty,
                        ':ua': datetime.now(timezone.utc).isoformat(),
                    }
                )
        else:
            # Create new position
            transaction_type = order.get('transaction_type')
            position_record = {
                'user_id': user_id,
                'sort_key': f'POSITION#{position_id}',
                'position_id': position_id,
                'symbol': symbol,
                'exchange': order.get('exchange'),
                'broker_id': broker_id,
                'client_id': order.get('client_id'),
                'trading_mode': order.get('trading_mode'),
                'strategy_id': order.get('strategy_id'),
                'basket_id': order.get('basket_id'),
                'product_type': order.get('product_type', 'NRML'),
                'quantity': filled_quantity if transaction_type == 'BUY' else -filled_quantity,
                'buy_quantity': filled_quantity if transaction_type == 'BUY' else 0,
                'sell_quantity': filled_quantity if transaction_type == 'SELL' else 0,
                'average_buy_price': Decimal(str(fill_price)) if transaction_type == 'BUY' else Decimal('0'),
                'average_sell_price': Decimal(str(fill_price)) if transaction_type == 'SELL' else Decimal('0'),
                'last_price': Decimal(str(fill_price)),
                'pnl': Decimal('0'),
                'pnl_percentage': Decimal('0'),
                'status': 'OPEN',
                'opened_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'entity_type': 'POSITION',
            }

            self.trading_table.put_item(Item=position_record)

        return {'position_id': position_id, 'status': 'updated'}


# Singleton instance
_bridge_instance: Optional[TradingExecutionBridge] = None


def get_trading_bridge() -> TradingExecutionBridge:
    """Get or create the singleton trading bridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = TradingExecutionBridge()
    return _bridge_instance
