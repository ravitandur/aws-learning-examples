/**
 * Advanced Strategy Validation Service
 * 
 * Provides comprehensive validation for options strategy configurations including:
 * - Strike selection method validation
 * - Risk management configuration validation  
 * - Market timing validation
 * - Complex multi-leg strategy validation
 * - Indian market specialization rules
 */

import { FrontendStrategyData, FrontendStrategyLeg } from './strategyTransformationService';

interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

interface LegValidationResult {
  legIndex: number;
  legId: string;
  errors: string[];
  warnings: string[];
}

class StrategyValidationService {
  /**
   * Comprehensive strategy validation
   */
  validateStrategy(strategyData: FrontendStrategyData): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Basic field validation
    const basicValidation = this.validateBasicFields(strategyData);
    errors.push(...basicValidation.errors);
    warnings.push(...basicValidation.warnings);

    // Leg-specific validation
    const legValidation = this.validateLegs(strategyData.legs);
    legValidation.forEach(result => {
      result.errors.forEach(error => 
        errors.push(`Position ${result.legIndex + 1}: ${error}`)
      );
      result.warnings.forEach(warning => 
        warnings.push(`Position ${result.legIndex + 1}: ${warning}`)
      );
    });

    // Strategy-level configuration validation
    const configValidation = this.validateStrategyConfig(strategyData);
    errors.push(...configValidation.errors);
    warnings.push(...configValidation.warnings);

    // Advanced strategy validation
    const advancedValidation = this.validateAdvancedRules(strategyData);
    errors.push(...advancedValidation.errors);
    warnings.push(...advancedValidation.warnings);

