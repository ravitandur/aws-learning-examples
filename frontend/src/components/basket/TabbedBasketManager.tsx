import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Badge from '../ui/Badge';
import { useToast } from '../common/ToastContainer';
import ConfirmDialog from '../common/ConfirmDialog';
import { 
  Plus, Settings, Search, TrendingUp, 
  Activity, BarChart3, 
  Edit, Trash2, Target, Zap
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

const TabbedBasketManager: React.FC = () => {
  const { showSuccess, showError } = useToast();
  const [baskets, setBaskets] = useState<BasketWithStrategies[]>([]);
  const [selectedBasket, setSelectedBasket] = useState<BasketWithStrategies | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showStrategyWizard, setShowStrategyWizard] = useState(false);
  const [activeTab, setActiveTab] = useState<'details' | 'performance'>('details');
  const [deleteConfirmDialog, setDeleteConfirmDialog] = useState<{
    isOpen: boolean;
    basket: BasketWithStrategies | null;
  }>({ isOpen: false, basket: null });

  // Load baskets on component mount 
  useEffect(() => {
    loadBaskets();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Listen for external create basket events
  useEffect(() => {
    const handleCreateBasketEvent = () => {
      setShowCreateDialog(true);
    };

    window.addEventListener('openCreateBasketDialog', handleCreateBasketEvent);
    
    return () => {
      window.removeEventListener('openCreateBasketDialog', handleCreateBasketEvent);
    };
  }, []);

  const loadBaskets = async () => {
    try {
      setLoading(true);
      
      const basketsData = await basketService.getBaskets();
      
      // Enhance baskets with additional data
      const enhancedBaskets: BasketWithStrategies[] = basketsData.map(basket => ({
        ...basket,
        strategyCount: basket.strategies?.length || 0,
        totalPnL: Math.random() * 2000 - 500, // Mock data
        lastExecution: Math.random() > 0.5 ? new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString() : undefined
      }));
      
      setBaskets(enhancedBaskets);
      
      // Auto-select first basket if available
      if (enhancedBaskets.length > 0 && !selectedBasket) {
        setSelectedBasket(enhancedBaskets[0]);
      }
      
    } catch (error: any) {
      console.error('Failed to load baskets:', error);
      showError('Failed to load baskets. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBasket = async (basketData: CreateBasket) => {
    try {
      const createdBasket = await basketService.createBasket(basketData);
      
      const newBasket: BasketWithStrategies = {
        ...createdBasket,
        strategyCount: 0,
        totalPnL: 0,
        status: 'INACTIVE'
      };
      
      setBaskets(prev => [newBasket, ...prev]);
      setSelectedBasket(newBasket);
      setShowCreateDialog(false);
      showSuccess(`Basket "${createdBasket.basket_name || 'Unnamed'}" created successfully!`);
      
    } catch (error: any) {
      console.error('Failed to create basket:', error);
      // Don't close the dialog on error, let the dialog handle the error display
      throw error; // Re-throw to let the dialog handle the error
    }
  };

  const handleDeleteBasket = (basket: BasketWithStrategies) => {
    // Show modern confirmation dialog
    setDeleteConfirmDialog({
      isOpen: true,
      basket: basket
    });
  };

  const confirmDeleteBasket = async () => {
    if (!deleteConfirmDialog.basket) return;

    try {
      await basketService.deleteBasket(deleteConfirmDialog.basket.basket_id);
      
      // Remove from local state
      setBaskets(prev => prev.filter(b => b.basket_id !== deleteConfirmDialog.basket!.basket_id));
      
      // Clear selection if the deleted basket was selected
      if (selectedBasket?.basket_id === deleteConfirmDialog.basket.basket_id) {
        setSelectedBasket(null);
      }
      
      showSuccess(`Basket "${deleteConfirmDialog.basket.basket_name}" deleted successfully!`);
      
    } catch (error: any) {
      console.error('Failed to delete basket:', error);
      showError(error.message || 'Failed to delete basket');
    }
  };

  const handleAddStrategy = async (strategyData: any) => {
    try {
      if (!selectedBasket) return;
      
      const newStrategy: Strategy = {
        strategyId: `strategy-${Date.now()}`,
        strategyName: strategyData.name,
        strategyType: strategyData.type,
        status: 'ACTIVE',
        legs: strategyData.legs?.length || 1
      };
      
      const updatedBasket = {
        ...selectedBasket,
        strategies: [...(selectedBasket.strategies || []), newStrategy],
        strategyCount: (selectedBasket.strategyCount || 0) + 1
      };
      
      setBaskets(prev => 
        prev.map(basket => 
          basket.basket_id === selectedBasket.basket_id ? updatedBasket : basket
        )
      );
      
      setSelectedBasket(updatedBasket);
      setShowStrategyWizard(false);
      showSuccess(`Strategy "${strategyData.name}" added successfully!`);
      
    } catch (error: any) {
      console.error('Failed to add strategy:', error);
      showError(error.message || 'Failed to add strategy. Please try again.');
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
    <>
      {/* Main Content Card with Split Pane */}
      <Card className="h-[calc(100vh-300px)] min-h-[600px]">
        <div className="h-full flex overflow-hidden rounded-lg">
        
        {/* Left Panel - Simple Basket Name List */}
        <div className="w-1/4 border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex flex-col">
          
          {/* Left Panel Header */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Baskets</h2>
              <Badge variant="info" size="sm">{baskets.length}</Badge>
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
                  <div className="text-sm font-medium text-gray-500 mb-4">Performance</div>
                  <h3 className="text-lg font-medium mb-2">No Baskets Yet</h3>
                  <p className="text-sm text-gray-600 mb-4">Create your first basket</p>
                  <Button onClick={() => setShowCreateDialog(true)} leftIcon={<Plus className="h-4 w-4" />} size="sm">
                    Create Basket
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-1 p-3">
                {filteredBaskets.map(basket => (
                  <div
                    key={basket.basket_id}
                    className={`group p-3 transition-all rounded-lg cursor-pointer ${
                      selectedBasket?.basket_id === basket.basket_id
                        ? 'bg-blue-100 dark:bg-blue-900/30 border-l-4 border-l-blue-500'
                        : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                    onClick={() => setSelectedBasket(basket)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="font-medium text-sm text-gray-900 dark:text-white flex-1">
                        {basket.basket_name || 'Unnamed Basket'}
                      </div>
                      <div className="flex items-center gap-2">
                        <div className={`px-2 py-1 rounded-full text-xs ${getStatusColor(basket.status)}`}>
                          {basket.status}
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="opacity-0 group-hover:opacity-100 transition-opacity h-6 w-6 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteBasket(basket);
                          }}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Panel - Tabbed Content */}
        <div className="flex-1 bg-white dark:bg-gray-800 flex flex-col">
          
          {/* Right Panel Header */}
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {selectedBasket ? (selectedBasket.basket_name || 'Unnamed Basket') : 'Select a Basket'}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                {selectedBasket 
                  ? 'Manage strategies and monitor performance' 
                  : 'Choose a basket from the left panel to view details'
                }
              </p>
            </div>
            
            {/* Tab Navigation */}
            {selectedBasket && (
              <div className="flex space-x-1 mt-4">
                <button
                  onClick={() => setActiveTab('details')}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeTab === 'details'
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  Details & Strategies
                </button>
                <button
                  onClick={() => setActiveTab('performance')}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeTab === 'performance'
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  Performance
                </button>
              </div>
            )}
          </div>

          {/* Right Panel Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {selectedBasket ? (
              <div className="space-y-6">
                {activeTab === 'details' ? (
                  /* Details Tab */
                  <>
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
                                      <Badge variant="default" size="sm">{strategy.strategyType}</Badge>
                                      <span>•</span>
                                      <span>{strategy.legs} legs</span>
                                      <span>•</span>
                                      <Badge variant={strategy.status === 'ACTIVE' ? 'success' : 'default'} size="sm">
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
                            <div className="text-sm font-medium text-gray-500 mb-4">Details</div>
                            <h3 className="text-lg font-medium mb-2">No Strategies Yet</h3>
                            <p className="text-gray-600 mb-4">Add your first strategy to start building this basket</p>
                            <Button onClick={() => setShowStrategyWizard(true)} leftIcon={<Plus className="h-4 w-4" />}>
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
                            onClick={() => showSuccess('Broker allocation feature coming soon!')}
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
                          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-3">
                                <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center text-white text-xs font-bold">Z</div>
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
                                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs font-bold">A</div>
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
                        </div>
                      </CardContent>
                    </Card>
                  </>
                ) : (
                  /* Performance Tab */
                  <>
                    {/* Performance Overview */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <Card className="hover:shadow-md transition-shadow">
                        <CardContent className="p-4 text-center">
                          <div className={`text-2xl font-bold mb-1 ${getPnLColor(selectedBasket.totalPnL)}`}>
                            ₹{selectedBasket.totalPnL.toFixed(0)}
                          </div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">Total P&L</p>
                          <div className="mt-2">
                            <TrendingUp className={`h-4 w-4 mx-auto ${selectedBasket.totalPnL > 0 ? 'text-green-500' : 'text-red-500'}`} />
                          </div>
                        </CardContent>
                      </Card>
                      
                      <Card className="hover:shadow-md transition-shadow">
                        <CardContent className="p-4 text-center">
                          <div className="text-2xl font-bold text-blue-600 mb-1">
                            {((selectedBasket.totalPnL / 100000) * 100).toFixed(1)}%
                          </div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">Return</p>
                          <div className="mt-2">
                            <BarChart3 className="h-4 w-4 text-blue-500 mx-auto" />
                          </div>
                        </CardContent>
                      </Card>
                      
                      <Card className="hover:shadow-md transition-shadow">
                        <CardContent className="p-4 text-center">
                          <div className="text-2xl font-bold text-purple-600 mb-1">
                            {Math.random() > 0.5 ? '+' : '-'}{(Math.random() * 10).toFixed(1)}%
                          </div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">Max Drawdown</p>
                          <div className="mt-2">
                            <Activity className="h-4 w-4 text-purple-500 mx-auto" />
                          </div>
                        </CardContent>
                      </Card>
                      
                      <Card className="hover:shadow-md transition-shadow">
                        <CardContent className="p-4 text-center">
                          <div className="text-2xl font-bold text-green-600 mb-1">
                            {(Math.random() * 100).toFixed(0)}%
                          </div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">Win Rate</p>
                          <div className="mt-2">
                            <Target className="h-4 w-4 text-green-500 mx-auto" />
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                    
                    {/* Performance Chart Placeholder */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <BarChart3 className="h-5 w-5" />
                          Performance Chart
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="h-64 bg-gray-50 dark:bg-gray-700 rounded-lg flex items-center justify-center">
                          <div className="text-center">
                            <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                            <p className="text-gray-600 dark:text-gray-400">Performance chart coming soon</p>
                            <p className="text-sm text-gray-500 dark:text-gray-500">Real-time P&L visualization</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                    
                    {/* Strategy Performance Breakdown */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <Target className="h-5 w-5" />
                          Strategy Performance
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          {selectedBasket.strategies && selectedBasket.strategies.map(strategy => (
                            <div key={strategy.strategyId} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                              <div className="flex items-center gap-3">
                                <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
                                  <Zap className="h-4 w-4 text-blue-600" />
                                </div>
                                <div>
                                  <div className="font-medium text-sm">{strategy.strategyName}</div>
                                  <div className="text-xs text-gray-600 dark:text-gray-400">{strategy.strategyType}</div>
                                </div>
                              </div>
                              <div className="text-right">
                                <div className={`font-bold text-sm ${Math.random() > 0.5 ? 'text-green-600' : 'text-red-600'}`}>
                                  {Math.random() > 0.5 ? '+' : '-'}₹{(Math.random() * 5000).toFixed(0)}
                                </div>
                                <div className="text-xs text-gray-600 dark:text-gray-400">
                                  {Math.random() > 0.5 ? '+' : '-'}{(Math.random() * 10).toFixed(1)}%
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  </>
                )}
              </div>
            ) : (
              /* Empty State */
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="text-sm font-medium text-gray-500 mb-6">No baskets</div>
                  <h3 className="text-xl font-semibold mb-4">Welcome to Basket Management</h3>
                  <p className="text-gray-600 mb-8 max-w-md">
                    Create and manage your strategy baskets with revolutionary multi-broker allocation and performance tracking.
                  </p>
                  <Button onClick={() => setShowCreateDialog(true)} leftIcon={<Plus className="h-4 w-4" />}>
                    Create Your First Basket
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
        </div>
      </Card>

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

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteConfirmDialog.isOpen}
        onClose={() => setDeleteConfirmDialog({ isOpen: false, basket: null })}
        onConfirm={confirmDeleteBasket}
        title="Delete Basket"
        message={`Are you sure you want to delete the basket "${deleteConfirmDialog.basket?.basket_name || 'this basket'}"? This action cannot be undone. All associated strategies and data will be permanently removed.`}
        confirmText="Delete Basket"
        cancelText="Keep Basket"
        variant="danger"
        icon={<Trash2 className="h-6 w-6 text-red-600" />}
      />
    </>
  );
};

export default TabbedBasketManager;