import { StrategyMetadata, Basket } from '../types';

/**
 * Transform strategy fields from backend snake_case to frontend camelCase
 * Updated to use clean StrategyMetadata interface with legCount
 */
export function transformStrategyFields(backendStrategy: any): StrategyMetadata {
  return {
    strategyId: backendStrategy.strategy_id,
    strategyName: backendStrategy.strategy_name,
    strategyType: backendStrategy.strategy_type || backendStrategy.underlying || 'Unknown',
    status: backendStrategy.status || 'ACTIVE',
    legCount: backendStrategy.leg_count || backendStrategy.legs?.length || 0,

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

    // POSITIONAL trading fields for derived trading type calculation
    entryTradingDaysBeforeExpiry: backendStrategy.entry_trading_days_before_expiry,
    exitTradingDaysBeforeExpiry: backendStrategy.exit_trading_days_before_expiry,

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

    // Note: isIntraDay and sequenceNumber are now handled in StrategyWithLegs for editing mode
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