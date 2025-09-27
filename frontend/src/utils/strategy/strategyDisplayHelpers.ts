/**
 * Strategy Display Helpers
 *
 * Comprehensive utility functions for displaying strategy information consistently across components.
 * Consolidates formatting, badge variants, and display logic from StrategyCard and StrategyTable.
 */

import { StrategyMetadata } from '../../types';

export interface StrategyTradingInfo {
  tradingType?: string;
  intradayExitMode?: string;
  entryTradingDaysBeforeExpiry?: number;
  exitTradingDaysBeforeExpiry?: number;
}

/**
 * Calculate derived trading type based on business logic
 *
 * @param strategy Strategy object with trading configuration
 * @returns Human-readable derived trading type
 */
export const getDerivedTradingType = (strategy: StrategyTradingInfo): string => {
  // POSITIONAL: Based on days before expiry
  if (strategy.tradingType === 'POSITIONAL') {
    const entryDays = strategy.entryTradingDaysBeforeExpiry || 0;
    const exitDays = strategy.exitTradingDaysBeforeExpiry || 0;

    if (entryDays === exitDays) {
      return 'Intraday';
    } else {
      return 'Positional';
    }
  }

  // INTRADAY: Based on exit mode
  if (strategy.tradingType === 'INTRADAY') {
    if (strategy.intradayExitMode === 'NEXT_DAY_BTST') {
      return 'BTST/STBT';
    } else {
      return 'Intraday';
    }
  }

  // Fallback
  return strategy.tradingType || 'Standard';
};

/**
 * Get a short abbreviation for the derived trading type
 * Useful for compact displays
 *
 * @param strategy Strategy object with trading configuration
 * @returns Short abbreviation
 */
export const getDerivedTradingTypeShort = (strategy: StrategyTradingInfo): string => {
  // POSITIONAL: Based on days before expiry
  if (strategy.tradingType === 'POSITIONAL') {
    const entryDays = strategy.entryTradingDaysBeforeExpiry || 0;
    const exitDays = strategy.exitTradingDaysBeforeExpiry || 0;

    if (entryDays === exitDays) {
      return 'INT';
    } else {
      return 'POS';
    }
  }

  // INTRADAY: Based on exit mode
  if (strategy.tradingType === 'INTRADAY') {
    if (strategy.intradayExitMode === 'NEXT_DAY_BTST') {
      return 'BTST/STBT';
    } else {
      return 'INT';
    }
  }

  // Fallback
  return 'STD';
};

/**
 * Get color variant for the derived trading type badge
 *
 * @param strategy Strategy object with trading configuration
 * @returns Color variant string
 */
export const getDerivedTradingTypeVariant = (strategy: StrategyTradingInfo): 'default' | 'success' | 'warning' | 'danger' | 'info' => {
  const derivedType = getDerivedTradingType(strategy);

  switch (derivedType) {
    case 'Intraday':
      return 'success';
    case 'BTST/STBT':
      return 'warning';
    case 'Positional':
      return 'info';
    case 'Positional (Same Day)':
      return 'info';
    default:
      return 'default';
  }
};

/**
 * FORMAT UTILITIES - Shared formatting functions
 */

/**
 * Format days array to readable string
 *
 * @param days Array of day names
 * @returns Formatted day string (e.g., "MON, TUE, WED")
 */
export const formatDays = (days?: string[]): string => {
  if (!days || days.length === 0) return 'Not set';

  const dayMap: { [key: string]: string } = {
    'MONDAY': 'MON', 'TUESDAY': 'TUE', 'WEDNESDAY': 'WED',
    'THURSDAY': 'THU', 'FRIDAY': 'FRI', 'SATURDAY': 'SAT', 'SUNDAY': 'SUN'
  };

  return days.map(day => dayMap[day.toUpperCase()] || day.toUpperCase()).join(', ');
};

/**
 * Format time to readable format
 *
 * @param time Time string (HHMM or HH:MM format)
 * @returns Formatted time string (HH:MM)
 */
export const formatTime = (time?: string): string => {
  if (!time) return 'Not set';

  // If it's already in HH:MM format, return as is
  if (time.includes(':')) return time;

  // If it's in HHMM format, add colon
  if (time.length === 4) {
    return `${time.substring(0, 2)}:${time.substring(2, 4)}`;
  }

  return time;
};

/**
 * BADGE VARIANT UTILITIES - Consistent badge color variants
 */

