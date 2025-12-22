"""
Broker Trading Strategy Interface
Abstract base class for all broker trading implementations (Zerodha, Zebu, Paper Trading)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class OrderType(Enum):
    """Order types supported by brokers"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"          # Stop Loss Limit
    SL_M = "SL-M"      # Stop Loss Market


class TransactionType(Enum):
    """Buy or Sell transaction"""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    """Order lifecycle states"""
    PENDING = "PENDING"           # Order created, not yet placed
    PLACED = "PLACED"             # Order sent to broker
    OPEN = "OPEN"                 # Order accepted, waiting for fill
    FILLED = "FILLED"             # Order completely filled
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"       # Order cancelled by user/system
    REJECTED = "REJECTED"         # Order rejected by broker
    EXPIRED = "EXPIRED"           # Order expired (GTD orders)


class TradingMode(Enum):
    """Trading mode - Paper or Live"""
    PAPER = "PAPER"
    LIVE = "LIVE"


class ProductType(Enum):
    """Product type for Indian markets"""
    MIS = "MIS"       # Margin Intraday Square-off
    NRML = "NRML"     # Normal (for F&O overnight positions)
    CNC = "CNC"       # Cash and Carry (delivery)


@dataclass
class OrderParams:
    """Parameters for placing an order"""
    symbol: str                           # Trading symbol (e.g., "NIFTY24DEC19500CE")
    exchange: str                         # Exchange (NSE, NFO, BSE, BFO)
    transaction_type: TransactionType     # BUY or SELL
    order_type: OrderType                 # MARKET, LIMIT, SL, SL-M
    quantity: int                         # Number of units
    price: Optional[float] = None         # Limit price (required for LIMIT, SL)
    trigger_price: Optional[float] = None # Trigger price (required for SL, SL-M)
    product_type: ProductType = ProductType.NRML
    validity: str = "DAY"                 # DAY, IOC, GTT
    tag: Optional[str] = None             # Custom tag for tracking

    # Internal tracking
    strategy_id: Optional[str] = None
    basket_id: Optional[str] = None
    leg_id: Optional[str] = None
    execution_type: Optional[str] = None  # ENTRY or EXIT


@dataclass
class OrderResponse:
    """Response from order placement"""
    success: bool
    order_id: Optional[str] = None        # Internal order ID
    broker_order_id: Optional[str] = None # Broker's order ID
    status: OrderStatus = OrderStatus.PENDING
    message: Optional[str] = None
    placed_at: Optional[datetime] = None
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class OrderStatusResponse:
    """Order status response"""
    order_id: str
    broker_order_id: Optional[str]
    status: OrderStatus
    filled_quantity: int = 0
    pending_quantity: int = 0
    average_price: float = 0.0
    last_price: float = 0.0
    rejection_reason: Optional[str] = None
    updated_at: Optional[datetime] = None
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class Position:
    """Trading position data"""
    symbol: str
    exchange: str
    product_type: ProductType
    quantity: int                          # Net quantity (positive=long, negative=short)
    buy_quantity: int = 0
    sell_quantity: int = 0
    average_buy_price: float = 0.0
    average_sell_price: float = 0.0
    last_price: float = 0.0
    pnl: float = 0.0
    pnl_percentage: float = 0.0
    day_change: float = 0.0
    day_change_percentage: float = 0.0
    value: float = 0.0                     # Current position value

    # Internal tracking
    position_id: Optional[str] = None
    strategy_id: Optional[str] = None
    basket_id: Optional[str] = None
    trading_mode: TradingMode = TradingMode.PAPER
    broker_id: Optional[str] = None
    client_id: Optional[str] = None


@dataclass
class MarginInfo:
    """Margin/fund information"""
    available_margin: float
    used_margin: float
    total_balance: float
    payin_amount: float = 0.0
    payout_amount: float = 0.0
    day_pnl: float = 0.0


class BrokerTradingStrategy(ABC):
    """
    Abstract base class for broker trading implementations.
    All broker-specific strategies must implement these methods.
    """

    def __init__(self, broker_name: str, trading_mode: TradingMode = TradingMode.PAPER):
        self.broker_name = broker_name
        self.trading_mode = trading_mode
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    @abstractmethod
    def connect(self, credentials: Dict[str, Any]) -> bool:
        """
        Establish connection with broker API.

        Args:
            credentials: Broker-specific credentials (api_key, access_token, etc.)

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnect from broker API.

        Returns:
            True if disconnection successful
        """
        pass

    @abstractmethod
    def place_order(self, order_params: OrderParams) -> OrderResponse:
        """
        Place an order with the broker.

        Args:
            order_params: Order parameters

        Returns:
            OrderResponse with order details and status
        """
        pass

    @abstractmethod
    def modify_order(self, order_id: str, modifications: Dict[str, Any]) -> OrderResponse:
        """
        Modify an existing order.

        Args:
            order_id: The order ID to modify
            modifications: Dict with fields to modify (price, quantity, etc.)

        Returns:
            OrderResponse with updated order details
        """
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: The order ID to cancel

        Returns:
            True if cancellation successful
        """
        pass

    @abstractmethod
    def get_order_status(self, order_id: str) -> OrderStatusResponse:
        """
        Get current status of an order.

        Args:
            order_id: The order ID to check

        Returns:
            OrderStatusResponse with current status
        """
        pass

    @abstractmethod
    def get_orders(self, filters: Optional[Dict[str, Any]] = None) -> List[OrderStatusResponse]:
        """
        Get list of orders for the day.

        Args:
            filters: Optional filters (status, symbol, etc.)

        Returns:
            List of order status responses
        """
        pass

    @abstractmethod
    def get_positions(self) -> List[Position]:
        """
        Get current positions.

        Returns:
            List of Position objects
        """
        pass

    @abstractmethod
    def get_margins(self) -> MarginInfo:
        """
        Get margin/fund information.

        Returns:
            MarginInfo with available funds
        """
        pass

    def validate_order(self, order_params: OrderParams) -> tuple[bool, Optional[str]]:
        """
        Validate order parameters before placing.

        Args:
            order_params: Order parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Basic validation
        if not order_params.symbol:
            return False, "Symbol is required"

        if not order_params.exchange:
            return False, "Exchange is required"

        if order_params.quantity <= 0:
            return False, "Quantity must be positive"

        if order_params.order_type in [OrderType.LIMIT, OrderType.SL]:
            if order_params.price is None or order_params.price <= 0:
                return False, f"Price is required for {order_params.order_type.value} orders"

        if order_params.order_type in [OrderType.SL, OrderType.SL_M]:
            if order_params.trigger_price is None or order_params.trigger_price <= 0:
                return False, f"Trigger price is required for {order_params.order_type.value} orders"

        return True, None

    def calculate_order_value(self, order_params: OrderParams, current_price: float) -> float:
        """
        Calculate approximate order value for margin requirements.

        Args:
            order_params: Order parameters
            current_price: Current market price

        Returns:
            Estimated order value
        """
        price = order_params.price or current_price
        return price * order_params.quantity
