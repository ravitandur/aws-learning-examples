/**
 * WaitAndTradeControl Component
 * 
 * Individual wait & trade configuration control for positions.
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import React from 'react';
import Input from '../../ui/Input';
import Select from '../../ui/Select';
import { StrategyLeg } from '../../../types/strategy';
import { TARGET_PROFIT_TYPE_OPTIONS } from '../../../utils/strategy';

interface WaitAndTradeControlProps {
  leg: StrategyLeg;
  onUpdate: (updates: Partial<StrategyLeg>) => void;
}

const WaitAndTradeControl: React.FC<WaitAndTradeControlProps> = ({ leg, onUpdate }) => {
  // Provide default values if properties are undefined
  const waitAndTrade = leg.waitAndTrade || { enabled: false, type: 'POINTS' as const, value: 0 };

  const handleEnabledChange = (enabled: boolean) => {
    onUpdate({
      waitAndTrade: { ...waitAndTrade, enabled }
    });
  };

  const handleTypeChange = (type: 'POINTS' | 'PERCENTAGE') => {
    onUpdate({
      waitAndTrade: { ...waitAndTrade, type, value: 0 }
    });
  };

  const handleValueChange = (value: number) => {
    onUpdate({
      waitAndTrade: { ...waitAndTrade, value }
    });
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center space-x-2">
        <input
          type="checkbox"
          id={`waitAndTrade-${leg.id}`}
          checked={waitAndTrade.enabled}
          onChange={(e) => handleEnabledChange(e.target.checked)}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        <label
          htmlFor={`waitAndTrade-${leg.id}`}
          className="text-sm font-medium text-gray-700 dark:text-gray-200"
        >
          Wait & Trade
        </label>
      </div>

      {waitAndTrade.enabled && (
        <div className="space-y-2">
          <Select
            value={waitAndTrade.type}
            onChange={(e) => handleTypeChange(e.target.value as 'POINTS' | 'PERCENTAGE')}
            options={TARGET_PROFIT_TYPE_OPTIONS}
            className="h-8 text-sm"
          />
          <Input
            type="number"
            min="0"
            step="0.1"
            value={waitAndTrade.value}
            onChange={(e) => handleValueChange(parseFloat(e.target.value) || 0)}
            placeholder="Wait & trade value"
            className="h-8 text-sm"
          />
        </div>
      )}
    </div>
  );
};

export default WaitAndTradeControl;