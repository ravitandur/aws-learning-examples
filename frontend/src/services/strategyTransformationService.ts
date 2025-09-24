/**
 * Strategy Transformation Service
 * 
 * Transforms complex frontend StrategyWizardDialog data into backend-compatible format
 * and vice versa. Handles the mapping between the sophisticated UI state and the
 * simplified backend API schema.
 */

import strategyValidationService from './strategyValidationService';
import { parseStrikeValue, validateStrikeFormat, formatStrikeForDisplay } from '../utils/strategy/strikeValueParser';
import { getProductTypeValidationError, autoCorrectProductType, isValidProductType } from '../utils/strategy/productTypeValidation';
import { SelectionMethod } from '../types/strategy';

// Frontend types from StrategyWizardDialog
interface FrontendStrategyLeg {
  id: string;
  optionType: 'CE' | 'PE';
  actionType: 'BUY' | 'SELL';
  strikePrice: string;
  totalLots: number;
  selectionMethod: SelectionMethod;
  
  // Premium selection fields
  premiumOperator?: 'CLOSEST' | 'GTE' | 'LTE';
  premiumValue?: number;
  
  // Straddle premium fields
  straddlePremiumOperator?: 'CLOSEST' | 'GTE' | 'LTE';
  straddlePremiumPercentage?: number;
  
  // Risk Management Fields (6 types)
  stopLoss: {
    enabled: boolean;
    type: 'POINTS' | 'PERCENTAGE' | 'RANGE';
    value: number;
  };
  targetProfit: {
    enabled: boolean;
    type: 'POINTS' | 'PERCENTAGE';
    value: number;
  };
  trailingStopLoss: {
    enabled: boolean;
    type: 'POINTS' | 'PERCENTAGE';
    instrumentMoveValue: number;
    stopLossMoveValue: number;
  };
  waitAndTrade: {
    enabled: boolean;
    type: 'POINTS' | 'PERCENTAGE';
    value: number;
  };
  reEntry: {
    enabled: boolean;
    type: 'SL_REENTRY' | 'SL_RECOST' | 'SL_REEXEC';
    count: number;
  };
  reExecute: {
    enabled: boolean;
    type: 'TP_REEXEC';
    count: number;
  };
}

interface FrontendStrategyConfig {
  entryTimeHour: string;
  entryTimeMinute: string;
  exitTimeHour: string;
  exitTimeMinute: string;
  rangeBreakout: boolean;
  rangeBreakoutTimeHour: string;
  rangeBreakoutTimeMinute: string;
  moveSlToCost: boolean;
  // Product type configuration
  productType: 'MIS' | 'NRML';
  // New trading type configuration
  tradingType: 'INTRADAY' | 'POSITIONAL';
  intradayExitMode: 'SAME_DAY' | 'NEXT_DAY_BTST';
  entryTradingDaysBeforeExpiry: number;
  exitTradingDaysBeforeExpiry: number;
  // Strategy-level expiry type (NEW)
  expiryType: 'weekly' | 'monthly';
  targetProfit: {
    type: 'TOTAL_MTM' | 'COMBINED_PREMIUM_PERCENT';
    value: number;
  };
  mtmStopLoss: {
    type: 'TOTAL_MTM' | 'COMBINED_PREMIUM_PERCENT';
    value: number;
  };
}

interface FrontendStrategyData {
  basketId: string;
  strategyName: string;
  index: string;
  config: FrontendStrategyConfig;
  legs: FrontendStrategyLeg[];
}

// Backend API schema
interface BackendStrategyLeg {
  option_type: 'CE' | 'PE';
  action: 'BUY' | 'SELL';
  lots: number;

  // Dynamic strike selection criteria (flat structure)
  selection_method: SelectionMethod;
  selection_value?: number;        // Numeric value for all methods
  selection_operator?: 'CLOSEST' | 'GTE' | 'LTE'; // For premium methods only

  // Optional fields
  symbol?: string;
  description?: string;
  
  // Flattened risk management fields (conditional based on enabled state)
  stop_loss?: {
    enabled: boolean;
    type: string;
    value: number;
  };
  target_profit?: {
    enabled: boolean;
    type: string;
    value: number;
  };
  trailing_stop_loss?: {
    enabled: boolean;
    type: string;
    instrument_move_value: number;
    stop_loss_move_value: number;
  };
  wait_and_trade?: {
    enabled: boolean;
    type: string;
    value: number;
  };
  re_entry?: {
    enabled: boolean;
    type: string;
    count: number;
  };
  re_execute?: {
    enabled: boolean;
    type: string;
    count: number;
  };
}

