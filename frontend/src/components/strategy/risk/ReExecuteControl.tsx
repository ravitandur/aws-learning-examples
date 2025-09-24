/**
 * ReExecuteControl Component
 * 
 * Individual re-execute configuration control for positions.
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import React from 'react';
import Select from '../../ui/Select';
import { StrategyLeg } from '../../../types/strategy';
import { RE_EXECUTE_TYPE_OPTIONS, COUNT_OPTIONS } from '../../../utils/strategy';
import { canEnableReExecute, getTargetProfitInvalidReason } from '../../../utils/strategy/riskValidators';

interface ReExecuteControlProps {
  leg: StrategyLeg;
  onUpdate: (updates: Partial<StrategyLeg>) => void;
}

const ReExecuteControl: React.FC<ReExecuteControlProps> = ({ leg, onUpdate }) => {
  // Provide default values if properties are undefined
  const targetProfit = leg.targetProfit || { enabled: false, type: 'POINTS' as const, value: 0 };
  const reExecute = leg.reExecute || { enabled: false, type: 'TP_REEXEC' as const, count: 1 };

  const canEnable = canEnableReExecute(targetProfit);
  const disabledReason = getTargetProfitInvalidReason(targetProfit);

  const handleEnabledChange = (enabled: boolean) => {
    // Only allow enabling if Target Profit is valid
    if (enabled && !canEnable) {
      return;
    }
    onUpdate({
      reExecute: { ...reExecute, enabled }
    });
  };

  const handleTypeChange = (type: 'TP_REEXEC') => {
    onUpdate({
      reExecute: { ...reExecute, type, count: 1 }
    });
  };

  const handleCountChange = (count: number) => {
    onUpdate({
      reExecute: { ...reExecute, count }
    });
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center space-x-2">
        <input
          type="checkbox"
          id={`reExecute-${leg.id}`}
          checked={reExecute.enabled}
          disabled={!canEnable}
          onChange={(e) => handleEnabledChange(e.target.checked)}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:opacity-50"
          title={!canEnable ? disabledReason || 'Requires valid Target Profit configuration' : ''}
        />
        <label
          htmlFor={`reExecute-${leg.id}`}
          className={`text-sm font-medium ${
            !canEnable
              ? 'text-gray-400'
              : 'text-gray-700 dark:text-gray-200'
          }`}
          title={!canEnable ? disabledReason || 'Requires valid Target Profit configuration' : ''}
        >
          Re-Execute (TP)
        </label>
      </div>

      {reExecute.enabled && canEnable && (
        <div className="space-y-2">
          <Select
            value={reExecute.type}
            onChange={(e) => handleTypeChange(e.target.value as 'TP_REEXEC')}
            options={RE_EXECUTE_TYPE_OPTIONS}
            className="h-8 text-sm"
          />
          <Select
            value={reExecute.count.toString()}
            onChange={(e) => handleCountChange(parseInt(e.target.value))}
            options={COUNT_OPTIONS}
            className="h-8 text-sm"
          />
        </div>
      )}
    </div>
  );
};

export default ReExecuteControl;