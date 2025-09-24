import React from 'react';
import { Strategy } from '../../types';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import { Edit3, Trash2, Play, Pause, MoreHorizontal } from 'lucide-react';

interface StrategyTableProps {
  strategies: Strategy[];
  onEdit: (strategy: Strategy) => void;
  onDelete?: (strategy: Strategy) => void;
  isLoading?: boolean;
}

const StrategyTable: React.FC<StrategyTableProps> = ({
  strategies,
  onEdit,
  onDelete,
  isLoading = false
}) => {
  // Format days array to readable string
  const formatDays = (days?: string[]): string => {
    if (!days || days.length === 0) return 'Not set';

    const dayMap: { [key: string]: string } = {
      'MONDAY': 'Mon', 'TUESDAY': 'Tue', 'WEDNESDAY': 'Wed',
      'THURSDAY': 'Thu', 'FRIDAY': 'Fri', 'SATURDAY': 'Sat', 'SUNDAY': 'Sun'
    };

    return days.map(day => dayMap[day.toUpperCase()] || day).join(', ');
  };

  // Format time to readable format
  const formatTime = (time?: string): string => {
    if (!time) return 'Not set';

    if (time.includes(':')) return time;

    if (time.length === 4) {
      return `${time.substring(0, 2)}:${time.substring(2, 4)}`;
    }

    return time;
  };

  // Get badge variant based on value
  const getProductBadgeVariant = (product?: string) => {
    switch (product?.toUpperCase()) {
      case 'MIS': return 'success';
      case 'NRML': return 'warning';
      default: return 'default';
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'ACTIVE': return 'success';
      case 'PAUSED': return 'warning';
      case 'COMPLETED': return 'default';
      default: return 'default';
    }
  };

  // Generate features display
  const getFeatures = (strategy: Strategy) => {
    const features = [];

    if (strategy.moveSlToCost) features.push('MSLC');
    if (strategy.rangeBreakout) features.push('ORB');

    // Target Profit
    if (strategy.targetProfit && typeof strategy.targetProfit.value === 'number' && strategy.targetProfit.value > 0 &&
        (strategy.targetProfit.enabled !== false)) {
      const tpValue = strategy.targetProfit.value;
      const tpType = strategy.targetProfit.type;
      let displayText = `TP: ${tpValue}`;
      if (tpType === "COMBINED_PREMIUM_PERCENT") displayText += "% Prem";
      else if (tpType === "TOTAL_MTM") displayText += " Pts.";
      else displayText += "pts";
      features.push(displayText);
    }

    // Stop Loss
    if (strategy.stopLoss && typeof strategy.stopLoss.value === 'number' && strategy.stopLoss.value > 0 &&
        (strategy.stopLoss.enabled !== false)) {
      const slValue = strategy.stopLoss.value;
      const slType = strategy.stopLoss.type;
      let displayText = `SL: ${slValue}`;
      if (slType === "TOTAL_MTM") displayText += " Pts.";
      else if (slType === "COMBINED_PREMIUM_PERCENT") displayText += "% Prem";
      else displayText += "pts";
      features.push(displayText);
    }

    if (features.length === 0) {
      return strategy.tradingType || 'Standard';
    }

    return features.join(', ');
  };

  if (strategies.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500 dark:text-gray-400">No strategies available</p>
      </div>
    );
  }

  return (
    <div className="relative">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-700">
          <tr>
            <th className="px-2 md:px-3 lg:px-6 py-2 md:py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider min-w-[140px]">
              Strategy
            </th>
            <th className="hidden sm:table-cell px-2 md:px-3 lg:px-6 py-2 md:py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider min-w-[90px]">
              Type & Product
            </th>
            <th className="hidden lg:table-cell px-2 md:px-3 lg:px-6 py-2 md:py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider min-w-[130px]">
              Timing
            </th>
            <th className="hidden lg:table-cell px-2 md:px-3 lg:px-6 py-2 md:py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider min-w-[90px]">
              Features
            </th>
            <th className="px-2 md:px-3 lg:px-6 py-2 md:py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider min-w-[60px]">
              Status
            </th>
            <th className="sticky right-0 bg-gray-50 dark:bg-gray-700 px-2 md:px-3 lg:px-6 py-2 md:py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider border-l border-gray-200 dark:border-gray-600 shadow-lg z-10 min-w-[120px]">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
          {strategies.map(strategy => (
            <tr key={strategy.strategyId} className="hover:bg-gray-50 dark:hover:bg-gray-700">
              {/* Strategy Name & Details */}
              <td className="px-2 md:px-3 lg:px-6 py-3 md:py-4">
                <div className="flex items-center">
                  <div className="flex-shrink-0 h-6 w-6 sm:h-8 sm:w-8 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
                    <Play className="h-3 w-3 sm:h-4 sm:w-4 text-blue-600" />
                  </div>
                  <div className="ml-2 sm:ml-3 min-w-0">
                    <div className="text-xs sm:text-sm font-medium text-gray-900 dark:text-white truncate">
                      {strategy.strategyName}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {Array.isArray(strategy.legsArray) ? strategy.legsArray.length : strategy.legs} legs
                      {/* Show critical info on mobile when columns are hidden */}
                      <span className="sm:hidden">
                        {strategy.underlying && ` • ${strategy.underlying}`}
                        {strategy.product && ` • ${strategy.product}`}
                      </span>
                    </div>
                    {/* Show features on medium screens when Features column is hidden */}
                    <div className="text-xs text-gray-500 dark:text-gray-400 lg:hidden mt-1 truncate">
                      {getFeatures(strategy)}
                    </div>
                  </div>
                </div>
              </td>

              {/* Type & Product */}
              <td className="hidden sm:table-cell px-2 md:px-3 lg:px-6 py-3 md:py-4 whitespace-nowrap">
                <div className="space-y-1">
                  {strategy.underlying && (
                    <Badge variant="default" size="sm">
                      {strategy.underlying}
                    </Badge>
                  )}
                  {strategy.product && (
                    <Badge variant={getProductBadgeVariant(strategy.product)} size="sm">
                      {strategy.product}
                    </Badge>
                  )}
                </div>
              </td>

              {/* Timing */}
              <td className="hidden lg:table-cell px-2 md:px-3 lg:px-6 py-3 md:py-4">
                <div className="text-xs space-y-1">
                  <div className="flex">
                    <span className="text-gray-500 dark:text-gray-400 w-12">Entry:</span>
                    <span className="text-gray-900 dark:text-white truncate">
                      {formatDays(strategy.entryDays)} {formatTime(strategy.entryTime)}
                    </span>
                  </div>
                  <div className="flex">
                    <span className="text-gray-500 dark:text-gray-400 w-12">Exit:</span>
                    <span className="text-gray-900 dark:text-white truncate">
                      {formatDays(strategy.exitDays)} {formatTime(strategy.exitTime)}
                    </span>
                  </div>
                </div>
              </td>

              {/* Features */}
              <td className="hidden lg:table-cell px-2 md:px-3 lg:px-6 py-3 md:py-4">
                <div className="text-xs text-gray-900 dark:text-white truncate max-w-[80px]">
                  {getFeatures(strategy)}
                </div>
              </td>

              {/* Status */}
              <td className="px-2 md:px-3 lg:px-6 py-3 md:py-4 whitespace-nowrap">
                <Badge
                  variant={getStatusBadgeVariant(strategy.status)}
                  size="sm"
                >
                  {strategy.status}
                </Badge>
              </td>

              {/* Actions */}
              <td className="sticky right-0 bg-white dark:bg-gray-800 px-2 md:px-3 lg:px-6 py-3 md:py-4 whitespace-nowrap text-right text-sm font-medium border-l border-gray-200 dark:border-gray-600 shadow-lg z-10 min-w-[120px]">
                <div className="flex items-center justify-end gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onEdit(strategy)}
                    disabled={isLoading}
                    className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900/20 px-1 md:px-2"
                  >
                    <Edit3 className="h-4 w-4" />
                    <span className="sr-only">Edit</span>
                  </Button>
                  {onDelete && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onDelete(strategy)}
                      disabled={isLoading}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 px-1 md:px-2"
                    >
                      <Trash2 className="h-4 w-4" />
                      <span className="sr-only">Delete</span>
                    </Button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
        </table>
      </div>
    </div>
  );
};

export default React.memo(StrategyTable);