interface BackendStrategyData {
  name: string;
  description: string;
  underlying: string;              // Strategy-level: NIFTY/BANKNIFTY
  expiry_type: 'weekly' | 'monthly'; // Strategy-level: weekly/monthly
  product: 'NRML' | 'MIS';
  entry_time: string;
  exit_time: string;
  entry_days: string[];
  exit_days: string[];
  legs: BackendStrategyLeg[];
  
  // Trading type configuration
  trading_type: 'INTRADAY' | 'POSITIONAL';  // MANDATORY
  
  // Conditional fields based on trading_type:
  intraday_exit_mode?: 'SAME_DAY' | 'NEXT_DAY_BTST';  // Only for INTRADAY
  entry_trading_days_before_expiry?: number;  // Only for POSITIONAL
  exit_trading_days_before_expiry?: number;   // Only for POSITIONAL
  
  // Flattened strategy configuration fields
  range_breakout?: boolean;
  range_breakout_time?: string;
  move_sl_to_cost?: boolean;
  target_profit?: {
    type: string;
    value: number;
  };
  mtm_stop_loss?: {
    type: string;
    value: number;
  };
}

class StrategyTransformationService {
  /**
   * Transform frontend StrategyWizardDialog data to backend API format
   * @param frontendData - Strategy data from frontend
   * @param strategyIndex - Strategy-level index selection (NIFTY/BANKNIFTY)
   * @param expiryType - Strategy-level expiry type selection (weekly/monthly)
   */
  transformToBackend(
    frontendData: FrontendStrategyData,
    strategyIndex: string,
    expiryType: 'weekly' | 'monthly'
  ): BackendStrategyData {
    const { strategyName, index, config, legs } = frontendData;
    
    // Validate product type against trading configuration
    const productTypeError = getProductTypeValidationError(
      config.productType,
      config.tradingType,
      config.intradayExitMode
    );
    
    if (productTypeError) {
      throw new Error(`Product type validation failed: ${productTypeError}`);
    }
    
    // Auto-correct product type if needed (additional safety check)
    const { productType: validatedProductType, wasChanged } = autoCorrectProductType(
      config.productType,
      config.tradingType,
      config.intradayExitMode
    );
    
    if (wasChanged) {
      console.warn(`Product type auto-corrected from ${config.productType} to ${validatedProductType}`);
      config.productType = validatedProductType;
    }
    
    // Transform legs with flat selection criteria (no strategy-level duplication)
    const backendLegs: BackendStrategyLeg[] = legs.map(leg => {
      const backendLeg: BackendStrategyLeg = {
        option_type: leg.optionType,  // Direct pass-through: CE → CE, PE → PE
        action: leg.actionType,
        lots: leg.totalLots,

        // Dynamic strike selection criteria (flat structure)
        selection_method: leg.selectionMethod,
        selection_value: undefined,
        selection_operator: undefined,
      };

      // Map selection criteria to flat structure based on method
      switch (leg.selectionMethod) {
        case 'ATM_POINTS':
        case 'ATM_PERCENT':
          const parsedValue = parseStrikeValue(leg.strikePrice, leg.selectionMethod);
          backendLeg.selection_value = typeof parsedValue === 'number' ? parsedValue : parseFloat(parsedValue.toString());
          // selection_operator remains undefined for ATM methods
          break;

        case 'PREMIUM':
          backendLeg.selection_value = leg.premiumValue || undefined;
          backendLeg.selection_operator = leg.premiumOperator || undefined;
          break;

        case 'PERCENTAGE_OF_STRADDLE_PREMIUM':
          backendLeg.selection_value = leg.straddlePremiumPercentage || undefined;
          backendLeg.selection_operator = leg.straddlePremiumOperator || undefined;
          break;
      }
      
      // Add flattened risk management fields conditionally (with defensive checks)
      if (leg.stopLoss?.enabled) {
        backendLeg.stop_loss = {
          enabled: true,
          type: leg.stopLoss.type,
          value: leg.stopLoss.value
        };
      }

      if (leg.targetProfit?.enabled) {
        backendLeg.target_profit = {
          enabled: true,
          type: leg.targetProfit.type,
          value: leg.targetProfit.value
        };
      }

      if (leg.trailingStopLoss?.enabled) {
        backendLeg.trailing_stop_loss = {
          enabled: true,
          type: leg.trailingStopLoss.type,
          instrument_move_value: leg.trailingStopLoss.instrumentMoveValue,
          stop_loss_move_value: leg.trailingStopLoss.stopLossMoveValue
        };
      }

      if (leg.waitAndTrade?.enabled) {
        backendLeg.wait_and_trade = {
          enabled: true,
          type: leg.waitAndTrade.type,
          value: leg.waitAndTrade.value
        };
      }

      if (leg.reEntry?.enabled) {
        backendLeg.re_entry = {
          enabled: true,
          type: leg.reEntry.type,
          count: leg.reEntry.count
        };
      }

      if (leg.reExecute?.enabled) {
        backendLeg.re_execute = {
          enabled: true,
          type: leg.reExecute.type,
          count: leg.reExecute.count
        };
      }
      
      return backendLeg;
    });
    
    // Format time strings
    const entryTime = `${config.entryTimeHour}:${config.entryTimeMinute}`;
    const exitTime = `${config.exitTimeHour}:${config.exitTimeMinute}`;
    
    // Default trading days (Monday-Friday)
    const tradingDays = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY'];
    
    const backendData: BackendStrategyData = {
      name: strategyName,
      description: `${index} strategy with ${legs.length} legs`,
      underlying: index, // NIFTY, BANKNIFTY, etc. (strategy-level)
      expiry_type: expiryType, // weekly/monthly (strategy-level)
      product: config.productType, // Use user-selected product type
      entry_time: entryTime,
      exit_time: exitTime,
      entry_days: tradingDays,
      exit_days: tradingDays,
      legs: backendLegs,
      
      // Trading type configuration (always required)
      trading_type: config.tradingType,
      
      // Conditional fields based on trading type
      ...(config.tradingType === 'INTRADAY' && {
        intraday_exit_mode: config.intradayExitMode
      }),
      ...(config.tradingType === 'POSITIONAL' && {
        entry_trading_days_before_expiry: config.entryTradingDaysBeforeExpiry,
        exit_trading_days_before_expiry: config.exitTradingDaysBeforeExpiry
      }),
      
      // Flattened strategy configuration
      range_breakout: config.rangeBreakout,
      range_breakout_time: config.rangeBreakout ? `${config.rangeBreakoutTimeHour}:${config.rangeBreakoutTimeMinute}` : undefined,
      move_sl_to_cost: config.moveSlToCost,
      target_profit: (config.targetProfit?.value || 0) > 0 ? {
        type: config.targetProfit?.type || 'POINTS',
        value: config.targetProfit?.value || 0
      } : undefined,
      mtm_stop_loss: (config.mtmStopLoss?.value || 0) > 0 ? {
        type: config.mtmStopLoss?.type || 'POINTS',
        value: config.mtmStopLoss?.value || 0
      } : undefined
    };
    
    return backendData;
  }
  
