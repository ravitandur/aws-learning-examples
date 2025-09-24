/**
 * ReEntryControl Component
 * 
 * Individual re-entry configuration control for positions.
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import React from 'react';
import Select from '../../ui/Select';
import { StrategyLeg } from '../../../types/strategy';
import { RE_ENTRY_TYPE_OPTIONS, COUNT_OPTIONS } from '../../../utils/strategy';
import { canEnableReEntry, getStopLossInvalidReason } from '../../../utils/strategy/riskValidators';

interface ReEntryControlProps {
  leg: StrategyLeg;
  onUpdate: (updates: Partial<StrategyLeg>) => void;
}

const ReEntryControl: React.FC<ReEntryControlProps> = ({ leg, onUpdate }) => {
  // Provide default values if properties are undefined
  const stopLoss = leg.stopLoss || { enabled: false, type: 'POINTS' as const, value: 0 };
  const reEntry = leg.reEntry || { enabled: false, type: 'SL_REENTRY' as const, count: 1 };

  const canEnable = canEnableReEntry(stopLoss);
  const disabledReason = getStopLossInvalidReason(stopLoss);

  const handleEnabledChange = (enabled: boolean) => {
    // Only allow enabling if Stop Loss is valid
    if (enabled && !canEnable) {
      return;
    }
    onUpdate({
      reEntry: { ...reEntry, enabled }
    });
  };

  const handleTypeChange = (type: 'SL_REENTRY' | 'SL_RECOST' | 'SL_REEXEC') => {
    onUpdate({
      reEntry: { ...reEntry, type, count: 1 }
    });
  };

  const handleCountChange = (count: number) => {
    onUpdate({
      reEntry: { ...reEntry, count }
    });
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center space-x-2">
        <input
          type="checkbox"
          id={`reEntry-${leg.id}`}
          checked={reEntry.enabled}
          disabled={!canEnable}
          onChange={(e) => handleEnabledChange(e.target.checked)}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:opacity-50"
          title={!canEnable ? disabledReason || 'Requires valid Stop Loss configuration' : ''}
        />
        <label
          htmlFor={`reEntry-${leg.id}`}
          className={`text-sm font-medium ${
            !canEnable
              ? 'text-gray-400'
              : 'text-gray-700 dark:text-gray-200'
          }`}
          title={!canEnable ? disabledReason || 'Requires valid Stop Loss configuration' : ''}
        >
          Re-Entry (SL)
        </label>
      </div>

      {reEntry.enabled && canEnable && (
        <div className="space-y-2">
          <Select
            value={reEntry.type}
            onChange={(e) => handleTypeChange(e.target.value as 'SL_REENTRY' | 'SL_RECOST' | 'SL_REEXEC')}
            options={RE_ENTRY_TYPE_OPTIONS}
            className="h-8 text-sm"
          />
          <Select
            value={reEntry.count.toString()}
            onChange={(e) => handleCountChange(parseInt(e.target.value))}
            options={COUNT_OPTIONS}
            className="h-8 text-sm"
          />
        </div>
      )}
    </div>
  );
};

export default ReEntryControl;