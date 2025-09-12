/**
 * StrikeSelection Component
 * 
 * Handles complex strike price selection logic including:
 * - ATM Points/Percent selection
 * - Closest Premium selection with operator and value
 * - Closest Straddle Premium selection with operator and percentage
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import React from 'react';
import Input from '../../ui/Input';
import Select from '../../ui/Select';
import { StrategyLeg } from '../../../types/strategy';
import { 
  SELECTION_METHOD_OPTIONS, 
  PREMIUM_OPERATOR_OPTIONS 
} from '../../../utils/strategy';
import { useStrikeOptions } from '../../../hooks/strategy/useStrikeOptions';

interface StrikeSelectionProps {
  leg: StrategyLeg;
  onUpdate: (updates: Partial<StrategyLeg>) => void;
}

const StrikeSelection: React.FC<StrikeSelectionProps> = ({ leg, onUpdate }) => {
  const { generatePositionStrikeOptions, generateStraddlePremiumPercentageOptions } = useStrikeOptions();

  const handleSelectionMethodChange = (method: StrategyLeg['selectionMethod']) => {
    onUpdate({
      selectionMethod: method,
      strikePrice: 'ATM'
    });
  };

  const handleStrikePriceChange = (strikePrice: string) => {
    onUpdate({ strikePrice });
  };

  const handlePremiumOperatorChange = (operator: 'CLOSEST' | 'GTE' | 'LTE') => {
    onUpdate({ premiumOperator: operator });
  };

  const handlePremiumValueChange = (value: number) => {
    onUpdate({ premiumValue: value });
  };

  const handleStraddlePremiumOperatorChange = (operator: 'CLOSEST' | 'GTE' | 'LTE') => {
    onUpdate({ straddlePremiumOperator: operator });
  };

  const handleStraddlePremiumPercentageChange = (percentage: number) => {
    onUpdate({ straddlePremiumPercentage: percentage });
  };

  return (
    <div>
      <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
        Strike Selection
      </label>
      
      {/* Single Row Layout for Strike Selection */}
      {leg.selectionMethod === 'PREMIUM' ? (
        // Premium Selection UI - 3 columns
        <div className="grid grid-cols-3 gap-2">
          {/* Selection Method */}
          <Select
            value={leg.selectionMethod}
            onChange={(e) => handleSelectionMethodChange(e.target.value as StrategyLeg['selectionMethod'])}
            options={SELECTION_METHOD_OPTIONS}
            className="h-9 text-sm"
          />
          
          {/* Premium Operator */}
          <Select
            value={leg.premiumOperator || 'CLOSEST'}
            onChange={(e) => handlePremiumOperatorChange(e.target.value as 'CLOSEST' | 'GTE' | 'LTE')}
            options={PREMIUM_OPERATOR_OPTIONS}
            className="h-9 text-sm"
          />
          
          {/* Premium Value */}
          <Input
            type="number"
            min="0"
            step="0.1"
            value={leg.premiumValue || 0}
            onChange={(e) => handlePremiumValueChange(parseFloat(e.target.value) || 0)}
            placeholder="Enter premium"
            className="h-9 text-sm"
          />
        </div>
      ) : leg.selectionMethod === 'PERCENTAGE_OF_STRADDLE_PREMIUM' ? (
        // Straddle Premium Selection UI - 3 columns
        <div className="grid grid-cols-3 gap-2">
          {/* Selection Method */}
          <Select
            value={leg.selectionMethod}
            onChange={(e) => handleSelectionMethodChange(e.target.value as StrategyLeg['selectionMethod'])}
            options={SELECTION_METHOD_OPTIONS}
            className="h-9 text-sm"
          />
          
          {/* Straddle Premium Operator */}
          <Select
            value={leg.straddlePremiumOperator || 'CLOSEST'}
            onChange={(e) => handleStraddlePremiumOperatorChange(e.target.value as 'CLOSEST' | 'GTE' | 'LTE')}
            options={PREMIUM_OPERATOR_OPTIONS}
            className="h-9 text-sm"
          />
          
          {/* Straddle Premium Percentage */}
          <Select
            value={(leg.straddlePremiumPercentage || 5).toString()}
            onChange={(e) => handleStraddlePremiumPercentageChange(parseInt(e.target.value))}
            options={generateStraddlePremiumPercentageOptions()}
            className="h-9 text-sm"
          />
        </div>
      ) : (
        // Regular Strike Price Selection - 2 columns
        <div className="grid grid-cols-2 gap-2">
          {/* Selection Method */}
          <Select
            value={leg.selectionMethod}
            onChange={(e) => handleSelectionMethodChange(e.target.value as StrategyLeg['selectionMethod'])}
            options={SELECTION_METHOD_OPTIONS}
            className="h-9 text-sm"
          />
          
          {/* Strike Price */}
          <Select
            value={leg.strikePrice}
            onChange={(e) => handleStrikePriceChange(e.target.value)}
            options={generatePositionStrikeOptions(leg.selectionMethod)}
            className="h-9 text-sm"
          />
        </div>
      )}
    </div>
  );
};

export default StrikeSelection;