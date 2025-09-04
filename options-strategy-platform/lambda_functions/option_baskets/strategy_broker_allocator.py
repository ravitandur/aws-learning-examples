# Phase 1 Hybrid Architecture - Import from Phase 1 implementation
from .strategy_broker_allocator_phase1 import lambda_handler

# Re-export the main handler
__all__ = ['lambda_handler']