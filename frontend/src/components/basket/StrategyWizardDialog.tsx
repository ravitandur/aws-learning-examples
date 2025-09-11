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

import React, { useRef } from 'react';
import { Card, CardContent } from '../ui/Card';
import Button from '../ui/Button';
import StrategyHeader from '../strategy/header/StrategyHeader';
import PositionConfig from '../strategy/position/PositionConfig';
import StrategyConfiguration from '../strategy/config/StrategyConfiguration';
import { StrategyConfig } from '../../types/strategy';
import { useToast } from '../common/ToastContainer';
import { useStrategyForm } from '../../hooks/strategy/useStrategyForm';
import { usePositionManagement } from '../../hooks/strategy/usePositionManagement';
import { useStrategyValidation } from '../../hooks/strategy/useStrategyValidation';
import { useStrategySubmission } from '../../hooks/strategy/useStrategySubmission';

interface StrategyWizardDialogProps {
  basketId: string;
  onClose: () => void;
  onSubmit: (strategyData: any) => void;
}

const StrategyWizardDialog: React.FC<StrategyWizardDialogProps> = ({ 
  basketId, 
  onClose, 
  onSubmit 
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
    setStrategyConfig
  } = useStrategyForm({ basketId, onClose });

  const {
    actions,
    updatePosition
  } = usePositionManagement({ legs, setLegs, strategyIndex, showError });

  const validation = useStrategyValidation();

  const { handleSubmit, isSubmitting } = useStrategySubmission({
    basketId,
    strategyName,
    legs,
    strategyConfig,
    onSubmit,
    onClose,
    showError,
    showSuccess,
    validation
  });

  // Handler for strategy config updates
  const handleStrategyConfigUpdate = (updates: Partial<StrategyConfig>) => {
    setStrategyConfig(prev => ({ ...prev, ...updates }));
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
          {/* Fixed Header */}
          <StrategyHeader
            strategyName={strategyName}
            strategyIndex={strategyIndex}
            positionCount={legs.length}
            onStrategyNameChange={setStrategyName}
            onStrategyIndexChange={setStrategyIndex}
            onAddPosition={actions.add}
            onClose={onClose}
          />
          
          {/* Scrollable Content */}
          <CardContent className="flex-1 flex flex-col overflow-hidden p-0">
            <div 
              className="flex-1 overflow-y-auto"
            >
              {/* Positions List */}
              {legs.length > 0 && (
                <div className="py-4">
                  {legs.map((leg, index) => (
                    <PositionConfig
                      key={leg.id}
                      leg={leg}
                      legNumber={index + 1}
                      isFirst={index === 0}
                      onUpdate={(updates) => updatePosition(leg.id, updates)}
                      onDuplicate={() => actions.copy(leg.id)}
                      onDelete={() => actions.remove(leg.id)}
                    />
                  ))}
                </div>
              )}

              {/* Strategy Configuration - Only show after first position */}
              {legs.length > 0 && (
                <StrategyConfiguration
                  config={strategyConfig}
                  onUpdate={handleStrategyConfigUpdate}
                />
              )}
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
                    {isSubmitting ? 'Creating...' : 'Create Strategy'}
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