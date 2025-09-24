import { Strategy, Basket } from '../types';

/**
 * Transform strategy fields from backend snake_case to frontend camelCase
 */
export function transformStrategyFields(backendStrategy: any): Strategy {
  return {
    strategyId: backendStrategy.strategy_id,
    strategyName: backendStrategy.strategy_name,
    strategyType: backendStrategy.strategy_type || backendStrategy.underlying || 'Unknown',
    status: backendStrategy.status || 'ACTIVE',
    legs: backendStrategy.leg_count || backendStrategy.legs?.length || 0,
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