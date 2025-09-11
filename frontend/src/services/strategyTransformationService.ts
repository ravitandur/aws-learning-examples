/**
 * Strategy Transformation Service
 * 
 * Transforms complex frontend StrategyWizardDialog data into backend-compatible format
 * and vice versa. Handles the mapping between the sophisticated UI state and the
 * simplified backend API schema.
 */

import strategyValidationService from './strategyValidationService';
import { parseStrikeValue, validateStrikeFormat, formatStrikeForDisplay } from '../utils/strategy/strikeValueParser';

// Frontend types from StrategyWizardDialog
interface FrontendStrategyLeg {
  id: string;
  index: string;
  optionType: 'CE' | 'PE';
  actionType: 'BUY' | 'SELL';
  strikePrice: string;
  totalLots: number;
  expiryType: 'weekly' | 'monthly';
  selectionMethod: 'ATM_POINTS' | 'ATM_PERCENT' | 'CLOSEST_PREMIUM' | 'CLOSEST_STRADDLE_PREMIUM';
  
  // Premium selection fields
  premiumOperator?: 'CP_EQUAL' | 'CP_GREATER_EQUAL' | 'CP_LESS_EQUAL';
  premiumValue?: number;
  
  // Straddle premium fields
  straddlePremiumOperator?: 'CP_EQUAL' | 'CP_GREATER_EQUAL' | 'CP_LESS_EQUAL';
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
  // New trading type configuration
  tradingType: 'INTRADAY' | 'POSITIONAL';
  intradayExitMode: 'SAME_DAY' | 'NEXT_DAY_BTST';
  positionalEntryDays: number;
  positionalExitDays: number;
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
  option_type: 'CALL' | 'PUT';
  action: 'BUY' | 'SELL';
  strike: number | string; // Backend handles both numeric strikes and ATM references
  lots: number;
  expiry?: string;
  symbol?: string;
  description?: string;
  
  // Extended backend fields for advanced features
  selection_method?: string;
  premium_criteria?: {
    operator: string;
    value: number;
  };
  straddle_premium_criteria?: {
    operator: string;
    percentage: number;
  };
  risk_management?: {
    stop_loss?: any;
    target_profit?: any;
    trailing_stop_loss?: any;
    wait_and_trade?: any;
    re_entry?: any;
    re_execute?: any;
  };
}

interface BackendStrategyData {
  name: string;
  description: string;
  underlying: string;
  product: 'NRML' | 'MIS';
  entry_time: string;
  exit_time: string;
  entry_days: string[];
  exit_days: string[];
  legs: BackendStrategyLeg[];
  
  // Strategy-level configuration
  strategy_config?: {
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
  };
}

