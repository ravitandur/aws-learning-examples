/**
 * useStrategyValidation Hook
 * 
 * Hook for handling strategy form validation.
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import { useCallback } from 'react';
import { StrategyFormData, ValidationResult } from '../../types/strategy';
import { 
  validateStrategyForm, 
  validateRequiredFields 
} from '../../utils/strategy';

interface UseStrategyValidationReturn {
  validateForm: (data: StrategyFormData) => ValidationResult;
  validateRequired: (data: Partial<StrategyFormData>) => ValidationResult;
  validateAndSetError: (data: StrategyFormData, setError: (error: string | null) => void) => boolean;
}

export const useStrategyValidation = (): UseStrategyValidationReturn => {
  
  // Validate complete form
  const validateForm = useCallback((data: StrategyFormData): ValidationResult => {
    return validateStrategyForm(data);
  }, []);
  
  // Validate required fields only
  const validateRequired = useCallback((data: Partial<StrategyFormData>): ValidationResult => {
    return validateRequiredFields(data);
  }, []);
  
  // Validate and set error state
  const validateAndSetError = useCallback((
    data: StrategyFormData, 
    setError: (error: string | null) => void
  ): boolean => {
    const validation = validateForm(data);
    
    if (!validation.isValid) {
      // Show first error to user
      setError(validation.errors[0] || 'Please fix the validation errors');
      return false;
    }
    
    setError(null);
    return true;
  }, [validateForm]);
  
  return {
    validateForm,
    validateRequired,
    validateAndSetError
  };
};