/**
 * useStrategySubmission Hook
 * 
 * Hook for handling strategy submission to API.
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import { useCallback, useState } from 'react';
import { StrategyFormData } from '../../types/strategy';
import { FrontendStrategyData } from '../../services/strategyTransformationService';
import strategyService from '../../services/strategyService';
import strategyTransformationService from '../../services/strategyTransformationService';

interface UseStrategySubmissionProps {
  basketId: string;
  strategyName: string;
  strategyIndex: string;  // NEW: Strategy-level index selection
  legs: any[];
  strategyConfig: any;
  editingStrategy?: any; // Optional strategy data for edit mode
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
  strategyIndex,  // NEW: Strategy-level index
  legs,
  strategyConfig,
  editingStrategy, // NEW: Strategy data for edit mode
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
      index: strategyIndex, // Use actual strategy-level index
      config: strategyConfig,
      legs: legs.map(leg => ({
        id: leg.id,
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
    console.log('🔍 [DEBUG] Form data validation:', {
      formData,
      hasValidation: !!validation,
      validateMethod: typeof validation.validateAndSetError
    });

    // Create wrapper function to convert showError to setError signature
    const setErrorWrapper = (error: string | null) => {
      if (error) {
        console.error('🚨 [VALIDATION ERROR]:', error);
        showError(error);
      }
    };

    if (!validation.validateAndSetError(formData, setErrorWrapper)) {
      console.error('❌ [VALIDATION] Form validation failed');
      return;
    }

    console.log('✅ [VALIDATION] Form validation passed');

    try {
      setIsSubmitting(true);

      // Determine if we're editing or creating
      const isEditing = !!editingStrategy;

      // Prepare strategy data in frontend format
      const strategyData: FrontendStrategyData = {
        basketId: formData.basketId,
        strategyName: formData.strategyName,
        strategyId: isEditing ? editingStrategy.strategyId : 'temp-id', // Required field
        index: formData.index,
        config: formData.config,
        legs: formData.legs.map((leg, index) => {
          // Handle property name variations and provide defaults
          const optionType = leg.optionType || (leg as any).option_type || 'CE';
          const actionType = leg.actionType || (leg as any).action_type || 'BUY';
          const selectionMethod = leg.selectionMethod || (leg as any).selection_method || 'ATM_POINTS';

          console.log(`🔍 [DEBUG] Processing leg ${index + 1} for submission:`, {
            originalLeg: leg,
            resolvedOptionType: optionType,
            resolvedActionType: actionType,
            resolvedSelectionMethod: selectionMethod,
            availableKeys: Object.keys(leg)
          });

          return {
            id: leg.id,
            optionType: optionType,
            actionType: actionType,
            strikePrice: leg.strikePrice,
            totalLots: leg.totalLots,
            expiryType: strategyConfig.expiryType,
            selectionMethod: selectionMethod,
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
          };
        })
      };

      console.log(`🔄 [DEBUG] ${isEditing ? 'Updating' : 'Creating'} strategy:`, {
        isEditing,
        strategyId: isEditing ? editingStrategy.strategyId : 'new',
        strategyName: strategyName.trim(),
        basketId: formData.basketId
      });

      let result;
      if (isEditing) {
        // For updates, we need to transform the frontend data to backend format
        // just like the create operation does
        console.log('🔍 [DEBUG] Strategy data before validation:', {
          strategyData,
          legsCount: strategyData.legs.length,
          firstLeg: strategyData.legs[0],
          allLegsValid: strategyData.legs.every(leg => leg.optionType && leg.actionType && leg.selectionMethod)
        });

        console.log('🔍 [DEBUG] Calling validateFrontendDataAdvanced with:', {
          strategyData,
          hasTransformationService: !!strategyTransformationService,
          validateMethod: typeof strategyTransformationService.validateFrontendDataAdvanced
        });

        const validation = await strategyTransformationService.validateFrontendDataAdvanced(strategyData);

        console.log('🔍 [DEBUG] Advanced validation result:', {
          isValid: validation.isValid,
          errorsCount: validation.errors?.length || 0,
          warningsCount: validation.warnings?.length || 0,
          errors: validation.errors,
          warnings: validation.warnings
        });

        if (!validation.isValid) {
          const errorMessage = `Validation failed: ${validation.errors.join(', ')}`;
          if (validation.warnings.length > 0) {
            console.warn('⚠️ [VALIDATION WARNINGS]:', validation.warnings);
          }
          console.error('❌ [ADVANCED VALIDATION] Failed:', errorMessage);
          throw new Error(errorMessage);
        }

        console.log('✅ [ADVANCED VALIDATION] Passed successfully');

        // Transform frontend data to backend format for update
        const backendPayload = strategyTransformationService.createApiPayload(
          formData.basketId,
          strategyData,
          strategyData.index,
          strategyData.config.expiryType
        );

        // Use the standard strategyId property
        const strategyId = editingStrategy.strategyId;

        if (!strategyId) {
          throw new Error('Strategy ID not found in editing strategy. Available properties: ' + Object.keys(editingStrategy).join(', '));
        }

        // Update existing strategy with transformed backend data
        result = await strategyService.updateStrategy(strategyId, backendPayload);
      } else {
        // Create new strategy (this already handles transformation internally)
        result = await strategyService.createStrategy(formData.basketId, strategyData);
      }

      if (result.success) {
        // Both editing and creation: API already done in hook, parent handles UI updates only
        if (isEditing) {
          // Pass the updated strategy data to parent for UI state management
          onSubmit({
            success: true,
            data: result,
            message: result.message || 'Strategy updated successfully',
            updatedStrategy: strategyData // Include the strategy data for UI updates
          });
        } else {
          // For creation, pass the real API result to parent for UI updates only
          onSubmit({
            success: true,
            data: result,
            message: result.message || 'Strategy created successfully',
            createdStrategy: result.data // Real strategy data from API
          });
        }

        // Show success message and close dialog
        const actionText = isEditing ? 'updated' : 'created';
        showSuccess(`Strategy "${strategyName.trim()}" ${actionText} successfully!`);
        onClose();
      } else {
        const actionText = isEditing ? 'update' : 'create';
        throw new Error(result.message || `Failed to ${actionText} strategy`);
      }
    } catch (error: any) {
      const actionText = !!editingStrategy ? 'update' : 'create';
      console.error(`Strategy ${actionText} error:`, error);
      showError(error.message || `Failed to ${actionText} strategy. Please try again.`);
    } finally {
      setIsSubmitting(false);
    }
  }, [basketId, strategyName, strategyIndex, legs, strategyConfig, editingStrategy, onSubmit, onClose, showError, showSuccess, validation]);
  
  return {
    handleSubmit,
    isSubmitting
  };
};