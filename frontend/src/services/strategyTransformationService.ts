/**
 * Strategy Transformation Service
 * 
 * Transforms complex frontend StrategyWizardDialog data into backend-compatible format
 * and vice versa. Handles the mapping between the sophisticated UI state and the
 * simplified backend API schema.
 */

import strategyValidationService from './strategyValidationService';

// Frontend types from StrategyWizardDialog
interface FrontendStrategyLeg {
  id: string;
  index: string;
  optionType: 'CE' | 'PE';
  actionType: 'BUY' | 'SELL';
  strikePrice: string;
  totalLots: number;
  expiryType: 'weekly' | 'monthly';
  selectionMethod: 'ATM_POINT' | 'ATM_PERCENT' | 'CLOSEST_PREMIUM' | 'CLOSEST_STRADDLE_PREMIUM';
  
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
    // This will be implemented when we need to edit existing strategies
    // For now, we focus on create flow
    return {
      basketId,
      strategyName: backendData.name || backendData.strategy_name,
      index: backendData.underlying,
      // TODO: Map backend data back to frontend format
    };
  }
  
  /**
   * Transform strike price based on selection method
   */
  private transformStrike(strikePrice: string, selectionMethod: string): number | string {
    switch (selectionMethod) {
      case 'ATM_POINT':
      case 'ATM_PERCENT':
        // Keep as string for backend to interpret (ATM, OTM1, ITM2, etc.)
        return strikePrice;
      case 'CLOSEST_PREMIUM':
      case 'CLOSEST_STRADDLE_PREMIUM':
        // For premium-based selection, backend handles the logic
        return 'DYNAMIC'; // Special marker for backend
      default:
        // Try to parse as number, fallback to string
        const numericStrike = parseFloat(strikePrice);
        return isNaN(numericStrike) ? strikePrice : numericStrike;
    }
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
  createApiPayload(basketId: string, frontendData: FrontendStrategyData): BackendStrategyData {
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