  /**
   * Parse and validate time string in HH:MM format
   * Returns default values for invalid input
   */
  private parseTimeString(
    timeString: string | undefined, 
    defaultHour: string, 
    defaultMinute: string
  ): [string, string] {
    // If no time string provided, use defaults
    if (!timeString) {
      return [defaultHour, defaultMinute];
    }
    
    // Check if string matches HH:MM format (supports H:MM and HH:MM)
    const timeRegex = /^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$/;
    if (!timeRegex.test(timeString)) {
      return [defaultHour, defaultMinute];
    }
    
    const [hour, minute] = timeString.split(':');
    return [hour.padStart(2, '0'), minute.padStart(2, '0')];
  }
  
  /**
   * Transform backend strategy data to frontend format
   */
  transformToFrontend(backendData: any, basketId: string): Partial<FrontendStrategyData> {
    const { name, strategy_name, underlying, legs = [], entry_time, exit_time } = backendData;
    
    // Transform backend legs to frontend format
    const frontendLegs: FrontendStrategyLeg[] = legs.map((backendLeg: any, index: number) => {
      const leg: FrontendStrategyLeg = {
        id: `leg-${index}`,
        optionType: backendLeg.option_type,  // Direct pass-through: CE → CE, PE → PE
        actionType: backendLeg.action,
        strikePrice: formatStrikeForDisplay(backendLeg.selection_value || 0, backendLeg.selection_method || 'ATM_POINTS'),
        totalLots: backendLeg.lots || 1,
        selectionMethod: backendLeg.selection_method || 'ATM_POINTS',
        
        // Method-specific field mapping from new selection_value/selection_operator architecture
        premiumOperator: backendLeg.selection_method === 'PREMIUM' ? (backendLeg.selection_operator || 'CLOSEST') : 'CLOSEST',
        premiumValue: backendLeg.selection_method === 'PREMIUM' ? (backendLeg.selection_value || 0) : 0,
        straddlePremiumOperator: backendLeg.selection_method === 'PERCENTAGE_OF_STRADDLE_PREMIUM' ? (backendLeg.selection_operator || 'CLOSEST') : 'CLOSEST',
        straddlePremiumPercentage: backendLeg.selection_method === 'PERCENTAGE_OF_STRADDLE_PREMIUM' ? (backendLeg.selection_value || 5) : 5,
        
        // Risk Management Fields - transform from flattened backend structure
        stopLoss: {
          enabled: backendLeg.stop_loss?.enabled || false,
          type: backendLeg.stop_loss?.type || 'PERCENTAGE',
          value: backendLeg.stop_loss?.value || 0,
        },
        targetProfit: {
          enabled: backendLeg.target_profit?.enabled || false,
          type: backendLeg.target_profit?.type || 'PERCENTAGE',
          value: backendLeg.target_profit?.value || 0,
        },
        trailingStopLoss: {
          enabled: backendLeg.trailing_stop_loss?.enabled || false,
          type: backendLeg.trailing_stop_loss?.type || 'POINTS',
          instrumentMoveValue: backendLeg.trailing_stop_loss?.instrument_move_value || 0,
          stopLossMoveValue: backendLeg.trailing_stop_loss?.stop_loss_move_value || 0,
        },
        waitAndTrade: {
          enabled: backendLeg.wait_and_trade?.enabled || false,
          type: backendLeg.wait_and_trade?.type || 'PERCENTAGE',
          value: backendLeg.wait_and_trade?.value || 0,
        },
        reEntry: {
          enabled: backendLeg.re_entry?.enabled || false,
          type: backendLeg.re_entry?.type || 'SL_REENTRY',
          count: backendLeg.re_entry?.count || 1,
        },
        reExecute: {
          enabled: backendLeg.re_execute?.enabled || false,
          type: backendLeg.re_execute?.type || 'TP_REEXEC',
          count: backendLeg.re_execute?.count || 1,
        },
      };
      
      return leg;
    });
    
    // Parse time strings with robust validation and defaults
    const [entryHour, entryMinute] = this.parseTimeString(entry_time, '09', '15');
    const [exitHour, exitMinute] = this.parseTimeString(exit_time, '15', '30');
    const [rangeBreakoutHour, rangeBreakoutMinute] = this.parseTimeString(
      backendData.range_breakout_time, 
      '09', 
      '30'
    );
    
    // Transform strategy configuration (includes expiryType)
    const config: FrontendStrategyConfig = {
      entryTimeHour: entryHour,
      entryTimeMinute: entryMinute,
      exitTimeHour: exitHour,
      exitTimeMinute: exitMinute,
      rangeBreakout: backendData.range_breakout || false,
      rangeBreakoutTimeHour: rangeBreakoutHour,
      rangeBreakoutTimeMinute: rangeBreakoutMinute,
      moveSlToCost: backendData.move_sl_to_cost || false,
      expiryType: backendData.expiry_type || 'weekly',
      productType: backendData.product || 'MIS',
      tradingType: backendData.trading_type || 'INTRADAY',
      intradayExitMode: backendData.intraday_exit_mode || 'SAME_DAY',
      entryTradingDaysBeforeExpiry: backendData.entry_trading_days_before_expiry || 4,
      exitTradingDaysBeforeExpiry: backendData.exit_trading_days_before_expiry || 0,
      targetProfit: {
        type: backendData.target_profit?.type || 'TOTAL_MTM',
        value: backendData.target_profit?.value || 0,
      },
      mtmStopLoss: {
        type: backendData.mtm_stop_loss?.type || 'TOTAL_MTM',
        value: backendData.mtm_stop_loss?.value || 0,
      },
    };
    
    return {
      basketId,
      strategyName: name || strategy_name || 'Imported Strategy',
      index: underlying || 'NIFTY',
      config,
      legs: frontendLegs,
    };
  }
  
