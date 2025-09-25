import React from 'react';
import { Card, CardContent } from '../ui/Card';
import Badge from '../ui/Badge';
import Input from '../ui/Input';
import {
  Network, ExternalLink, Edit3, Save, X, Power, RefreshCw, Trash2
} from 'lucide-react';

interface EnhancedAllocation {
  allocation_id: string;
  basket_id: string;
  basket_name: string;
  broker_id: string;
  client_id: string;
  lot_multiplier: number;
  status: 'ACTIVE' | 'INACTIVE';
  created_at: string;
  updated_at: string;
}

interface AllocationCardProps {
  allocation: EnhancedAllocation;
  isSelected: boolean;
  onSelect: (allocationId: string) => void;
  onStatusToggle: (allocation: EnhancedAllocation) => void;
  onDelete: (allocation: EnhancedAllocation) => void;
  onStartEdit: (allocation: EnhancedAllocation) => void;
  onSaveEdit: (allocation: EnhancedAllocation) => void;
  onCancelEdit: () => void;
  isEditing: boolean;
  isUpdating: boolean;
  editLotMultiplier: number;
  onEditLotMultiplierChange: (value: number) => void;
}

const AllocationCard: React.FC<AllocationCardProps> = ({
  allocation,
  isSelected,
  onSelect,
  onStatusToggle,
  onDelete,
  onStartEdit,
  onSaveEdit,
  onCancelEdit,
  isEditing,
  isUpdating,
  editLotMultiplier,
  onEditLotMultiplierChange
}) => {
  return (
    <Card className={`transition-all hover:shadow-md ${
      isSelected ? 'ring-2 ring-blue-500 bg-blue-50 dark:bg-blue-900/10' : ''
    }`}>
      <CardContent className="p-4">
        {/* Header with selection and status */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => onSelect(allocation.allocation_id)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <div className="flex items-center gap-2">
              <Network className="h-4 w-4 text-blue-500" />
              <span className="font-medium text-gray-900 dark:text-white">
                {allocation.basket_name}
              </span>
            </div>
          </div>
          <Badge
            variant={allocation.status === 'ACTIVE' ? 'success' : 'default'}
            size="sm"
          >
            {allocation.status}
          </Badge>
        </div>

        {/* Basket ID with external link */}
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs text-gray-500 dark:text-gray-400">
            Basket ID: {allocation.basket_id}
          </span>
          <button
            onClick={() => window.open(`/baskets`, '_blank')}
            className="text-gray-400 hover:text-blue-600 transition-colors"
            title="View basket details"
          >
            <ExternalLink className="h-3 w-3" />
          </button>
        </div>

        {/* Main allocation details */}
        <div className="space-y-3 mb-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600 dark:text-gray-400">Broker:</span>
            <Badge variant="info" size="sm">{allocation.broker_id}</Badge>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600 dark:text-gray-400">Client ID:</span>
            <span className="text-sm font-medium text-gray-900 dark:text-white">
              {allocation.client_id}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600 dark:text-gray-400">Lot Multiplier:</span>
            <div className="flex items-center gap-2">
              {isEditing ? (
                <>
                  <Input
                    type="number"
                    min="1"
                    max="1000"
                    value={editLotMultiplier}
                    onChange={(e) => onEditLotMultiplierChange(parseInt(e.target.value) || 1)}
                    className="w-20 text-sm h-8"
                  />
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => onSaveEdit(allocation)}
                      disabled={isUpdating}
                      className="text-green-600 hover:text-green-700 disabled:opacity-50 p-1"
                      title="Save"
                    >
                      {isUpdating ? (
                        <RefreshCw className="h-3 w-3 animate-spin" />
                      ) : (
                        <Save className="h-3 w-3" />
                      )}
                    </button>
                    <button
                      onClick={onCancelEdit}
                      className="text-red-600 hover:text-red-700 p-1"
                      title="Cancel"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {allocation.lot_multiplier}
                  </span>
                  <button
                    onClick={() => onStartEdit(allocation)}
                    className="text-gray-400 hover:text-blue-600 transition-colors p-1"
                    title="Edit lot multiplier"
                  >
                    <Edit3 className="h-3 w-3" />
                  </button>
                </>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600 dark:text-gray-400">Created:</span>
            <span className="text-sm text-gray-900 dark:text-white">
              {new Date(allocation.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-2 pt-3 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={() => onStatusToggle(allocation)}
            disabled={isUpdating}
            className={`p-2 rounded transition-colors ${
              allocation.status === 'ACTIVE'
                ? 'text-orange-600 hover:text-orange-700 hover:bg-orange-50 dark:hover:bg-orange-900/20'
                : 'text-green-600 hover:text-green-700 hover:bg-green-50 dark:hover:bg-green-900/20'
            } disabled:opacity-50`}
            title={allocation.status === 'ACTIVE' ? 'Disable' : 'Enable'}
          >
            {isUpdating ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Power className="h-4 w-4" />
            )}
          </button>
          <button
            onClick={() => onDelete(allocation)}
            disabled={isUpdating}
            className="p-2 rounded text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-50"
            title="Delete allocation"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </CardContent>
    </Card>
  );
};

export default AllocationCard;