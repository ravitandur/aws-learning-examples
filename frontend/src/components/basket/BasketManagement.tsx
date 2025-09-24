import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Badge from '../ui/Badge';
import { Trash2, Plus, Edit, Settings, AlertCircle, RefreshCw } from 'lucide-react';
import { BrokerAccount, Strategy, Basket, CreateBasket } from '../../types';
import basketService from '../../services/basketService';
import brokerService from '../../services/brokerService';
import BasketAllocation from './BasketAllocation';

const BasketManagement: React.FC = () => {
  const [baskets, setBaskets] = useState<Basket[]>([]);
  const [brokerAccounts, setBrokerAccounts] = useState<BrokerAccount[]>([]);
  const [availableStrategies, setAvailableStrategies] = useState<Strategy[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingBasket, setEditingBasket] = useState<string | null>(null);
  const [allocatingBasket, setAllocatingBasket] = useState<Basket | null>(null);
  
  // Loading states
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  
  // Error states
  const [error, setError] = useState<string | null>(null);

  // Form state for creating/editing baskets
  const [formData, setFormData] = useState({
    basketName: '',
    description: '',
    strategies: [] as string[]
  });

  // Load initial data
  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Load data in parallel
      const [brokersResult, strategiesResult, basketsResult] = await Promise.allSettled([
        brokerService.getBrokerAccounts(),
        basketService.getAvailableStrategies(),
        basketService.getBaskets()
      ]);
      
      // Handle broker accounts
      if (brokersResult.status === 'fulfilled') {
        setBrokerAccounts(brokersResult.value);
      } else {
        console.error('Failed to load broker accounts:', brokersResult.reason);
      }
      
      // Handle strategies
      if (strategiesResult.status === 'fulfilled') {
        setAvailableStrategies(strategiesResult.value);
      } else {
        console.error('Failed to load strategies:', strategiesResult.reason);
      }
      
      // Handle baskets
      if (basketsResult.status === 'fulfilled') {
        setBaskets(basketsResult.value);
      } else {
        console.error('Failed to load baskets:', basketsResult.reason);
      }
      
    } catch (error) {
      console.error('Failed to load data:', error);
      setError('Failed to load data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateBasket = async () => {
    try {
      setCreating(true);
      setError(null);

      // Validate form
      if (!formData.basketName.trim()) {
        setError('Basket name is required');
        return;
      }
      
      if (formData.strategies.length === 0) {
        setError('Please select at least one strategy');
        return;
      }

      const createBasketData: CreateBasket = {
        basket_name: formData.basketName.trim(),
        description: formData.description.trim() || undefined,
        strategies: formData.strategies,
        initial_capital: 100000 // Default initial capital
      };

      const newBasket = await basketService.createBasket(createBasketData);
      setBaskets(prev => [...prev, newBasket]);
      setShowCreateForm(false);
      resetForm();
      
    } catch (error: any) {
      console.error('Failed to create basket:', error);
      setError(error.message || 'Failed to create basket. Please try again.');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteBasket = async (basketId: string) => {
    try {
      setDeleting(basketId);
      setError(null);
      
      await basketService.deleteBasket(basketId);
      setBaskets(prev => prev.filter(basket => basket.basket_id !== basketId));
      
    } catch (error: any) {
      console.error('Failed to delete basket:', error);
      setError(error.message || 'Failed to delete basket. Please try again.');
    } finally {
      setDeleting(null);
    }
  };

  const resetForm = () => {
    setFormData({
      basketName: '',
      description: '',
      strategies: []
    });
    setEditingBasket(null);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return 'success';
      case 'PAUSED':
        return 'warning';
      case 'INACTIVE':
      case 'COMPLETED':
        return 'default';
      default:
        return 'default';
    }
  };

  // Show allocation view if a basket is being allocated
  if (allocatingBasket) {
    return (
      <BasketAllocation
        basket={allocatingBasket}
        onBack={() => setAllocatingBasket(null)}
        onAllocationComplete={() => {
          setAllocatingBasket(null);
          // Optionally refresh the baskets list
          loadData();
        }}
      />
    );
  }

  // Show loading state while data loads
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold">Basket Management</h1>
            <p className="text-gray-600 dark:text-gray-300">
              Manage your options trading strategy baskets
            </p>
          </div>
        </div>
        
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mr-3" />
          <span className="text-gray-600 dark:text-gray-400">Loading baskets and data...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Error Message */}
      {error && (
        <Card className="border-red-200 bg-red-50 dark:bg-red-900/20">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <div className="flex-1">
                <p className="text-red-800 dark:text-red-200">{error}</p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setError(null)}
              >
                Dismiss
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">🧺 Basket Management</h1>
          <p className="text-gray-600 dark:text-gray-300">
            Manage your options trading strategy baskets
          </p>
        </div>
        <div className="flex space-x-3">
          <Button
            variant="outline"
            onClick={loadData}
            leftIcon={<RefreshCw className="h-4 w-4" />}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            onClick={() => setShowCreateForm(true)}
            leftIcon={<Plus className="h-4 w-4" />}
          >
            Create New Basket
          </Button>
        </div>
      </div>

      {/* Create/Edit Basket Form */}
      {showCreateForm && (
        <Card className="border-2 border-blue-500">
          <CardHeader>
            <CardTitle>Create New Basket</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Basket Name *</label>
                <Input
                  value={formData.basketName}
                  onChange={(e) => setFormData(prev => ({ ...prev, basketName: e.target.value }))}
                  placeholder="Conservative Multi-Broker Basket"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <Input
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Strategy basket description..."
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Add Strategies to Basket</label>
              <div className="space-y-2">
                {availableStrategies.map(strategy => (
                  <div key={strategy.strategyId} className="flex items-center space-x-2 p-3 border rounded-lg">
                    <input
                      type="checkbox"
                      id={strategy.strategyId}
                      checked={formData.strategies.includes(strategy.strategyId)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setFormData(prev => ({
                            ...prev,
                            strategies: [...prev.strategies, strategy.strategyId]
                          }));
                        } else {
                          setFormData(prev => ({
                            ...prev,
                            strategies: prev.strategies.filter(id => id !== strategy.strategyId)
                          }));
                        }
                      }}
                      className="rounded"
                    />
                    <label htmlFor={strategy.strategyId} className="flex-1 cursor-pointer">
                      <div className="font-medium">{strategy.strategyName}</div>
                      <div className="text-sm text-gray-600">{strategy.strategyType} • {strategy.legs} legs</div>
                    </label>
                    <Badge variant={getStatusColor(strategy.status)} size="sm">
                      {strategy.status}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex space-x-4 pt-4">
              <Button 
                onClick={handleCreateBasket} 
                className="flex-1" 
                disabled={creating}
                leftIcon={creating ? <RefreshCw className="h-4 w-4 animate-spin" /> : undefined}
              >
                {creating ? 'Creating...' : 'Create Basket'}
              </Button>
              <Button 
                variant="outline" 
                onClick={() => { setShowCreateForm(false); resetForm(); }}
                disabled={creating}
              >
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Baskets List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {baskets.map(basket => (
          <Card key={basket.basket_id} className="border-l-4 border-l-blue-500">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg">{basket.basket_name}</CardTitle>
                  {basket.description && (
                    <p className="text-sm text-gray-600 mt-1">{basket.description}</p>
                  )}
                </div>
                <div className="flex space-x-2">
                  <Badge variant={getStatusColor(basket.status)}>
                    {basket.status}
                  </Badge>
                  <Button variant="ghost" size="sm">
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={() => handleDeleteBasket(basket.basket_id)}
                    disabled={deleting === basket.basket_id}
                  >
                    {deleting === basket.basket_id ? (
                      <RefreshCw className="h-4 w-4 animate-spin" />
                    ) : (
                      <Trash2 className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* Basket Stats */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-gray-600">Status</div>
                  <Badge variant={getStatusColor(basket.status)} className="text-sm">
                    {basket.status}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Strategies</div>
                  <div className="font-semibold text-lg">{basket.strategies.length}</div>
                </div>
              </div>

              {/* Strategies in Basket */}
              <div>
                <div className="text-sm font-medium text-gray-700 mb-2">Strategies</div>
                <div className="space-y-2">
                  {basket.strategies.map(strategy => (
                    <div key={strategy.strategyId} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded">
                      <div>
                        <div className="font-medium text-sm">{strategy.strategyName}</div>
                        <div className="text-xs text-gray-600">{strategy.strategyType} • {strategy.legs} legs</div>
                      </div>
                      <Badge variant={getStatusColor(strategy.status)} size="sm">
                        {strategy.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex space-x-2 pt-2">
                <Button 
                  variant="primary" 
                  size="sm" 
                  className="flex-1"
                  onClick={() => setAllocatingBasket(basket)}
                >
                  <Settings className="h-4 w-4 mr-2" />
                  Allocate to Brokers
                </Button>
                <Button variant="outline" size="sm">
                  View Details
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {baskets.length === 0 && !showCreateForm && (
        <Card className="text-center py-12">
          <CardContent>
            <div className="text-sm font-medium text-gray-500 mb-4">No baskets</div>
            <h3 className="text-lg font-semibold mb-2">No Baskets Created Yet</h3>
            <p className="text-gray-600 mb-6">
              Create your first revolutionary basket to start managing strategies with multi-broker allocation
            </p>
            <Button onClick={() => setShowCreateForm(true)} leftIcon={<Plus className="h-4 w-4" />}>
              Create Your First Basket
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default BasketManagement;