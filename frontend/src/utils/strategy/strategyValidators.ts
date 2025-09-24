/**
 * Strategy Validators
 * 
 * Validation utilities for strategy form data.
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import { StrategyFormData, StrategyLeg, ValidationResult } from '../../types/strategy';

/**
 * Validate strategy name
 */
export const validateStrategyName = (name: string): string[] => {
  const errors: string[] = [];
  
  if (!name?.trim()) {
    errors.push('Strategy name is required');
  }
  
  if (name && name.trim().length < 3) {
    errors.push('Strategy name must be at least 3 characters long');
  }
  
  if (name && name.trim().length > 100) {
    errors.push('Strategy name must be less than 100 characters');
  }
  
  return errors;
};

/**
 * Validate positions/legs
 */
export const validatePositions = (legs: StrategyLeg[]): string[] => {
  const errors: string[] = [];
  
  if (!legs || legs.length === 0) {
    errors.push('At least one position is required');
  }
  
  legs?.forEach((leg, index) => {
    const positionErrors = validateSinglePosition(leg, index + 1);
    errors.push(...positionErrors);
  });
  
  return errors;
};

/**
 * Validate a single position
 */
export const validateSinglePosition = (leg: StrategyLeg, positionNumber: number): string[] => {
  const errors: string[] = [];
  const prefix = `Position ${positionNumber}:`;
  
  // Validate lots
  if (leg.totalLots <= 0) {
    errors.push(`${prefix} Total lots must be greater than 0`);
  }
  
  if (leg.totalLots > 1000) {
    errors.push(`${prefix} Total lots cannot exceed 1000`);
  }
  
  // Validate premium criteria for PREMIUM method
  if (leg.selectionMethod === 'PREMIUM') {
    if (!leg.premiumOperator) {
      errors.push(`${prefix} Premium operator is required for Premium selection`);
    }
    
    if (leg.premiumValue === undefined || leg.premiumValue < 0) {
      errors.push(`${prefix} Premium value must be a positive number for Premium selection`);
    }
  }
  
  // Validate straddle premium criteria for PERCENTAGE_OF_STRADDLE_PREMIUM method
  if (leg.selectionMethod === 'PERCENTAGE_OF_STRADDLE_PREMIUM') {
    if (!leg.straddlePremiumOperator) {
      errors.push(`${prefix} Straddle premium operator is required for Percentage of Straddle Premium selection`);
    }
    
    if (leg.straddlePremiumPercentage === undefined || leg.straddlePremiumPercentage < 5 || leg.straddlePremiumPercentage > 60) {
      errors.push(`${prefix} Straddle premium percentage must be between 5% and 60%`);
    }
  }
  
  // Validate risk management settings
  const riskErrors = validateRiskManagement(leg, positionNumber);
  errors.push(...riskErrors);
  
  return errors;
};

/**
 * Validate risk management configuration for a position
 */
