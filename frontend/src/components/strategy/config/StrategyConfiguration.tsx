/**
 * StrategyConfiguration Component
 * 
 * Strategy-level configuration including:
 * - Range breakout settings
 * - Entry and exit time configuration
 * - Trading type (intraday/positional)
 * - Strategy-level target profit and stop loss
 * - Move SL to cost option
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import React from 'react';
import Input from '../../ui/Input';
import Select from '../../ui/Select';
import { StrategyConfig } from '../../../types/strategy';
import { 
  HOUR_OPTIONS, 
  MINUTE_OPTIONS, 
  MTM_TYPE_OPTIONS 
} from '../../../utils/strategy';

interface StrategyConfigurationProps {
  config: StrategyConfig;
  onUpdate: (updates: Partial<StrategyConfig>) => void;
}

const StrategyConfiguration: React.FC<StrategyConfigurationProps> = ({ config, onUpdate }) => {
  const handleRangeBreakoutChange = (rangeBreakout: boolean) => {
    onUpdate({ rangeBreakout });
  };

  const handleEntryTimeChange = (field: 'entryTimeHour' | 'entryTimeMinute', value: string) => {
    onUpdate({ [field]: value });
  };

  const handleExitTimeChange = (field: 'exitTimeHour' | 'exitTimeMinute', value: string) => {
    onUpdate({ [field]: value });
  };

  const handleRangeBreakoutTimeChange = (field: 'rangeBreakoutTimeHour' | 'rangeBreakoutTimeMinute', value: string) => {
    onUpdate({ [field]: value });
  };

  const handleTradingTypeChange = (tradingType: 'INTRADAY' | 'POSITIONAL') => {
    onUpdate({ tradingType });
  };

  const handleIntradayExitModeChange = (intradayExitMode: 'SAME_DAY' | 'NEXT_DAY_BTST') => {
    onUpdate({ intradayExitMode });
  };

  const handlePositionalDaysChange = (field: 'positionalEntryDays' | 'positionalExitDays', value: number) => {
    onUpdate({ [field]: value });
  };

  const handleTargetProfitChange = (field: 'type' | 'value', value: any) => {
    onUpdate({
      targetProfit: { ...config.targetProfit, [field]: value }
    });
  };

  const handleMtmStopLossChange = (field: 'type' | 'value', value: any) => {
    onUpdate({
      mtmStopLoss: { ...config.mtmStopLoss, [field]: value }
    });
  };

  const handleMoveSlToCostChange = (moveSlToCost: boolean) => {
    onUpdate({ moveSlToCost });
  };

  return (
    <div className="bg-white dark:bg-gray-800 mx-4 mb-4 rounded-xl shadow-lg border border-gray-200/50 dark:border-gray-600/50 p-6">
      <div className="space-y-6">
        {/* Range Breakout Checkbox */}
        <div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={config.rangeBreakout}
              onChange={(e) => handleRangeBreakoutChange(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 focus:ring-2"
            />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-200">Range Breakout</span>
          </label>
        </div>

        {/* Time Configuration Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Entry Time Card */}
          <div className="bg-white/90 dark:bg-gray-800/90 rounded-xl shadow-lg border border-gray-200/50 dark:border-gray-600/50 p-5">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-200">
                  Entry Time
                </label>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Hour</label>
                  <Select
                    value={config.entryTimeHour}
                    onChange={(e) => handleEntryTimeChange('entryTimeHour', e.target.value)}
                    options={HOUR_OPTIONS}
                    className="h-10 text-sm rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Minute</label>
                  <Select
                    value={config.entryTimeMinute}
                    onChange={(e) => handleEntryTimeChange('entryTimeMinute', e.target.value)}
                    options={MINUTE_OPTIONS}
                    className="h-10 text-sm rounded-lg"
                  />
                </div>
              </div>
              
              {/* Range Breakout Time */}
              {config.rangeBreakout && (
                <div className="pt-4 border-t border-gray-200/50 dark:border-gray-600/50">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                    <label className="block text-xs font-medium text-gray-600 dark:text-gray-300">
                      Range Breakout Time
                    </label>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <Select
                      value={config.rangeBreakoutTimeHour}
                      onChange={(e) => handleRangeBreakoutTimeChange('rangeBreakoutTimeHour', e.target.value)}
                      options={HOUR_OPTIONS}
                      className="h-9 text-sm rounded-lg"
                    />
                    <Select
                      value={config.rangeBreakoutTimeMinute}
                      onChange={(e) => handleRangeBreakoutTimeChange('rangeBreakoutTimeMinute', e.target.value)}
                      options={MINUTE_OPTIONS}
                      className="h-9 text-sm rounded-lg"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Exit Time Card */}
          <div className="bg-white/90 dark:bg-gray-800/90 rounded-xl shadow-lg border border-gray-200/50 dark:border-gray-600/50 p-5">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-200">
                  Exit Time
                </label>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Hour</label>
                  <Select
                    value={config.exitTimeHour}
                    onChange={(e) => handleExitTimeChange('exitTimeHour', e.target.value)}
                    options={HOUR_OPTIONS}
                    className="h-10 text-sm rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Minute</label>
                  <Select
                    value={config.exitTimeMinute}
                    onChange={(e) => handleExitTimeChange('exitTimeMinute', e.target.value)}
                    options={MINUTE_OPTIONS}
                    className="h-10 text-sm rounded-lg"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Trading Type Configuration */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Trading Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
              Trading Type
            </label>
            <Select
              value={config.tradingType}
              onChange={(e) => handleTradingTypeChange(e.target.value as 'INTRADAY' | 'POSITIONAL')}
              options={[
                { value: 'INTRADAY', label: 'Intraday' },
                { value: 'POSITIONAL', label: 'Positional' }
              ]}
              className="h-10 text-sm"
            />
          </div>

          {/* Conditional Configuration based on Trading Type */}
          {config.tradingType === 'INTRADAY' ? (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                Intraday Exit Mode
              </label>
              <Select
                value={config.intradayExitMode}
                onChange={(e) => handleIntradayExitModeChange(e.target.value as 'SAME_DAY' | 'NEXT_DAY_BTST')}
                options={[
                  { value: 'SAME_DAY', label: 'Same Day' },
                  { value: 'NEXT_DAY_BTST', label: 'Next Day BTST' }
                ]}
                className="h-10 text-sm"
              />
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                  Entry Days
                </label>
                <Input
                  type="number"
                  min="0"
                  max="30"
                  value={config.positionalEntryDays}
                  onChange={(e) => handlePositionalDaysChange('positionalEntryDays', parseInt(e.target.value) || 0)}
                  className="h-10 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                  Exit Days
                </label>
                <Input
                  type="number"
                  min="0"
                  max="30"
                  value={config.positionalExitDays}
                  onChange={(e) => handlePositionalDaysChange('positionalExitDays', parseInt(e.target.value) || 0)}
                  className="h-10 text-sm"
                />
              </div>
            </div>
          )}
        </div>

        {/* Strategy-level Risk Management */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Target Profit */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
              Strategy Target Profit
            </label>
            <div className="grid grid-cols-2 gap-2">
              <Select
                value={config.targetProfit.type}
                onChange={(e) => handleTargetProfitChange('type', e.target.value)}
                options={MTM_TYPE_OPTIONS}
                className="h-10 text-sm"
              />
              <Input
                type="number"
                min="0"
                step="0.1"
                value={config.targetProfit.value}
                onChange={(e) => handleTargetProfitChange('value', parseFloat(e.target.value) || 0)}
                placeholder="Value"
                className="h-10 text-sm"
              />
            </div>
          </div>

          {/* MTM Stop Loss */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
              Strategy Stop Loss
            </label>
            <div className="grid grid-cols-2 gap-2">
              <Select
                value={config.mtmStopLoss.type}
                onChange={(e) => handleMtmStopLossChange('type', e.target.value)}
                options={MTM_TYPE_OPTIONS}
                className="h-10 text-sm"
              />
              <Input
                type="number"
                min="0"
                step="0.1"
                value={config.mtmStopLoss.value}
                onChange={(e) => handleMtmStopLossChange('value', parseFloat(e.target.value) || 0)}
                placeholder="Value"
                className="h-10 text-sm"
              />
            </div>
          </div>
        </div>

        {/* Move SL to Cost */}
        <div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={config.moveSlToCost}
              onChange={(e) => handleMoveSlToCostChange(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 focus:ring-2"
            />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-200">Move SL to Cost</span>
          </label>
        </div>
      </div>
    </div>
  );
};

export default StrategyConfiguration;