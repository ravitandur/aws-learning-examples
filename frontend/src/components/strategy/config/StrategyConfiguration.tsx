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

  const handleTradingDaysChange = (field: 'entryTradingDaysBeforeExpiry' | 'exitTradingDaysBeforeExpiry', value: number) => {
    onUpdate({ [field]: value });
  };

  // Get slider range based on expiry type
  const getSliderRange = () => {
    return config.expiryType === 'weekly' ? { max: 4, min: 0 } : { max: 24, min: 0 };
  };

  const getTradingDaysText = (value: number) => {
    return `${value} trading days before ${config.expiryType} expiry (excluding holidays)`;
  };

  // Get default values based on expiry type
  const getDefaultTradingDays = () => {
    if (config.expiryType === 'weekly') {
      return { entry: 4, exit: 0 };
    } else {
      return { entry: 24, exit: 0 };
    }
  };

  // Reset trading days when expiry type changes
  React.useEffect(() => {
    const defaults = getDefaultTradingDays();
    onUpdate({
      entryTradingDaysBeforeExpiry: defaults.entry,
      exitTradingDaysBeforeExpiry: defaults.exit
    });
  }, [config.expiryType]);

  return (
    <div className="mx-4 mb-4">
      <div className="bg-blue-50 dark:bg-blue-900/10 border-l-4 border-blue-500 rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Strategy Configuration
          </h3>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => handleTradingTypeChange('INTRADAY')}
              className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                config.tradingType === 'INTRADAY'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              Intraday
            </button>
            <button
              type="button"
              onClick={() => handleTradingTypeChange('POSITIONAL')}
              className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                config.tradingType === 'POSITIONAL'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              Positional
            </button>
          </div>
        </div>
        
        <div className="space-y-6">
        {/* Time Configuration Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Entry Time Card */}
          <div className="bg-white/90 dark:bg-gray-800/90 rounded-xl shadow-lg border border-gray-200/50 dark:border-gray-600/50 p-5">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <label className="block text-sm font-semibold text-gray-700 dark:text-gray-200">
                    {config.rangeBreakout ? 'Range Start Time' : 'Entry Time'}
                  </label>
                </div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={config.rangeBreakout}
                    onChange={(e) => handleRangeBreakoutChange(e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 focus:ring-2"
                  />
                  <span className="text-xs font-medium text-gray-700 dark:text-gray-200">Range Breakout</span>
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
                      Range End Time
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
              
              {/* Trading Days Slider - Only for Positional */}
              {config.tradingType === 'POSITIONAL' && (
                <div className="pt-4 border-t border-gray-200/50 dark:border-gray-600/50">
                  <div className="space-y-3">
                    <div className="space-y-2">
                      <input
                        type="range"
                        min={getSliderRange().min}
                        max={getSliderRange().max}
                        value={getSliderRange().max - config.entryTradingDaysBeforeExpiry}
                        onChange={(e) => handleTradingDaysChange('entryTradingDaysBeforeExpiry', getSliderRange().max - parseInt(e.target.value))}
                        className="w-full h-2 bg-gray-200 dark:bg-gray-600 rounded-lg appearance-none cursor-pointer"
                      />
                      <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
                        {getTradingDaysText(config.entryTradingDaysBeforeExpiry)}
                      </div>
                    </div>
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
              
              {/* Exit Mode Radio Buttons - Only show for Intraday */}
              {config.tradingType === 'INTRADAY' && (
                <div className="pt-3 border-t border-gray-200/50 dark:border-gray-600/50">
                  <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="intradayExitMode"
                        value="SAME_DAY"
                        checked={config.intradayExitMode === 'SAME_DAY'}
                        onChange={(e) => handleIntradayExitModeChange(e.target.value as 'SAME_DAY' | 'NEXT_DAY_BTST')}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 dark:border-gray-600"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Same Day</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="intradayExitMode"
                        value="NEXT_DAY_BTST"
                        checked={config.intradayExitMode === 'NEXT_DAY_BTST'}
                        onChange={(e) => handleIntradayExitModeChange(e.target.value as 'SAME_DAY' | 'NEXT_DAY_BTST')}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 dark:border-gray-600"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Next Day (STBT/BTST)</span>
                    </label>
                  </div>
                </div>
              )}
              
              {/* Trading Days Slider - Only for Positional */}
              {config.tradingType === 'POSITIONAL' && (
                <div className="pt-4 border-t border-gray-200/50 dark:border-gray-600/50">
                  <div className="space-y-3">
                    <div className="space-y-2">
                      <input
                        type="range"
                        min={getSliderRange().min}
                        max={getSliderRange().max}
                        value={getSliderRange().max - config.exitTradingDaysBeforeExpiry}
                        onChange={(e) => handleTradingDaysChange('exitTradingDaysBeforeExpiry', getSliderRange().max - parseInt(e.target.value))}
                        className="w-full h-2 bg-gray-200 dark:bg-gray-600 rounded-lg appearance-none cursor-pointer"
                      />
                      <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
                        {getTradingDaysText(config.exitTradingDaysBeforeExpiry)}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
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
    </div>
  );
};

export default StrategyConfiguration;