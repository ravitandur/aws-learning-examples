import { Strategy, Basket } from '../types';

/**
 * Transform strategy fields from backend snake_case to frontend camelCase
 * Fixed: Added missing field mappings for proper strategy editing
 */
export function transformStrategyFields(backendStrategy: any): Strategy {
  return {
    strategyId: backendStrategy.strategy_id,
    strategyName: backendStrategy.strategy_name,
    strategyType: backendStrategy.strategy_type || backendStrategy.underlying || 'Unknown',
    status: backendStrategy.status || 'ACTIVE',
    legs: backendStrategy.leg_count || backendStrategy.legs?.length || 0,
    legsArray: Array.isArray(backendStrategy.legs) ? backendStrategy.legs : undefined,

    // Phase 2: Add missing field mappings for strategy editing
    moveSlToCost: backendStrategy.move_sl_to_cost || false,
    rangeBreakout: backendStrategy.range_breakout || false,
    tradingType: backendStrategy.trading_type || 'INTRADAY',
    intradayExitMode: backendStrategy.intraday_exit_mode || 'SAME_DAY',

    // Configuration fields that might also be needed
    underlying: backendStrategy.underlying,
    expiryType: backendStrategy.expiry_type,
    product: backendStrategy.product,
    description: backendStrategy.description,
    entryTime: backendStrategy.entry_time,
    exitTime: backendStrategy.exit_time,
    entryDays: backendStrategy.entry_days,
    exitDays: backendStrategy.exit_days,

    // Strategy-level risk management
    targetProfit: backendStrategy.target_profit ? {
      enabled: true,
      type: backendStrategy.target_profit.type || 'PERCENTAGE',
      value: backendStrategy.target_profit.value || 0
    } : undefined,
    stopLoss: backendStrategy.mtm_stop_loss ? {
      enabled: true,
      type: (backendStrategy.mtm_stop_loss)?.type || 'PERCENTAGE',
      value: (backendStrategy.mtm_stop_loss)?.value || 0
    } : undefined,

    // On-demand derived fields (calculated instead of stored)
    legCount: backendStrategy.legs?.length || 0,
    isIntraDay: backendStrategy.product === 'MIS',
    sequenceNumber: backendStrategy.sequence_number || 1,
  };
}

/**
 * Transform basket with strategy field transformation
 */
export function transformBasket(backendBasket: any): Basket {
  return {
    ...backendBasket,
    strategies: backendBasket.strategies?.map(transformStrategyFields) || [],
  };
}