import React from 'react';
import { StrategyMetadata } from '../../types';
import Badge from '../ui/Badge';
import { Edit3, Trash2, Power, RefreshCw } from 'lucide-react';
import {
  formatDays,
  formatTime,
  getProductBadgeVariant,
  getStatusBadgeVariant,
  getAdvancedFeaturesForTable,
  getDerivedTradingType,
  getDerivedTradingTypeVariant
} from '../../utils/strategy/strategyDisplayHelpers';

interface StrategyTableProps {
  strategies: StrategyMetadata[];
  onEdit: (strategy: StrategyMetadata) => void;
  onDelete: (strategy: StrategyMetadata) => void;
  onStatusToggle: (strategy: StrategyMetadata) => void;
  loadingEditStrategy: boolean;
  updatingStrategy: string | null;
}

const StrategyTable: React.FC<StrategyTableProps> = ({
  strategies,
  onEdit,
  onDelete,
  onStatusToggle,
  loadingEditStrategy,
  updatingStrategy
}) => {

  if (strategies.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500 dark:text-gray-400">No strategies available</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              Strategy Details
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              Entry Schedule
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              Exit Schedule
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              Trading Type
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              Features
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
          {strategies.map((strategy) => (
            <tr
              key={strategy.strategyId}
              className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              {/* Strategy Details */}
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                  {strategy.strategyName}
                </div>
                <div className="flex flex-wrap gap-1">
                  <Badge variant="info" size="sm">{strategy.strategyType}</Badge>
                  <Badge variant="default" size="sm">{strategy.legCount || 0} legs</Badge>
                  {strategy.expiryType && (
                    <Badge variant="info" size="sm">
                      {strategy.expiryType.toUpperCase()}
                    </Badge>
                  )}
                  {strategy.product && (
                    <Badge variant={getProductBadgeVariant(strategy.product)} size="sm">
                      {strategy.product}
                    </Badge>
                  )}
                </div>
              </td>

              {/* Entry Schedule */}
              <td className="px-6 py-4">
                <div className="text-sm">
                  <div className="text-gray-900 dark:text-white font-medium mb-2">
                    {formatDays(strategy.entryDays)}
                  </div>
                  <div className="text-gray-900 dark:text-white font-medium">
                    {formatTime(strategy.entryTime)}
                  </div>
                </div>
              </td>

              {/* Exit Schedule */}
              <td className="px-6 py-4">
                <div className="text-sm">
                  <div className="text-gray-900 dark:text-white font-medium mb-2">
                    {formatDays(strategy.exitDays)}
                  </div>
                  <div className="text-gray-900 dark:text-white font-medium">
                    {formatTime(strategy.exitTime)}
                  </div>
                </div>
              </td>

              {/* Trading Type */}
              <td className="px-6 py-4 whitespace-nowrap">
                <Badge
                  variant={getDerivedTradingTypeVariant(strategy)}
                  size="sm"
                >
                  {getDerivedTradingType(strategy)}
                </Badge>
              </td>

              {/* Features */}
              <td className="px-6 py-4">
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  {getAdvancedFeaturesForTable(strategy)}
                </div>
              </td>

              {/* Status */}
              <td className="px-6 py-4 whitespace-nowrap">
                <Badge
                  variant={getStatusBadgeVariant(strategy.status)}
                >
                  {strategy.status}
                </Badge>
              </td>

              {/* Actions */}
              <td className="px-6 py-4 whitespace-nowrap text-right">
                <div className="flex items-center justify-end gap-2">
                  <button
                    onClick={() => onStatusToggle(strategy)}
                    disabled={updatingStrategy === strategy.strategyId}
                    className={`p-1 rounded transition-colors ${
                      strategy.status === 'ACTIVE'
                        ? 'text-orange-600 hover:text-orange-700 hover:bg-orange-50 dark:hover:bg-orange-900/20'
                        : 'text-green-600 hover:text-green-700 hover:bg-green-50 dark:hover:bg-green-900/20'
                    } disabled:opacity-50`}
                    title={strategy.status === 'ACTIVE' ? 'Disable' : 'Enable'}
                  >
                    {updatingStrategy === strategy.strategyId ? (
                      <RefreshCw className="h-4 w-4 animate-spin" />
                    ) : (
                      <Power className="h-4 w-4" />
                    )}
                  </button>
                  <button
                    onClick={() => onEdit(strategy)}
                    disabled={loadingEditStrategy}
                    className="p-1 rounded text-blue-600 hover:text-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors disabled:opacity-50"
                    title="Edit strategy"
                  >
                    <Edit3 className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => onDelete(strategy)}
                    className="p-1 rounded text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                    title="Delete strategy"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default React.memo(StrategyTable);