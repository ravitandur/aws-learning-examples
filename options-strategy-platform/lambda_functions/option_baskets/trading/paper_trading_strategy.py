"""
Paper Trading Strategy Implementation
Simulates order placement and execution for testing without real money
"""

import uuid
import random
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from .broker_trading_strategy import (
    BrokerTradingStrategy, OrderParams, OrderResponse, OrderStatusResponse,
    Position, MarginInfo, OrderType, OrderStatus, TradingMode, TransactionType
)

# Import shared logger
try:
    from shared_utils.logger import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class PaperTradingStrategy(BrokerTradingStrategy):
    """
    Paper trading implementation for simulated order execution.

    Features:
    - Realistic order fills with configurable slippage
    - Market orders fill immediately at current price ± slippage
    - Limit orders fill when price crosses
    - Stop loss orders trigger at trigger_price
    - Position tracking and P&L calculation
    """

    # Default configuration
    DEFAULT_SLIPPAGE_BPS = 5  # 0.05% slippage
    DEFAULT_INITIAL_BALANCE = 1000000.0  # 10 Lakh starting balance

    def __init__(self, trading_mode: TradingMode = TradingMode.PAPER):
        super().__init__("PAPER", trading_mode)

        # Paper trading state
        self._orders: Dict[str, Dict[str, Any]] = {}
        self._positions: Dict[str, Position] = {}
        self._balance = self.DEFAULT_INITIAL_BALANCE
        self._used_margin = 0.0
        self._slippage_bps = self.DEFAULT_SLIPPAGE_BPS

        # Market data simulation (in real impl, would fetch from market data service)
        self._simulated_prices: Dict[str, float] = {}

    def connect(self, credentials: Dict[str, Any]) -> bool:
        """
        Initialize paper trading session.

        Args:
            credentials: Configuration dict with optional:
                - initial_balance: Starting paper balance
                - slippage_bps: Slippage in basis points
        """
        try:
            self._balance = credentials.get('initial_balance', self.DEFAULT_INITIAL_BALANCE)
            self._slippage_bps = credentials.get('slippage_bps', self.DEFAULT_SLIPPAGE_BPS)
            self._connected = True

            logger.info("Paper trading session initialized", extra={
                "initial_balance": self._balance,
                "slippage_bps": self._slippage_bps
            })

            return True
        except Exception as e:
            logger.error(f"Failed to initialize paper trading: {e}")
            return False

    def disconnect(self) -> bool:
        """End paper trading session."""
        self._connected = False
        logger.info("Paper trading session ended")
        return True

    def place_order(self, order_params: OrderParams) -> OrderResponse:
        """
        Place a paper order with simulated execution.

        Market orders: Fill immediately with slippage
        Limit orders: Hold until price crosses
        SL orders: Trigger when price hits trigger_price
        """
        # Validate order
        is_valid, error = self.validate_order(order_params)
        if not is_valid:
            return OrderResponse(
                success=False,
                message=error,
                status=OrderStatus.REJECTED
            )

        # Generate order ID
        order_id = f"PAPER_{uuid.uuid4().hex[:12].upper()}"
        broker_order_id = f"P{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
        placed_at = datetime.now(timezone.utc)

        # Get simulated current price
        current_price = self._get_simulated_price(order_params.symbol)

        # Determine fill behavior based on order type
        if order_params.order_type == OrderType.MARKET:
            # Market order: Fill immediately with slippage
            fill_price = self._apply_slippage(
                current_price,
                order_params.transaction_type
            )
            status = OrderStatus.FILLED
            filled_quantity = order_params.quantity
        elif order_params.order_type == OrderType.LIMIT:
            # Limit order: Check if price is favorable, else hold as open
            if self._is_limit_fillable(order_params, current_price):
                fill_price = order_params.price
                status = OrderStatus.FILLED
                filled_quantity = order_params.quantity
            else:
                fill_price = 0.0
                status = OrderStatus.OPEN
                filled_quantity = 0
        elif order_params.order_type in [OrderType.SL, OrderType.SL_M]:
            # Stop loss: Hold until trigger price is hit
            fill_price = 0.0
            status = OrderStatus.OPEN
            filled_quantity = 0
        else:
            fill_price = 0.0
            status = OrderStatus.OPEN
            filled_quantity = 0

        # Store order
        order_data = {
            "order_id": order_id,
            "broker_order_id": broker_order_id,
            "params": order_params,
            "status": status,
            "filled_quantity": filled_quantity,
            "average_price": fill_price if filled_quantity > 0 else 0.0,
            "placed_at": placed_at,
            "updated_at": placed_at,
            "current_price": current_price,
        }
        self._orders[order_id] = order_data

        # Update position if filled
        if status == OrderStatus.FILLED:
            self._update_position(order_params, fill_price, filled_quantity)

        logger.info("Paper order placed", extra={
            "order_id": order_id,
            "broker_order_id": broker_order_id,
            "symbol": order_params.symbol,
            "transaction_type": order_params.transaction_type.value,
            "order_type": order_params.order_type.value,
            "quantity": order_params.quantity,
            "status": status.value,
            "fill_price": fill_price
        })

        return OrderResponse(
            success=True,
            order_id=order_id,
            broker_order_id=broker_order_id,
            status=status,
            message=f"Paper order {'filled' if status == OrderStatus.FILLED else 'placed'}",
            placed_at=placed_at,
            raw_response=order_data
        )

    def modify_order(self, order_id: str, modifications: Dict[str, Any]) -> OrderResponse:
        """Modify a paper order."""
        if order_id not in self._orders:
            return OrderResponse(
                success=False,
                message=f"Order {order_id} not found",
                status=OrderStatus.REJECTED
            )

        order = self._orders[order_id]

        # Can only modify open orders
        if order['status'] != OrderStatus.OPEN:
            return OrderResponse(
                success=False,
                order_id=order_id,
                message=f"Cannot modify order in {order['status'].value} status",
                status=order['status']
            )

        # Apply modifications
        params = order['params']
        if 'price' in modifications:
            params.price = modifications['price']
        if 'quantity' in modifications:
            params.quantity = modifications['quantity']
        if 'trigger_price' in modifications:
            params.trigger_price = modifications['trigger_price']

        order['updated_at'] = datetime.now(timezone.utc)

        logger.info("Paper order modified", extra={
            "order_id": order_id,
            "modifications": modifications
        })

        return OrderResponse(
            success=True,
            order_id=order_id,
            broker_order_id=order['broker_order_id'],
            status=order['status'],
            message="Order modified",
            raw_response=order
        )

    def cancel_order(self, order_id: str) -> bool:
        """Cancel a paper order."""
        if order_id not in self._orders:
            logger.warning(f"Order {order_id} not found for cancellation")
            return False

        order = self._orders[order_id]

        # Can only cancel open/pending orders
        if order['status'] not in [OrderStatus.OPEN, OrderStatus.PENDING]:
            logger.warning(f"Cannot cancel order in {order['status'].value} status")
            return False

        order['status'] = OrderStatus.CANCELLED
        order['updated_at'] = datetime.now(timezone.utc)

        logger.info("Paper order cancelled", extra={"order_id": order_id})
        return True

    def get_order_status(self, order_id: str) -> OrderStatusResponse:
        """Get status of a paper order."""
        if order_id not in self._orders:
            return OrderStatusResponse(
                order_id=order_id,
                broker_order_id=None,
                status=OrderStatus.REJECTED,
                rejection_reason="Order not found"
            )

        order = self._orders[order_id]
        params = order['params']

        # Check if open SL orders should trigger
        if order['status'] == OrderStatus.OPEN:
            self._check_sl_trigger(order_id)

        return OrderStatusResponse(
            order_id=order_id,
            broker_order_id=order['broker_order_id'],
            status=order['status'],
            filled_quantity=order['filled_quantity'],
            pending_quantity=params.quantity - order['filled_quantity'],
            average_price=order['average_price'],
            last_price=order.get('current_price', 0.0),
            updated_at=order['updated_at'],
            raw_response=order
        )

    def get_orders(self, filters: Optional[Dict[str, Any]] = None) -> List[OrderStatusResponse]:
        """Get all paper orders with optional filtering."""
        orders = []

        for order_id, order in self._orders.items():
            # Apply filters
            if filters:
                if 'status' in filters and order['status'].value != filters['status']:
                    continue
                if 'symbol' in filters and order['params'].symbol != filters['symbol']:
                    continue

            orders.append(self.get_order_status(order_id))

        return orders

    def get_positions(self) -> List[Position]:
        """Get all paper positions."""
        positions = []

        for symbol, position in self._positions.items():
            # Update P&L with simulated current price
            current_price = self._get_simulated_price(symbol)
            position.last_price = current_price

            if position.quantity != 0:
                if position.quantity > 0:  # Long position
                    position.pnl = (current_price - position.average_buy_price) * position.quantity
                else:  # Short position
                    position.pnl = (position.average_sell_price - current_price) * abs(position.quantity)

                position.value = abs(current_price * position.quantity)
                position.pnl_percentage = (position.pnl / position.value * 100) if position.value > 0 else 0.0

            positions.append(position)

        return positions

    def get_margins(self) -> MarginInfo:
        """Get paper trading margin info."""
        # Calculate P&L from positions
        day_pnl = sum(pos.pnl for pos in self._positions.values())

        return MarginInfo(
            available_margin=self._balance - self._used_margin,
            used_margin=self._used_margin,
            total_balance=self._balance + day_pnl,
            day_pnl=day_pnl
        )

    # Private helper methods

    def _get_simulated_price(self, symbol: str) -> float:
        """
        Get simulated price for a symbol.
        In real implementation, would fetch from market data service.
        """
        if symbol not in self._simulated_prices:
            # Generate a realistic price based on symbol type
            if 'NIFTY' in symbol.upper():
                base_price = 100.0 + random.uniform(-20, 50)  # Options premium
            elif 'BANKNIFTY' in symbol.upper():
                base_price = 150.0 + random.uniform(-30, 80)
            else:
                base_price = 50.0 + random.uniform(-10, 30)

            self._simulated_prices[symbol] = base_price

        # Add small random movement
        current = self._simulated_prices[symbol]
        movement = current * random.uniform(-0.005, 0.005)  # ±0.5% movement
        self._simulated_prices[symbol] = max(0.05, current + movement)

        return self._simulated_prices[symbol]

    def set_simulated_price(self, symbol: str, price: float):
        """Set a specific price for testing."""
        self._simulated_prices[symbol] = price

    def _apply_slippage(self, price: float, transaction_type: TransactionType) -> float:
        """Apply slippage to market orders."""
        slippage_factor = self._slippage_bps / 10000

        if transaction_type == TransactionType.BUY:
            # Buy orders get filled slightly higher
            return price * (1 + slippage_factor)
        else:
            # Sell orders get filled slightly lower
            return price * (1 - slippage_factor)

    def _is_limit_fillable(self, params: OrderParams, current_price: float) -> bool:
        """Check if limit order can be filled at current price."""
        if params.transaction_type == TransactionType.BUY:
            # Buy limit fills if market price <= limit price
            return current_price <= params.price
        else:
            # Sell limit fills if market price >= limit price
            return current_price >= params.price

    def _check_sl_trigger(self, order_id: str):
        """Check if stop loss order should trigger."""
        order = self._orders[order_id]
        params = order['params']

        if params.order_type not in [OrderType.SL, OrderType.SL_M]:
            return

        current_price = self._get_simulated_price(params.symbol)

        # Check trigger condition
        triggered = False
        if params.transaction_type == TransactionType.SELL:
            # Sell SL triggers when price falls to trigger price
            triggered = current_price <= params.trigger_price
        else:
            # Buy SL triggers when price rises to trigger price
            triggered = current_price >= params.trigger_price

        if triggered:
            # Execute the stop loss
            if params.order_type == OrderType.SL_M:
                # SL-M fills at market with slippage
                fill_price = self._apply_slippage(current_price, params.transaction_type)
            else:
                # SL fills at limit price or better
                fill_price = params.price

            order['status'] = OrderStatus.FILLED
            order['filled_quantity'] = params.quantity
            order['average_price'] = fill_price
            order['updated_at'] = datetime.now(timezone.utc)

            # Update position
            self._update_position(params, fill_price, params.quantity)

            logger.info("Paper SL order triggered", extra={
                "order_id": order_id,
                "trigger_price": params.trigger_price,
                "fill_price": fill_price
            })

    def _update_position(self, params: OrderParams, fill_price: float, quantity: int):
        """Update position after order fill."""
        symbol = params.symbol

        if symbol not in self._positions:
            self._positions[symbol] = Position(
                symbol=symbol,
                exchange=params.exchange,
                product_type=params.product_type,
                quantity=0,
                position_id=f"POS_{uuid.uuid4().hex[:8].upper()}",
                strategy_id=params.strategy_id,
                basket_id=params.basket_id,
                trading_mode=self.trading_mode
            )

        pos = self._positions[symbol]

        if params.transaction_type == TransactionType.BUY:
            # Add to buy side
            total_buy_value = (pos.average_buy_price * pos.buy_quantity) + (fill_price * quantity)
            pos.buy_quantity += quantity
            pos.average_buy_price = total_buy_value / pos.buy_quantity if pos.buy_quantity > 0 else 0
            pos.quantity += quantity
        else:
            # Add to sell side
            total_sell_value = (pos.average_sell_price * pos.sell_quantity) + (fill_price * quantity)
            pos.sell_quantity += quantity
            pos.average_sell_price = total_sell_value / pos.sell_quantity if pos.sell_quantity > 0 else 0
            pos.quantity -= quantity

        # Update margin usage (simplified)
        self._used_margin += fill_price * quantity * 0.1  # 10% margin requirement

        logger.info("Paper position updated", extra={
            "symbol": symbol,
            "net_quantity": pos.quantity,
            "buy_qty": pos.buy_quantity,
            "sell_qty": pos.sell_quantity,
            "avg_buy": pos.average_buy_price,
            "avg_sell": pos.average_sell_price
        })

    def reset(self):
        """Reset paper trading state."""
        self._orders.clear()
        self._positions.clear()
        self._balance = self.DEFAULT_INITIAL_BALANCE
        self._used_margin = 0.0
        self._simulated_prices.clear()
        logger.info("Paper trading state reset")
