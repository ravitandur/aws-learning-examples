/**
 * Risk Management Validation Utilities
 * 
 * Centralized validation logic for risk management controls
 * to ensure consistent dependency checking across components.
 */

import { StopLossConfig, TargetProfitConfig, TrailingStopLossConfig } from '../../types/strategy';

/**
 * Validates if a Stop Loss configuration is complete and valid
 * @param stopLoss - Stop Loss configuration to validate
 * @returns true if Stop Loss is enabled with valid settings
 */
export const isValidStopLoss = (stopLoss: StopLossConfig | undefined): boolean => {
  if (!stopLoss) return false;
  return stopLoss.enabled &&
         stopLoss.value > 0 &&
         (stopLoss.type !== 'PERCENTAGE' || stopLoss.value <= 100);
};

/**
 * Validates if a Target Profit configuration is complete and valid
 * @param targetProfit - Target Profit configuration to validate
 * @returns true if Target Profit is enabled with valid settings
 */
export const isValidTargetProfit = (targetProfit: TargetProfitConfig | undefined): boolean => {
  if (!targetProfit) return false;
  return targetProfit.enabled &&
         targetProfit.value > 0 &&
         (targetProfit.type !== 'PERCENTAGE' || targetProfit.value <= 1000); // Allow higher percentages for profit
};

/**
 * Gets the reason why Stop Loss is invalid (for user feedback)
 * @param stopLoss - Stop Loss configuration to check
 * @returns string describing the issue, or null if valid
 */
export const getStopLossInvalidReason = (stopLoss: StopLossConfig | undefined): string | null => {
  if (!stopLoss) {
    return 'Stop Loss configuration is missing';
  }
  if (!stopLoss.enabled) {
    return 'Stop Loss must be enabled';
  }
  if (stopLoss.value <= 0) {
    return 'Stop Loss value must be greater than 0';
  }
  if (stopLoss.type === 'PERCENTAGE' && stopLoss.value > 100) {
    return 'Stop Loss percentage cannot exceed 100%';
  }
  return null;
};

/**
 * Validates if Trailing Stop Loss can be enabled based on Stop Loss
 * @param stopLoss - Stop Loss configuration
 * @param trailingStopLoss - Trailing Stop Loss configuration
 * @returns true if Trailing Stop Loss is valid
 */
export const canEnableTrailingStopLoss = (stopLoss: StopLossConfig | undefined, trailingStopLoss: TrailingStopLossConfig | undefined): boolean => {
  return isValidStopLoss(stopLoss);
};

/**
 * Validates if Re Entry can be enabled based on Stop Loss
 * @param stopLoss - Stop Loss configuration
 * @returns true if Re Entry can be enabled
 */
export const canEnableReEntry = (stopLoss: StopLossConfig | undefined): boolean => {
  return isValidStopLoss(stopLoss);
};

/**
 * Gets the reason why Target Profit is invalid (for user feedback)
 * @param targetProfit - Target Profit configuration to check
 * @returns string describing the issue, or null if valid
 */
export const getTargetProfitInvalidReason = (targetProfit: TargetProfitConfig | undefined): string | null => {
  if (!targetProfit) {
    return 'Target Profit configuration is missing';
  }
  if (!targetProfit.enabled) {
    return 'Target Profit must be enabled';
  }
  if (targetProfit.value <= 0) {
    return 'Target Profit value must be greater than 0';
  }
  if (targetProfit.type === 'PERCENTAGE' && targetProfit.value > 1000) {
    return 'Target Profit percentage is too high';
  }
  return null;
};

/**
 * Validates if Re Execute can be enabled based on Target Profit
 * @param targetProfit - Target Profit configuration
 * @returns true if Re Execute can be enabled
 */
export const canEnableReExecute = (targetProfit: TargetProfitConfig | undefined): boolean => {
  return isValidTargetProfit(targetProfit);
};