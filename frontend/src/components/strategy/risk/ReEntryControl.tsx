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
  const canEnable = canEnableReEntry(leg.stopLoss);
  const disabledReason = getStopLossInvalidReason(leg.stopLoss);

  const handleEnabledChange = (enabled: boolean) => {
    // Only allow enabling if Stop Loss is valid
    if (enabled && !canEnable) {
      return;
    }
    onUpdate({
      reEntry: { ...leg.reEntry, enabled }
    });
  };

  const handleTypeChange = (type: 'SL_REENTRY' | 'SL_RECOST' | 'SL_REEXEC') => {
    onUpdate({
      reEntry: { ...leg.reEntry, type, count: 1 }
    });
  };

  const handleCountChange = (count: number) => {
    onUpdate({
      reEntry: { ...leg.reEntry, count }
    });
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center space-x-2">
        <input
          type="checkbox"
          id={`reEntry-${leg.id}`}
          checked={leg.reEntry.enabled}
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
      
      {leg.reEntry.enabled && canEnable && (
        <div className="space-y-2">
          <Select
            value={leg.reEntry.type}
            onChange={(e) => handleTypeChange(e.target.value as 'SL_REENTRY' | 'SL_RECOST' | 'SL_REEXEC')}
            options={RE_ENTRY_TYPE_OPTIONS}
            className="h-8 text-sm"
          />
          <Select
            value={leg.reEntry.count.toString()}
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