/**
 * usePositionManagement Hook
 * 
 * Hook for managing position add/remove/copy operations.
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import { useCallback } from 'react';
import { StrategyLeg, PositionActions } from '../../types/strategy';
import { 
  createNewPosition, 
  clonePosition, 
  updatePositionInArray, 
  removePositionFromArray,
  updateAllPositionsIndex,
  autoCorrectPositionInterdependencies
} from '../../utils/strategy';

interface UsePositionManagementProps {
  legs: StrategyLeg[];
  setLegs: React.Dispatch<React.SetStateAction<StrategyLeg[]>>;
  strategyIndex: string;
  showError: (message: string) => void;
}

interface UsePositionManagementReturn {
  actions: PositionActions;
  updateIndex: (newIndex: string) => void;
  updatePosition: (legId: string, updates: Partial<StrategyLeg>) => void;
}

export const usePositionManagement = ({
  legs,
  setLegs,
  strategyIndex,
  showError
}: UsePositionManagementProps): UsePositionManagementReturn => {
  
  // Add new position
  const addPosition = useCallback(() => {
    const newPosition = createNewPosition(strategyIndex);
    setLegs(prev => [...prev, newPosition]);
  }, [strategyIndex, setLegs]);
  
  // Remove position
  const removePosition = useCallback((legId: string) => {
    setLegs(prev => removePositionFromArray(prev, legId));
  }, [setLegs]);
  
  // Copy existing position
  const copyPosition = useCallback((legId: string) => {
    const positionToCopy = legs.find(leg => leg.id === legId);
    if (positionToCopy) {
      const newPosition = clonePosition(positionToCopy);
      setLegs(prev => [...prev, newPosition]);
    }
  }, [legs, setLegs]);
  
  // Update specific position
  const updatePosition = useCallback((legId: string, updates: Partial<StrategyLeg>) => {
    setLegs(prev => {
      const updatedLegs = updatePositionInArray(prev, legId, updates);
      // Auto-correct interdependencies
      return updatedLegs.map(leg => 
        leg.id === legId ? autoCorrectPositionInterdependencies(leg) : leg
      );
    });
  }, [setLegs]);
  
  // Update index for all positions
  const updateIndex = useCallback((newIndex: string) => {
    setLegs(prev => updateAllPositionsIndex(prev, newIndex));
  }, [setLegs]);
  
  // Position actions object
  const actions: PositionActions = {
    add: addPosition,
    remove: removePosition,
    copy: copyPosition,
    update: updatePosition
  };
  
  return {
    actions,
    updateIndex,
    updatePosition
  };
};