import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Badge from '../ui/Badge';
import { 
  Plus, Settings, Search, MoreVertical, TrendingUp, 
  Activity, BarChart3, Clock, AlertCircle, CheckCircle,
  Edit, Trash2, Target, Zap, X
} from 'lucide-react';
import { Basket, Strategy, CreateBasket } from '../../types';
import basketService from '../../services/basketService';
import CreateBasketDialog from './CreateBasketDialog';
import StrategyWizardDialog from './StrategyWizardDialog';

interface BasketWithStrategies extends Basket {
  strategyCount: number;
  totalPnL: number;
  lastExecution?: string;
}

const SplitPaneBasketManager: React.FC = () => {
  const [baskets, setBaskets] = useState<BasketWithStrategies[]>([]);
  const [selectedBasket, setSelectedBasket] = useState<BasketWithStrategies | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showStrategyWizard, setShowStrategyWizard] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'details' | 'performance'>('details');

  // Load baskets on component mount
  useEffect(() => {
    loadBaskets();
  }, []);

  // Auto-clear error and success messages after 5 seconds
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  const loadBaskets = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const basketsData = await basketService.getBaskets();
      
      // Enhance baskets with additional data
      const enhancedBaskets: BasketWithStrategies[] = basketsData.map(basket => ({
        ...basket,
        strategyCount: basket.strategies?.length || 0,
        totalPnL: Math.random() * 2000 - 500, // Mock data - replace with real API
        lastExecution: Math.random() > 0.5 ? new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString() : undefined
      }));
      
      setBaskets(enhancedBaskets);
      
      // Auto-select first basket if available
      if (enhancedBaskets.length > 0 && !selectedBasket) {
        setSelectedBasket(enhancedBaskets[0]);
      }
      
    } catch (error: any) {
      console.error('Failed to load baskets:', error);
      setError('Failed to load baskets. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBasket = async (basketData: CreateBasket) => {
    try {
      const createdBasket = await basketService.createBasket(basketData);
      
      // Add to local state
      const newBasket: BasketWithStrategies = {
        ...createdBasket,
        strategyCount: 0,
        totalPnL: 0,
        status: 'INACTIVE'
      };
      
      setBaskets(prev => [newBasket, ...prev]);
      setSelectedBasket(newBasket);
      setShowCreateDialog(false);
      setSuccess(`Basket "${createdBasket.basket_name || 'Unnamed'}" created successfully!`);
      
    } catch (error: any) {
      console.error('Failed to create basket:', error);
      setError(error.message || 'Failed to create basket. Please try again.');
    }
  };

  const handleAddStrategy = async (strategyData: any) => {
    try {
      if (!selectedBasket) return;
      
      // Mock strategy creation - replace with actual API call
      const newStrategy: Strategy = {
        strategyId: `strategy-${Date.now()}`,
        strategyName: strategyData.name,
        strategyType: strategyData.type,
        status: 'ACTIVE',
        legs: strategyData.legs?.length || 1
      };
      
      // Update selected basket
      const updatedBasket = {
        ...selectedBasket,
        strategies: [...(selectedBasket.strategies || []), newStrategy],
        strategyCount: (selectedBasket.strategyCount || 0) + 1
      };
      
      // Update baskets list
      setBaskets(prev => 
        prev.map(basket => 
          basket.basket_id === selectedBasket.basket_id ? updatedBasket : basket
        )
      );
      
      setSelectedBasket(updatedBasket);
      setShowStrategyWizard(false);
      setSuccess(`Strategy "${strategyData.name}" added to basket successfully!`);
      
    } catch (error: any) {
      console.error('Failed to add strategy:', error);
      setError(error.message || 'Failed to add strategy. Please try again.');
    }
  };

  const handleDeleteBasket = async (basketId: string) => {
    try {
      await basketService.deleteBasket(basketId);
      
      const updatedBaskets = baskets.filter(b => b.basket_id !== basketId);
      setBaskets(updatedBaskets);
      
      // Select next basket or clear selection
      if (selectedBasket?.basket_id === basketId) {
        setSelectedBasket(updatedBaskets.length > 0 ? updatedBaskets[0] : null);
      }
      
      setSuccess('Basket deleted successfully!');
      setTimeout(() => setSuccess(null), 3000);
      
    } catch (error: any) {
      console.error('Failed to delete basket:', error);
      setError(error.message || 'Failed to delete basket. Please try again.');
    }
  };

  const filteredBaskets = baskets.filter(basket =>
    (basket.basket_name && basket.basket_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (basket.description && basket.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return 'text-green-600 bg-green-100 dark:bg-green-900/20';
      case 'PAUSED':
        return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/20';
      case 'INACTIVE':
      case 'COMPLETED':
        return 'text-gray-600 bg-gray-100 dark:bg-gray-700';
      default:
        return 'text-gray-600 bg-gray-100 dark:bg-gray-700';
    }
  };

  const getPnLColor = (pnl: number) => {
    if (pnl > 0) return 'text-green-600';
    if (pnl < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      
      {/* Success Message */}
      {success && (
        <div className="mx-6 mt-4">
          <Card className="border-green-200 bg-green-50 dark:bg-green-900/20">
            <CardContent className="py-3">
              <div className="flex items-center gap-3">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <span className="text-green-800 dark:text-green-200 flex-1">{success}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSuccess(null)}
                  className="h-8 w-8 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mx-6 mt-4">
          <Card className="border-red-200 bg-red-50 dark:bg-red-900/20">
            <CardContent className="py-3">
              <div className="flex items-center gap-3">
                <AlertCircle className="h-5 w-5 text-red-600" />
                <span className="text-red-800 dark:text-red-200 flex-1">{error}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setError(null)}
                  className="h-8 w-8 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Left Panel - Basket List */}
        <div className="w-1/3 border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex flex-col">
          
          {/* Left Panel Header */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">🧺 My Baskets</h2>
              <Badge variant="info" size="sm">
                {baskets.length} total
              </Badge>
            </div>
            
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search baskets..."
                className="pl-10"
              />
            </div>
          </div>

          {/* Basket List */}
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <Activity className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-2" />
                  <p className="text-sm text-gray-600">Loading baskets...</p>
                </div>
              </div>
            ) : filteredBaskets.length === 0 ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="text-6xl mb-4">📊</div>
                  <h3 className="text-lg font-medium mb-2">No Baskets Yet</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Create your first basket to start managing your strategies
                  </p>
                  <Button
                    onClick={() => setShowCreateDialog(true)}
                    leftIcon={<Plus className="h-4 w-4" />}
                    size="sm"
                  >
                    Create Basket
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-2 p-4">
                {filteredBaskets.map(basket => (
                  <Card
                    key={basket.basket_id}
                    className={`cursor-pointer transition-all hover:shadow-md ${
                      selectedBasket?.basket_id === basket.basket_id
                        ? 'ring-2 ring-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                    onClick={() => setSelectedBasket(basket)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h4 className="font-medium text-sm">{basket.basket_name || 'Unnamed Basket'}</h4>
                          {basket.description && (
                            <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                              {basket.description}
                            </p>
                          )}
                        </div>
                        <div className="ml-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0"
                            onClick={(e) => {
                              e.stopPropagation();
                              // Show context menu
                            }}
                          >
                            <MoreVertical className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3 text-xs">
                          <span className="flex items-center gap-1">
                            <Target className="h-3 w-3" />
                            {basket.strategyCount}
                          </span>
                          <span className={`font-medium ${getPnLColor(basket.totalPnL)}`}>
                            ₹{basket.totalPnL.toFixed(0)}
                          </span>
                        </div>
                        <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(basket.status)}`}>
                          {basket.status}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Panel - Basket Details */}
        <div className="flex-1 bg-white dark:bg-gray-800 flex flex-col">
          
          {/* Right Panel Header */}
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold">
                  {selectedBasket ? (selectedBasket.basket_name || 'Unnamed Basket') : 'Basket Management'}
                </h1>
                <p className="text-gray-600 dark:text-gray-300">
                  {selectedBasket 
                    ? 'Manage strategies and monitor performance' 
                    : 'Select a basket to view details or create a new one'
                  }
                </p>
              </div>
              <div className="flex space-x-3">
                <Button
                  variant="outline"
                  onClick={() => loadBaskets()}
                  leftIcon={loading ? <Activity className="h-4 w-4 animate-spin" /> : <Activity className="h-4 w-4" />}
                  disabled={loading}
                >
                  {loading ? 'Refreshing...' : 'Refresh'}
                </Button>
                <Button
                  onClick={() => setShowCreateDialog(true)}
                  leftIcon={<Plus className="h-4 w-4" />}
                >
                  Add Basket
                </Button>
              </div>
            </div>
          </div>

          {/* Right Panel Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {selectedBasket ? (
              <div className="space-y-6">
                
                {/* Basket Stats */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <Card className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4 text-center">
                      <div className="text-2xl font-bold text-blue-600 mb-1">
                        {selectedBasket.strategyCount}
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Active Strategies</p>
                      <div className="mt-2">
                        <Target className="h-4 w-4 text-blue-500 mx-auto" />
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4 text-center">
                      <div className={`text-2xl font-bold mb-1 ${getPnLColor(selectedBasket.totalPnL)}`}>
                        ₹{selectedBasket.totalPnL.toFixed(0)}
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Total P&L</p>
                      <div className="mt-2">
                        <TrendingUp className="h-4 w-4 text-green-500 mx-auto" />
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4 text-center">
                      <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(selectedBasket.status)}`}>
                        {selectedBasket.status}
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">Status</p>
                      <div className="mt-2">
                        <Activity className="h-4 w-4 text-blue-500 mx-auto" />
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardContent className="p-4 text-center">
                      <div className="text-2xl font-bold text-purple-600">
                        {selectedBasket.lastExecution ? (
                          new Date(selectedBasket.lastExecution).toLocaleDateString()
                        ) : (
                          'Never'
                        )}
                      </div>
                      <div className="text-sm text-gray-600">Last Run</div>
                    </CardContent>
                  </Card>
                </div>

                {/* Strategies Section */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center gap-2">
                        <Target className="h-5 w-5" />
                        Strategies ({selectedBasket.strategyCount})
                      </CardTitle>
                      <Button
                        onClick={() => setShowStrategyWizard(true)}
                        leftIcon={<Plus className="h-4 w-4" />}
                        size="sm"
                      >
                        Add Strategy
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {selectedBasket.strategies && selectedBasket.strategies.length > 0 ? (
                      <div className="space-y-3">
                        {selectedBasket.strategies.map(strategy => (
                          <div
                            key={strategy.strategyId}
                            className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
                          >
                            <div className="flex items-center gap-4">
                              <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
                                <Zap className="h-5 w-5 text-blue-600" />
                              </div>
                              <div>
                                <h4 className="font-medium">{strategy.strategyName}</h4>
                                <div className="flex items-center gap-2 text-sm text-gray-600">
                                  <Badge variant="default" size="sm">
                                    {strategy.strategyType}
                                  </Badge>
                                  <span>•</span>
                                  <span>{strategy.legs} legs</span>
                                  <span>•</span>
                                  <Badge 
                                    variant={strategy.status === 'ACTIVE' ? 'success' : 'default'} 
                                    size="sm"
                                  >
                                    {strategy.status}
                                  </Badge>
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <Button variant="ghost" size="sm">
                                <Edit className="h-4 w-4" />
                              </Button>
                              <Button variant="ghost" size="sm" className="text-red-600">
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <div className="text-4xl mb-4">🎯</div>
                        <h3 className="text-lg font-medium mb-2">No Strategies Yet</h3>
                        <p className="text-gray-600 mb-4">
                          Add your first strategy to start building this basket
                        </p>
                        <Button
                          onClick={() => setShowStrategyWizard(true)}
                          leftIcon={<Plus className="h-4 w-4" />}
                        >
                          Add Strategy
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Broker Allocation Section */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center gap-2">
                        <Settings className="h-5 w-5" />
                        Broker Allocations
                      </CardTitle>
                      <Button
                        onClick={() => {
                          // TODO: Add broker allocation modal
                          setSuccess('Broker allocation feature coming soon!');
                        }}
                        leftIcon={<Plus className="h-4 w-4" />}
                        size="sm"
                        variant="outline"
                      >
                        Add Allocation
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {/* Mock broker allocations - replace with actual data */}
                      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
                              Z
                            </div>
                            <div>
                              <div className="font-medium text-sm">Zerodha</div>
                              <div className="text-xs text-gray-600">Client: DEMO123</div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-bold text-lg text-blue-600">5x</div>
                            <div className="text-xs text-gray-600">Lot Multiplier</div>
                          </div>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-600">Capital Allocation: ₹2,50,000</span>
                          <Badge variant="success" size="sm">Active</Badge>
                        </div>
                      </div>

                      <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
                              A
                            </div>
                            <div>
                              <div className="font-medium text-sm">Angel One</div>
                              <div className="text-xs text-gray-600">Client: ANGEL456</div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-bold text-lg text-green-600">3x</div>
                            <div className="text-xs text-gray-600">Lot Multiplier</div>
                          </div>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-600">Capital Allocation: ₹1,50,000</span>
                          <Badge variant="success" size="sm">Active</Badge>
                        </div>
                      </div>

                      <div className="text-center py-4 border-2 border-dashed border-gray-200 dark:border-gray-700 rounded-lg">
                        <p className="text-sm text-gray-600 mb-3">
                          Revolutionary multi-broker allocation enables institutional-grade risk distribution
                        </p>
                        <Button
                          onClick={() => {
                            setSuccess('Advanced broker allocation coming soon with full API integration!');
                          }}
                          variant="outline"
                          size="sm"
                          leftIcon={<Settings className="h-4 w-4" />}
                        >
                          Configure Advanced Allocation
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Actions */}
                <div className="flex items-center gap-4">
                  <Button variant="outline" leftIcon={<Edit className="h-4 w-4" />}>
                    Edit Basket
                  </Button>
                  <Button variant="outline" leftIcon={<Settings className="h-4 w-4" />}>
                    Configure
                  </Button>
                  <Button 
                    variant="outline" 
                    className="text-red-600 hover:text-red-700"
                    leftIcon={<Trash2 className="h-4 w-4" />}
                    onClick={() => {
                      if (window.confirm('Are you sure you want to delete this basket?')) {
                        handleDeleteBasket(selectedBasket.basket_id);
                      }
                    }}
                  >
                    Delete Basket
                  </Button>
                </div>
              </div>
            ) : (
              /* Empty State - No Basket Selected */
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="text-8xl mb-6">🧺</div>
                  <h3 className="text-xl font-semibold mb-4">Welcome to Basket Management</h3>
                  <p className="text-gray-600 mb-8 max-w-md">
                    Create and manage your strategy baskets with revolutionary multi-broker allocation, 
                    0-second precision timing, and institutional-grade performance tracking.
                  </p>
                  <div className="flex items-center justify-center gap-4">
                    <Button
                      onClick={() => setShowCreateDialog(true)}
                      leftIcon={<Plus className="h-4 w-4" />}
                    >
                      Create Your First Basket
                    </Button>
                    {baskets.length > 0 && (
                      <Button variant="outline">
                        Select Basket from List
                      </Button>
                    )}
                  </div>
                  
                  <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4 text-left max-w-2xl">
                    <Card className="p-4">
                      <div className="flex items-center gap-3 mb-2">
                        <TrendingUp className="h-5 w-5 text-green-600" />
                        <span className="font-medium">Multi-Strategy</span>
                      </div>
                      <p className="text-sm text-gray-600">
                        Combine multiple options strategies in one basket
                      </p>
                    </Card>
                    
                    <Card className="p-4">
                      <div className="flex items-center gap-3 mb-2">
                        <BarChart3 className="h-5 w-5 text-blue-600" />
                        <span className="font-medium">Performance Tracking</span>
                      </div>
                      <p className="text-sm text-gray-600">
                        Real-time P&L and execution monitoring
                      </p>
                    </Card>
                    
                    <Card className="p-4">
                      <div className="flex items-center gap-3 mb-2">
                        <Clock className="h-5 w-5 text-purple-600" />
                        <span className="font-medium">Precision Timing</span>
                      </div>
                      <p className="text-sm text-gray-600">
                        0-second precision execution timing
                      </p>
                    </Card>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Dialogs */}
      {showCreateDialog && (
        <CreateBasketDialog
          onClose={() => setShowCreateDialog(false)}
          onSubmit={handleCreateBasket}
        />
      )}

      {showStrategyWizard && selectedBasket && (
        <StrategyWizardDialog
          basketId={selectedBasket.basket_id}
          onClose={() => setShowStrategyWizard(false)}
          onSubmit={handleAddStrategy}
        />
      )}
    </div>
  );
};

export default SplitPaneBasketManager;