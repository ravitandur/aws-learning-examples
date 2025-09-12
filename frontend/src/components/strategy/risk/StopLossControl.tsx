/**
 * StopLossControl Component
 * 
 * Individual stop loss configuration control for positions.
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import React from 'react';
import Input from '../../ui/Input';
import Select from '../../ui/Select';
import { StrategyLeg } from '../../../types/strategy';
import { RISK_MANAGEMENT_TYPE_OPTIONS } from '../../../utils/strategy';
import { isValidStopLoss } from '../../../utils/strategy/riskValidators';

interface StopLossControlProps {
  leg: StrategyLeg;
  onUpdate: (updates: Partial<StrategyLeg>) => void;
}

const StopLossControl: React.FC<StopLossControlProps> = ({ leg, onUpdate }) => {
  const handleEnabledChange = (enabled: boolean) => {
    const newStopLoss = { ...leg.stopLoss, enabled };
    const isValid = enabled && isValidStopLoss(newStopLoss);
    
    onUpdate({
      stopLoss: newStopLoss,
      // Disable dependent controls if stop loss becomes invalid
      trailingStopLoss: isValid ? leg.trailingStopLoss : { ...leg.trailingStopLoss, enabled: false },
      reEntry: isValid ? leg.reEntry : { ...leg.reEntry, enabled: false }
    });
  };

  const handleTypeChange = (type: 'POINTS' | 'PERCENTAGE' | 'RANGE') => {
    const newStopLoss = { ...leg.stopLoss, type, value: 0 };
    const isValid = isValidStopLoss(newStopLoss);
    
    onUpdate({
      stopLoss: newStopLoss,
      // Disable dependent controls if stop loss becomes invalid
      trailingStopLoss: isValid ? leg.trailingStopLoss : { ...leg.trailingStopLoss, enabled: false },
      reEntry: isValid ? leg.reEntry : { ...leg.reEntry, enabled: false }
    });
  };

  const handleValueChange = (value: number) => {
    const newStopLoss = { ...leg.stopLoss, value };
    const isValid = isValidStopLoss(newStopLoss);
    
    onUpdate({
      stopLoss: newStopLoss,
      // Disable dependent controls if stop loss becomes invalid
      trailingStopLoss: isValid ? leg.trailingStopLoss : { ...leg.trailingStopLoss, enabled: false },
      reEntry: isValid ? leg.reEntry : { ...leg.reEntry, enabled: false }
    });
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center space-x-2">
        <input
          type="checkbox"
          id={`stopLoss-${leg.id}`}
          checked={leg.stopLoss.enabled}
          onChange={(e) => handleEnabledChange(e.target.checked)}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        <label 
          htmlFor={`stopLoss-${leg.id}`} 
          className="text-sm font-medium text-gray-700 dark:text-gray-200"
        >
          Stop Loss
        </label>
      </div>
      
      {leg.stopLoss.enabled && (
        <div className="space-y-2">
          <Select
            value={leg.stopLoss.type}
            onChange={(e) => handleTypeChange(e.target.value as 'POINTS' | 'PERCENTAGE' | 'RANGE')}
            options={RISK_MANAGEMENT_TYPE_OPTIONS}
            className="h-8 text-sm"
          />
          <Input
            type="number"
            min="0"
            step="0.1"
            value={leg.stopLoss.value}
            onChange={(e) => handleValueChange(parseFloat(e.target.value) || 0)}
            placeholder="Stop loss value"
            className="h-8 text-sm"
          />
        </div>
      )}
    </div>
  );
};

export default StopLossControl;