/**
 * useStrategySubmission Hook
 * 
 * Hook for handling strategy submission to API.
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import { useCallback } from 'react';
import { StrategyFormData } from '../../types/strategy';
import { FrontendStrategyData } from '../../services/strategyTransformationService';
import strategyService from '../../services/strategyService';

interface UseStrategySubmissionProps {
  onSubmit: (strategyData: any) => void;
  onClose: () => void;
  setIsSubmitting: (submitting: boolean) => void;
  setError: (error: string | null) => void;
}

interface UseStrategySubmissionReturn {
  submitStrategy: (formData: StrategyFormData) => Promise<void>;
}

export const useStrategySubmission = ({
  onSubmit,
  onClose,
  setIsSubmitting,
  setError
}: UseStrategySubmissionProps): UseStrategySubmissionReturn => {
  
  const submitStrategy = useCallback(async (formData: StrategyFormData) => {
    try {
      setIsSubmitting(true);
      setError(null);

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
          expiryType: leg.expiryType,
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
        // Call the parent onSubmit handler with the result
        await onSubmit(result);
        // Close dialog on success
        onClose();
      } else {
        throw new Error(result.message || 'Failed to create strategy');
      }
    } catch (error: any) {
      console.error('Strategy creation error:', error);
      setError(error.message || 'Failed to create strategy. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }, [onSubmit, onClose, setIsSubmitting, setError]);
  
  return {
    submitStrategy
  };
};