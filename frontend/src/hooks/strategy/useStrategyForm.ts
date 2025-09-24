/**
 * useStrategyForm Hook
 * 
 * Main hook for managing strategy form state and configuration.
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { 
  StrategyFormData, 
  StrategyConfig, 
  StrategyLeg 
} from '../../types/strategy';
import { 
  DEFAULT_STRATEGY_CONFIG,
  getDefaultPositionalValues,
  getExpiryText,
  getMaxSliderRange 
} from '../../utils/strategy';

interface UseStrategyFormProps {
  basketId: string;
  editingStrategy?: any; // Optional strategy data for editing mode
  onClose: () => void;
}

interface UseStrategyFormReturn {
  // Form data
  strategyName: string;
  setStrategyName: (name: string) => void;
  strategyIndex: string;
  setStrategyIndex: (index: string) => void;
  strategyConfig: StrategyConfig;
  setStrategyConfig: React.Dispatch<React.SetStateAction<StrategyConfig>>;
  legs: StrategyLeg[];
  setLegs: React.Dispatch<React.SetStateAction<StrategyLeg[]>>;
  
  // UI state
  error: string | null;
  setError: (error: string | null) => void;
  isSubmitting: boolean;
  setIsSubmitting: (submitting: boolean) => void;
  
  // Dialog ref for accessibility
  dialogRef: React.RefObject<HTMLDivElement>;
  
  // Derived values
  expiryText: string;
  maxSliderRange: number;
  defaultPositionalValues: { entryDays: number; exitDays: number };
  
  // Form data getter
  getFormData: () => StrategyFormData;
}

export const useStrategyForm = ({
  basketId,
  editingStrategy,
  onClose
}: UseStrategyFormProps): UseStrategyFormReturn => {
  // Refs
  const dialogRef = useRef<HTMLDivElement>(null);
  
  // Form state - initialize with editing data if available (handle property name variations)
  const getStrategyName = (strategy: any) => {
    return strategy?.strategyName || strategy?.strategy_name || '';
  };

  // Extract config from flat strategy structure for editing mode
  const getStrategyConfig = (strategy: any): StrategyConfig => {
    if (!strategy) return DEFAULT_STRATEGY_CONFIG;

    // If strategy has nested config, use it (for backward compatibility)
    if (strategy.config) return strategy.config;

    // Otherwise, extract config fields from flat strategy structure
    return {
      entryTimeHour: strategy.entryTime?.split(':')[0] || DEFAULT_STRATEGY_CONFIG.entryTimeHour,
      entryTimeMinute: strategy.entryTime?.split(':')[1] || DEFAULT_STRATEGY_CONFIG.entryTimeMinute,
      exitTimeHour: strategy.exitTime?.split(':')[0] || DEFAULT_STRATEGY_CONFIG.exitTimeHour,
      exitTimeMinute: strategy.exitTime?.split(':')[1] || DEFAULT_STRATEGY_CONFIG.exitTimeMinute,
      rangeBreakout: strategy.rangeBreakout ?? DEFAULT_STRATEGY_CONFIG.rangeBreakout,
      rangeBreakoutTimeHour: DEFAULT_STRATEGY_CONFIG.rangeBreakoutTimeHour,
      rangeBreakoutTimeMinute: DEFAULT_STRATEGY_CONFIG.rangeBreakoutTimeMinute,
      moveSlToCost: strategy.moveSlToCost ?? DEFAULT_STRATEGY_CONFIG.moveSlToCost,
      expiryType: strategy.expiryType || DEFAULT_STRATEGY_CONFIG.expiryType,
      productType: strategy.product || DEFAULT_STRATEGY_CONFIG.productType,
      tradingType: strategy.tradingType || DEFAULT_STRATEGY_CONFIG.tradingType,
      intradayExitMode: strategy.intradayExitMode || DEFAULT_STRATEGY_CONFIG.intradayExitMode,
      entryTradingDaysBeforeExpiry: strategy.entryDays || DEFAULT_STRATEGY_CONFIG.entryTradingDaysBeforeExpiry,
      exitTradingDaysBeforeExpiry: strategy.exitDays || DEFAULT_STRATEGY_CONFIG.exitTradingDaysBeforeExpiry,
      targetProfit: DEFAULT_STRATEGY_CONFIG.targetProfit,
      mtmStopLoss: DEFAULT_STRATEGY_CONFIG.mtmStopLoss,
    };
  };

  const [strategyName, setStrategyName] = useState(getStrategyName(editingStrategy));
  const [strategyIndex, setStrategyIndex] = useState(editingStrategy?.index || 'NIFTY');
  const [strategyConfig, setStrategyConfig] = useState<StrategyConfig>(
    getStrategyConfig(editingStrategy)
  );
  const [legs, setLegs] = useState<StrategyLeg[]>(editingStrategy?.legsArray || editingStrategy?.legs || []);

  // UI state
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Initialize form with editing strategy data
  useEffect(() => {
    if (editingStrategy) {
      const resolvedStrategyName = getStrategyName(editingStrategy);

      console.log('🔄 [DEBUG] Initializing form with editing strategy data:', {
        originalStrategyName: editingStrategy.strategyName,
        strategyName_snake: editingStrategy.strategy_name,
        resolvedStrategyName: resolvedStrategyName,
        index: editingStrategy.index,
        configKeys: editingStrategy.config ? Object.keys(editingStrategy.config) : [],
        legsCount: Array.isArray(editingStrategy.legsArray) ? editingStrategy.legsArray.length :
                  Array.isArray(editingStrategy.legs) ? editingStrategy.legs.length : editingStrategy.legs,
        availableKeys: Object.keys(editingStrategy),
        fullData: editingStrategy
      });

      setStrategyName(resolvedStrategyName);
      setStrategyIndex(editingStrategy.index || 'NIFTY');
      setStrategyConfig(getStrategyConfig(editingStrategy));
      setLegs(editingStrategy.legsArray || editingStrategy.legs || []);
    }
  }, [editingStrategy]);
  
  // Focus management for accessibility
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    if (dialogRef.current) {
      dialogRef.current.focus();
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose]);
  
  // Derived values
  const expiryText = getExpiryText(strategyConfig.expiryType);
  const maxSliderRange = getMaxSliderRange(strategyConfig.expiryType);
  const defaultPositionalValues = getDefaultPositionalValues();
  
  // Form data getter
  const getFormData = useCallback((): StrategyFormData => ({
    basketId,
    strategyName: strategyName.trim(),
    index: strategyIndex,
    config: strategyConfig,
    legs: legs.map(leg => ({
      id: leg.id,
      optionType: leg.optionType,
      actionType: leg.actionType,
      strikePrice: leg.strikePrice,
      totalLots: leg.totalLots,
      selectionMethod: leg.selectionMethod,
      premiumOperator: leg.premiumOperator,
      premiumValue: leg.premiumValue,
      straddlePremiumOperator: leg.straddlePremiumOperator,
      straddlePremiumPercentage: leg.straddlePremiumPercentage,
      stopLoss: leg.stopLoss,
      targetProfit: leg.targetProfit,
      trailingStopLoss: leg.trailingStopLoss,
      waitAndTrade: leg.waitAndTrade,
      reEntry: leg.reEntry,
      reExecute: leg.reExecute
    }))
  }), [basketId, strategyName, strategyIndex, strategyConfig, legs]);
  
  return {
    // Form data
    strategyName,
    setStrategyName,
    strategyIndex,
    setStrategyIndex,
    strategyConfig,
    setStrategyConfig,
    legs,
    setLegs,
    
    // UI state
    error,
    setError,
    isSubmitting,
    setIsSubmitting,
    
    // Dialog ref
    dialogRef,
    
    // Derived values
    expiryText,
    maxSliderRange,
    defaultPositionalValues,
    
    // Form data getter
    getFormData
  };
};