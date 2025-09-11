/**
 * StrikeSelection Component
 * 
 * Handles complex strike price selection logic including:
 * - ATM Point/Percent selection
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

  const handlePremiumOperatorChange = (operator: 'CP_EQUAL' | 'CP_GREATER_EQUAL' | 'CP_LESS_EQUAL') => {
    onUpdate({ premiumOperator: operator });
  };

  const handlePremiumValueChange = (value: number) => {
    onUpdate({ premiumValue: value });
  };

  const handleStraddlePremiumOperatorChange = (operator: 'CP_EQUAL' | 'CP_GREATER_EQUAL' | 'CP_LESS_EQUAL') => {
    onUpdate({ straddlePremiumOperator: operator });
  };

  const handleStraddlePremiumPercentageChange = (percentage: number) => {
    onUpdate({ straddlePremiumPercentage: percentage });
  };

  return (
    <div className="space-y-4">
      {/* Selection Method */}
      <div>
        <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
          Strike Selection
        </label>
        <Select
          value={leg.selectionMethod}
          onChange={(e) => handleSelectionMethodChange(e.target.value as StrategyLeg['selectionMethod'])}
          options={SELECTION_METHOD_OPTIONS}
          className="h-9 text-sm"
        />
      </div>

      {/* Dynamic Selection UI based on method */}
      {leg.selectionMethod === 'CLOSEST_PREMIUM' ? (
        // Premium Selection UI
        <div className="grid grid-cols-2 gap-2">
          {/* Premium Operator */}
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
              Premium Operator
            </label>
            <Select
              value={leg.premiumOperator || 'CP_EQUAL'}
              onChange={(e) => handlePremiumOperatorChange(e.target.value as 'CP_EQUAL' | 'CP_GREATER_EQUAL' | 'CP_LESS_EQUAL')}
              options={PREMIUM_OPERATOR_OPTIONS}
              className="h-9 text-sm"
            />
          </div>
          
          {/* Premium Value */}
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
              Premium Value
            </label>
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
        </div>
      ) : leg.selectionMethod === 'CLOSEST_STRADDLE_PREMIUM' ? (
        // Straddle Premium Selection UI
        <div className="grid grid-cols-2 gap-2">
          {/* Straddle Premium Operator */}
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
              Premium Operator
            </label>
            <Select
              value={leg.straddlePremiumOperator || 'CP_EQUAL'}
              onChange={(e) => handleStraddlePremiumOperatorChange(e.target.value as 'CP_EQUAL' | 'CP_GREATER_EQUAL' | 'CP_LESS_EQUAL')}
              options={PREMIUM_OPERATOR_OPTIONS}
              className="h-9 text-sm"
            />
          </div>
          
          {/* Straddle Premium Percentage */}
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
              Premium %
            </label>
            <Select
              value={(leg.straddlePremiumPercentage || 5).toString()}
              onChange={(e) => handleStraddlePremiumPercentageChange(parseInt(e.target.value))}
              options={generateStraddlePremiumPercentageOptions()}
              className="h-9 text-sm"
            />
          </div>
        </div>
      ) : (
        // Regular Strike Price Selection
        <div>
          <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
            Strike Price
          </label>
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