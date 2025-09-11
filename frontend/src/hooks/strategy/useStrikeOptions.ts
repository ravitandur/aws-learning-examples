/**
 * useStrikeOptions Hook
 * 
 * Hook for managing strike price options generation.
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import { useMemo } from 'react';
import { SelectOption, SelectionMethod } from '../../types/strategy';
import { 
  generatePositionStrikeOptions,
  generateStraddlePremiumPercentageOptions,
  requiresPremiumCriteria,
  requiresStraddlePremiumCriteria,
  usesRegularStrikeSelection
} from '../../utils/strategy';

interface UseStrikeOptionsReturn {
  getStrikeOptions: (selectionMethod: SelectionMethod) => SelectOption[];
  straddlePremiumOptions: SelectOption[];
  checkRequiresPremiumCriteria: (selectionMethod: SelectionMethod) => boolean;
  checkRequiresStraddlePremiumCriteria: (selectionMethod: SelectionMethod) => boolean;
  checkUsesRegularStrikeSelection: (selectionMethod: SelectionMethod) => boolean;
}

export const useStrikeOptions = (): UseStrikeOptionsReturn => {
  
  // Memoize straddle premium options since they don't change
  const straddlePremiumOptions = useMemo(() => 
    generateStraddlePremiumPercentageOptions(), 
    []
  );
  
  // Generate strike options based on selection method
  const getStrikeOptions = useMemo(() => 
    (selectionMethod: SelectionMethod): SelectOption[] => 
      generatePositionStrikeOptions(selectionMethod),
    []
  );
  
  return {
    getStrikeOptions,
    straddlePremiumOptions,
    checkRequiresPremiumCriteria: requiresPremiumCriteria,
    checkRequiresStraddlePremiumCriteria: requiresStraddlePremiumCriteria,
    checkUsesRegularStrikeSelection: usesRegularStrikeSelection
  };
};