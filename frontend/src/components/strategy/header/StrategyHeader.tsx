/**
 * StrategyHeader Component
 *
 * Dialog header including:
 * - Strategy name input
 * - Add Position button with count
 * - Close dialog button
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 * Index selection moved to GlobalIndexSelector component.
 */

import React from "react";
import { X, Plus } from "lucide-react";
import Button from "../../ui/Button";
import Input from "../../ui/Input";

interface StrategyHeaderProps {
  strategyName: string;
  positionCount: number;
  isEditing?: boolean; // New prop to determine if we're editing
  onStrategyNameChange: (name: string) => void;
  onAddPosition: () => void;
  onClose: () => void;
}

const StrategyHeader: React.FC<StrategyHeaderProps> = ({
  strategyName,
  positionCount,
  isEditing = false,
  onStrategyNameChange,
  onAddPosition,
  onClose,
}) => {
  return (
    <div className="flex-shrink-0 bg-white/95 dark:bg-gray-900/95 backdrop-blur-md p-6 border-b border-gray-200/50 dark:border-gray-600/50">
      <div className="flex items-center justify-between mb-6">
        <h2
          id="strategy-dialog-title"
          className="text-2xl font-bold text-gray-900 dark:text-white"
        >
          {isEditing ? 'Edit Strategy' : 'Create Strategy'}
        </h2>
        <button
          onClick={onClose}
          className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
        >
          <X className="h-6 w-6" />
        </button>
      </div>

      {/* Strategy Name and Add Position Button in same row */}
      <div>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <Input
              type="text"
              value={strategyName}
              onChange={(e) => onStrategyNameChange(e.target.value)}
              placeholder="Enter strategy name"
              className="w-full"
            />
          </div>
          <Button
            type="button"
            onClick={onAddPosition}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex-shrink-0"
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