/**
 * Get badge variant for product type
 *
 * @param product Product type (MIS, NRML)
 * @returns Badge variant string
 */
export const getProductBadgeVariant = (product?: string): 'default' | 'success' | 'warning' | 'danger' | 'info' => {
  switch (product?.toUpperCase()) {
    case 'MIS': return 'success';
    case 'NRML': return 'warning';
    default: return 'default';
  }
};

/**
 * Get badge variant for strategy status
 *
 * @param status Strategy status
 * @returns Badge variant string
 */
export const getStatusBadgeVariant = (status: string): 'default' | 'success' | 'warning' | 'danger' | 'info' => {
  switch (status) {
    case 'ACTIVE': return 'success';
    case 'PAUSED': return 'warning';
    case 'COMPLETED': return 'default';
    default: return 'default';
  }
};

/**
 * ADVANCED FEATURES DISPLAY - Consolidated logic for showing strategy features
 */

/**
 * Generate advanced features display for strategy cards
 * Includes derived trading type as first feature
 *
 * @param strategy Strategy object
 * @returns Formatted features string
 */
export const getAdvancedFeaturesWithDerivedType = (strategy: StrategyMetadata): string => {
  const features = [];

  // Always show derived trading type as the first feature
  features.push(getDerivedTradingType(strategy));

  // Check for advanced features based on available strategy data
  if (strategy.moveSlToCost) features.push('MSLC');
  if (strategy.rangeBreakout) features.push('ORB');

  // Check for strategy-level risk management features
  // If enabled is undefined but value exists and > 0, treat as enabled
  if (strategy.targetProfit && typeof strategy.targetProfit.value === 'number' && strategy.targetProfit.value > 0 &&
      (strategy.targetProfit.enabled !== false)) {
    const tpValue = strategy.targetProfit.value;
    const tpType = strategy.targetProfit.type;
    // Format display based on type
    let displayText = `TP: ${tpValue}`;
    if (tpType === "COMBINED_PREMIUM_PERCENT") displayText += "% Prem";
    else if (tpType === "TOTAL_MTM") displayText += " Pts.";
    else displayText += "pts";
    features.push(displayText);
  }

  if (strategy.stopLoss && typeof strategy.stopLoss.value === 'number' && strategy.stopLoss.value > 0 &&
      (strategy.stopLoss.enabled !== false)) {
    const slValue = strategy.stopLoss.value;
    const slType = strategy.stopLoss.type;
    // Format display based on type
    let displayText = `SL: ${slValue}`;
    if (slType === "TOTAL_MTM") displayText += " Pts.";
    else if (slType === "COMBINED_PREMIUM_PERCENT") displayText += "% Prem";
    else displayText += "pts";
    features.push(displayText);
  }

  return features.join(', ');
};

/**
 * Generate advanced features display for strategy tables
 * Does NOT include derived trading type (shown separately in table)
 *
 * @param strategy Strategy object
 * @returns Formatted features string or "None" if no features
 */
export const getAdvancedFeaturesForTable = (strategy: StrategyMetadata): string => {
  const features = [];

  // Check for advanced features based on available strategy data
  if (strategy.moveSlToCost) features.push('MSLC');
  if (strategy.rangeBreakout) features.push('ORB');

  // Check for strategy-level risk management features
  if (strategy.targetProfit && typeof strategy.targetProfit.value === 'number' && strategy.targetProfit.value > 0 &&
      (strategy.targetProfit.enabled !== false)) {
    const tpValue = strategy.targetProfit.value;
    const tpType = strategy.targetProfit.type;
    let displayText = `TP: ${tpValue}`;
    if (tpType === "COMBINED_PREMIUM_PERCENT") displayText += "% Prem";
    else if (tpType === "TOTAL_MTM") displayText += " Pts.";
    else displayText += "pts";
    features.push(displayText);
  }

  if (strategy.stopLoss && typeof strategy.stopLoss.value === 'number' && strategy.stopLoss.value > 0 &&
      (strategy.stopLoss.enabled !== false)) {
    const slValue = strategy.stopLoss.value;
    const slType = strategy.stopLoss.type;
    let displayText = `SL: ${slValue}`;
    if (slType === "TOTAL_MTM") displayText += " Pts.";
    else if (slType === "COMBINED_PREMIUM_PERCENT") displayText += "% Prem";
    else displayText += "pts";
    features.push(displayText);
  }

  return features.length > 0 ? features.join(', ') : 'None';
};