  /**
   * Transform strike price based on selection method
   * Now extracts numeric values for ATM_POINTS and ATM_PERCENT methods
   */
  private transformStrike(strikePrice: string, selectionMethod: string): number | string {
    // Use the new parser to extract numeric values for backend API
    const transformedValue = parseStrikeValue(strikePrice, selectionMethod as any);
    
    // Debug logging to verify transformation
    if (process.env.REACT_APP_DEBUG === 'true') {
      console.log(`Strike transformation [${selectionMethod}]: "${strikePrice}" → ${JSON.stringify(transformedValue)}`);
    }
    
    return transformedValue;
  }
  
  
  /**
   * Validate frontend data before transformation using basic validation
   */
  validateFrontendData(data: FrontendStrategyData): { isValid: boolean; errors: string[]; warnings?: string[] } {
    // Basic validation - for advanced validation use validateFrontendDataAdvanced
    const errors: string[] = [];
    
    // Basic validation
    if (!data.strategyName?.trim()) {
      errors.push('Strategy name is required');
    }
    
    if (!data.basketId?.trim()) {
      errors.push('Basket ID is required');
    }
    
    if (!data.legs || data.legs.length === 0) {
      errors.push('At least one position is required');
    }
    
    // Validate each leg
    data.legs?.forEach((leg, index) => {
      if (leg.totalLots <= 0) {
        errors.push(`Position ${index + 1}: Total lots must be greater than 0`);
      }
      
      if (leg.selectionMethod === 'PREMIUM') {
        if (!leg.premiumOperator || leg.premiumValue === undefined) {
          errors.push(`Position ${index + 1}: Premium criteria required for Premium selection`);
        }
      }
      
      if (leg.selectionMethod === 'PERCENTAGE_OF_STRADDLE_PREMIUM') {
        if (!leg.straddlePremiumOperator || leg.straddlePremiumPercentage === undefined) {
          errors.push(`Position ${index + 1}: Straddle premium criteria required for Percentage of Straddle Premium selection`);
        }
      }
      
      // Validate strike value format for ATM_POINTS and ATM_PERCENT methods
      if (leg.selectionMethod === 'ATM_POINTS' || leg.selectionMethod === 'ATM_PERCENT') {
        if (!validateStrikeFormat(leg.strikePrice, leg.selectionMethod)) {
          errors.push(`Position ${index + 1}: Invalid strike price format "${leg.strikePrice}" for ${leg.selectionMethod} method`);
        }
      }
    });
    
    // Validate time configuration
    const entryHour = parseInt(data.config.entryTimeHour);
    const exitHour = parseInt(data.config.exitTimeHour);
    
    if (entryHour < 9 || entryHour > 15) {
      errors.push('Entry time must be between 09:00 and 15:30');
    }
    
    if (exitHour < 9 || exitHour > 15) {
      errors.push('Exit time must be between 09:00 and 15:30');
    }
    
    if (entryHour >= exitHour) {
      errors.push('Entry time must be before exit time');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Validate frontend data with advanced validation (async)
   */
  async validateFrontendDataAdvanced(data: FrontendStrategyData): Promise<{ isValid: boolean; errors: string[]; warnings: string[] }> {
    return strategyValidationService.validateStrategy(data);
  }
  
  /**
   * Create a strategy creation API call payload
   */
  createApiPayload(
    _basketId: string,
    frontendData: FrontendStrategyData,
    strategyIndex: string,
    expiryType: 'weekly' | 'monthly'
  ): BackendStrategyData {
    const validation = this.validateFrontendData(frontendData);

    if (!validation.isValid) {
      throw new Error(`Validation failed: ${validation.errors.join(', ')}`);
    }

    return this.transformToBackend(frontendData, strategyIndex, expiryType);
  }
}

const strategyTransformationService = new StrategyTransformationService();
export default strategyTransformationService;
export { StrategyTransformationService };
export type { FrontendStrategyData, BackendStrategyData, FrontendStrategyLeg, BackendStrategyLeg };