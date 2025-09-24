/**
 * StrategyWizardDialog (Refactored)
 *
 * COMPLETE MODULAR REFACTORING of the original 1,580-line monolithic component.
 * Now uses proper component architecture with single responsibility principle.
 *
 * Architecture:
 * - StrategyHeader: Dialog header with name, index, and add position
 * - PositionConfig: Complete position configuration with risk management
 * - StrategyConfiguration: Strategy-level settings and timing
 * - Custom hooks: Business logic separation
 * - Type system: Centralized type definitions
 * - Utility modules: Reusable constants and helpers
 *
 * All functionality and look/feel maintained while improving maintainability.
 */

import React, { useRef, useEffect } from "react";
import { Card, CardContent } from "../ui/Card";
import Button from "../ui/Button";
import StrategyHeader from "../strategy/header/StrategyHeader";
import GlobalIndexSelector from "../strategy/config/GlobalIndexSelector";
import PositionsSection from "../strategy/position/PositionsSection";
import StrategyConfiguration from "../strategy/config/StrategyConfiguration";
import { StrategyConfig } from "../../types/strategy";
import { useToast } from "../common/ToastContainer";
import { useStrategyForm } from "../../hooks/strategy/useStrategyForm";
import { usePositionManagement } from "../../hooks/strategy/usePositionManagement";
import { useStrategyValidation } from "../../hooks/strategy/useStrategyValidation";
import { useStrategySubmission } from "../../hooks/strategy/useStrategySubmission";

interface StrategyWizardDialogProps {
  basketId: string;
  editingStrategy?: any; // Optional strategy data for editing mode
  onClose: () => void;
  onSubmit: (strategyData: any) => void;
}

const StrategyWizardDialog: React.FC<StrategyWizardDialogProps> = ({
  basketId,
  editingStrategy,
  onClose,
  onSubmit,
}) => {
  const dialogRef = useRef<HTMLDivElement>(null);
  const { showSuccess, showError } = useToast();

  // Use custom hooks for business logic
  const {
    strategyName,
    setStrategyName,
    strategyIndex,
    setStrategyIndex,
    legs,
    setLegs,
    strategyConfig,
    setStrategyConfig,
  } = useStrategyForm({ basketId, editingStrategy, onClose });

  const { actions, updatePosition } = usePositionManagement({
    legs,
    setLegs,
    showError,
  });

  // Sync expiry type changes across the strategy
  useEffect(() => {
    console.log('Strategy expiry type changed to:', strategyConfig.expiryType);
    // Expiry type is now strategy-level, so it automatically applies to all positions
    // No need to update individual positions as we did with index
  }, [strategyConfig.expiryType]);

  const validation = useStrategyValidation();

  const { handleSubmit, isSubmitting } = useStrategySubmission({
    basketId,
    strategyName,
    strategyIndex,  // Pass the strategy-level index
    legs,
    strategyConfig,
    editingStrategy, // Pass editing strategy for update mode
    onSubmit,
    onClose,
    showError,
    showSuccess,
    validation,
  });

  // Handler for strategy config updates
  const handleStrategyConfigUpdate = (updates: Partial<StrategyConfig>) => {
    setStrategyConfig((prev) => ({ ...prev, ...updates }));
  };

  return (
    <div
      className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-2 sm:p-4 z-50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="strategy-dialog-title"
    >
      <div
        ref={dialogRef}
        tabIndex={-1}
        className="w-full max-w-5xl h-full sm:h-[95vh] flex flex-col"
      >
        <Card className="flex flex-col bg-white/95 dark:bg-gray-900/95 backdrop-blur-md border border-white/20 dark:border-gray-700/20 rounded-none sm:rounded-2xl shadow-2xl overflow-hidden h-full">
          {/* Row 1: Fixed Header */}
          <StrategyHeader
            strategyName={strategyName}
            positionCount={legs.length}
            isEditing={!!editingStrategy}
            onStrategyNameChange={setStrategyName}
            onAddPosition={actions.add}
            onClose={onClose}
          />

          {/* Content Area */}
          <CardContent className="flex-1 flex flex-col overflow-hidden p-0">
            <div className="flex-1 overflow-y-auto">
              {/* Row 2: Global Index Selection */}
              <div className="flex-shrink-0">
                <GlobalIndexSelector
                  value={strategyIndex}
                  onChange={setStrategyIndex}
                  expiryType={strategyConfig.expiryType}
                  onExpiryTypeChange={(expiryType) => handleStrategyConfigUpdate({ expiryType })}
                  productType={strategyConfig.productType}
                  onProductTypeChange={(productType) => handleStrategyConfigUpdate({ productType })}
                  tradingType={strategyConfig.tradingType}
                  intradayExitMode={strategyConfig.intradayExitMode}
                />
              </div>

              {/* Row 3: Positions Section */}
              <div className="flex-shrink-0">
                <PositionsSection
                  positions={legs}
                  onPositionUpdate={updatePosition}
                  onPositionRemove={actions.remove}
                  onPositionCopy={actions.copy}
                  onAddPosition={actions.add}
                  strategyIndex={strategyIndex}
                  strategyExpiryType={strategyConfig.expiryType}
                  strategyProductType={strategyConfig.productType}
                />
              </div>

              {/* Row 4: Strategy Configuration - Always visible */}
              <div className="flex-shrink-0">
                <StrategyConfiguration
                  config={strategyConfig}
                  onUpdate={handleStrategyConfigUpdate}
                />
              </div>
            </div>

            {/* Sticky Footer */}
            <div className="flex-shrink-0 sticky bottom-0 bg-white/95 dark:bg-gray-900/95 backdrop-blur-md border-t border-gray-200/50 dark:border-gray-600/50 p-4">
              <div className="flex items-center justify-end">
                <div className="flex items-center gap-3">
                  <Button
                    variant="outline"
                    onClick={onClose}
                    disabled={isSubmitting}
                    className="min-w-[80px]"
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleSubmit}
                    disabled={isSubmitting || legs.length === 0}
                    className="bg-blue-600 hover:bg-blue-700 text-white min-w-[120px]"
                  >
                    {isSubmitting
                      ? (editingStrategy ? "Updating..." : "Creating...")
                      : (editingStrategy ? "Update Strategy" : "Create Strategy")
                    }
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default StrategyWizardDialog;
