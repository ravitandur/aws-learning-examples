/**
 * Strategy Constants
 * 
 * Centralized constants and default values for strategy creation.
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import { SelectOption, StrategyConfig, StrategyLeg } from '../../types/strategy';

// Index options
export const INDEX_OPTIONS: SelectOption[] = [
  { value: 'NIFTY', label: 'NIFTY' },
  { value: 'BANKNIFTY', label: 'BANKNIFTY' },
  { value: 'FINNIFTY', label: 'FINNIFTY' }
];

// Selection method options
export const SELECTION_METHOD_OPTIONS: SelectOption[] = [
  { value: 'ATM_POINT', label: 'ATM Point' },
  { value: 'ATM_PERCENT', label: 'ATM Percent' },
  { value: 'CLOSEST_PREMIUM', label: 'Closest Premium' },
  { value: 'CLOSEST_STRADDLE_PREMIUM', label: 'Closest Straddle' }
];

// Premium operator options
export const PREMIUM_OPERATOR_OPTIONS: SelectOption[] = [
  { value: 'CP_EQUAL', label: 'CP ~' },
  { value: 'CP_GREATER_EQUAL', label: 'CP >=' },
  { value: 'CP_LESS_EQUAL', label: 'CP <=' }
];

// Expiry type options
export const EXPIRY_TYPE_OPTIONS: SelectOption[] = [
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' }
];

// Risk management type options
export const RISK_MANAGEMENT_TYPE_OPTIONS: SelectOption[] = [
  { value: 'POINTS', label: 'Points' },
  { value: 'PERCENTAGE', label: 'Percentage' },
  { value: 'RANGE', label: 'Range' }
];

// Target profit type options (without RANGE)
export const TARGET_PROFIT_TYPE_OPTIONS: SelectOption[] = [
  { value: 'POINTS', label: 'Points' },
  { value: 'PERCENTAGE', label: 'Percentage' }
];

// Re-entry type options
export const RE_ENTRY_TYPE_OPTIONS: SelectOption[] = [
  { value: 'SL_REENTRY', label: 'SL ReEntry' },
  { value: 'SL_RECOST', label: 'SL ReCost' },
  { value: 'SL_REEXEC', label: 'SL ReExec' }
];

// Re-execute type options
export const RE_EXECUTE_TYPE_OPTIONS: SelectOption[] = [
  { value: 'TP_REEXEC', label: 'TP ReExec' }
];

// Count options (1-5)
export const COUNT_OPTIONS: SelectOption[] = [
  { value: '1', label: '1' },
  { value: '2', label: '2' },
  { value: '3', label: '3' },
  { value: '4', label: '4' },
  { value: '5', label: '5' }
];

// MTM type options
export const MTM_TYPE_OPTIONS: SelectOption[] = [
  { value: 'TOTAL_MTM', label: 'Total MTM' },
  { value: 'COMBINED_PREMIUM_PERCENT', label: 'Combined Premium %' }
];

// Time options (24 hours)
export const HOUR_OPTIONS: SelectOption[] = Array.from({ length: 24 }, (_, i) => ({ 
  value: i.toString().padStart(2, '0'), 
  label: i.toString().padStart(2, '0') 
}));

// Minute options (60 minutes)
export const MINUTE_OPTIONS: SelectOption[] = Array.from({ length: 60 }, (_, i) => ({ 
  value: i.toString().padStart(2, '0'), 
  label: i.toString().padStart(2, '0') 
}));

// Default strategy configuration
export const DEFAULT_STRATEGY_CONFIG: StrategyConfig = {
  entryTimeHour: '09',
  entryTimeMinute: '15',
  exitTimeHour: '15',
  exitTimeMinute: '30',
  rangeBreakout: false,
  rangeBreakoutTimeHour: '09',
  rangeBreakoutTimeMinute: '30',
  moveSlToCost: false,
  tradingType: 'INTRADAY',
  intradayExitMode: 'SAME_DAY',
  positionalEntryDays: 2,
  positionalExitDays: 0,
  targetProfit: {
    type: 'TOTAL_MTM',
    value: 0
  },
  mtmStopLoss: {
    type: 'TOTAL_MTM',
    value: 0
  }
};

// Default position template (without ID)
export const createDefaultPositionTemplate = (index: string): Omit<StrategyLeg, 'id'> => ({
  index,
  optionType: 'CE',
  actionType: 'BUY',
  strikePrice: 'ATM',
  totalLots: 1,
  expiryType: 'weekly',
  selectionMethod: 'ATM_POINT',
  
  // Default premium selection values
  premiumOperator: 'CP_EQUAL',
  premiumValue: 0,
  
  // Default straddle premium values
  straddlePremiumOperator: 'CP_EQUAL',
  straddlePremiumPercentage: 5,
  
  // Default risk management values
  stopLoss: {
    enabled: false,
    type: 'POINTS',
    value: 0
  },
  targetProfit: {
    enabled: false,
    type: 'POINTS',
    value: 0
  },
  trailingStopLoss: {
    enabled: false,
    type: 'POINTS',
    instrumentMoveValue: 0,
    stopLossMoveValue: 0
  },
  waitAndTrade: {
    enabled: false,
    type: 'POINTS',
    value: 0
  },
  reEntry: {
    enabled: false,
    type: 'SL_REENTRY',
    count: 1
  },
  reExecute: {
    enabled: false,
    type: 'TP_REEXEC',
    count: 1
  }
});

// Default positional values
export const DEFAULT_POSITIONAL_VALUES = {
  entryDays: 4,
  exitDays: 0
};

// Slider range limits
export const SLIDER_RANGE = {
  WEEKLY_MAX: 4,
  MONTHLY_MAX: 24
};