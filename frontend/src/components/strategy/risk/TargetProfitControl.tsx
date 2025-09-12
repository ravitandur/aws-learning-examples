/**
 * TargetProfitControl Component
 * 
 * Individual target profit configuration control for positions.
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import React from 'react';
import Input from '../../ui/Input';
import Select from '../../ui/Select';
import { StrategyLeg } from '../../../types/strategy';
import { TARGET_PROFIT_TYPE_OPTIONS } from '../../../utils/strategy';
import { isValidTargetProfit } from '../../../utils/strategy/riskValidators';

interface TargetProfitControlProps {
  leg: StrategyLeg;
  onUpdate: (updates: Partial<StrategyLeg>) => void;
}

const TargetProfitControl: React.FC<TargetProfitControlProps> = ({ leg, onUpdate }) => {
  const handleEnabledChange = (enabled: boolean) => {
    const newTargetProfit = { ...leg.targetProfit, enabled };
    const isValid = enabled && isValidTargetProfit(newTargetProfit);
    
    onUpdate({
      targetProfit: newTargetProfit,
      // Disable Re Execute if Target Profit becomes invalid
      reExecute: isValid ? leg.reExecute : { ...leg.reExecute, enabled: false }
    });
  };

  const handleTypeChange = (type: 'POINTS' | 'PERCENTAGE') => {
    const newTargetProfit = { ...leg.targetProfit, type, value: 0 };
    const isValid = isValidTargetProfit(newTargetProfit);
    
    onUpdate({
      targetProfit: newTargetProfit,
      // Disable Re Execute if Target Profit becomes invalid
      reExecute: isValid ? leg.reExecute : { ...leg.reExecute, enabled: false }
    });
  };

  const handleValueChange = (value: number) => {
    const newTargetProfit = { ...leg.targetProfit, value };
    const isValid = isValidTargetProfit(newTargetProfit);
    
    onUpdate({
      targetProfit: newTargetProfit,
      // Disable Re Execute if Target Profit becomes invalid
      reExecute: isValid ? leg.reExecute : { ...leg.reExecute, enabled: false }
    });
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center space-x-2">
        <input
          type="checkbox"
          id={`targetProfit-${leg.id}`}
          checked={leg.targetProfit.enabled}
          onChange={(e) => handleEnabledChange(e.target.checked)}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        <label 
          htmlFor={`targetProfit-${leg.id}`} 
          className="text-sm font-medium text-gray-700 dark:text-gray-200"
        >
          Target Profit
        </label>
      </div>
      
      {leg.targetProfit.enabled && (
        <div className="space-y-2">
          <Select
            value={leg.targetProfit.type}
            onChange={(e) => handleTypeChange(e.target.value as 'POINTS' | 'PERCENTAGE')}
            options={TARGET_PROFIT_TYPE_OPTIONS}
            className="h-8 text-sm"
          />
          <Input
            type="number"
            min="0"
            step="0.1"
            value={leg.targetProfit.value}
            onChange={(e) => handleValueChange(parseFloat(e.target.value) || 0)}
            placeholder="Target profit value"
            className="h-8 text-sm"
          />
        </div>
      )}
    </div>
  );
};

export default TargetProfitControl;