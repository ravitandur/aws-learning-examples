/**
 * useStrategySubmission Hook
 * 
 * Hook for handling strategy submission to API.
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import { useCallback, useState } from 'react';
import { StrategyFormData, ValidationResult } from '../../types/strategy';
import { FrontendStrategyData } from '../../services/strategyTransformationService';
import strategyService from '../../services/strategyService';

interface UseStrategySubmissionProps {
  basketId: string;
  strategyName: string;
  legs: any[];
  strategyConfig: any;
  onSubmit: (strategyData: any) => void;
  onClose: () => void;
  showError: (message: string) => void;
  showSuccess: (message: string) => void;
  validation: {
    validateAndSetError: (data: StrategyFormData, setError: (error: string | null) => void) => boolean;
  };
}

interface UseStrategySubmissionReturn {
  handleSubmit: () => Promise<void>;
  isSubmitting: boolean;
}

export const useStrategySubmission = ({
  basketId,
  strategyName,
  legs,
  strategyConfig,
  onSubmit,
  onClose,
  showError,
  showSuccess,
  validation
}: UseStrategySubmissionProps): UseStrategySubmissionReturn => {
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const handleSubmit = useCallback(async () => {
    // Prepare form data for validation
    const formData: StrategyFormData = {
      basketId,
      strategyName: strategyName.trim(),
      index: 'NIFTY', // Default index
      config: strategyConfig,
      legs: legs.map(leg => ({
        id: leg.id,
        index: leg.index,
        optionType: leg.optionType,
        actionType: leg.actionType,
        strikePrice: leg.strikePrice,
        totalLots: leg.totalLots,
        expiryType: strategyConfig.expiryType,
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
    };

    // Validate form data
    // Create wrapper function to convert showError to setError signature
    const setErrorWrapper = (error: string | null) => {
      if (error) {
        showError(error);
      }
    };
    
    if (!validation.validateAndSetError(formData, setErrorWrapper)) {
      return;
    }

    try {
      setIsSubmitting(true);

      // Prepare strategy data in frontend format
      const strategyData: FrontendStrategyData = {
        basketId: formData.basketId,
        strategyName: formData.strategyName,
        index: formData.index,
        config: formData.config,
        legs: formData.legs.map(leg => ({
          id: leg.id,
          index: leg.index,
          optionType: leg.optionType,
          actionType: leg.actionType,
          strikePrice: leg.strikePrice,
          totalLots: leg.totalLots,
          expiryType: strategyConfig.expiryType,
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
      };

      // Use strategy service to create strategy (includes data transformation)
      const result = await strategyService.createStrategy(formData.basketId, strategyData);

      if (result.success) {
        // Show success notification
        showSuccess(`Strategy "${strategyName.trim()}" created successfully!`);
        
        // Call the parent onSubmit handler with the result
        await onSubmit(result);
        // Close dialog on success
        onClose();
      } else {
        throw new Error(result.message || 'Failed to create strategy');
      }
    } catch (error: any) {
      console.error('Strategy creation error:', error);
      showError(error.message || 'Failed to create strategy. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }, [basketId, strategyName, legs, strategyConfig, onSubmit, onClose, showError, showSuccess, validation]);
  
  return {
    handleSubmit,
    isSubmitting
  };
};