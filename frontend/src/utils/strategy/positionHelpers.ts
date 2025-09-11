/**
 * Position Helpers
 * 
 * Utility functions for position manipulation and calculations.
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import { StrategyLeg, ExpiryType } from '../../types/strategy';
import { createDefaultPositionTemplate, DEFAULT_POSITIONAL_VALUES, SLIDER_RANGE } from './strategyConstants';

// Stable ID counter for better performance
let legIdCounter = 0;

/**
 * Generate stable ID for new positions
 */
export const generateStableId = (): string => `leg-${++legIdCounter}-${Date.now()}`;

/**
 * Create a new position with default values
 */
export const createNewPosition = (index: string): StrategyLeg => {
  const template = createDefaultPositionTemplate(index);
  return {
    id: generateStableId(),
    ...template
  };
};

/**
 * Clone an existing position with new ID
 */
export const clonePosition = (position: StrategyLeg): StrategyLeg => {
  return {
    ...position,
    id: generateStableId()
  };
};

/**
 * Update a specific position in an array
 */
export const updatePositionInArray = (
  positions: StrategyLeg[], 
  positionId: string, 
  updates: Partial<StrategyLeg>
): StrategyLeg[] => {
  return positions.map(position => 
    position.id === positionId ? { ...position, ...updates } : position
  );
};

/**
 * Remove a position from an array
 */
export const removePositionFromArray = (
  positions: StrategyLeg[], 
  positionId: string
): StrategyLeg[] => {
  return positions.filter(position => position.id !== positionId);
};

/**
 * Update all positions with new index
 */
export const updateAllPositionsIndex = (
  positions: StrategyLeg[], 
  newIndex: string
): StrategyLeg[] => {
  return positions.map(position => ({ ...position, index: newIndex }));
};

/**
 * Get expiry text based on positions selection
 * Returns 'monthly' if any position has monthly expiry, otherwise 'weekly'
 */
export const getExpiryText = (positions: StrategyLeg[]): ExpiryType => {
  if (positions.length === 0) return 'weekly';
  
  const hasMonthlyExpiry = positions.some(position => position.expiryType === 'monthly');
  return hasMonthlyExpiry ? 'monthly' : 'weekly';
};

/**
 * Get maximum slider range based on expiry type
 */
export const getMaxSliderRange = (positions: StrategyLeg[]): number => {
  const hasMonthlyExpiry = positions.some(position => position.expiryType === 'monthly');
  return hasMonthlyExpiry ? SLIDER_RANGE.MONTHLY_MAX : SLIDER_RANGE.WEEKLY_MAX;
};

/**
 * Get default values for positional sliders
 */
export const getDefaultPositionalValues = () => DEFAULT_POSITIONAL_VALUES;

/**
 * Check if position has enabled risk management
 */
export const hasEnabledRiskManagement = (position: StrategyLeg): boolean => {
  return position.stopLoss.enabled ||
         position.targetProfit.enabled ||
         position.trailingStopLoss.enabled ||
         position.waitAndTrade.enabled ||
         position.reEntry.enabled ||
         position.reExecute.enabled;
};

/**
 * Count positions with specific risk management enabled
 */
export const countPositionsWithRiskType = (
  positions: StrategyLeg[], 
  riskType: keyof Pick<StrategyLeg, 'stopLoss' | 'targetProfit' | 'trailingStopLoss' | 'waitAndTrade' | 'reEntry' | 'reExecute'>
): number => {
  return positions.filter(position => position[riskType].enabled).length;
};

/**
 * Get position summary statistics
 */
export const getPositionSummary = (positions: StrategyLeg[]) => {
  return {
    total: positions.length,
    buyPositions: positions.filter(p => p.actionType === 'BUY').length,
    sellPositions: positions.filter(p => p.actionType === 'SELL').length,
    callPositions: positions.filter(p => p.optionType === 'CE').length,
    putPositions: positions.filter(p => p.optionType === 'PE').length,
    totalLots: positions.reduce((sum, p) => sum + p.totalLots, 0),
    withStopLoss: countPositionsWithRiskType(positions, 'stopLoss'),
    withTargetProfit: countPositionsWithRiskType(positions, 'targetProfit'),
    withTrailingStopLoss: countPositionsWithRiskType(positions, 'trailingStopLoss')
  };
};

/**
 * Validate position interdependencies
 */
export const validatePositionInterdependencies = (position: StrategyLeg): string[] => {
  const errors: string[] = [];
  
  // Trailing stop loss requires stop loss to be enabled
  if (position.trailingStopLoss.enabled && !position.stopLoss.enabled) {
    errors.push('Trailing stop loss requires stop loss to be enabled');
  }
  
  return errors;
};

/**
 * Auto-correct position interdependencies
 */
export const autoCorrectPositionInterdependencies = (position: StrategyLeg): StrategyLeg => {
  const correctedPosition = { ...position };
  
  // Disable trailing stop loss if stop loss is disabled
  if (!correctedPosition.stopLoss.enabled && correctedPosition.trailingStopLoss.enabled) {
    correctedPosition.trailingStopLoss.enabled = false;
  }
  
  return correctedPosition;
};

/**
 * Reset position selection method and related fields
 */
export const resetPositionSelectionMethod = (
  position: StrategyLeg, 
  newMethod: StrategyLeg['selectionMethod']
): Partial<StrategyLeg> => {
  return {
    selectionMethod: newMethod,
    strikePrice: 'ATM', // Reset to ATM when method changes
    // Clear method-specific fields
    premiumOperator: newMethod === 'CLOSEST_PREMIUM' ? position.premiumOperator : undefined,
    premiumValue: newMethod === 'CLOSEST_PREMIUM' ? position.premiumValue : undefined,
    straddlePremiumOperator: newMethod === 'CLOSEST_STRADDLE_PREMIUM' ? position.straddlePremiumOperator : undefined,
    straddlePremiumPercentage: newMethod === 'CLOSEST_STRADDLE_PREMIUM' ? position.straddlePremiumPercentage : undefined
  };
};