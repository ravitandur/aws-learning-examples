/**
 * usePositionManagement Hook
 * 
 * Hook for managing position add/remove/copy operations.
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import { useCallback } from 'react';
import { Leg, PositionActions } from '../../types/strategy';
import {
  createNewPosition,
  clonePosition,
  updatePositionInArray,
  removePositionFromArray,
  autoCorrectPositionInterdependencies
} from '../../utils/strategy';

interface UsePositionManagementProps {
  legs: Leg[];
  setLegs: React.Dispatch<React.SetStateAction<Leg[]>>;
  showError: (message: string) => void;
}

interface UsePositionManagementReturn {
  actions: PositionActions;
  updatePosition: (legId: string, updates: Partial<Leg>) => void;
}

export const usePositionManagement = ({
  legs,
  setLegs,
  showError
}: UsePositionManagementProps): UsePositionManagementReturn => {

  // Add new position
  const addPosition = useCallback(() => {
    const newPosition = createNewPosition();
    setLegs(prev => [...prev, newPosition]);
  }, [setLegs]);
  
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
  const updatePosition = useCallback((legId: string, updates: Partial<Leg>) => {
    setLegs(prev => {
      const updatedLegs = updatePositionInArray(prev, legId, updates);
      // Auto-correct interdependencies
      return updatedLegs.map(leg => 
        leg.id === legId ? autoCorrectPositionInterdependencies(leg) : leg
      );
    });
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
    updatePosition
  };
};