class StrategyTransformationService {
  /**
   * Transform frontend StrategyWizardDialog data to backend API format
   */
  transformToBackend(frontendData: FrontendStrategyData): BackendStrategyData {
    const { basketId, strategyName, index, config, legs } = frontendData;
    
    // Transform legs with advanced mappings
    const backendLegs: BackendStrategyLeg[] = legs.map(leg => {
      const backendLeg: BackendStrategyLeg = {
        option_type: leg.optionType === 'CE' ? 'CALL' : 'PUT',
        action: leg.actionType,
        strike: this.transformStrike(leg.strikePrice, leg.selectionMethod),
        lots: leg.totalLots,
        selection_method: leg.selectionMethod
      };
      
      // Add premium criteria for CLOSEST_PREMIUM method
      if (leg.selectionMethod === 'CLOSEST_PREMIUM' && leg.premiumOperator && leg.premiumValue !== undefined) {
        backendLeg.premium_criteria = {
          operator: leg.premiumOperator,
          value: leg.premiumValue
        };
      }
      
      // Add straddle premium criteria for CLOSEST_STRADDLE_PREMIUM method
      if (leg.selectionMethod === 'CLOSEST_STRADDLE_PREMIUM' && leg.straddlePremiumOperator && leg.straddlePremiumPercentage !== undefined) {
        backendLeg.straddle_premium_criteria = {
          operator: leg.straddlePremiumOperator,
          percentage: leg.straddlePremiumPercentage
        };
      }
      
      // Add risk management configuration
      backendLeg.risk_management = this.transformRiskManagement(leg);
      
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
      underlying: index, // NIFTY, BANKNIFTY, etc.
      product: 'MIS', // Default to intraday for options strategies
      entry_time: entryTime,
      exit_time: exitTime,
      entry_days: tradingDays,
      exit_days: tradingDays,
      legs: backendLegs,
      strategy_config: {
        range_breakout: config.rangeBreakout,
        range_breakout_time: config.rangeBreakout ? `${config.rangeBreakoutTimeHour}:${config.rangeBreakoutTimeMinute}` : undefined,
        move_sl_to_cost: config.moveSlToCost,
        target_profit: config.targetProfit.value > 0 ? {
          type: config.targetProfit.type,
          value: config.targetProfit.value
        } : undefined,
        mtm_stop_loss: config.mtmStopLoss.value > 0 ? {
          type: config.mtmStopLoss.type,
          value: config.mtmStopLoss.value
        } : undefined
      }
    };
    
    return backendData;
  }
  
  /**
   * Transform backend strategy data to frontend format
   */
  transformToFrontend(backendData: any, basketId: string): Partial<FrontendStrategyData> {
    const { name, strategy_name, underlying, legs = [], strategy_config = {}, entry_time, exit_time } = backendData;
    
    // Transform backend legs to frontend format
    const frontendLegs: FrontendStrategyLeg[] = legs.map((backendLeg: any, index: number) => {
      const leg: FrontendStrategyLeg = {
        id: `leg-${index}`,
        index: underlying || 'NIFTY',
        optionType: backendLeg.option_type === 'CALL' ? 'CE' : 'PE',
        actionType: backendLeg.action,
        strikePrice: formatStrikeForDisplay(backendLeg.strike, backendLeg.selection_method || 'ATM_POINTS'),
        totalLots: backendLeg.lots || 1,
        expiryType: 'weekly', // Default, can be enhanced later
        selectionMethod: backendLeg.selection_method || 'ATM_POINTS',
        
        // Premium selection fields
        premiumOperator: backendLeg.premium_criteria?.operator || 'CP_EQUAL',
        premiumValue: backendLeg.premium_criteria?.value || 0,
        
        // Straddle premium fields
        straddlePremiumOperator: backendLeg.straddle_premium_criteria?.operator || 'CP_EQUAL',
        straddlePremiumPercentage: backendLeg.straddle_premium_criteria?.percentage || 5,
        
        // Risk Management Fields - transform from backend
        stopLoss: {
          enabled: backendLeg.risk_management?.stop_loss?.enabled || false,
          type: backendLeg.risk_management?.stop_loss?.type || 'POINTS',
          value: backendLeg.risk_management?.stop_loss?.value || 0,
        },
        targetProfit: {
          enabled: backendLeg.risk_management?.target_profit?.enabled || false,
          type: backendLeg.risk_management?.target_profit?.type || 'POINTS',
          value: backendLeg.risk_management?.target_profit?.value || 0,
        },
        trailingStopLoss: {
          enabled: backendLeg.risk_management?.trailing_stop_loss?.enabled || false,
          type: backendLeg.risk_management?.trailing_stop_loss?.type || 'POINTS',
          instrumentMoveValue: backendLeg.risk_management?.trailing_stop_loss?.instrument_move_value || 0,
          stopLossMoveValue: backendLeg.risk_management?.trailing_stop_loss?.stop_loss_move_value || 0,
        },
        waitAndTrade: {
          enabled: backendLeg.risk_management?.wait_and_trade?.enabled || false,
          type: backendLeg.risk_management?.wait_and_trade?.type || 'POINTS',
          value: backendLeg.risk_management?.wait_and_trade?.value || 0,
        },
        reEntry: {
          enabled: backendLeg.risk_management?.re_entry?.enabled || false,
          type: backendLeg.risk_management?.re_entry?.type || 'SL_REENTRY',
          count: backendLeg.risk_management?.re_entry?.count || 1,
        },
        reExecute: {
          enabled: backendLeg.risk_management?.re_execute?.enabled || false,
          type: backendLeg.risk_management?.re_execute?.type || 'TP_REEXEC',
          count: backendLeg.risk_management?.re_execute?.count || 1,
        },
      };
      
      return leg;
    });
    
    // Parse time strings
    const [entryHour = '09', entryMinute = '15'] = entry_time ? entry_time.split(':') : [];
    const [exitHour = '15', exitMinute = '30'] = exit_time ? exit_time.split(':') : [];
    const [rangeBreakoutHour = '09', rangeBreakoutMinute = '30'] = strategy_config.range_breakout_time ? strategy_config.range_breakout_time.split(':') : [];
    
    // Transform strategy configuration
    const config: FrontendStrategyConfig = {
      entryTimeHour: entryHour,
      entryTimeMinute: entryMinute,
      exitTimeHour: exitHour,
      exitTimeMinute: exitMinute,
      rangeBreakout: strategy_config.range_breakout || false,
      rangeBreakoutTimeHour: rangeBreakoutHour,
      rangeBreakoutTimeMinute: rangeBreakoutMinute,
      moveSlToCost: strategy_config.move_sl_to_cost || false,
      tradingType: 'INTRADAY', // Default, can be enhanced
      intradayExitMode: 'SAME_DAY', // Default
      positionalEntryDays: 2,
      positionalExitDays: 0,
      targetProfit: {
        type: strategy_config.target_profit?.type || 'TOTAL_MTM',
        value: strategy_config.target_profit?.value || 0,
      },
      mtmStopLoss: {
        type: strategy_config.mtm_stop_loss?.type || 'TOTAL_MTM',
        value: strategy_config.mtm_stop_loss?.value || 0,
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
   * Transform complex risk management configuration
   */
  private transformRiskManagement(leg: FrontendStrategyLeg): any {
    const riskManagement: any = {};
    
    if (leg.stopLoss.enabled) {
      riskManagement.stop_loss = {
        enabled: true,
        type: leg.stopLoss.type,
        value: leg.stopLoss.value
      };
    }
    
    if (leg.targetProfit.enabled) {
      riskManagement.target_profit = {
        enabled: true,
        type: leg.targetProfit.type,
        value: leg.targetProfit.value
      };
    }
    
    if (leg.trailingStopLoss.enabled) {
      riskManagement.trailing_stop_loss = {
        enabled: true,
        type: leg.trailingStopLoss.type,
        instrument_move_value: leg.trailingStopLoss.instrumentMoveValue,
        stop_loss_move_value: leg.trailingStopLoss.stopLossMoveValue
      };
    }
    
    if (leg.waitAndTrade.enabled) {
      riskManagement.wait_and_trade = {
        enabled: true,
        type: leg.waitAndTrade.type,
        value: leg.waitAndTrade.value
      };
    }
    
    if (leg.reEntry.enabled) {
      riskManagement.re_entry = {
        enabled: true,
        type: leg.reEntry.type,
        count: leg.reEntry.count
      };
    }
    
    if (leg.reExecute.enabled) {
      riskManagement.re_execute = {
        enabled: true,
        type: leg.reExecute.type,
        count: leg.reExecute.count
      };
    }
    
    return Object.keys(riskManagement).length > 0 ? riskManagement : undefined;
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
      
      if (leg.selectionMethod === 'CLOSEST_PREMIUM') {
        if (!leg.premiumOperator || leg.premiumValue === undefined) {
          errors.push(`Position ${index + 1}: Premium criteria required for Closest Premium selection`);
        }
      }
      
      if (leg.selectionMethod === 'CLOSEST_STRADDLE_PREMIUM') {
        if (!leg.straddlePremiumOperator || leg.straddlePremiumPercentage === undefined) {
          errors.push(`Position ${index + 1}: Straddle premium criteria required for Closest Straddle Premium selection`);
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
  createApiPayload(_basketId: string, frontendData: FrontendStrategyData): BackendStrategyData {
    const validation = this.validateFrontendData(frontendData);
    
    if (!validation.isValid) {
      throw new Error(`Validation failed: ${validation.errors.join(', ')}`);
    }
    
    return this.transformToBackend(frontendData);
  }
}

const strategyTransformationService = new StrategyTransformationService();
export default strategyTransformationService;
export { StrategyTransformationService };
export type { FrontendStrategyData, BackendStrategyData, FrontendStrategyLeg, BackendStrategyLeg };