    return {
      isValid: errors.length === 0,
      errors: Array.from(new Set(errors)), // Remove duplicates
      warnings: Array.from(new Set(warnings))
    };
  }

  /**
   * Validate basic required fields
   */
  private validateBasicFields(strategyData: FrontendStrategyData): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Required fields
    if (!strategyData.strategyName?.trim()) {
      errors.push('Strategy name is required');
    } else if (strategyData.strategyName.length < 3) {
      warnings.push('Strategy name should be at least 3 characters long');
    }

    if (!strategyData.basketId?.trim()) {
      errors.push('Basket ID is required');
    }

    if (!strategyData.index) {
      errors.push('Index selection is required');
    } else if (!['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX'].includes(strategyData.index)) {
      errors.push('Invalid index selected');
    }

    if (!strategyData.legs || strategyData.legs.length === 0) {
      errors.push('At least one position is required');
    } else if (strategyData.legs.length > 6) {
      warnings.push('Strategies with more than 6 legs may have higher execution complexity');
    }

    return { isValid: errors.length === 0, errors, warnings };
  }

  /**
   * Validate individual legs/positions
   */
  private validateLegs(legs: FrontendStrategyLeg[]): LegValidationResult[] {
    return legs.map((leg, index) => {
      const errors: string[] = [];
      const warnings: string[] = [];

      // Basic leg validation
      if (leg.totalLots <= 0) {
        errors.push('Total lots must be greater than 0');
      } else if (leg.totalLots > 100) {
        warnings.push('High lot count may lead to significant capital requirements');
      }

      // Strike selection method validation
      const strikeValidation = this.validateStrikeSelection(leg);
      errors.push(...strikeValidation.errors);
      warnings.push(...strikeValidation.warnings);

      // Risk management validation
      const riskValidation = this.validateRiskManagement(leg);
      errors.push(...riskValidation.errors);
      warnings.push(...riskValidation.warnings);

      return {
        legIndex: index,
        legId: leg.id,
        errors,
        warnings
      };
    });
  }

  /**
   * Validate strike selection methods and their configurations
   */
  private validateStrikeSelection(leg: FrontendStrategyLeg): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    switch (leg.selectionMethod) {
      case 'ATM_POINTS':
        if (!leg.strikePrice) {
          errors.push('Strike price is required for ATM Points method');
        } else if (!this.isValidATMPointStrike(leg.strikePrice)) {
          errors.push('Invalid ATM Points strike price format');
        }
        break;

      case 'ATM_PERCENT':
        if (!leg.strikePrice) {
          errors.push('Strike price is required for ATM Percent method');
        } else if (!this.isValidATMPercentStrike(leg.strikePrice)) {
          errors.push('Invalid ATM Percent strike price format');
        }
        break;

      case 'CLOSEST_PREMIUM':
        // Validate premium criteria
        if (!leg.premiumOperator) {
          errors.push('Premium operator is required for Closest Premium method');
        }
        if (leg.premiumValue === undefined || leg.premiumValue < 0) {
          errors.push('Premium value must be a positive number');
        } else if (leg.premiumValue > 1000) {
          warnings.push('Very high premium value may limit available strikes');
        }
        break;

      case 'CLOSEST_STRADDLE_PREMIUM':
        // Validate straddle premium criteria
        if (!leg.straddlePremiumOperator) {
          errors.push('Premium operator is required for Closest Straddle Premium method');
        }
        if (leg.straddlePremiumPercentage === undefined || leg.straddlePremiumPercentage <= 0) {
          errors.push('Straddle premium percentage must be greater than 0');
        } else if (leg.straddlePremiumPercentage > 80) {
          warnings.push('High straddle premium percentage may limit available strikes');
        }
        break;

      default:
        errors.push('Invalid strike selection method');
    }

    return { isValid: errors.length === 0, errors, warnings };
  }

  /**
   * Validate risk management configurations
   */
  private validateRiskManagement(leg: FrontendStrategyLeg): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Stop Loss validation
    if (leg.stopLoss.enabled) {
      if (leg.stopLoss.value <= 0) {
        errors.push('Stop Loss value must be greater than 0');
      } else if (leg.stopLoss.type === 'PERCENTAGE' && leg.stopLoss.value > 100) {
        errors.push('Stop Loss percentage cannot exceed 100%');
      } else if (leg.stopLoss.type === 'POINTS' && leg.stopLoss.value > 500) {
        warnings.push('Very high Stop Loss points value may not trigger effectively');
      }
    }

    // Target Profit validation
    if (leg.targetProfit.enabled) {
      if (leg.targetProfit.value <= 0) {
        errors.push('Target Profit value must be greater than 0');
      } else if (leg.targetProfit.type === 'PERCENTAGE' && leg.targetProfit.value > 500) {
        warnings.push('Very high Target Profit percentage may rarely trigger');
      }
    }

    // Trailing Stop Loss validation
    if (leg.trailingStopLoss.enabled) {
      if (!leg.stopLoss.enabled) {
        errors.push('Trailing Stop Loss requires regular Stop Loss to be enabled');
      }
      if (leg.trailingStopLoss.instrumentMoveValue <= 0) {
        errors.push('Instrument move value must be greater than 0');
      }
      if (leg.trailingStopLoss.stopLossMoveValue <= 0) {
        errors.push('Stop Loss move value must be greater than 0');
      }
      if (leg.trailingStopLoss.instrumentMoveValue < leg.trailingStopLoss.stopLossMoveValue) {
        warnings.push('Stop Loss move value should typically be less than instrument move value');
      }
    }

    // Wait & Trade validation
    if (leg.waitAndTrade.enabled && leg.waitAndTrade.value <= 0) {
      errors.push('Wait & Trade value must be greater than 0');
    }

    // Re-entry validation
    if (leg.reEntry.enabled) {
      if (leg.reEntry.count <= 0 || leg.reEntry.count > 5) {
        errors.push('Re-entry count must be between 1 and 5');
      }
      if (leg.reEntry.count > 2) {
        warnings.push('High re-entry count may lead to significant losses');
      }
    }

    // Re-execute validation
    if (leg.reExecute.enabled) {
      if (leg.reExecute.count <= 0 || leg.reExecute.count > 5) {
        errors.push('Re-execute count must be between 1 and 5');
      }
      if (!leg.targetProfit.enabled) {
        warnings.push('Re-execute is typically used with Target Profit');
      }
    }

    return { isValid: errors.length === 0, errors, warnings };
  }

  /**
   * Validate strategy-level configuration
   */
  private validateStrategyConfig(strategyData: FrontendStrategyData): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    const config = strategyData.config;

    // Time validation
    const entryTime = this.parseTime(config.entryTimeHour, config.entryTimeMinute);
    const exitTime = this.parseTime(config.exitTimeHour, config.exitTimeMinute);

    if (!this.isMarketHours(entryTime)) {
      warnings.push('Entry time is outside typical market hours (09:15-15:30 IST)');
    }

    if (!this.isMarketHours(exitTime)) {
      warnings.push('Exit time is outside typical market hours (09:15-15:30 IST)');
    }

    if (entryTime >= exitTime) {
      errors.push('Entry time must be before exit time');
    }

    if (exitTime - entryTime < 900000) { // 15 minutes in milliseconds
      warnings.push('Very short strategy duration may limit effectiveness');
    }

    // Range breakout validation
    if (config.rangeBreakout) {
      const rangeBreakoutTime = this.parseTime(config.rangeBreakoutTimeHour, config.rangeBreakoutTimeMinute);
      
      if (rangeBreakoutTime <= entryTime) {
        errors.push('Range breakout time must be after entry time');
      }
      
      if (rangeBreakoutTime >= exitTime) {
        errors.push('Range breakout time must be before exit time');
      }
    }

    // Risk management validation
    if (config.targetProfit.value > 0 && config.mtmStopLoss.value > 0) {
      const isTPPercent = config.targetProfit.type === 'COMBINED_PREMIUM_PERCENT';
      const isSLPercent = config.mtmStopLoss.type === 'COMBINED_PREMIUM_PERCENT';
      
      if (isTPPercent && isSLPercent) {
        if (config.targetProfit.value <= config.mtmStopLoss.value) {
          warnings.push('Target profit should typically be higher than stop loss for better risk-reward ratio');
        }
      }
    }

    return { isValid: errors.length === 0, errors, warnings };
  }

  /**
   * Advanced strategy validation rules
   */
  private validateAdvancedRules(strategyData: FrontendStrategyData): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Multi-leg strategy validation
    if (strategyData.legs.length > 1) {
      const multiLegValidation = this.validateMultiLegStrategy(strategyData);
      errors.push(...multiLegValidation.errors);
      warnings.push(...multiLegValidation.warnings);
    }

    // Index-specific validation
    const indexValidation = this.validateIndexSpecificRules(strategyData);
    errors.push(...indexValidation.errors);
    warnings.push(...indexValidation.warnings);

    // Capital requirements estimation
    const capitalValidation = this.validateCapitalRequirements(strategyData);
    warnings.push(...capitalValidation.warnings);

    return { isValid: errors.length === 0, errors, warnings };
  }

  /**
   * Validate multi-leg strategy configurations
   */
  private validateMultiLegStrategy(strategyData: FrontendStrategyData): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    const legs = strategyData.legs;
    
    // Check for balanced strategy (equal buy/sell legs)
    const buyLegs = legs.filter(leg => leg.actionType === 'BUY').length;
    const sellLegs = legs.filter(leg => leg.actionType === 'SELL').length;
    
    if (Math.abs(buyLegs - sellLegs) > 2) {
      warnings.push('Highly unbalanced buy/sell ratio may indicate unusual risk profile');
    }

    // Check for same expiry consistency
    const expiryTypes = Array.from(new Set(legs.map(leg => leg.expiryType)));
    if (expiryTypes.length > 1) {
      warnings.push('Mixed expiry types may complicate strategy management');
    }

    // Detect common strategy patterns and validate
    const strategyPattern = this.detectStrategyPattern(legs);
    if (strategyPattern) {
      const patternValidation = this.validateStrategyPattern(strategyPattern, legs);
      errors.push(...patternValidation.errors);
      warnings.push(...patternValidation.warnings);
    }

    return { isValid: errors.length === 0, errors, warnings };
  }

  /**
   * Validate index-specific rules
   */
  private validateIndexSpecificRules(strategyData: FrontendStrategyData): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    const indexLotSizes = {
      'NIFTY': 25,
      'BANKNIFTY': 15,
      'FINNIFTY': 25,
      'MIDCPNIFTY': 75,
      'SENSEX': 10
    };

    const lotSize = indexLotSizes[strategyData.index as keyof typeof indexLotSizes];
    
    if (lotSize) {
      const totalLots = strategyData.legs.reduce((sum, leg) => sum + leg.totalLots, 0);
      const totalQuantity = totalLots * lotSize;
      
      if (totalQuantity > 1800) { // NSE position limit threshold
        warnings.push(`High total quantity (${totalQuantity}) may approach position limits`);
      }

      // Index-specific warnings
      if (strategyData.index === 'BANKNIFTY' && totalLots > 50) {
        warnings.push('High BANKNIFTY lot count requires significant margin');
      }
      
      if (strategyData.index === 'MIDCPNIFTY' && totalLots > 10) {
        warnings.push('MIDCPNIFTY has large lot sizes (75) - verify capital requirements');
      }
    }

    return { isValid: errors.length === 0, errors, warnings };
  }

  /**
   * Estimate capital requirements and validate
   */
  private validateCapitalRequirements(strategyData: FrontendStrategyData): ValidationResult {
    const warnings: string[] = [];

    const totalLots = strategyData.legs.reduce((sum, leg) => sum + leg.totalLots, 0);
    const netSellLegs = strategyData.legs.filter(leg => leg.actionType === 'SELL').length;

    if (totalLots > 20) {
      warnings.push('High lot count strategy may require substantial margin');
    }

    if (netSellLegs > 0) {
      warnings.push('Strategy involves option selling - ensure adequate margin availability');
    }

    if (strategyData.legs.length > 4 && totalLots > 10) {
      warnings.push('Complex multi-leg strategy with high lots may have execution slippage');
    }

    return { isValid: true, errors: [], warnings };
  }

  /**
   * Detect common options strategy patterns
   */
  private detectStrategyPattern(legs: FrontendStrategyLeg[]): string | null {
    if (legs.length === 2) {
      const ceLegs = legs.filter(leg => leg.optionType === 'CE');
      const peLegs = legs.filter(leg => leg.optionType === 'PE');
      
      if (ceLegs.length === 1 && peLegs.length === 1) {
        const ceLeg = ceLegs[0];
        const peLeg = peLegs[0];
        
        if (ceLeg.strikePrice === peLeg.strikePrice) {
          if (ceLeg.actionType === 'BUY' && peLeg.actionType === 'BUY') {
            return 'LONG_STRADDLE';
          } else if (ceLeg.actionType === 'SELL' && peLeg.actionType === 'SELL') {
            return 'SHORT_STRADDLE';
          }
        }
      }
    } else if (legs.length === 4) {
      const sellLegs = legs.filter(leg => leg.actionType === 'SELL');
      const buyLegs = legs.filter(leg => leg.actionType === 'BUY');
      
      if (sellLegs.length === 2 && buyLegs.length === 2) {
        return 'IRON_CONDOR';
      }
    }

    return null;
  }

  /**
   * Validate specific strategy patterns
   */
  private validateStrategyPattern(pattern: string, legs: FrontendStrategyLeg[]): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    switch (pattern) {
      case 'LONG_STRADDLE':
        warnings.push('Long Straddle requires significant price movement to be profitable');
        break;
      case 'SHORT_STRADDLE':
        warnings.push('Short Straddle has unlimited risk - ensure proper risk management');
        break;
      case 'IRON_CONDOR':
        warnings.push('Iron Condor profits from low volatility - monitor implied volatility');
        break;
    }

    return { isValid: errors.length === 0, errors, warnings };
  }

  /**
   * Utility methods
   */
  private isValidATMPointStrike(strike: string): boolean {
    return /^(ATM|ITM\d+|OTM\d+)$/.test(strike);
  }

  private isValidATMPercentStrike(strike: string): boolean {
    return /^(ATM|ATM[+-]\d+(\.\d+)?%)$/.test(strike);
  }

  private parseTime(hour: string, minute: string): number {
    const h = parseInt(hour, 10);
    const m = parseInt(minute, 10);
    return h * 3600000 + m * 60000; // Convert to milliseconds
  }

  private isMarketHours(timeMs: number): boolean {
    const marketOpen = 9 * 3600000 + 15 * 60000; // 09:15
    const marketClose = 15 * 3600000 + 30 * 60000; // 15:30
    return timeMs >= marketOpen && timeMs <= marketClose;
  }
}

const strategyValidationService = new StrategyValidationService();
export default strategyValidationService;
export { StrategyValidationService };
export type { ValidationResult, LegValidationResult };