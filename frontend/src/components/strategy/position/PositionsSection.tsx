import React from "react";
import PositionConfig from "./PositionConfig";
import { Leg, ProductType } from "../../../types/strategy";

interface PositionsSectionProps {
  positions: Leg[];
  onPositionUpdate: (legId: string, updates: Partial<Leg>) => void;
  onPositionRemove: (legId: string) => void;
  onPositionCopy: (legId: string) => void;
  onAddPosition: () => void;
  strategyIndex: string;
  strategyExpiryType: string;
  strategyProductType: ProductType;
}

const PositionsSection: React.FC<PositionsSectionProps> = ({
  positions,
  onPositionUpdate,
  onPositionRemove,
  onPositionCopy,
  onAddPosition,
  strategyIndex,
  strategyExpiryType,
  strategyProductType,
}) => {
  const positionCount = positions.length;

  return (
    <div className="mx-4 mb-4">
      <div className="bg-gray-50 dark:bg-gray-800/30 border border-gray-200 dark:border-gray-700 rounded-lg">
        {/* Section Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Positions {positionCount > 0 && `(${positionCount})`}
            </h3>
          </div>
        </div>

        {/* Positions Content */}
        <div className="p-4">
          {positionCount === 0 ? (
            <div className="text-center py-12">
              <button
                onClick={onAddPosition}
                className="group transition-colors hover:text-blue-600 dark:hover:text-blue-400"
              >
                <div className="text-gray-400 dark:text-gray-500 mb-2 group-hover:text-blue-500 dark:group-hover:text-blue-400 transition-colors">
                  <svg
                    className="mx-auto h-12 w-12"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                    />
                  </svg>
                </div>
                <p className="text-gray-500 dark:text-gray-400 text-sm group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                  No positions added yet
                </p>
                <p className="text-gray-400 dark:text-gray-500 text-xs mt-1 group-hover:text-blue-500 dark:group-hover:text-blue-400 transition-colors">
                  Click to create your first position
                </p>
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {positions.map((leg, index) => (
                <PositionConfig
                  key={leg.id}
                  leg={leg}
                  index={index + 1}
                  onUpdate={(updates) => onPositionUpdate(leg.id, updates)}
                  onRemove={() => onPositionRemove(leg.id)}
                  onCopy={() => onPositionCopy(leg.id)}
                  strategyIndex={strategyIndex}
                  strategyExpiryType={strategyExpiryType}
                  strategyProductType={strategyProductType}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PositionsSection;
