"""
Zebu Trading Strategy Implementation
Uses MYNT API (NorenWClientAPI) for order placement and management
Documentation: https://api.zebuetrade.com/
Reference: myntapi Python library
"""

import json
import hashlib
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


class ZebuOrderType:
    """Zebu-specific order type mapping"""
    MARKET = "MKT"
    LIMIT = "LMT"
    SL = "SL-LMT"
    SL_M = "SL-MKT"

    @classmethod
    def from_order_type(cls, order_type: OrderType) -> str:
        mapping = {
            OrderType.MARKET: cls.MARKET,
            OrderType.LIMIT: cls.LIMIT,
            OrderType.SL: cls.SL,
            OrderType.SL_M: cls.SL_M,
        }
        return mapping.get(order_type, cls.MARKET)


class ZebuProductType:
    """Zebu product type mapping"""
    MIS = "I"  # Intraday
    NRML = "M"  # Normal/Margin
    CNC = "C"  # Cash and Carry

    @classmethod
    def from_product_type(cls, product_type: ProductType) -> str:
        mapping = {
            ProductType.MIS: cls.MIS,
            ProductType.NRML: cls.NRML,
            ProductType.CNC: cls.CNC,
        }
        return mapping.get(product_type, cls.NRML)


class ZebuOrderStatus:
    """Zebu order status mapping"""
    STATUS_MAP = {
        "COMPLETE": OrderStatus.FILLED,
        "REJECTED": OrderStatus.REJECTED,
        "CANCELLED": OrderStatus.CANCELLED,
        "OPEN": OrderStatus.OPEN,
        "PENDING": OrderStatus.PENDING,
        "TRIGGER_PENDING": OrderStatus.OPEN,
        "OPEN PENDING": OrderStatus.PENDING,
        "AFTER MARKET ORDER REQ RECEIVED": OrderStatus.PLACED,
    }

    @classmethod
    def to_order_status(cls, zebu_status: str) -> OrderStatus:
        return cls.STATUS_MAP.get(zebu_status.upper(), OrderStatus.PENDING)


