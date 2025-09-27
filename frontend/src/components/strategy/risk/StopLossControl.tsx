/**
 * StopLossControl Component
 * 
 * Individual stop loss configuration control for positions.
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import React from 'react';
import Input from '../../ui/Input';
import Select from '../../ui/Select';
import { Leg } from '../../../types/strategy';
import { RISK_MANAGEMENT_TYPE_OPTIONS } from '../../../utils/strategy';
import { isValidStopLoss } from '../../../utils/strategy/riskValidators';

interface StopLossControlProps {
  leg: Leg;
  onUpdate: (updates: Partial<Leg>) => void;
}

const StopLossControl: React.FC<StopLossControlProps> = ({ leg, onUpdate }) => {
  // Provide default values if stopLoss is undefined
  const stopLoss = leg.stopLoss || { enabled: false, type: 'POINTS' as const, value: 0 };
  const trailingStopLoss = leg.trailingStopLoss || { enabled: false, type: 'POINTS' as const, instrumentMoveValue: 0, stopLossMoveValue: 0 };
  const reEntry = leg.reEntry || { enabled: false, type: 'SL_REENTRY' as const, count: 1 };

  const handleEnabledChange = (enabled: boolean) => {
    const newStopLoss = { ...stopLoss, enabled };
    const isValid = enabled && isValidStopLoss(newStopLoss);

    onUpdate({
      stopLoss: newStopLoss,
      // Disable dependent controls if stop loss becomes invalid
      trailingStopLoss: isValid ? trailingStopLoss : { ...trailingStopLoss, enabled: false },
      reEntry: isValid ? reEntry : { ...reEntry, enabled: false }
    });
  };

  const handleTypeChange = (type: 'POINTS' | 'PERCENTAGE' | 'RANGE') => {
    const newStopLoss = { ...stopLoss, type, value: 0 };
    const isValid = isValidStopLoss(newStopLoss);

    onUpdate({
      stopLoss: newStopLoss,
      // Disable dependent controls if stop loss becomes invalid
      trailingStopLoss: isValid ? trailingStopLoss : { ...trailingStopLoss, enabled: false },
      reEntry: isValid ? reEntry : { ...reEntry, enabled: false }
    });
  };

  const handleValueChange = (value: number) => {
    const newStopLoss = { ...stopLoss, value };
    const isValid = isValidStopLoss(newStopLoss);

    onUpdate({
      stopLoss: newStopLoss,
      // Disable dependent controls if stop loss becomes invalid
      trailingStopLoss: isValid ? trailingStopLoss : { ...trailingStopLoss, enabled: false },
      reEntry: isValid ? reEntry : { ...reEntry, enabled: false }
    });
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center space-x-2">
        <input
          type="checkbox"
          id={`stopLoss-${leg.id}`}
          checked={stopLoss.enabled}
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

      {stopLoss.enabled && (
        <div className="space-y-2">
          <Select
            value={stopLoss.type}
            onChange={(e) => handleTypeChange(e.target.value as 'POINTS' | 'PERCENTAGE' | 'RANGE')}
            options={RISK_MANAGEMENT_TYPE_OPTIONS}
            className="h-8 text-sm"
          />
          <Input
            type="number"
            min="0"
            step="0.1"
            value={stopLoss.value}
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