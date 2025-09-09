# Industry Best Practice: Basket-Level Broker Allocation
from .basket_broker_allocator_phase1 import lambda_handler

# Re-export the main handler
__all__ = ['lambda_handler']