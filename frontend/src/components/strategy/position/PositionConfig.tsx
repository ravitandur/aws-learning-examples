/**
 * PositionConfig Component
 * 
 * Complete position configuration including:
 * - Basic position settings (index, option type, action, lots, expiry)
 * - Strike selection with advanced methods
 * - Risk management controls
 * - Position actions (duplicate, delete)
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import React from 'react';
import { Copy, Trash2 } from 'lucide-react';
import Input from '../../ui/Input';
import { StrategyLeg, ProductType } from '../../../types/strategy';
import StrikeSelection from './StrikeSelection';
import RiskManagementSection from '../risk/RiskManagementSection';

interface PositionConfigProps {
  leg: StrategyLeg;
  index: number;
  onUpdate: (updates: Partial<StrategyLeg>) => void;
  onRemove: () => void;
  onCopy: () => void;
  strategyIndex: string;
  strategyExpiryType: string;
  strategyProductType: ProductType;
}

const PositionConfig: React.FC<PositionConfigProps> = ({ 
  leg, 
  index, 
  onUpdate, 
  onRemove, 
  onCopy,
  strategyIndex,
  strategyExpiryType,
  strategyProductType
}) => {

  const handleOptionTypeToggle = () => {
    const newOptionType = leg.optionType === 'CE' ? 'PE' : 'CE';
    onUpdate({ optionType: newOptionType });
  };

  const handleActionTypeToggle = () => {
    const newActionType = leg.actionType === 'BUY' ? 'SELL' : 'BUY';
    onUpdate({ actionType: newActionType });
  };

  const handleLotsChange = (lots: number) => {
    onUpdate({ totalLots: lots });
  };


  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200/50 dark:border-gray-600/50 mx-4 mb-4">
      {/* Position Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Position {index}
          </h3>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
              {strategyIndex}
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 px-2 py-1 rounded capitalize">
              {strategyExpiryType}
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 px-2 py-1 rounded">
              {strategyProductType}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onCopy}
            className="p-2 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 transition-colors"
            title="Duplicate Position"
          >
            <Copy className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={onRemove}
            className="p-2 text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 transition-colors"
            title="Delete Position"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Basic Configuration */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Option Type Toggle */}
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
              Option Type
            </label>
            <button
              type="button"
              onClick={handleOptionTypeToggle}
              className={`h-9 w-full px-3 py-1 text-sm font-medium rounded-md border transition-colors ${
                leg.optionType === 'CE'
                  ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-green-300 dark:border-green-600'
                  : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border-red-300 dark:border-red-600'
              }`}
            >
              {leg.optionType}
            </button>
          </div>

          {/* Action Type Toggle */}
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
              Action
            </label>
            <button
              type="button"
              onClick={handleActionTypeToggle}
              className={`h-9 w-full px-3 py-1 text-sm font-medium rounded-md border transition-colors ${
                leg.actionType === 'BUY'
                  ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-300 dark:border-blue-600'
                  : 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 border-orange-300 dark:border-orange-600'
              }`}
            >
              {leg.actionType}
            </button>
          </div>

          {/* Total Lots */}
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
              Total Lots
            </label>
            <Input
              type="number"
              min="1"
              value={leg.totalLots}
              onChange={(e) => handleLotsChange(parseInt(e.target.value) || 1)}
              className="h-9 text-sm"
            />
          </div>
        </div>

        {/* Strike Selection - Full Row */}
        <StrikeSelection leg={leg} onUpdate={onUpdate} />

        {/* Risk Management */}
        <RiskManagementSection leg={leg} onUpdate={onUpdate} />
      </div>
    </div>
  );
};

export default PositionConfig;