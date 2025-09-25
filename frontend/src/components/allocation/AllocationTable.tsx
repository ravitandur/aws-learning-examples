import React from 'react';
import Badge from '../ui/Badge';
import Input from '../ui/Input';
import {
  ExternalLink, Edit3, Save, X, Power, RefreshCw, Trash2
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

interface AllocationTableProps {
  allocations: EnhancedAllocation[];
  selectedAllocations: Set<string>;
  onSelectAll: () => void;
  onSelectAllocation: (allocationId: string) => void;
  onStatusToggle: (allocation: EnhancedAllocation) => void;
  onDelete: (allocation: EnhancedAllocation) => void;
  onStartEdit: (allocation: EnhancedAllocation) => void;
  onSaveEdit: (allocation: EnhancedAllocation) => void;
  onCancelEdit: () => void;
  editingAllocation: string | null;
  updating: string | null;
  editLotMultiplier: number;
  onEditLotMultiplierChange: (value: number) => void;
}

const AllocationTable: React.FC<AllocationTableProps> = ({
  allocations,
  selectedAllocations,
  onSelectAll,
  onSelectAllocation,
  onStatusToggle,
  onDelete,
  onStartEdit,
  onSaveEdit,
  onCancelEdit,
  editingAllocation,
  updating,
  editLotMultiplier,
  onEditLotMultiplierChange
}) => {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th className="px-6 py-3 text-left">
              <input
                type="checkbox"
                checked={selectedAllocations.size === allocations.length && allocations.length > 0}
                onChange={onSelectAll}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              Basket
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              Broker
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              Client ID
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              Lot Multiplier
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              Created
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
          {allocations.map((allocation) => (
            <tr
              key={allocation.allocation_id}
              className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              <td className="px-6 py-4">
                <input
                  type="checkbox"
                  checked={selectedAllocations.has(allocation.allocation_id)}
                  onChange={() => onSelectAllocation(allocation.allocation_id)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {allocation.basket_name}
                  </span>
                  <button
                    onClick={() => window.open(`/baskets`, '_blank')}
                    className="text-gray-400 hover:text-blue-600 transition-colors"
                    title="View basket details"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </button>
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {allocation.basket_id}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <Badge variant="info">{allocation.broker_id}</Badge>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                {allocation.client_id}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                {editingAllocation === allocation.allocation_id ? (
                  <div className="flex items-center gap-2">
                    <Input
                      type="number"
                      min="1"
                      max="1000"
                      value={editLotMultiplier}
                      onChange={(e) => onEditLotMultiplierChange(parseInt(e.target.value) || 1)}
                      className="w-20 text-sm"
                    />
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => onSaveEdit(allocation)}
                        disabled={updating === allocation.allocation_id}
                        className="text-green-600 hover:text-green-700 disabled:opacity-50"
                        title="Save"
                      >
                        {updating === allocation.allocation_id ? (
                          <RefreshCw className="h-4 w-4 animate-spin" />
                        ) : (
                          <Save className="h-4 w-4" />
                        )}
                      </button>
                      <button
                        onClick={onCancelEdit}
                        className="text-red-600 hover:text-red-700"
                        title="Cancel"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {allocation.lot_multiplier}
                    </span>
                    <button
                      onClick={() => onStartEdit(allocation)}
                      className="text-gray-400 hover:text-blue-600 transition-colors"
                      title="Edit lot multiplier"
                    >
                      <Edit3 className="h-4 w-4" />
                    </button>
                  </div>
                )}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <Badge
                  variant={allocation.status === 'ACTIVE' ? 'success' : 'default'}
                >
                  {allocation.status}
                </Badge>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                {new Date(allocation.created_at).toLocaleDateString()}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right">
                <div className="flex items-center justify-end gap-2">
                  <button
                    onClick={() => onStatusToggle(allocation)}
                    disabled={updating === allocation.allocation_id}
                    className={`p-1 rounded transition-colors ${
                      allocation.status === 'ACTIVE'
                        ? 'text-orange-600 hover:text-orange-700 hover:bg-orange-50 dark:hover:bg-orange-900/20'
                        : 'text-green-600 hover:text-green-700 hover:bg-green-50 dark:hover:bg-green-900/20'
                    } disabled:opacity-50`}
                    title={allocation.status === 'ACTIVE' ? 'Disable' : 'Enable'}
                  >
                    {updating === allocation.allocation_id ? (
                      <RefreshCw className="h-4 w-4 animate-spin" />
                    ) : (
                      <Power className="h-4 w-4" />
                    )}
                  </button>
                  <button
                    onClick={() => onDelete(allocation)}
                    disabled={updating === allocation.allocation_id}
                    className="p-1 rounded text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-50"
                    title="Delete allocation"
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

export default AllocationTable;