import React from 'react';
import { Strategy } from '../../types';
import { Card, CardContent } from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import { Edit3, Zap } from 'lucide-react';

interface StrategyCardProps {
  strategy: Strategy;
  onEdit: (strategy: Strategy) => void;
  onDelete?: (strategy: Strategy) => void;
  isLoading?: boolean;
}

const StrategyCard: React.FC<StrategyCardProps> = ({
  strategy,
  onEdit,
  onDelete,
  isLoading = false
}) => {
  // Format days array to readable string
  const formatDays = (days?: string[]): string => {
    if (!days || days.length === 0) return 'Not set';

    // Convert to short format
    const dayMap: { [key: string]: string } = {
      'MONDAY': 'Mon', 'TUESDAY': 'Tue', 'WEDNESDAY': 'Wed',
      'THURSDAY': 'Thu', 'FRIDAY': 'Fri', 'SATURDAY': 'Sat', 'SUNDAY': 'Sun'
    };

    return days.map(day => dayMap[day.toUpperCase()] || day).join(', ');
  };

  // Format time to readable format
  const formatTime = (time?: string): string => {
    if (!time) return 'Not set';

    // If it's already in HH:MM format, return as is
    if (time.includes(':')) return time;

    // If it's in HHMM format, add colon
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

  // Generate advanced features display
  const getAdvancedFeatures = () => {
    const features = [];

    // Check for advanced features based on available strategy data
    if (strategy.moveSlToCost) features.push('MSLC');
    if (strategy.rangeBreakout) features.push('ORB');

    // Check for strategy-level risk management features
    // If enabled is undefined but value exists and > 0, treat as enabled
    if (strategy.targetProfit && typeof strategy.targetProfit.value === 'number' && strategy.targetProfit.value > 0 &&
        (strategy.targetProfit.enabled !== false)) {
      const tpValue = strategy.targetProfit.value;
      const tpType = strategy.targetProfit.type;
      // Format display based on type
      let displayText = `TP: ${tpValue}`;
      if (tpType === "COMBINED_PREMIUM_PERCENT") displayText += "% Prem";
      else if (tpType === "TOTAL_MTM") displayText += " Pts.";
      else displayText += "pts";
      features.push(displayText);
    }
    if (strategy.stopLoss && typeof strategy.stopLoss.value === 'number' && strategy.stopLoss.value > 0 &&
        (strategy.stopLoss.enabled !== false)) {
      const slValue = strategy.stopLoss.value;
      const slType = strategy.stopLoss.type;
      // Format display based on type
      let displayText = `SL: ${slValue}`;
      if (slType === "TOTAL_MTM") displayText += " Pts.";
      else if (slType === "COMBINED_PREMIUM_PERCENT") displayText += "% Prem";
      else displayText += "pts";
      features.push(displayText);
    }

    // If no specific advanced features, show trading type as a feature
    if (features.length === 0) {
      return strategy.tradingType || 'Standard';
    }

    return features.join(', ');
  };

  return (
    <Card className="hover:shadow-md transition-shadow duration-200">
      <CardContent className="p-4">
        {/* Header Row: Strategy Name + Status */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
              <Zap className="h-4 w-4 text-blue-600" />
            </div>
            <div>
              <h3 className="font-medium text-base text-gray-900 dark:text-white">
                {strategy.strategyName}
              </h3>
              <div className="text-xs text-gray-600 dark:text-gray-400">
                {Array.isArray(strategy.legsArray) ? strategy.legsArray.length : strategy.legs} legs
              </div>
            </div>
          </div>
          <Badge
            variant={getStatusBadgeVariant(strategy.status)}
            size="sm"
          >
            {strategy.status}
          </Badge>
        </div>

        {/* Primary Info Row: Index, Expiry, Product */}
        <div className="flex flex-wrap gap-2 mb-3">
          {strategy.underlying && (
            <Badge variant="default" size="sm">
              {strategy.underlying}
            </Badge>
          )}
          {strategy.expiryType && (
            <Badge variant="info" size="sm">
              {strategy.expiryType}
            </Badge>
          )}
          {strategy.product && (
            <Badge variant={getProductBadgeVariant(strategy.product)} size="sm">
              {strategy.product}
            </Badge>
          )}
        </div>

        {/* Timing Data Row with Enhanced Organization */}
        <div className="bg-gray-50 dark:bg-gray-700/30 rounded-lg p-3 mb-3">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
            <div className="flex flex-col">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Entry Days</div>
              <div className="font-medium text-gray-900 dark:text-white">
                {formatDays(strategy.entryDays)}
              </div>
            </div>
            <div className="flex flex-col">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Entry Time</div>
              <div className="font-medium text-gray-900 dark:text-white">
                {formatTime(strategy.entryTime)}
              </div>
            </div>
            <div className="flex flex-col">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Exit Time</div>
              <div className="font-medium text-gray-900 dark:text-white">
                {formatTime(strategy.exitTime)}
              </div>
            </div>
            <div className="flex flex-col">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Exit Days</div>
              <div className="font-medium text-gray-900 dark:text-white">
                {formatDays(strategy.exitDays)}
              </div>
            </div>
          </div>
        </div>

        {/* Configuration Row */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-500 dark:text-gray-400">Features:</span>
            <span className="text-gray-900 dark:text-white font-medium">
              {getAdvancedFeatures()}
            </span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onEdit(strategy)}
            disabled={isLoading}
            className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900/20"
          >
            <Edit3 className="h-4 w-4 mr-1" />
            Edit
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default React.memo(StrategyCard);