class ZebuTradingStrategy(BrokerTradingStrategy):
    """
    Zebu MYNT API trading implementation.

    Uses NorenWClientAPI for:
    - Order placement (PlaceOrder)
    - Order modification (ModifyOrder)
    - Order cancellation (CancelOrder)
    - Position queries (PositionBook)
    - Margin queries (Limits)
    """

    # MYNT API endpoints
    BASE_URL = "https://go.mynt.in/NorenWClientAPI"
    PLACE_ORDER_ENDPOINT = "/PlaceOrder"
    MODIFY_ORDER_ENDPOINT = "/ModifyOrder"
    CANCEL_ORDER_ENDPOINT = "/CancelOrder"
    ORDER_BOOK_ENDPOINT = "/OrderBook"
    POSITION_BOOK_ENDPOINT = "/PositionBook"
    LIMITS_ENDPOINT = "/Limits"

    def __init__(self, trading_mode: TradingMode = TradingMode.LIVE):
        super().__init__("zebu", trading_mode)
        self._user_id: Optional[str] = None
        self._access_token: Optional[str] = None
        self._session = requests.Session()

    def connect(self, credentials: Dict[str, Any]) -> bool:
        """
        Connect to Zebu MYNT API.

        Args:
            credentials: Dict containing:
                - user_id: Zebu user ID (uid)
                - access_token: Valid access token (susertoken from OAuth)
        """
        try:
            self._user_id = credentials.get('user_id')
            self._access_token = credentials.get('access_token')

            if not self._user_id or not self._access_token:
                logger.error("Missing user_id or access_token for Zebu connection")
                return False

            # Verify connection by checking limits
            response = self._make_request(self.LIMITS_ENDPOINT, {})
            if response and response.get('stat') == 'Ok':
                self._connected = True
                logger.info("Connected to Zebu MYNT API", extra={
                    "user_id": self._user_id
                })
                return True

            logger.error("Failed to verify Zebu connection", extra={
                "response": response
            })
            return False

        except Exception as e:
            logger.error(f"Failed to connect to Zebu: {e}")
            return False

    def disconnect(self) -> bool:
        """Disconnect from Zebu API."""
        self._connected = False
        self._user_id = None
        self._access_token = None
        logger.info("Disconnected from Zebu MYNT API")
        return True

    def place_order(self, order_params: OrderParams) -> OrderResponse:
        """
        Place order via MYNT PlaceOrder API.

        API: POST /NorenWClientAPI/PlaceOrder
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
            # Build Zebu order payload
            payload = {
                "uid": self._user_id,
                "actid": self._user_id,  # Account ID same as user ID
                "exch": self._map_exchange(order_params.exchange),
                "tsym": order_params.symbol,
                "qty": str(order_params.quantity),
                "prc": str(order_params.price or 0),
                "trgprc": str(order_params.trigger_price or 0),
                "prd": ZebuProductType.from_product_type(order_params.product_type),
                "trantype": "B" if order_params.transaction_type == TransactionType.BUY else "S",
                "prctyp": ZebuOrderType.from_order_type(order_params.order_type),
                "ret": "DAY",  # Retention type
            }

            # Add remarks/tag if provided
            if order_params.tag:
                payload["remarks"] = order_params.tag[:50]

            logger.info("Placing Zebu order", extra={
                "symbol": order_params.symbol,
                "transaction_type": order_params.transaction_type.value,
                "order_type": order_params.order_type.value,
                "quantity": order_params.quantity
            })

            # Make API request
            response = self._make_request(self.PLACE_ORDER_ENDPOINT, payload)

            if response and response.get('stat') == 'Ok':
                broker_order_id = response.get('norenordno')

                logger.info("Zebu order placed successfully", extra={
                    "broker_order_id": broker_order_id,
                    "symbol": order_params.symbol
                })

                return OrderResponse(
                    success=True,
                    order_id=broker_order_id,
                    broker_order_id=broker_order_id,
                    status=OrderStatus.PLACED,
                    message="Order placed successfully",
                    placed_at=datetime.now(timezone.utc),
                    raw_response=response
                )
            else:
                error_msg = response.get('emsg', 'Order placement failed') if response else 'No response from Zebu'
                logger.error("Zebu order failed", extra={
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
            logger.error(f"Exception placing Zebu order: {e}")
            return OrderResponse(
                success=False,
                message=str(e),
                status=OrderStatus.REJECTED
            )

    def modify_order(self, order_id: str, modifications: Dict[str, Any]) -> OrderResponse:
        """
        Modify an existing order.

        API: POST /NorenWClientAPI/ModifyOrder
        """
        try:
            payload = {
                "uid": self._user_id,
                "norenordno": order_id,
            }

            if 'quantity' in modifications:
                payload['qty'] = str(modifications['quantity'])
            if 'price' in modifications:
                payload['prc'] = str(modifications['price'])
            if 'trigger_price' in modifications:
                payload['trgprc'] = str(modifications['trigger_price'])
            if 'order_type' in modifications:
                payload['prctyp'] = ZebuOrderType.from_order_type(modifications['order_type'])

            response = self._make_request(self.MODIFY_ORDER_ENDPOINT, payload)

            if response and response.get('stat') == 'Ok':
                return OrderResponse(
                    success=True,
                    order_id=order_id,
                    broker_order_id=order_id,
                    status=OrderStatus.OPEN,
                    message="Order modified successfully",
                    raw_response=response
                )
            else:
                error_msg = response.get('emsg', 'Modification failed') if response else 'No response'
                return OrderResponse(
                    success=False,
                    order_id=order_id,
                    message=error_msg,
                    status=OrderStatus.REJECTED,
                    raw_response=response
                )

        except Exception as e:
            logger.error(f"Exception modifying Zebu order: {e}")
            return OrderResponse(
                success=False,
                order_id=order_id,
                message=str(e),
                status=OrderStatus.REJECTED
            )

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        API: POST /NorenWClientAPI/CancelOrder
        """
        try:
            payload = {
                "uid": self._user_id,
                "norenordno": order_id,
            }

            response = self._make_request(self.CANCEL_ORDER_ENDPOINT, payload)

            if response and response.get('stat') == 'Ok':
                logger.info("Zebu order cancelled", extra={"order_id": order_id})
                return True

            logger.warning("Zebu order cancellation failed", extra={
                "order_id": order_id,
                "response": response
            })
            return False

        except Exception as e:
            logger.error(f"Exception cancelling Zebu order: {e}")
            return False

    def get_order_status(self, order_id: str) -> OrderStatusResponse:
        """
        Get order status by fetching order book and finding the order.

        API: POST /NorenWClientAPI/OrderBook
        """
        try:
            orders = self.get_orders()
            for order in orders:
                if order.broker_order_id == order_id:
                    return order

            return OrderStatusResponse(
                order_id=order_id,
                broker_order_id=order_id,
                status=OrderStatus.PENDING,
                rejection_reason="Order not found"
            )

        except Exception as e:
            logger.error(f"Exception getting Zebu order status: {e}")
            return OrderStatusResponse(
                order_id=order_id,
                broker_order_id=order_id,
                status=OrderStatus.PENDING,
                rejection_reason=str(e)
            )

    def get_orders(self, filters: Optional[Dict[str, Any]] = None) -> List[OrderStatusResponse]:
        """
        Get all orders for the day.

        API: POST /NorenWClientAPI/OrderBook
        """
        try:
            payload = {
                "uid": self._user_id,
            }

            response = self._make_request(self.ORDER_BOOK_ENDPOINT, payload)

            if response and response.get('stat') == 'Ok':
                orders = response if isinstance(response, list) else [response]
                # If single order, it may not be in a list
                if not isinstance(response, list) and 'norenordno' in response:
                    orders = [response]
                elif isinstance(response, list):
                    orders = response
                else:
                    # Response might have orders in a nested structure
                    orders = []

                result = []

                for order in orders:
                    if not isinstance(order, dict) or 'norenordno' not in order:
                        continue

                    # Apply filters
                    if filters:
                        if 'status' in filters:
                            order_status = ZebuOrderStatus.to_order_status(order.get('status', ''))
                            if order_status.value != filters['status']:
                                continue
                        if 'symbol' in filters and order.get('tsym') != filters['symbol']:
                            continue

                    result.append(OrderStatusResponse(
                        order_id=order.get('norenordno'),
                        broker_order_id=order.get('norenordno'),
                        status=ZebuOrderStatus.to_order_status(order.get('status', '')),
                        filled_quantity=int(order.get('fillshares', 0)),
                        pending_quantity=int(order.get('qty', 0)) - int(order.get('fillshares', 0)),
                        average_price=float(order.get('avgprc', 0.0)),
                        last_price=float(order.get('prc', 0.0)),
                        rejection_reason=order.get('rejreason'),
                        updated_at=self._parse_timestamp(order.get('ordrtm')),
                        raw_response=order
                    ))

                return result

            return []

        except Exception as e:
            logger.error(f"Exception getting Zebu orders: {e}")
            return []

    def get_positions(self) -> List[Position]:
        """
        Get current positions.

        API: POST /NorenWClientAPI/PositionBook
        """
        try:
            payload = {
                "uid": self._user_id,
                "actid": self._user_id,
            }

            response = self._make_request(self.POSITION_BOOK_ENDPOINT, payload)

            if response:
                # Handle both list and dict responses
                positions_data = response if isinstance(response, list) else []
                if isinstance(response, dict) and response.get('stat') == 'Ok':
                    # Single position or no positions
                    positions_data = [response] if 'tsym' in response else []
                elif isinstance(response, dict) and response.get('stat') == 'Not_Ok':
                    # No positions
                    return []

                positions = []

                for pos in positions_data:
                    if not isinstance(pos, dict) or 'tsym' not in pos:
                        continue

                    net_qty = int(pos.get('netqty', 0))
                    if net_qty == 0:
                        continue

                    position = Position(
                        symbol=pos.get('tsym'),
                        exchange=self._reverse_map_exchange(pos.get('exch', '')),
                        product_type=self._map_product_type(pos.get('prd', '')),
                        quantity=net_qty,
                        buy_quantity=int(pos.get('buyqty', 0)),
                        sell_quantity=int(pos.get('sellqty', 0)),
                        average_buy_price=float(pos.get('buyavgprc', 0.0)),
                        average_sell_price=float(pos.get('sellavgprc', 0.0)),
                        last_price=float(pos.get('lp', 0.0)),
                        pnl=float(pos.get('rpnl', 0.0)) + float(pos.get('urmtom', 0.0)),
                        value=abs(net_qty * float(pos.get('lp', 0.0))),
                        day_change=float(pos.get('daysellavgprc', 0.0)) - float(pos.get('daybuyavgprc', 0.0)),
                        trading_mode=self.trading_mode,
                        broker_id="zebu"
                    )

                    # Calculate P&L percentage
                    if position.value > 0:
                        position.pnl_percentage = (position.pnl / position.value) * 100

                    positions.append(position)

                return positions

            return []

        except Exception as e:
            logger.error(f"Exception getting Zebu positions: {e}")
            return []

    def get_margins(self) -> MarginInfo:
        """
        Get margin/fund information.

        API: POST /NorenWClientAPI/Limits
        """
        try:
            payload = {
                "uid": self._user_id,
                "actid": self._user_id,
            }

            response = self._make_request(self.LIMITS_ENDPOINT, payload)

            if response and response.get('stat') == 'Ok':
                return MarginInfo(
                    available_margin=float(response.get('cash', 0.0)),
                    used_margin=float(response.get('marginused', 0.0)),
                    total_balance=float(response.get('cash', 0.0)) + float(response.get('marginused', 0.0)),
                    payin_amount=float(response.get('payin', 0.0)),
                    payout_amount=float(response.get('payout', 0.0)),
                    day_pnl=float(response.get('rpnl', 0.0))
                )

            return MarginInfo(
                available_margin=0.0,
                used_margin=0.0,
                total_balance=0.0
            )

        except Exception as e:
            logger.error(f"Exception getting Zebu margins: {e}")
            return MarginInfo(
                available_margin=0.0,
                used_margin=0.0,
                total_balance=0.0
            )

    # Private helper methods

    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Optional[Dict]:
        """Make HTTP request to MYNT API."""
        if not self._connected and endpoint != self.LIMITS_ENDPOINT:
            logger.error("Not connected to Zebu API")
            return None

        try:
            url = f"{self.BASE_URL}{endpoint}"

            # Add authentication token
            payload['susertoken'] = self._access_token

            # MYNT API uses jData format with text/plain content type
            data = f"jData={json.dumps(payload)}"

            headers = {
                'Content-Type': 'text/plain'
            }

            response = self._session.post(url, data=data, headers=headers, timeout=30)
            return response.json()

        except requests.exceptions.Timeout:
            logger.error(f"Timeout calling Zebu API: {endpoint}")
            return {"stat": "Not_Ok", "emsg": "Request timeout"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error calling Zebu API: {e}")
            return {"stat": "Not_Ok", "emsg": str(e)}
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from Zebu API")
            return {"stat": "Not_Ok", "emsg": "Invalid JSON response"}

    def _map_exchange(self, exchange: str) -> str:
        """Map internal exchange code to Zebu exchange code."""
        mapping = {
            "NSE": "NSE",
            "NFO": "NFO",
            "BSE": "BSE",
            "BFO": "BFO",
            "MCX": "MCX",
            "CDS": "CDS",
        }
        return mapping.get(exchange.upper(), exchange)

    def _reverse_map_exchange(self, zebu_exchange: str) -> str:
        """Map Zebu exchange code to internal exchange code."""
        return zebu_exchange  # Same mapping

    def _map_product_type(self, zebu_product: str) -> ProductType:
        """Map Zebu product type to internal ProductType."""
        mapping = {
            "I": ProductType.MIS,
            "M": ProductType.NRML,
            "C": ProductType.CNC,
        }
        return mapping.get(zebu_product.upper(), ProductType.NRML)

    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse Zebu timestamp string to datetime."""
        if not timestamp_str:
            return None
        try:
            # Zebu uses various formats, try common ones
            for fmt in ["%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%H:%M:%S %d-%m-%Y"]:
                try:
                    return datetime.strptime(timestamp_str, fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            return None
        except Exception:
            return None
