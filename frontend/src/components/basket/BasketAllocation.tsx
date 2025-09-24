import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Badge from '../ui/Badge';
import { useToast } from '../common/ToastContainer';
import { ArrowLeft, Plus, Trash2, RefreshCw, AlertCircle, Power, Edit3, Save, X } from 'lucide-react';
import { BrokerAccount, Basket, BasketBrokerAllocation, CreateAllocation } from '../../types';
import brokerService from '../../services/brokerService';
import allocationService from '../../services/allocationService';

interface BasketAllocationProps {
  basket: Basket;
  onBack: () => void;
  onAllocationComplete: () => void;
}

interface AllocationFormData {
  broker_id: string;
  client_id: string;
  lot_multiplier: number;
}

const BasketAllocation: React.FC<BasketAllocationProps> = ({
  basket,
  onBack,
  onAllocationComplete
}) => {
  const { showSuccess, showError } = useToast();
  const [brokerAccounts, setBrokerAccounts] = useState<BrokerAccount[]>([]);
  const [existingAllocations, setExistingAllocations] = useState<BasketBrokerAllocation[]>([]);
  const [newAllocations, setNewAllocations] = useState<AllocationFormData[]>([]);

  // Loading states
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Edit mode state
  const [editingAllocation, setEditingAllocation] = useState<string | null>(null);
  const [editLotMultiplier, setEditLotMultiplier] = useState<number>(1);

  // Load broker accounts and existing allocations
  const loadData = async () => {
    try {
      setLoading(true);

      // Load broker accounts
      const accounts = await brokerService.getBrokerAccounts();
      setBrokerAccounts(accounts.filter(account => account.account_status === 'enabled'));

      // Load existing allocations for this basket
      try {
        const allocations = await allocationService.getBasketAllocations(basket.basket_id);
        setExistingAllocations(allocations);
      } catch (allocError) {
        console.warn('Failed to load existing allocations:', allocError);
        // Continue without existing allocations - user can still create new ones
        setExistingAllocations([]);
      }

    } catch (error: any) {
      console.error('Failed to load data:', error);
      showError('Failed to load broker accounts. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [basket.basket_id]); // eslint-disable-line react-hooks/exhaustive-deps

  const addNewAllocation = () => {
    setNewAllocations(prev => [...prev, {
      broker_id: '',
      client_id: '',
      lot_multiplier: 1
    }]);
  };

  const removeNewAllocation = (index: number) => {
    setNewAllocations(prev => prev.filter((_, i) => i !== index));
  };

  const updateNewAllocation = (index: number, field: keyof AllocationFormData, value: string | number) => {
    setNewAllocations(prev => prev.map((allocation, i) => 
      i === index ? { ...allocation, [field]: value } : allocation
    ));
  };

  const handleBrokerChange = (index: number, brokerId: string) => {
    const selectedBroker = brokerAccounts.find(b => `${b.broker_name}-${b.client_id}` === brokerId);
    if (selectedBroker) {
      updateNewAllocation(index, 'broker_id', selectedBroker.broker_name);
      updateNewAllocation(index, 'client_id', selectedBroker.client_id);
    }
  };

  const validateAllocations = (): boolean => {
    // Check if all allocations are complete
    for (const allocation of newAllocations) {
      if (!allocation.broker_id || !allocation.client_id || allocation.lot_multiplier <= 0) {
        showError('Please complete all allocation details with valid lot multipliers (> 0)');
        return false;
      }
    }

    // Check for duplicate broker-client combinations
    const combinations = newAllocations.map(a => `${a.broker_id}-${a.client_id}`);
    const uniqueCombinations = new Set(combinations);
    if (combinations.length !== uniqueCombinations.size) {
      showError('Duplicate broker-client combinations are not allowed');
      return false;
    }

    // Check against existing allocations
    if (Array.isArray(existingAllocations)) {
      for (const newAlloc of newAllocations) {
        const exists = existingAllocations.some(existing =>
          existing.broker_id === newAlloc.broker_id && existing.client_id === newAlloc.client_id
        );
        if (exists) {
          showError(`Allocation already exists for ${newAlloc.broker_id} - ${newAlloc.client_id}`);
          return false;
        }
      }
    }

    return true;
  };

  const handleDeleteAllocation = async (allocation: BasketBrokerAllocation) => {
    try {
      setSaving(true);

      await allocationService.deleteAllocation(basket.basket_id, allocation.allocation_id);

      showSuccess(`Successfully deleted allocation for ${allocation.broker_id} - ${allocation.client_id}`);

      // Remove from state locally instead of full reload - much faster!
      setExistingAllocations(prev =>
        prev.filter(a => a.allocation_id !== allocation.allocation_id)
      );

    } catch (error: any) {
      console.error('Failed to delete allocation:', error);
      showError(error.message || 'Failed to delete allocation. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleStartEdit = (allocation: BasketBrokerAllocation) => {
    setEditingAllocation(allocation.allocation_id);
    setEditLotMultiplier(allocation.lot_multiplier);
  };

  const handleCancelEdit = () => {
    setEditingAllocation(null);
    setEditLotMultiplier(1);
  };

  const handleSaveEdit = async (allocation: BasketBrokerAllocation) => {
    try {
      setSaving(true);

      if (editLotMultiplier <= 0) {
        showError('Lot multiplier must be greater than 0');
        return;
      }

      await allocationService.updateAllocation(basket.basket_id, allocation.allocation_id, {
        status: allocation.status,
        lot_multiplier: editLotMultiplier
      });

      showSuccess(`Successfully updated lot multiplier for ${allocation.broker_id} - ${allocation.client_id}`);

      // Update state locally
      setExistingAllocations(prev =>
        prev.map(a =>
          a.allocation_id === allocation.allocation_id
            ? { ...a, lot_multiplier: editLotMultiplier }
            : a
        )
      );

      // Exit edit mode
      setEditingAllocation(null);
      setEditLotMultiplier(1);

    } catch (error: any) {
      console.error('Failed to update lot multiplier:', error);
      showError(error.message || 'Failed to update lot multiplier. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleToggleAllocationStatus = async (allocation: BasketBrokerAllocation) => {
    try {
      setSaving(true);

      const newStatus = allocation.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE';

      await allocationService.updateAllocation(basket.basket_id, allocation.allocation_id, {
        status: newStatus,
        lot_multiplier: allocation.lot_multiplier
      });

      showSuccess(`Successfully ${newStatus === 'ACTIVE' ? 'enabled' : 'disabled'} allocation for ${allocation.broker_id} - ${allocation.client_id}`);

      // Update state locally instead of full reload - much faster!
      setExistingAllocations(prev =>
        prev.map(a =>
          a.allocation_id === allocation.allocation_id
            ? { ...a, status: newStatus }
            : a
        )
      );

    } catch (error: any) {
      console.error('Failed to update allocation status:', error);
      showError(error.message || 'Failed to update allocation status. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAllocations = async () => {
    try {
      if (newAllocations.length === 0) {
        showError('Please add at least one broker allocation');
        return;
      }

      if (!validateAllocations()) {
        return;
      }

      setSaving(true);

      const createData: CreateAllocation = {
        allocations: newAllocations
      };

      // Create basket allocations using the allocation service
      await allocationService.createBasketAllocations(basket.basket_id, createData);

      showSuccess(`Successfully allocated basket to ${newAllocations.length} broker account(s)`);
      setNewAllocations([]);

      // Refresh the allocations list to show newly created ones
      try {
        const updatedAllocations = await allocationService.getBasketAllocations(basket.basket_id);
        setExistingAllocations(updatedAllocations);
      } catch (error) {
        console.warn('Failed to refresh allocations after create, will reload on next visit');
      }

      // Don't automatically switch tabs - let user stay on allocation tab to see their new allocations

    } catch (error: any) {
      console.error('Failed to create allocations:', error);
      showError(error.message || 'Failed to create allocations. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const calculateTotalMultiplier = (): number => {
    const newTotal = newAllocations.reduce((sum, allocation) => sum + allocation.lot_multiplier, 0);
    const existingTotal = Array.isArray(existingAllocations)
      ? existingAllocations.reduce((sum, allocation) => sum + allocation.lot_multiplier, 0)
      : 0;
    return newTotal + existingTotal;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="outline" onClick={onBack} leftIcon={<ArrowLeft className="h-4 w-4" />}>
            Back to Baskets
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Allocate Basket to Brokers</h1>
            <p className="text-gray-600 dark:text-gray-300">
              Allocating: {basket.basket_name}
            </p>
          </div>
        </div>
        
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mr-3" />
          <span className="text-gray-600 dark:text-gray-400">Loading broker accounts...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="outline" onClick={onBack} leftIcon={<ArrowLeft className="h-4 w-4" />}>
            Back to Baskets
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Allocate Basket to Brokers</h1>
            <p className="text-gray-600 dark:text-gray-300">
              Allocating: <span className="font-medium">{basket.basket_name}</span>
            </p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-600">Total Lot Multiplier</div>
          <div className="text-2xl font-bold text-blue-600">{calculateTotalMultiplier()}</div>
        </div>
      </div>

      {/* Basket Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Basket Summary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <div className="text-sm text-gray-600">Basket Name</div>
              <div className="font-semibold">{basket.basket_name}</div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Status</div>
              <Badge variant={basket.status === 'ACTIVE' ? 'success' : 'default'}>
                {basket.status}
              </Badge>
            </div>
            <div>
              <div className="text-sm text-gray-600">Strategies</div>
              <div className="font-semibold">{basket.strategies.length}</div>
            </div>
          </div>
          {basket.description && (
            <div>
              <div className="text-sm text-gray-600">Description</div>
              <div className="text-sm">{basket.description}</div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Existing Allocations */}
      {Array.isArray(existingAllocations) && existingAllocations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>🔗 Existing Allocations ({existingAllocations.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {existingAllocations.map((allocation) => (
                <div key={`${allocation.broker_id}-${allocation.client_id}`}
                     className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="font-medium">
                      {allocation.broker_id.charAt(0).toUpperCase() + allocation.broker_id.slice(1)}
                    </div>
                    <Badge variant="info" size="sm">
                      {allocation.client_id}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-600">Lot Multiplier:</span>
                      {editingAllocation === allocation.allocation_id ? (
                        <div className="flex items-center gap-2">
                          <Input
                            type="number"
                            min="1"
                            step="1"
                            value={editLotMultiplier}
                            onChange={(e) => setEditLotMultiplier(parseFloat(e.target.value) || 1)}
                            className="w-20"
                          />
                        </div>
                      ) : (
                        <span className="font-semibold text-blue-600">{allocation.lot_multiplier}</span>
                      )}
                      <Badge variant={allocation.status === 'ACTIVE' ? 'success' : 'default'} size="sm">
                        {allocation.status}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      {editingAllocation === allocation.allocation_id ? (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleSaveEdit(allocation)}
                            disabled={saving}
                            className="text-green-600 hover:text-green-700 border-green-200"
                          >
                            <Save className="h-3 w-3" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={handleCancelEdit}
                            disabled={saving}
                            className="text-gray-600 hover:text-gray-700 border-gray-200"
                          >
                            <X className="h-3 w-3" />
                          </Button>
                        </>
                      ) : (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleStartEdit(allocation)}
                            disabled={saving || editingAllocation !== null}
                            className="text-blue-600 hover:text-blue-700 border-blue-200"
                          >
                            <Edit3 className="h-3 w-3" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleToggleAllocationStatus(allocation)}
                            disabled={saving || editingAllocation !== null}
                            className={`${allocation.status === 'ACTIVE'
                              ? 'text-orange-600 hover:text-orange-700 border-orange-200'
                              : 'text-green-600 hover:text-green-700 border-green-200'
                            }`}
                          >
                            <Power className="h-3 w-3 mr-1" />
                            {allocation.status === 'ACTIVE' ? 'Disable' : 'Enable'}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDeleteAllocation(allocation)}
                            disabled={saving || editingAllocation !== null}
                            className="text-red-600 hover:text-red-700 border-red-200"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* New Allocations */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>➕ Add New Allocations</CardTitle>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={addNewAllocation}
              leftIcon={<Plus className="h-4 w-4" />}
            >
              Add Allocation
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {newAllocations.length === 0 ? (
            existingAllocations.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <div className="text-sm font-medium text-gray-500 mb-2">No Allocations Yet</div>
                <p>No broker allocations configured. Click "Add Allocation" to start allocating this basket to brokers.</p>
              </div>
            ) : (
              <div className="text-center py-4 text-gray-400">
                <p className="text-sm">Use "Add Allocation" button above to add more broker allocations.</p>
              </div>
            )
          ) : (
            <div className="space-y-4">
              {newAllocations.map((allocation, index) => (
                <div key={index} className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 border rounded-lg">
                  <div>
                    <label className="block text-sm font-medium mb-1">Broker Account</label>
                    <select
                      value={`${allocation.broker_id}-${allocation.client_id}`}
                      onChange={(e) => handleBrokerChange(index, e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    >
                      <option value="">Select broker account...</option>
                      {brokerAccounts.map(broker => (
                        <option key={broker.client_id} value={`${broker.broker_name}-${broker.client_id}`}>
                          {broker.broker_name.charAt(0).toUpperCase() + broker.broker_name.slice(1)} - {broker.client_id} (₹{broker.capital.toLocaleString()})
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-1">Broker ID</label>
                    <div className="px-3 py-2 bg-gray-50 dark:bg-gray-600 border border-gray-300 dark:border-gray-600 rounded-md text-sm text-gray-700 dark:text-gray-300">
                      {allocation.broker_id || 'Auto-filled'}
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-1">Client ID</label>
                    <div className="px-3 py-2 bg-gray-50 dark:bg-gray-600 border border-gray-300 dark:border-gray-600 rounded-md text-sm text-gray-700 dark:text-gray-300">
                      {allocation.client_id || 'Auto-filled'}
                    </div>
                  </div>
                  
                  <div className="flex items-end gap-2">
                    <div className="flex-1">
                      <label className="block text-sm font-medium mb-1">Lot Multiplier</label>
                      <Input
                        type="number"
                        min="1"
                        step="1"
                        value={allocation.lot_multiplier}
                        onChange={(e) => updateNewAllocation(index, 'lot_multiplier', parseFloat(e.target.value) || 1)}
                        placeholder="1"
                      />
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => removeNewAllocation(index)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {newAllocations.length > 0 && (
            <div className="flex justify-between items-center pt-4 border-t">
              <div className="text-sm text-gray-600">
                Adding {newAllocations.length} new allocation(s) with total multiplier of{' '}
                <span className="font-semibold text-blue-600">
                  {newAllocations.reduce((sum, a) => sum + a.lot_multiplier, 0)}
                </span>
              </div>
              <div className="flex gap-3">
                <Button 
                  variant="outline" 
                  onClick={() => setNewAllocations([])}
                  disabled={saving}
                >
                  Clear All
                </Button>
                <Button 
                  onClick={handleSaveAllocations}
                  disabled={saving}
                  leftIcon={saving ? <RefreshCw className="h-4 w-4 animate-spin" /> : undefined}
                >
                  {saving ? 'Saving...' : 'Save Allocations'}
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="border-blue-200 bg-blue-50 dark:bg-blue-900/20">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
            <div>
              <h4 className="font-medium text-blue-800 dark:text-blue-200">How Lot Multipliers Work</h4>
              <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                Each strategy leg has base lots. When executing through a broker, the final lots = base_lots × lot_multiplier.
                For example, if a leg has 2 base lots and you set multiplier to 3, the broker will execute 6 lots.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default BasketAllocation;