export const validateRiskManagement = (leg: StrategyLeg, positionNumber: number): string[] => {
  const errors: string[] = [];
  const prefix = `Position ${positionNumber}:`;

  // Validate stop loss (with defensive checks)
  if (leg.stopLoss?.enabled && (leg.stopLoss?.value || 0) <= 0) {
    errors.push(`${prefix} Stop loss value must be greater than 0 when enabled`);
  }

  // Validate target profit (with defensive checks)
  if (leg.targetProfit?.enabled && (leg.targetProfit?.value || 0) <= 0) {
    errors.push(`${prefix} Target profit value must be greater than 0 when enabled`);
  }
  
  // Validate trailing stop loss (with defensive checks)
  if (leg.trailingStopLoss?.enabled) {
    if (!leg.stopLoss?.enabled) {
      errors.push(`${prefix} Trailing stop loss requires stop loss to be enabled`);
    }

    if ((leg.trailingStopLoss?.instrumentMoveValue || 0) <= 0) {
      errors.push(`${prefix} Instrument move value must be greater than 0 for trailing stop loss`);
    }

    if ((leg.trailingStopLoss?.stopLossMoveValue || 0) <= 0) {
      errors.push(`${prefix} Stop loss move value must be greater than 0 for trailing stop loss`);
    }
  }

  // Validate wait and trade (with defensive checks)
  if (leg.waitAndTrade?.enabled && (leg.waitAndTrade?.value || 0) <= 0) {
    errors.push(`${prefix} Wait & trade value must be greater than 0 when enabled`);
  }
  
  // Validate re-entry count (with defensive checks)
  if (leg.reEntry?.enabled && ((leg.reEntry?.count || 0) < 1 || (leg.reEntry?.count || 0) > 5)) {
    errors.push(`${prefix} Re-entry count must be between 1 and 5`);
  }

  // Validate re-execute count (with defensive checks)
  if (leg.reExecute?.enabled && ((leg.reExecute?.count || 0) < 1 || (leg.reExecute?.count || 0) > 5)) {
    errors.push(`${prefix} Re-execute count must be between 1 and 5`);
  }
  
  return errors;
};

/**
 * Validate time configuration
 */
export const validateTimeConfiguration = (config: any): string[] => {
  const errors: string[] = [];
  
  const entryHour = parseInt(config.entryTimeHour);
  const exitHour = parseInt(config.exitTimeHour);
  const entryMinute = parseInt(config.entryTimeMinute);
  const exitMinute = parseInt(config.exitTimeMinute);
  
  // Validate hour ranges
  if (entryHour < 9 || entryHour > 15) {
    errors.push('Entry time must be between 09:00 and 15:30');
  }
  
  if (exitHour < 9 || exitHour > 15) {
    errors.push('Exit time must be between 09:00 and 15:30');
  }
  
  // Validate that entry time is before exit time
  const entryTimeMinutes = entryHour * 60 + entryMinute;
  const exitTimeMinutes = exitHour * 60 + exitMinute;
  
  if (entryTimeMinutes >= exitTimeMinutes) {
    errors.push('Entry time must be before exit time');
  }
  
  // Validate range breakout time if enabled
  if (config.rangeBreakout) {
    const rangeHour = parseInt(config.rangeBreakoutTimeHour);
    const rangeMinute = parseInt(config.rangeBreakoutTimeMinute);
    const rangeTimeMinutes = rangeHour * 60 + rangeMinute;
    
    if (rangeTimeMinutes <= entryTimeMinutes) {
      errors.push('Range breakout time must be after entry time');
    }
    
    if (rangeTimeMinutes >= exitTimeMinutes) {
      errors.push('Range breakout time must be before exit time');
    }
  }
  
  return errors;
};

/**
 * Validate basket ID
 */
export const validateBasketId = (basketId: string): string[] => {
  const errors: string[] = [];
  
  if (!basketId?.trim()) {
    errors.push('Basket ID is required');
  }
  
  return errors;
};

/**
 * Main validation function for complete strategy form data
 */
export const validateStrategyForm = (data: StrategyFormData): ValidationResult => {
  const errors: string[] = [];
  
  // Validate basket ID
  errors.push(...validateBasketId(data.basketId));
  
  // Validate strategy name
  errors.push(...validateStrategyName(data.strategyName));
  
  // Validate positions
  errors.push(...validatePositions(data.legs));
  
  // Validate time configuration
  errors.push(...validateTimeConfiguration(data.config));
  
  return {
    isValid: errors.length === 0,
    errors
  };
};

/**
 * Quick validation for required fields only
 */
export const validateRequiredFields = (data: Partial<StrategyFormData>): ValidationResult => {
  const errors: string[] = [];
  
  if (!data.strategyName?.trim()) {
    errors.push('Please enter a strategy name');
  }
  
  if (!data.legs || data.legs.length === 0) {
    errors.push('Please add at least one position');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};