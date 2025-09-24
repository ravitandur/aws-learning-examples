/**
 * Strategy Constants
 *
 * Centralized constants and default values for strategy creation.
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import {
  SelectOption,
  StrategyConfig,
  StrategyLeg,
} from "../../types/strategy";

// Index options
export const INDEX_OPTIONS: SelectOption[] = [
  { value: "NIFTY", label: "NIFTY" },
  { value: "BANKNIFTY", label: "BANKNIFTY" },
  { value: "FINNIFTY", label: "FINNIFTY" },
];

// Selection method options
export const SELECTION_METHOD_OPTIONS: SelectOption[] = [
  { value: "ATM_POINTS", label: "ATM Points" },
  { value: "ATM_PERCENT", label: "ATM Percent" },
  { value: "PREMIUM", label: "Premium" },
  { value: "PERCENTAGE_OF_STRADDLE_PREMIUM", label: "Straddle Premium %" },
];

// Premium operator options
export const PREMIUM_OPERATOR_OPTIONS: SelectOption[] = [
  { value: "CLOSEST", label: "Closest ~" },
  { value: "GTE", label: "GTE >=" },
  { value: "LTE", label: "LTE <=" },
];

// Expiry type options
export const EXPIRY_TYPE_OPTIONS: SelectOption[] = [
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
];

// Risk management type options
export const RISK_MANAGEMENT_TYPE_OPTIONS: SelectOption[] = [
  { value: "POINTS", label: "Points" },
  { value: "PERCENTAGE", label: "Percentage" },
  { value: "RANGE", label: "Range" },
];

// Target profit type options (without RANGE)
export const TARGET_PROFIT_TYPE_OPTIONS: SelectOption[] = [
  { value: "POINTS", label: "Points" },
  { value: "PERCENTAGE", label: "Percentage" },
];

// Re-entry type options
export const RE_ENTRY_TYPE_OPTIONS: SelectOption[] = [
  { value: "SL_REENTRY", label: "SL ReEntry" },
  { value: "SL_RECOST", label: "SL ReCost" },
  { value: "SL_REEXEC", label: "SL ReExec" },
];

// Re-execute type options
export const RE_EXECUTE_TYPE_OPTIONS: SelectOption[] = [
  { value: "TP_REEXEC", label: "TP ReExec" },
];

// Count options (1-5)
export const COUNT_OPTIONS: SelectOption[] = [
  { value: "1", label: "1" },
  { value: "2", label: "2" },
  { value: "3", label: "3" },
  { value: "4", label: "4" },
  { value: "5", label: "5" },
];

// MTM type options
export const MTM_TYPE_OPTIONS: SelectOption[] = [
  { value: "TOTAL_MTM", label: "Total MTM" },
  { value: "COMBINED_PREMIUM_PERCENT", label: "Combined Premium %" },
];

// Product type options
export const PRODUCT_TYPE_OPTIONS: SelectOption[] = [
  { value: "MIS", label: "MIS (Intraday)" },
  { value: "NRML", label: "NRML (Carry Forward)" },
];

// Time options (24 hours)
export const HOUR_OPTIONS: SelectOption[] = Array.from(
  { length: 24 },
  (_, i) => ({
    value: i.toString().padStart(2, "0"),
    label: i.toString().padStart(2, "0"),
  })
);

// Minute options (60 minutes)
export const MINUTE_OPTIONS: SelectOption[] = Array.from(
  { length: 60 },
  (_, i) => ({
    value: i.toString().padStart(2, "0"),
    label: i.toString().padStart(2, "0"),
  })
);

// Default strategy configuration
export const DEFAULT_STRATEGY_CONFIG: StrategyConfig = {
  entryTimeHour: "09",
  entryTimeMinute: "15",
  exitTimeHour: "15",
  exitTimeMinute: "30",
  rangeBreakout: false,
  rangeBreakoutTimeHour: "09",
  rangeBreakoutTimeMinute: "30",
  moveSlToCost: false,
  expiryType: "weekly",
  productType: "NRML",
  tradingType: "INTRADAY",
  intradayExitMode: "SAME_DAY",
  entryTradingDaysBeforeExpiry: 4, // Weekly default
  exitTradingDaysBeforeExpiry: 0, // Default for both weekly and monthly
  targetProfit: {
    type: "TOTAL_MTM",
    value: 0,
  },
  mtmStopLoss: {
    type: "TOTAL_MTM",
    value: 0,
  },
};

// Default position template (without ID)
export const createDefaultPositionTemplate = (): Omit<StrategyLeg, "id"> => ({
  optionType: "CE",
  actionType: "BUY",
  strikePrice: "ATM",
  totalLots: 1,
  selectionMethod: "ATM_POINTS",

  // Default premium selection values
  premiumOperator: "CLOSEST",
  premiumValue: 0,

  // Default straddle premium values
  straddlePremiumOperator: "CLOSEST",
  straddlePremiumPercentage: 5,

  // Default risk management values
  stopLoss: {
    enabled: false,
    type: "PERCENTAGE",
    value: 0,
  },
  targetProfit: {
    enabled: false,
    type: "PERCENTAGE",
    value: 0,
  },
  trailingStopLoss: {
    enabled: false,
    type: "POINTS",
    instrumentMoveValue: 0,
    stopLossMoveValue: 0,
  },
  waitAndTrade: {
    enabled: false,
    type: "PERCENTAGE",
    value: 0,
  },
  reEntry: {
    enabled: false,
    type: "SL_REENTRY",
    count: 1,
  },
  reExecute: {
    enabled: false,
    type: "TP_REEXEC",
    count: 1,
  },
});

// Default positional values
export const DEFAULT_POSITIONAL_VALUES = {
  entryDays: 4,
  exitDays: 0,
};

// Slider range limits
export const SLIDER_RANGE = {
  WEEKLY_MAX: 4,
  MONTHLY_MAX: 24,
};
