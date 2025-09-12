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
  onClose 
}: UseStrategyFormProps): UseStrategyFormReturn => {
  // Refs
  const dialogRef = useRef<HTMLDivElement>(null);
  
  // Form state
  const [strategyName, setStrategyName] = useState('');
  const [strategyIndex, setStrategyIndex] = useState('NIFTY');
  const [strategyConfig, setStrategyConfig] = useState<StrategyConfig>(DEFAULT_STRATEGY_CONFIG);
  const [legs, setLegs] = useState<StrategyLeg[]>([]);
  
  // UI state
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
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
      index: leg.index,
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