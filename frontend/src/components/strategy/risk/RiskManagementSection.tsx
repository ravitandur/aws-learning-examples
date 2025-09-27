/**
 * RiskManagementSection Component
 * 
 * Main orchestrator for all risk management controls.
 * Provides a clean interface for managing all risk-related settings for a position.
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import React from 'react';
import { Leg } from '../../../types/strategy';
import StopLossControl from './StopLossControl';
import TargetProfitControl from './TargetProfitControl';
import TrailingStopLossControl from './TrailingStopLossControl';
import WaitAndTradeControl from './WaitAndTradeControl';
import ReEntryControl from './ReEntryControl';
import ReExecuteControl from './ReExecuteControl';

interface RiskManagementSectionProps {
  leg: Leg;
  onUpdate: (updates: Partial<Leg>) => void;
}

const RiskManagementSection: React.FC<RiskManagementSectionProps> = ({ leg, onUpdate }) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      {/* Stop Loss Card */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200/50 dark:border-gray-600/50 p-4">
        <div className="space-y-3">
          <StopLossControl leg={leg} onUpdate={onUpdate} />
          <TrailingStopLossControl leg={leg} onUpdate={onUpdate} />
          <ReEntryControl leg={leg} onUpdate={onUpdate} />
        </div>
      </div>

      {/* Target Profit Card */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200/50 dark:border-gray-600/50 p-4">
        <div className="space-y-3">
          <TargetProfitControl leg={leg} onUpdate={onUpdate} />
          <ReExecuteControl leg={leg} onUpdate={onUpdate} />
        </div>
      </div>

      {/* Wait and Trade - Independent */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200/50 dark:border-gray-600/50 p-4">
        <WaitAndTradeControl leg={leg} onUpdate={onUpdate} />
      </div>
    </div>
  );
};

export default RiskManagementSection;