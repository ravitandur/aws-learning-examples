# Trading module - Broker trading strategies and order management
from .broker_trading_strategy import (
    BrokerTradingStrategy,
    OrderParams,
    OrderResponse,
    OrderStatusResponse,
    Position,
    MarginInfo,
    OrderType,
    OrderStatus,
    TradingMode,
    TransactionType,
    ProductType,
)
from .paper_trading_strategy import PaperTradingStrategy
from .zerodha_trading_strategy import ZerodhaTradingStrategy
from .zebu_trading_strategy import ZebuTradingStrategy

__all__ = [
    # Base classes and types
    'BrokerTradingStrategy',
    'OrderParams',
    'OrderResponse',
    'OrderStatusResponse',
    'Position',
    'MarginInfo',
    'OrderType',
    'OrderStatus',
    'TradingMode',
    'TransactionType',
    'ProductType',
    # Broker implementations
    'PaperTradingStrategy',
    'ZerodhaTradingStrategy',
    'ZebuTradingStrategy',
]


def get_trading_strategy(broker_name: str, trading_mode: TradingMode = TradingMode.PAPER):
    """
    Factory function to get appropriate trading strategy.

    Args:
        broker_name: Name of the broker (zerodha, zebu, paper)
        trading_mode: PAPER or LIVE trading mode

    Returns:
        Appropriate trading strategy instance
    """
    broker_lower = broker_name.lower()

    if trading_mode == TradingMode.PAPER:
        return PaperTradingStrategy(trading_mode)

    if broker_lower == 'zerodha':
        return ZerodhaTradingStrategy(trading_mode)
    elif broker_lower == 'zebu':
        return ZebuTradingStrategy(trading_mode)
    else:
        # Default to paper trading for unsupported brokers
        return PaperTradingStrategy(TradingMode.PAPER)
