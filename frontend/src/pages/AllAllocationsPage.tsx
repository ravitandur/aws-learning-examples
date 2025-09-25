import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Badge from '../components/ui/Badge';
import { useToast } from '../components/common/ToastContainer';
import StandardLayout from '../components/common/StandardLayout';
import PageHeader from '../components/common/PageHeader';
import AllocationCard from '../components/allocation/AllocationCard';
import AllocationTable from '../components/allocation/AllocationTable';
import ConfirmDialog from '../components/common/ConfirmDialog';
import {
  Search, Network, Filter, Download, Edit3, Trash2,
  Power, RefreshCw, TrendingUp, Activity, Users, Target,
  ChevronRight, ExternalLink, Eye, Save, X, Home, Grid3x3, List
} from 'lucide-react';
import { BasketBrokerAllocation, Basket } from '../types';
import allocationService from '../services/allocationService';
import basketService from '../services/basketService';

interface EnhancedAllocation extends BasketBrokerAllocation {
  basket_name: string;
}

interface AllocationStats {
  totalAllocations: number;
  activeAllocations: number;
  uniqueBaskets: number;
  uniqueBrokers: number;
  totalLotMultiplier: number;
}

const AllAllocationsPage: React.FC = () => {
  const { showSuccess, showError } = useToast();

  // Core data state
  const [allocations, setAllocations] = useState<EnhancedAllocation[]>([]);
  const [baskets, setBaskets] = useState<Basket[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<string | null>(null);

  // Filtering and search state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'ACTIVE' | 'INACTIVE'>('ALL');
  const [basketFilter, setBasketFilter] = useState<string>('ALL');
  const [brokerFilter, setBrokerFilter] = useState<string>('ALL');

  // Selection state for bulk operations
  const [selectedAllocations, setSelectedAllocations] = useState<Set<string>>(new Set());

  // View toggle state - mobile defaults to cards, desktop to table
  const [allocationView, setAllocationView] = useState<'cards' | 'table'>(() => {
    // Check if mobile (screen width < 1024px) - default to cards
    if (typeof window !== 'undefined') {
      return window.innerWidth < 1024 ? 'cards' : 'table';
    }
    return 'cards';
  });

  // Editing state
  const [editingAllocation, setEditingAllocation] = useState<string | null>(null);
  const [editLotMultiplier, setEditLotMultiplier] = useState<number>(1);

  // Delete confirmation dialog state
  const [deleteConfirmDialog, setDeleteConfirmDialog] = useState<{
    isOpen: boolean;
    allocation: EnhancedAllocation | null;
  }>({ isOpen: false, allocation: null });

  // Load all data on component mount
  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    try {
      setLoading(true);

      // Load both allocations and baskets in parallel
      const [allocationsData, basketsData] = await Promise.all([
        allocationService.getAllAllocations(),
        basketService.getBaskets()
      ]);

      setBaskets(basketsData);

      // Enhance allocations with basket names
      const enhancedAllocations: EnhancedAllocation[] = allocationsData.map(allocation => ({
        ...allocation,
        basket_name: basketsData.find(b => b.basket_id === allocation.basket_id)?.basket_name || 'Unknown Basket'
      }));

      setAllocations(enhancedAllocations);

    } catch (error: any) {
      console.error('Failed to load allocations data:', error);
      showError('Failed to load allocations. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Calculate summary statistics
  const calculateStats = (): AllocationStats => {
    const filtered = getFilteredAllocations();
    const uniqueBaskets = new Set(filtered.map(a => a.basket_id)).size;
    const uniqueBrokers = new Set(filtered.map(a => `${a.broker_id}-${a.client_id}`)).size;
    const totalLotMultiplier = filtered
      .filter(a => a.status === 'ACTIVE')
      .reduce((sum, a) => sum + a.lot_multiplier, 0);

    return {
      totalAllocations: filtered.length,
      activeAllocations: filtered.filter(a => a.status === 'ACTIVE').length,
      uniqueBaskets,
      uniqueBrokers,
      totalLotMultiplier
    };
  };

  // Filter allocations based on current filters
  const getFilteredAllocations = (): EnhancedAllocation[] => {
    return allocations.filter(allocation => {
      const matchesSearch = searchQuery === '' ||
        allocation.basket_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        allocation.broker_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        allocation.client_id.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesStatus = statusFilter === 'ALL' || allocation.status === statusFilter;
      const matchesBasket = basketFilter === 'ALL' || allocation.basket_id === basketFilter;
      const matchesBroker = brokerFilter === 'ALL' || allocation.broker_id === brokerFilter;

      return matchesSearch && matchesStatus && matchesBasket && matchesBroker;
    });
  };

  // Get unique broker IDs for filter dropdown
  const getUniqueBrokers = (): string[] => {
    const brokers = new Set(allocations.map(a => a.broker_id));
    return Array.from(brokers).sort();
  };

  // Handle status toggle for individual allocation
  const handleStatusToggle = async (allocation: EnhancedAllocation) => {
    const newStatus = allocation.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE';

    try {
      setUpdating(allocation.allocation_id);

      await allocationService.updateAllocation(
        allocation.basket_id,
        allocation.allocation_id,
        { status: newStatus, lot_multiplier: allocation.lot_multiplier }
      );

      // Update local state
      setAllocations(prev =>
        prev.map(a =>
          a.allocation_id === allocation.allocation_id
            ? { ...a, status: newStatus }
            : a
        )
      );

      showSuccess(`Allocation ${newStatus === 'ACTIVE' ? 'enabled' : 'disabled'} successfully`);

    } catch (error: any) {
      showError(error.message || 'Failed to update allocation status');
    } finally {
      setUpdating(null);
    }
  };

  // Handle lot multiplier editing
  const handleStartEdit = (allocation: EnhancedAllocation) => {
    setEditingAllocation(allocation.allocation_id);
    setEditLotMultiplier(allocation.lot_multiplier);
  };

  const handleSaveEdit = async (allocation: EnhancedAllocation) => {
    try {
      setUpdating(allocation.allocation_id);

      await allocationService.updateAllocation(
        allocation.basket_id,
        allocation.allocation_id,
        { lot_multiplier: editLotMultiplier, status: allocation.status }
      );

      // Update local state
      setAllocations(prev =>
        prev.map(a =>
          a.allocation_id === allocation.allocation_id
            ? { ...a, lot_multiplier: editLotMultiplier }
            : a
        )
      );

      setEditingAllocation(null);
      showSuccess('Lot multiplier updated successfully');

    } catch (error: any) {
      showError(error.message || 'Failed to update lot multiplier');
    } finally {
      setUpdating(null);
    }
  };

  const handleCancelEdit = () => {
    setEditingAllocation(null);
    setEditLotMultiplier(1);
  };

  // Handle individual allocation deletion
  const handleDeleteAllocation = (allocation: EnhancedAllocation) => {
    // Show enhanced confirmation dialog
    setDeleteConfirmDialog({
      isOpen: true,
      allocation: allocation
    });
  };

  // Confirm allocation deletion
  const confirmDeleteAllocation = async () => {
    if (!deleteConfirmDialog.allocation) return;

    try {
      setUpdating(deleteConfirmDialog.allocation.allocation_id);

      await allocationService.deleteAllocation(
        deleteConfirmDialog.allocation.basket_id,
        deleteConfirmDialog.allocation.allocation_id
      );

      // Remove from local state
      setAllocations(prev =>
        prev.filter(a => a.allocation_id !== deleteConfirmDialog.allocation!.allocation_id)
      );

      // Remove from selected allocations if it was selected
      setSelectedAllocations(prev => {
        const newSet = new Set(prev);
        newSet.delete(deleteConfirmDialog.allocation!.allocation_id);
        return newSet;
      });

      showSuccess(`Allocation for ${deleteConfirmDialog.allocation.broker_id} - ${deleteConfirmDialog.allocation.client_id} deleted successfully!`);

      // Close dialog
      setDeleteConfirmDialog({ isOpen: false, allocation: null });

    } catch (error: any) {
      showError(error.message || 'Failed to delete allocation');
    } finally {
      setUpdating(null);
    }
  };

  // Handle bulk selection
  const handleSelectAll = () => {
    const filtered = getFilteredAllocations();
    if (selectedAllocations.size === filtered.length) {
      setSelectedAllocations(new Set());
    } else {
      setSelectedAllocations(new Set(filtered.map(a => a.allocation_id)));
    }
  };

  const handleSelectAllocation = (allocationId: string) => {
    const newSelected = new Set(selectedAllocations);
    if (newSelected.has(allocationId)) {
      newSelected.delete(allocationId);
    } else {
      newSelected.add(allocationId);
    }
    setSelectedAllocations(newSelected);
  };

  // Export functionality
  const handleExport = () => {
    const filtered = getFilteredAllocations();
    const csvData = [
      ['Basket Name', 'Basket ID', 'Broker', 'Client ID', 'Lot Multiplier', 'Status', 'Created At', 'Updated At'],
      ...filtered.map(a => [
        a.basket_name,
        a.basket_id,
        a.broker_id,
        a.client_id,
        a.lot_multiplier.toString(),
        a.status,
        a.created_at,
        a.updated_at
      ])
    ];

    const csvContent = csvData.map(row => row.map(field => `"${field}"`).join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `allocations-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showSuccess('Allocations data exported successfully');
  };

  const stats = calculateStats();
  const filteredAllocations = getFilteredAllocations();

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mr-3" />
        <span className="text-lg text-gray-600 dark:text-gray-300">Loading all allocations...</span>
      </div>
    );
  }

  const actions = (
    <>
      <Button
        onClick={() => loadAllData()}
        leftIcon={<RefreshCw className="h-4 w-4" />}
        variant="outline"
        className="w-full sm:w-auto"
      >
        Refresh
      </Button>
      <Button
        onClick={handleExport}
        leftIcon={<Download className="h-4 w-4" />}
        variant="outline"
        className="w-full sm:w-auto"
      >
        Export CSV
      </Button>
    </>
  );

  return (
    <StandardLayout>
      <PageHeader
        title="All Allocations"
        description="Manage all basket-to-broker allocations across your trading platform. View, edit, and monitor allocation performance."
        pageType="management"
        breadcrumbs={[
          { label: 'Home', href: '/', icon: <Home className="w-4 h-4" /> },
          { label: 'All Allocations', icon: <Network className="w-4 h-4" /> }
        ]}
        actions={actions}
      />

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-600 mb-1">
              {stats.totalAllocations}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Total Allocations</p>
            <div className="mt-2">
              <Network className="h-4 w-4 text-blue-500 mx-auto" />
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-green-600 mb-1">
              {stats.activeAllocations}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Active</p>
            <div className="mt-2">
              <Activity className="h-4 w-4 text-green-500 mx-auto" />
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-purple-600 mb-1">
              {stats.uniqueBaskets}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Baskets</p>
            <div className="mt-2">
              <Target className="h-4 w-4 text-purple-500 mx-auto" />
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-orange-600 mb-1">
              {stats.uniqueBrokers}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Brokers</p>
            <div className="mt-2">
              <Users className="h-4 w-4 text-orange-500 mx-auto" />
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-cyan-600 mb-1">
              {stats.totalLotMultiplier}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Total Multiplier</p>
            <div className="mt-2">
              <TrendingUp className="h-4 w-4 text-cyan-500 mx-auto" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Search */}
      <Card>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                type="text"
                placeholder="Search baskets, brokers..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as 'ALL' | 'ACTIVE' | 'INACTIVE')}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="ALL">All Status</option>
              <option value="ACTIVE">Active</option>
              <option value="INACTIVE">Inactive</option>
            </select>

            {/* Basket Filter */}
            <select
              value={basketFilter}
              onChange={(e) => setBasketFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="ALL">All Baskets</option>
              {baskets.map(basket => (
                <option key={basket.basket_id} value={basket.basket_id}>
                  {basket.basket_name}
                </option>
              ))}
            </select>

            {/* Broker Filter */}
            <select
              value={brokerFilter}
              onChange={(e) => setBrokerFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="ALL">All Brokers</option>
              {getUniqueBrokers().map(broker => (
                <option key={broker} value={broker}>
                  {broker}
                </option>
              ))}
            </select>

            {/* Clear Filters */}
            <Button
              onClick={() => {
                setSearchQuery('');
                setStatusFilter('ALL');
                setBasketFilter('ALL');
                setBrokerFilter('ALL');
              }}
              variant="outline"
              size="sm"
            >
              Clear Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Allocations Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
              Allocations ({filteredAllocations.length})
            </CardTitle>
            <div className="flex items-center gap-4">
              {selectedAllocations.size > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {selectedAllocations.size} selected
                  </span>
                  <Button
                    onClick={() => setSelectedAllocations(new Set())}
                    variant="outline"
                    size="sm"
                  >
                    Clear Selection
                  </Button>
                </div>
              )}

              {/* View Toggle Buttons */}
              <div className="flex rounded-lg overflow-hidden border border-gray-300 dark:border-gray-600">
                <button
                  onClick={() => setAllocationView('cards')}
                  className={`px-3 py-2 text-sm font-medium transition-colors ${
                    allocationView === 'cards'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                  title="Card view"
                >
                  <Grid3x3 className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setAllocationView('table')}
                  className={`px-3 py-2 text-sm font-medium transition-colors border-l border-gray-300 dark:border-gray-600 ${
                    allocationView === 'table'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                  title="Table view"
                >
                  <List className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent className={allocationView === 'cards' ? 'p-6' : 'p-0'}>
          {filteredAllocations.length === 0 ? (
            <div className="text-center py-8">
              <Network className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No Allocations Found
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                {allocations.length === 0
                  ? "No basket-to-broker allocations have been created yet."
                  : "No allocations match your current filters."
                }
              </p>
            </div>
          ) : allocationView === 'cards' ? (
            /* Card View */
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {filteredAllocations.map((allocation) => (
                <AllocationCard
                  key={allocation.allocation_id}
                  allocation={allocation}
                  isSelected={selectedAllocations.has(allocation.allocation_id)}
                  onSelect={handleSelectAllocation}
                  onStatusToggle={handleStatusToggle}
                  onDelete={handleDeleteAllocation}
                  onStartEdit={handleStartEdit}
                  onSaveEdit={handleSaveEdit}
                  onCancelEdit={handleCancelEdit}
                  isEditing={editingAllocation === allocation.allocation_id}
                  isUpdating={updating === allocation.allocation_id}
                  editLotMultiplier={editLotMultiplier}
                  onEditLotMultiplierChange={setEditLotMultiplier}
                />
              ))}
            </div>
          ) : (
            /* Table View */
            <AllocationTable
              allocations={filteredAllocations}
              selectedAllocations={selectedAllocations}
              onSelectAll={handleSelectAll}
              onSelectAllocation={handleSelectAllocation}
              onStatusToggle={handleStatusToggle}
              onDelete={handleDeleteAllocation}
              onStartEdit={handleStartEdit}
              onSaveEdit={handleSaveEdit}
              onCancelEdit={handleCancelEdit}
              editingAllocation={editingAllocation}
              updating={updating}
              editLotMultiplier={editLotMultiplier}
              onEditLotMultiplierChange={setEditLotMultiplier}
            />
          )}
        </CardContent>
      </Card>

      {/* Delete Allocation Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteConfirmDialog.isOpen}
        onClose={() => setDeleteConfirmDialog({ isOpen: false, allocation: null })}
        onConfirm={confirmDeleteAllocation}
        title="Delete Allocation"
        message={`Are you sure you want to delete the allocation for ${deleteConfirmDialog.allocation?.broker_id || 'this broker'} - ${deleteConfirmDialog.allocation?.client_id || 'client'} in basket "${deleteConfirmDialog.allocation?.basket_name || 'this basket'}"? This action cannot be undone.`}
        confirmText="Delete Allocation"
        cancelText="Keep Allocation"
        variant="danger"
        icon={<Trash2 className="h-6 w-6 text-red-600" />}
      />
    </StandardLayout>
  );
};

export default AllAllocationsPage;