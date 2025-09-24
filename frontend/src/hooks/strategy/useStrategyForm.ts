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

  const [strategyName, setStrategyName] = useState(getStrategyName(editingStrategy));
  const [strategyIndex, setStrategyIndex] = useState(editingStrategy?.index || 'NIFTY');
  const [strategyConfig, setStrategyConfig] = useState<StrategyConfig>(
    editingStrategy?.config || DEFAULT_STRATEGY_CONFIG
  );
  const [legs, setLegs] = useState<StrategyLeg[]>(editingStrategy?.legs || []);

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
        legsCount: Array.isArray(editingStrategy.legs) ? editingStrategy.legs.length : editingStrategy.legs,
        availableKeys: Object.keys(editingStrategy),
        fullData: editingStrategy
      });

      setStrategyName(resolvedStrategyName);
      setStrategyIndex(editingStrategy.index || 'NIFTY');
      setStrategyConfig(editingStrategy.config || DEFAULT_STRATEGY_CONFIG);
      setLegs(editingStrategy.legs || []);
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