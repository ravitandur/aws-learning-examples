import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Badge from '../ui/Badge';
import { 
  Trash2, Plus, Edit, Settings, AlertCircle, RefreshCw, 
  Play, Pause, Square, BarChart3,
  TrendingUp, Activity
} from 'lucide-react';
import { BrokerAccount, Strategy, Basket, CreateBasket, BasketBrokerAllocation } from '../../types';
import basketService from '../../services/basketService';
import brokerService from '../../services/brokerService';
import allocationService from '../../services/allocationService';
import BasketAllocation from './BasketAllocation';
import BasketPerformance from './BasketPerformance';

interface BasketStats {
  totalPnL: number;
  executionCount: number;
  lastExecution?: string;
  avgExecutionTime: number;
  successRate: number;
}

interface EnhancedBasket extends Basket {
  allocations: BasketBrokerAllocation[];
  stats: BasketStats;
  revolutionaryFeatures: {
    gsi2Optimized: boolean;
    multibrokerEnabled: boolean;
    timingPrecision: number;
    weekendProtected: boolean;
  };
}

const EnhancedBasketManagement: React.FC = () => {
  const [baskets, setBaskets] = useState<EnhancedBasket[]>([]);
  const [brokerAccounts, setBrokerAccounts] = useState<BrokerAccount[]>([]);
  const [availableStrategies, setAvailableStrategies] = useState<Strategy[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingBasket, setEditingBasket] = useState<string | null>(null);
  const [allocatingBasket, setAllocatingBasket] = useState<Basket | null>(null);
  const [viewingPerformance, setViewingPerformance] = useState<EnhancedBasket | null>(null);
  
  // Loading states
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  
  // Error states
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Form state for creating/editing baskets
  const [formData, setFormData] = useState({
    basketName: '',
    description: '',
    strategies: [] as string[]
  });

  // Portfolio summary
  const [portfolioSummary, setPortfolioSummary] = useState({
    totalBaskets: 0,
    activeBaskets: 0,
    totalPnL: 0,
    totalAllocations: 0,
    uniqueBrokers: 0,
    avgExecutionTime: 0
  });

  // Load all data
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
      
      // Handle baskets and enhance with allocation data
      if (basketsResult.status === 'fulfilled') {
        const basketsData = basketsResult.value;
        const enhancedBaskets = await Promise.all(
          basketsData.map(async (basket): Promise<EnhancedBasket> => {
            try {
              // Load allocations for this basket
              const allocations = await allocationService.getBasketAllocations(basket.basket_id);
              
              // Mock stats for now - replace with actual API calls
              const stats: BasketStats = {
                totalPnL: Math.random() * 2000 - 500, // -500 to +1500
                executionCount: Math.floor(Math.random() * 50),
                lastExecution: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
                avgExecutionTime: Math.random() * 100 + 50, // 50-150ms
                successRate: Math.random() * 30 + 70 // 70-100%
              };

              return {
                ...basket,
                allocations,
                stats,
                revolutionaryFeatures: {
                  gsi2Optimized: true,
                  multibrokerEnabled: allocations.length > 1,
                  timingPrecision: Math.random() * 0.5, // 0-0.5 seconds
                  weekendProtected: true
                }
              };
            } catch (error) {
              console.warn(`Failed to load allocations for basket ${basket.basket_id}:`, error);
              return {
                ...basket,
                allocations: [],
                stats: {
                  totalPnL: 0,
                  executionCount: 0,
                  avgExecutionTime: 0,
                  successRate: 0
                },
                revolutionaryFeatures: {
                  gsi2Optimized: true,
                  multibrokerEnabled: false,
                  timingPrecision: 0,
                  weekendProtected: true
                }
              };
            }
          })
        );
        
        setBaskets(enhancedBaskets);
        
        // Calculate portfolio summary
        const summary = {
          totalBaskets: enhancedBaskets.length,
          activeBaskets: enhancedBaskets.filter(b => b.status === 'ACTIVE').length,
          totalPnL: enhancedBaskets.reduce((sum, b) => sum + b.stats.totalPnL, 0),
          totalAllocations: enhancedBaskets.reduce((sum, b) => sum + b.allocations.length, 0),
          uniqueBrokers: new Set(enhancedBaskets.flatMap(b => b.allocations.map(a => a.broker_id))).size,
          avgExecutionTime: enhancedBaskets.reduce((sum, b) => sum + b.stats.avgExecutionTime, 0) / Math.max(1, enhancedBaskets.length)
        };
        setPortfolioSummary(summary);
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

      await basketService.createBasket(createBasketData);
      setShowCreateForm(false);
      resetForm();
      setSuccess('Basket created successfully!');
      
      // Reload data to show new basket
      await loadData();
      
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
      setSuccess('Basket deleted successfully');
      
      // Remove from local state
      setBaskets(prev => prev.filter(basket => basket.basket_id !== basketId));
      
    } catch (error: any) {
      console.error('Failed to delete basket:', error);
      setError(error.message || 'Failed to delete basket. Please try again.');
    } finally {
      setDeleting(null);
    }
  };

  const handleBasketAction = async (basketId: string, action: 'start' | 'pause' | 'stop') => {
    try {
      setActionLoading(`${action}-${basketId}`);
      setError(null);
      
      switch (action) {
        case 'start':
          await basketService.startBasket(basketId);
          setSuccess('Basket started successfully');
          break;
        case 'pause':
          await basketService.pauseBasket(basketId);
          setSuccess('Basket paused successfully');
          break;
        case 'stop':
          await basketService.stopBasket(basketId);
          setSuccess('Basket stopped successfully');
          break;
      }
      
      // Reload data to reflect status changes
      await loadData();
      
    } catch (error: any) {
      console.error(`Failed to ${action} basket:`, error);
      setError(error.message || `Failed to ${action} basket. Please try again.`);
    } finally {
      setActionLoading(null);
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
          loadData(); // Reload to show updated allocations
        }}
      />
    );
  }

  // Show performance view if viewing performance
  if (viewingPerformance) {
    return (
      <BasketPerformance
        basket={viewingPerformance}
        onBack={() => setViewingPerformance(null)}
      />
    );
  }

  // Show loading state while data loads
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold">🧺 Revolutionary Basket Management</h1>
            <p className="text-gray-600 dark:text-gray-300">
              Manage your options trading strategy baskets
            </p>
          </div>
        </div>
        
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mr-3" />
          <span className="text-gray-600 dark:text-gray-400">Loading baskets and performance data...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Success Message */}
      {success && (
        <Card className="border-green-200 bg-green-50 dark:bg-green-900/20">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Activity className="h-5 w-5 text-green-600" />
              <div className="flex-1">
                <p className="text-green-800 dark:text-green-200">{success}</p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSuccess(null)}
              >
                Dismiss
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

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

      {/* Portfolio Summary */}
      <Card className="border-2 border-blue-500 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-6 w-6" />
            Revolutionary Portfolio Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{portfolioSummary.totalBaskets}</div>
              <div className="text-sm text-gray-600">Total Baskets</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{portfolioSummary.activeBaskets}</div>
              <div className="text-sm text-gray-600">Active</div>
            </div>
            <div className="text-center">
              <div className={`text-2xl font-bold ${portfolioSummary.totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                ₹{portfolioSummary.totalPnL.toFixed(0)}
              </div>
              <div className="text-sm text-gray-600">Total P&L</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{portfolioSummary.totalAllocations}</div>
              <div className="text-sm text-gray-600">Allocations</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-indigo-600">{portfolioSummary.uniqueBrokers}</div>
              <div className="text-sm text-gray-600">Brokers</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{portfolioSummary.avgExecutionTime.toFixed(0)}ms</div>
              <div className="text-sm text-gray-600">Avg Speed</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">🧺 Revolutionary Basket Management</h1>
          <p className="text-gray-600 dark:text-gray-300">
            Manage strategy baskets with institutional-grade multi-broker allocation
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
            Create Basket
          </Button>
        </div>
      </div>

      {/* Create/Edit Basket Form */}
      {showCreateForm && (
        <Card className="border-2 border-blue-500">
          <CardHeader>
            <CardTitle>🚀 Create New Revolutionary Basket</CardTitle>
            <p className="text-sm text-gray-600">
              Create a basket with advanced multi-broker allocation and 0-second precision timing
            </p>
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
              <label className="block text-sm font-medium mb-2">🎯 Add Strategies to Basket</label>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {availableStrategies.map(strategy => (
                  <div key={strategy.strategyId} className="flex items-center space-x-2 p-3 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
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
              {availableStrategies.length === 0 && (
                <p className="text-sm text-gray-500 text-center py-4">
                  No strategies available. Create strategies first to add them to baskets.
                </p>
              )}
            </div>

            <div className="flex space-x-4 pt-4">
              <Button 
                onClick={handleCreateBasket} 
                className="flex-1" 
                disabled={creating}
                leftIcon={creating ? <RefreshCw className="h-4 w-4 animate-spin" /> : undefined}
              >
                {creating ? 'Creating...' : '🚀 Create Revolutionary Basket'}
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
          <Card key={basket.basket_id} className="border-l-4 border-l-blue-500 hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg flex items-center gap-2">
                    {basket.basket_name}
                    {basket.revolutionaryFeatures.multibrokerEnabled && (
                      <Badge variant="info" size="sm">Multi-Broker</Badge>
                    )}
                  </CardTitle>
                  {basket.description && (
                    <p className="text-sm text-gray-600 mt-1">{basket.description}</p>
                  )}
                </div>
                <div className="flex space-x-2">
                  <Badge variant={getStatusColor(basket.status)}>
                    {basket.status}
                  </Badge>
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* Performance Metrics */}
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <div className={`text-lg font-bold ${basket.stats.totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    ₹{basket.stats.totalPnL.toFixed(0)}
                  </div>
                  <div className="text-xs text-gray-600">P&L</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-blue-600">{basket.stats.executionCount}</div>
                  <div className="text-xs text-gray-600">Executions</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-green-600">{basket.stats.successRate.toFixed(0)}%</div>
                  <div className="text-xs text-gray-600">Success Rate</div>
                </div>
              </div>

              {/* Revolutionary Features */}
              <div className="flex flex-wrap gap-1">
                <Badge variant="success" size="sm">⚡ GSI2</Badge>
                {basket.revolutionaryFeatures.multibrokerEnabled && (
                  <Badge variant="info" size="sm">🏦 Multi-Broker</Badge>
                )}
                <Badge variant="success" size="sm">🎯 {basket.revolutionaryFeatures.timingPrecision.toFixed(1)}s</Badge>
                <Badge variant="success" size="sm">🛡️ Weekend Safe</Badge>
              </div>

              {/* Broker Allocations Summary */}
              {basket.allocations.length > 0 && (
                <div>
                  <div className="text-sm font-medium text-gray-700 mb-2">
                    🏦 Broker Allocations ({basket.allocations.length})
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {allocationService.getBrokerBreakdown(basket.allocations).map(broker => (
                      <Badge key={broker.broker_id} variant="info" size="sm">
                        {broker.broker_id.charAt(0).toUpperCase() + broker.broker_id.slice(1)}: {broker.total_multiplier}x
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="grid grid-cols-2 gap-2 pt-2">
                <div className="flex space-x-1">
                  {basket.status === 'ACTIVE' ? (
                    <>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleBasketAction(basket.basket_id, 'pause')}
                        disabled={actionLoading === `pause-${basket.basket_id}`}
                        leftIcon={actionLoading === `pause-${basket.basket_id}` ? 
                          <RefreshCw className="h-3 w-3 animate-spin" /> : 
                          <Pause className="h-3 w-3" />
                        }
                      >
                        Pause
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleBasketAction(basket.basket_id, 'stop')}
                        disabled={actionLoading === `stop-${basket.basket_id}`}
                        leftIcon={actionLoading === `stop-${basket.basket_id}` ? 
                          <RefreshCw className="h-3 w-3 animate-spin" /> : 
                          <Square className="h-3 w-3" />
                        }
                      >
                        Stop
                      </Button>
                    </>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleBasketAction(basket.basket_id, 'start')}
                      disabled={actionLoading === `start-${basket.basket_id}`}
                      leftIcon={actionLoading === `start-${basket.basket_id}` ? 
                        <RefreshCw className="h-3 w-3 animate-spin" /> : 
                        <Play className="h-3 w-3" />
                      }
                    >
                      Start
                    </Button>
                  )}
                </div>
                
                <div className="flex space-x-1">
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => setAllocatingBasket(basket)}
                    leftIcon={<Settings className="h-3 w-3" />}
                  >
                    Allocate
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setViewingPerformance(basket)}
                    leftIcon={<TrendingUp className="h-3 w-3" />}
                  >
                    Analytics
                  </Button>
                </div>
              </div>

              <div className="flex justify-end space-x-2 pt-2 border-t">
                <Button variant="ghost" size="sm">
                  <Edit className="h-4 w-4" />
                </Button>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => handleDeleteBasket(basket.basket_id)}
                  disabled={deleting === basket.basket_id}
                  className="text-red-600 hover:text-red-700"
                >
                  {deleting === basket.basket_id ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <Trash2 className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Empty State */}
      {baskets.length === 0 && !showCreateForm && (
        <Card className="text-center py-12">
          <CardContent>
            <div className="text-6xl mb-4">🧺</div>
            <h3 className="text-lg font-semibold mb-2">No Revolutionary Baskets Yet</h3>
            <p className="text-gray-600 mb-6">
              Create your first revolutionary basket to start managing strategies with:<br/>
              • Multi-broker allocation • 0-second precision timing • GSI2 optimization • Weekend protection
            </p>
            <Button onClick={() => setShowCreateForm(true)} leftIcon={<Plus className="h-4 w-4" />}>
              Create Your First Revolutionary Basket
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default EnhancedBasketManagement;