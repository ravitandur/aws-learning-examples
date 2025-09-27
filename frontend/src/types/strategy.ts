/**
 * Strategy Types & Interfaces
 *
 * Centralized type definitions for strategy creation and management.
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

// Base enums for strategy options
export type OptionType = "CE" | "PE";
export type ActionType = "BUY" | "SELL";
export type ExpiryType = "weekly" | "monthly";
export type SelectionMethod =
  | "ATM_POINTS"
  | "ATM_PERCENT"
  | "PREMIUM"
  | "PERCENTAGE_OF_STRADDLE_PREMIUM";
export type PremiumOperator = "CLOSEST" | "GTE" | "LTE";
export type RiskManagementType = "POINTS" | "PERCENTAGE" | "RANGE";
export type ReEntryType = "SL_REENTRY" | "SL_RECOST" | "SL_REEXEC";
export type ReExecuteType = "TP_REEXEC";
export type TradingType = "INTRADAY" | "POSITIONAL";
export type IntradayExitMode = "SAME_DAY" | "NEXT_DAY_BTST";
export type MTMType = "TOTAL_MTM" | "COMBINED_PREMIUM_PERCENT";
export type ProductType = "MIS" | "NRML";

// Risk Management sub-interfaces
export interface StopLossConfig {
  enabled: boolean;
  type: RiskManagementType;
  value: number;
}

export interface TargetProfitConfig {
  enabled: boolean;
  type: "POINTS" | "PERCENTAGE";
  value: number;
}

export interface TrailingStopLossConfig {
  enabled: boolean;
  type: "POINTS" | "PERCENTAGE";
  instrumentMoveValue: number;
  stopLossMoveValue: number;
}

export interface WaitAndTradeConfig {
  enabled: boolean;
  type: "POINTS" | "PERCENTAGE";
  value: number;
}

export interface ReEntryConfig {
  enabled: boolean;
  type: ReEntryType;
  count: number; // 1 to 5
}

export interface ReExecuteConfig {
  enabled: boolean;
  type: ReExecuteType;
  count: number; // 1 to 5
}

// Main Strategy Leg interface
export interface Leg {
  id: string;
  optionType: OptionType;
  actionType: ActionType;
  strikePrice: string;
  totalLots: number;
  selectionMethod: SelectionMethod;

  // Premium selection fields for PREMIUM method
  premiumOperator?: PremiumOperator;
  premiumValue?: number;

  // Straddle premium fields for PERCENTAGE_OF_STRADDLE_PREMIUM method
  straddlePremiumOperator?: PremiumOperator;
  straddlePremiumPercentage?: number;

  // Risk Management Fields
  stopLoss: StopLossConfig;
  targetProfit: TargetProfitConfig;
  trailingStopLoss: TrailingStopLossConfig;
  waitAndTrade: WaitAndTradeConfig;
  reEntry: ReEntryConfig;
  reExecute: ReExecuteConfig;
}

// Strategy Configuration interface
export interface StrategyConfig {
  entryTimeHour: string;
  entryTimeMinute: string;
  exitTimeHour: string;
  exitTimeMinute: string;
  rangeBreakout: boolean;
  rangeBreakoutTimeHour: string;
  rangeBreakoutTimeMinute: string;
  moveSlToCost: boolean;

  // Strategy-level expiry type
  expiryType: ExpiryType;

  // Product type configuration
  productType: ProductType;

  // Trading type configuration
  tradingType: TradingType;
  intradayExitMode: IntradayExitMode;

  // Trading days before expiry (for positional trading)
  entryTradingDaysBeforeExpiry: number;
  exitTradingDaysBeforeExpiry: number;

  // Strategy-level risk management
  targetProfit: {
    type: MTMType;
    value: number;
  };
  mtmStopLoss: {
    type: MTMType;
    value: number;
  };
}

// Main Strategy data interface
export interface StrategyFormData {
  basketId: string;
  strategyName: string;
  index: string;
  config: StrategyConfig;
  legs: Leg[];
}

// Component Props interfaces
export interface StrategyWizardDialogProps {
  basketId: string;
  editingStrategy?: any; // Optional strategy data for editing mode
  onClose: () => void;
  onSubmit: (strategyData: any) => void;
}

// Option interfaces for dropdowns
export interface SelectOption {
  value: string;
  label: string;
}

// Form validation interface
export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

// Position management interface
export interface PositionActions {
  add: () => void;
  remove: (legId: string) => void;
  copy: (legId: string) => void;
  update: (legId: string, updates: Partial<Leg>) => void;
}

// Default values type
export interface DefaultValues {
  entryTradingDaysBeforeExpiry: number;
  exitTradingDaysBeforeExpiry: number;
}
