/**
 * TrailingStopLossControl Component
 * 
 * Individual trailing stop loss configuration control for positions.
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import React from 'react';
import Input from '../../ui/Input';
import Select from '../../ui/Select';
import { StrategyLeg } from '../../../types/strategy';
import { TARGET_PROFIT_TYPE_OPTIONS } from '../../../utils/strategy';
import { canEnableTrailingStopLoss, getStopLossInvalidReason } from '../../../utils/strategy/riskValidators';

interface TrailingStopLossControlProps {
  leg: StrategyLeg;
  onUpdate: (updates: Partial<StrategyLeg>) => void;
}

const TrailingStopLossControl: React.FC<TrailingStopLossControlProps> = ({ leg, onUpdate }) => {
  const canEnable = canEnableTrailingStopLoss(leg.stopLoss, leg.trailingStopLoss);
  const disabledReason = getStopLossInvalidReason(leg.stopLoss);

  const handleEnabledChange = (enabled: boolean) => {
    // Only allow enabling if Stop Loss is valid
    if (enabled && !canEnable) {
      return;
    }
    onUpdate({
      trailingStopLoss: { ...leg.trailingStopLoss, enabled }
    });
  };

  const handleTypeChange = (type: 'POINTS' | 'PERCENTAGE') => {
    onUpdate({
      trailingStopLoss: { 
        ...leg.trailingStopLoss, 
        type,
        instrumentMoveValue: 0,
        stopLossMoveValue: 0
      }
    });
  };

  const handleInstrumentMoveChange = (value: number) => {
    onUpdate({
      trailingStopLoss: { ...leg.trailingStopLoss, instrumentMoveValue: value }
    });
  };

  const handleStopLossMoveChange = (value: number) => {
    onUpdate({
      trailingStopLoss: { ...leg.trailingStopLoss, stopLossMoveValue: value }
    });
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center space-x-2">
        <input
          type="checkbox"
          id={`trailingStopLoss-${leg.id}`}
          checked={leg.trailingStopLoss.enabled}
          disabled={!canEnable}
          onChange={(e) => handleEnabledChange(e.target.checked)}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:opacity-50"
          title={!canEnable ? disabledReason || 'Requires valid Stop Loss configuration' : ''}
        />
        <label 
          htmlFor={`trailingStopLoss-${leg.id}`} 
          className={`text-sm font-medium ${
            !canEnable 
              ? 'text-gray-400' 
              : 'text-gray-700 dark:text-gray-200'
          }`}
          title={!canEnable ? disabledReason || 'Requires valid Stop Loss configuration' : ''}
        >
          Trailing Stop Loss
        </label>
      </div>
      
      {leg.trailingStopLoss.enabled && canEnable && (
        <div className="space-y-2">
          {/* Type Selection */}
          <Select
            value={leg.trailingStopLoss.type}
            onChange={(e) => handleTypeChange(e.target.value as 'POINTS' | 'PERCENTAGE')}
            options={TARGET_PROFIT_TYPE_OPTIONS}
            className="h-8 text-sm"
          />
          
          {/* Instrument Move Value */}
          <Input
            type="number"
            min="0"
            step="0.1"
            value={leg.trailingStopLoss.instrumentMoveValue}
            onChange={(e) => handleInstrumentMoveChange(parseFloat(e.target.value) || 0)}
            placeholder="Instrument Move by"
            className="h-8 text-sm"
          />
          
          {/* Stop Loss Move Value */}
          <Input
            type="number"
            min="0"
            step="0.1"
            value={leg.trailingStopLoss.stopLossMoveValue}
            onChange={(e) => handleStopLossMoveChange(parseFloat(e.target.value) || 0)}
            placeholder="Move StopLoss by"
            className="h-8 text-sm"
          />
        </div>
      )}
    </div>
  );
};

export default TrailingStopLossControl;