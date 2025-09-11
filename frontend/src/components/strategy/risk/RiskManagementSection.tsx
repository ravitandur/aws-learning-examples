/**
 * RiskManagementSection Component
 * 
 * Main orchestrator for all risk management controls.
 * Provides a clean interface for managing all risk-related settings for a position.
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import React from 'react';
import { StrategyLeg } from '../../../types/strategy';
import StopLossControl from './StopLossControl';
import TargetProfitControl from './TargetProfitControl';
import TrailingStopLossControl from './TrailingStopLossControl';
import WaitAndTradeControl from './WaitAndTradeControl';
import ReEntryControl from './ReEntryControl';
import ReExecuteControl from './ReExecuteControl';

interface RiskManagementSectionProps {
  leg: StrategyLeg;
  onUpdate: (updates: Partial<StrategyLeg>) => void;
}

const RiskManagementSection: React.FC<RiskManagementSectionProps> = ({ leg, onUpdate }) => {
  return (
    <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
      <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-4">
        Risk Management
      </h4>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Primary Risk Controls */}
        <div className="space-y-4">
          <StopLossControl leg={leg} onUpdate={onUpdate} />
          <TargetProfitControl leg={leg} onUpdate={onUpdate} />
          <TrailingStopLossControl leg={leg} onUpdate={onUpdate} />
        </div>
        
        {/* Advanced Risk Controls */}
        <div className="space-y-4">
          <WaitAndTradeControl leg={leg} onUpdate={onUpdate} />
          <ReEntryControl leg={leg} onUpdate={onUpdate} />
          <ReExecuteControl leg={leg} onUpdate={onUpdate} />
        </div>
      </div>
    </div>
  );
};

export default RiskManagementSection;