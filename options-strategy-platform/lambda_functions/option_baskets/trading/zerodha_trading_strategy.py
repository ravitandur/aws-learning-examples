"""
Zerodha Trading Strategy Implementation
Uses Kite Connect API for order placement and management
Documentation: https://kite.trade/docs/connect/v3/
"""

import json
import requests
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from .broker_trading_strategy import (
    BrokerTradingStrategy, OrderParams, OrderResponse, OrderStatusResponse,
    Position, MarginInfo, OrderType, OrderStatus, TradingMode, TransactionType, ProductType
)

# Import shared logger
try:
    from shared_utils.logger import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class ZerodhaOrderType:
    """Zerodha-specific order type mapping"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"
    SL_M = "SL-M"

    @classmethod
    def from_order_type(cls, order_type: OrderType) -> str:
        mapping = {
            OrderType.MARKET: cls.MARKET,
            OrderType.LIMIT: cls.LIMIT,
            OrderType.SL: cls.SL,
            OrderType.SL_M: cls.SL_M,
        }
        return mapping.get(order_type, cls.MARKET)


class ZerodhaProductType:
    """Zerodha product type mapping"""
    MIS = "MIS"
    NRML = "NRML"
    CNC = "CNC"

    @classmethod
    def from_product_type(cls, product_type: ProductType) -> str:
        mapping = {
            ProductType.MIS: cls.MIS,
            ProductType.NRML: cls.NRML,
            ProductType.CNC: cls.CNC,
        }
        return mapping.get(product_type, cls.NRML)


class ZerodhaOrderStatus:
    """Zerodha order status mapping"""
    STATUS_MAP = {
        "COMPLETE": OrderStatus.FILLED,
        "REJECTED": OrderStatus.REJECTED,
        "CANCELLED": OrderStatus.CANCELLED,
        "OPEN": OrderStatus.OPEN,
        "PENDING": OrderStatus.PENDING,
        "TRIGGER PENDING": OrderStatus.OPEN,
        "OPEN PENDING": OrderStatus.PENDING,
        "VALIDATION PENDING": OrderStatus.PENDING,
        "PUT ORDER REQ RECEIVED": OrderStatus.PLACED,
        "MODIFY PENDING": OrderStatus.OPEN,
        "CANCEL PENDING": OrderStatus.OPEN,
        "AMO REQ RECEIVED": OrderStatus.PLACED,
    }

    @classmethod
    def to_order_status(cls, zerodha_status: str) -> OrderStatus:
        return cls.STATUS_MAP.get(zerodha_status.upper(), OrderStatus.PENDING)


class ZerodhaTradingStrategy(BrokerTradingStrategy):
    """
    Zerodha Kite Connect API trading implementation.

    Uses Kite Connect v3 API for:
    - Order placement (regular and variety orders)
    - Order modification and cancellation
    - Position and holdings queries
    - Margin and fund queries
    """

    # Kite Connect API endpoints
    BASE_URL = "https://api.kite.trade"
    ORDERS_ENDPOINT = "/orders"
    POSITIONS_ENDPOINT = "/portfolio/positions"
    HOLDINGS_ENDPOINT = "/portfolio/holdings"
    MARGINS_ENDPOINT = "/user/margins"

    # Order varieties
    VARIETY_REGULAR = "regular"
    VARIETY_AMO = "amo"  # After Market Order

    def __init__(self, trading_mode: TradingMode = TradingMode.LIVE):
        super().__init__("zerodha", trading_mode)
        self._api_key: Optional[str] = None
        self._access_token: Optional[str] = None
        self._session = requests.Session()
        self._internal_orders: Dict[str, str] = {}  # internal_id -> zerodha_order_id

    def connect(self, credentials: Dict[str, Any]) -> bool:
        """
        Connect to Zerodha Kite API.

        Args:
            credentials: Dict containing:
                - api_key: Kite Connect API key
                - access_token: Valid access token (from OAuth flow)
        """
        try:
            self._api_key = credentials.get('api_key')
            self._access_token = credentials.get('access_token')

            if not self._api_key or not self._access_token:
                logger.error("Missing api_key or access_token for Zerodha connection")
                return False

            # Set up session headers
            self._session.headers.update({
                "X-Kite-Version": "3",
                "Authorization": f"token {self._api_key}:{self._access_token}",
                "Content-Type": "application/x-www-form-urlencoded"
            })

            # Verify connection by checking margins
            response = self._make_request("GET", self.MARGINS_ENDPOINT)
            if response and response.get('status') == 'success':
                self._connected = True
                logger.info("Connected to Zerodha Kite API", extra={
                    "api_key": self._api_key[:8] + "***" if self._api_key else None
                })
                return True

            logger.error("Failed to verify Zerodha connection", extra={
                "response": response
            })
            return False

        except Exception as e:
            logger.error(f"Failed to connect to Zerodha: {e}")
            return False

    def disconnect(self) -> bool:
        """Disconnect from Zerodha API."""
        self._connected = False
        self._api_key = None
        self._access_token = None
        self._session.headers.clear()
        logger.info("Disconnected from Zerodha Kite API")
        return True

    def place_order(self, order_params: OrderParams) -> OrderResponse:
        """
        Place order via Kite Connect API.

        API: POST /orders/{variety}
        """
        # Validate order
        is_valid, error = self.validate_order(order_params)
        if not is_valid:
            return OrderResponse(
                success=False,
                message=error,
                status=OrderStatus.REJECTED
            )

        try:
            # Build Zerodha order payload
            payload = {
                "tradingsymbol": order_params.symbol,
                "exchange": order_params.exchange,
                "transaction_type": order_params.transaction_type.value,
                "order_type": ZerodhaOrderType.from_order_type(order_params.order_type),
                "quantity": order_params.quantity,
                "product": ZerodhaProductType.from_product_type(order_params.product_type),
                "validity": order_params.validity,
            }

            # Add price for limit/SL orders
            if order_params.price and order_params.order_type in [OrderType.LIMIT, OrderType.SL]:
                payload["price"] = order_params.price

            # Add trigger price for SL orders
            if order_params.trigger_price and order_params.order_type in [OrderType.SL, OrderType.SL_M]:
                payload["trigger_price"] = order_params.trigger_price

            # Add tag if provided
            if order_params.tag:
                payload["tag"] = order_params.tag[:20]  # Zerodha limits tag to 20 chars

            logger.info("Placing Zerodha order", extra={
                "symbol": order_params.symbol,
                "transaction_type": order_params.transaction_type.value,
                "order_type": order_params.order_type.value,
                "quantity": order_params.quantity
            })

            # Make API request
            variety = self.VARIETY_REGULAR
            response = self._make_request(
                "POST",
                f"{self.ORDERS_ENDPOINT}/{variety}",
                data=payload
            )

            if response and response.get('status') == 'success':
                broker_order_id = response.get('data', {}).get('order_id')

                logger.info("Zerodha order placed successfully", extra={
                    "broker_order_id": broker_order_id,
                    "symbol": order_params.symbol
                })

                return OrderResponse(
                    success=True,
                    order_id=broker_order_id,  # Use broker ID as internal ID
                    broker_order_id=broker_order_id,
                    status=OrderStatus.PLACED,
                    message="Order placed successfully",
                    placed_at=datetime.now(timezone.utc),
                    raw_response=response
                )
            else:
                error_msg = response.get('message', 'Order placement failed') if response else 'No response from Zerodha'
                logger.error("Zerodha order failed", extra={
                    "error": error_msg,
                    "symbol": order_params.symbol
                })

                return OrderResponse(
                    success=False,
                    message=error_msg,
                    status=OrderStatus.REJECTED,
                    raw_response=response
                )

        except Exception as e:
            logger.error(f"Exception placing Zerodha order: {e}")
            return OrderResponse(
                success=False,
                message=str(e),
                status=OrderStatus.REJECTED
            )

    def modify_order(self, order_id: str, modifications: Dict[str, Any]) -> OrderResponse:
        """
        Modify an existing order.

        API: PUT /orders/{variety}/{order_id}
        """
        try:
            payload = {}

            if 'quantity' in modifications:
                payload['quantity'] = modifications['quantity']
            if 'price' in modifications:
                payload['price'] = modifications['price']
            if 'trigger_price' in modifications:
                payload['trigger_price'] = modifications['trigger_price']
            if 'order_type' in modifications:
                payload['order_type'] = ZerodhaOrderType.from_order_type(modifications['order_type'])

            variety = self.VARIETY_REGULAR
            response = self._make_request(
                "PUT",
                f"{self.ORDERS_ENDPOINT}/{variety}/{order_id}",
                data=payload
            )

            if response and response.get('status') == 'success':
                return OrderResponse(
                    success=True,
                    order_id=order_id,
                    broker_order_id=order_id,
                    status=OrderStatus.OPEN,
                    message="Order modified successfully",
                    raw_response=response
                )
            else:
                error_msg = response.get('message', 'Modification failed') if response else 'No response'
                return OrderResponse(
                    success=False,
                    order_id=order_id,
                    message=error_msg,
                    status=OrderStatus.REJECTED,
                    raw_response=response
                )

        except Exception as e:
            logger.error(f"Exception modifying Zerodha order: {e}")
            return OrderResponse(
                success=False,
                order_id=order_id,
                message=str(e),
                status=OrderStatus.REJECTED
            )

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        API: DELETE /orders/{variety}/{order_id}
        """
        try:
            variety = self.VARIETY_REGULAR
            response = self._make_request(
                "DELETE",
                f"{self.ORDERS_ENDPOINT}/{variety}/{order_id}"
            )

            if response and response.get('status') == 'success':
                logger.info("Zerodha order cancelled", extra={"order_id": order_id})
                return True

            logger.warning("Zerodha order cancellation failed", extra={
                "order_id": order_id,
                "response": response
            })
            return False

        except Exception as e:
            logger.error(f"Exception cancelling Zerodha order: {e}")
            return False

    def get_order_status(self, order_id: str) -> OrderStatusResponse:
        """
        Get order status.

        API: GET /orders/{order_id}
        """
        try:
            response = self._make_request("GET", f"{self.ORDERS_ENDPOINT}/{order_id}")

            if response and response.get('status') == 'success':
                orders = response.get('data', [])
                if orders:
                    # Get latest order update
                    order = orders[-1] if isinstance(orders, list) else orders

                    return OrderStatusResponse(
                        order_id=order_id,
                        broker_order_id=order.get('order_id'),
                        status=ZerodhaOrderStatus.to_order_status(order.get('status', '')),
                        filled_quantity=order.get('filled_quantity', 0),
                        pending_quantity=order.get('pending_quantity', 0),
                        average_price=order.get('average_price', 0.0),
                        last_price=order.get('price', 0.0),
                        rejection_reason=order.get('status_message'),
                        updated_at=self._parse_timestamp(order.get('order_timestamp')),
                        raw_response=order
                    )

            return OrderStatusResponse(
                order_id=order_id,
                broker_order_id=order_id,
                status=OrderStatus.PENDING,
                rejection_reason="Unable to fetch order status"
            )

        except Exception as e:
            logger.error(f"Exception getting Zerodha order status: {e}")
            return OrderStatusResponse(
                order_id=order_id,
                broker_order_id=order_id,
                status=OrderStatus.PENDING,
                rejection_reason=str(e)
            )

    def get_orders(self, filters: Optional[Dict[str, Any]] = None) -> List[OrderStatusResponse]:
        """
        Get all orders for the day.

        API: GET /orders
        """
        try:
            response = self._make_request("GET", self.ORDERS_ENDPOINT)

            if response and response.get('status') == 'success':
                orders = response.get('data', [])
                result = []

                for order in orders:
                    # Apply filters
                    if filters:
                        if 'status' in filters:
                            order_status = ZerodhaOrderStatus.to_order_status(order.get('status', ''))
                            if order_status.value != filters['status']:
                                continue
                        if 'symbol' in filters and order.get('tradingsymbol') != filters['symbol']:
                            continue

                    result.append(OrderStatusResponse(
                        order_id=order.get('order_id'),
                        broker_order_id=order.get('order_id'),
                        status=ZerodhaOrderStatus.to_order_status(order.get('status', '')),
                        filled_quantity=order.get('filled_quantity', 0),
                        pending_quantity=order.get('pending_quantity', 0),
                        average_price=order.get('average_price', 0.0),
                        last_price=order.get('price', 0.0),
                        rejection_reason=order.get('status_message'),
                        updated_at=self._parse_timestamp(order.get('order_timestamp')),
                        raw_response=order
                    ))

                return result

            return []

        except Exception as e:
            logger.error(f"Exception getting Zerodha orders: {e}")
            return []

    def get_positions(self) -> List[Position]:
        """
        Get current positions.

        API: GET /portfolio/positions
        """
        try:
            response = self._make_request("GET", self.POSITIONS_ENDPOINT)

            if response and response.get('status') == 'success':
                data = response.get('data', {})
                net_positions = data.get('net', [])
                positions = []

                for pos in net_positions:
                    quantity = pos.get('quantity', 0)
                    if quantity == 0:
                        continue  # Skip zero positions

                    position = Position(
                        symbol=pos.get('tradingsymbol'),
                        exchange=pos.get('exchange'),
                        product_type=self._map_product_type(pos.get('product', '')),
                        quantity=quantity,
                        buy_quantity=pos.get('buy_quantity', 0),
                        sell_quantity=pos.get('sell_quantity', 0),
                        average_buy_price=pos.get('buy_price', 0.0),
                        average_sell_price=pos.get('sell_price', 0.0),
                        last_price=pos.get('last_price', 0.0),
                        pnl=pos.get('pnl', 0.0),
                        value=pos.get('value', 0.0),
                        day_change=pos.get('day_m2m', 0.0),
                        trading_mode=self.trading_mode,
                        broker_id="zerodha"
                    )

                    # Calculate P&L percentage
                    if position.value > 0:
                        position.pnl_percentage = (position.pnl / position.value) * 100

                    positions.append(position)

                return positions

            return []

        except Exception as e:
            logger.error(f"Exception getting Zerodha positions: {e}")
            return []

    def get_margins(self) -> MarginInfo:
        """
        Get margin/fund information.

        API: GET /user/margins
        """
        try:
            response = self._make_request("GET", self.MARGINS_ENDPOINT)

            if response and response.get('status') == 'success':
                data = response.get('data', {})
                # Use equity segment by default
                equity = data.get('equity', {})

                return MarginInfo(
                    available_margin=equity.get('available', {}).get('live_balance', 0.0),
                    used_margin=equity.get('utilised', {}).get('debits', 0.0),
                    total_balance=equity.get('net', 0.0),
                    payin_amount=equity.get('available', {}).get('intraday_payin', 0.0),
                    day_pnl=equity.get('available', {}).get('live_balance', 0.0) - equity.get('net', 0.0)
                )

            return MarginInfo(
                available_margin=0.0,
                used_margin=0.0,
                total_balance=0.0
            )

        except Exception as e:
            logger.error(f"Exception getting Zerodha margins: {e}")
            return MarginInfo(
                available_margin=0.0,
                used_margin=0.0,
                total_balance=0.0
            )

    # Private helper methods

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make HTTP request to Kite API."""
        if not self._connected and endpoint != self.MARGINS_ENDPOINT:
            logger.error("Not connected to Zerodha API")
            return None

        try:
            url = f"{self.BASE_URL}{endpoint}"

            if method == "GET":
                response = self._session.get(url, timeout=30)
            elif method == "POST":
                response = self._session.post(url, data=data, timeout=30)
            elif method == "PUT":
                response = self._session.put(url, data=data, timeout=30)
            elif method == "DELETE":
                response = self._session.delete(url, timeout=30)
            else:
                return None

            return response.json()

        except requests.exceptions.Timeout:
            logger.error(f"Timeout calling Zerodha API: {endpoint}")
            return {"status": "error", "message": "Request timeout"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error calling Zerodha API: {e}")
            return {"status": "error", "message": str(e)}
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from Zerodha API")
            return {"status": "error", "message": "Invalid JSON response"}

    def _map_product_type(self, zerodha_product: str) -> ProductType:
        """Map Zerodha product type to internal ProductType."""
        mapping = {
            "MIS": ProductType.MIS,
            "NRML": ProductType.NRML,
            "CNC": ProductType.CNC,
        }
        return mapping.get(zerodha_product.upper(), ProductType.NRML)

    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse Zerodha timestamp string to datetime."""
        if not timestamp_str:
            return None
        try:
            # Zerodha uses format: "2024-01-15 09:30:00"
            return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            return None
