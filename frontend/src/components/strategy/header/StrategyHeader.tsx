/**
 * StrategyHeader Component
 * 
 * Dialog header including:
 * - Strategy name input
 * - Index selection dropdown
 * - Add Position button
 * - Close dialog button
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import React from 'react';
import { X, Plus } from 'lucide-react';
import Button from '../../ui/Button';
import Input from '../../ui/Input';
import Select from '../../ui/Select';
import { INDEX_OPTIONS } from '../../../utils/strategy';

interface StrategyHeaderProps {
  strategyName: string;
  strategyIndex: string;
  positionCount: number;
  onStrategyNameChange: (name: string) => void;
  onStrategyIndexChange: (index: string) => void;
  onAddPosition: () => void;
  onClose: () => void;
}

const StrategyHeader: React.FC<StrategyHeaderProps> = ({
  strategyName,
  strategyIndex,
  positionCount,
  onStrategyNameChange,
  onStrategyIndexChange,
  onAddPosition,
  onClose
}) => {
  return (
    <div className="flex-shrink-0 bg-white/95 dark:bg-gray-900/95 backdrop-blur-md p-6 border-b border-gray-200/50 dark:border-gray-600/50">
      <div className="flex items-center justify-between mb-6">
        <h2 id="strategy-dialog-title" className="text-2xl font-bold text-gray-900 dark:text-white">
          Create Strategy
        </h2>
        <button
          onClick={onClose}
          className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
        >
          <X className="h-6 w-6" />
        </button>
      </div>

      <div className="space-y-4">
        {/* Strategy Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
            Strategy Name
          </label>
          <Input
            type="text"
            value={strategyName}
            onChange={(e) => onStrategyNameChange(e.target.value)}
            placeholder="Enter strategy name"
            className="w-full"
          />
        </div>

        {/* Index Selection and Add Position */}
        <div className="flex items-end gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
              Index
            </label>
            <Select
              value={strategyIndex}
              onChange={(e) => onStrategyIndexChange(e.target.value)}
              options={INDEX_OPTIONS}
              className="w-full"
            />
          </div>
          
          <Button
            type="button"
            onClick={onAddPosition}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
          >
            <Plus className="h-4 w-4" />
            Add Position ({positionCount})
          </Button>
        </div>
      </div>
    </div>
  );
};

export default StrategyHeader;