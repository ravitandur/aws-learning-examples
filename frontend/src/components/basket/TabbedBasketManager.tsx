import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Badge from '../ui/Badge';
import { useToast } from '../common/ToastContainer';
import ConfirmDialog from '../common/ConfirmDialog';
import {
  Plus, Search, TrendingUp,
  Activity, BarChart3,
  Trash2, Target, Zap, Power, RefreshCw
} from 'lucide-react';
import { Basket, Strategy, CreateBasket } from '../../types';
import basketService from '../../services/basketService';
import strategyService from '../../services/strategyService';
import CreateBasketDialog from './CreateBasketDialog';
import StrategyWizardDialog from './StrategyWizardDialog';
import StrategyCard from '../strategy/StrategyCard';
import BasketAllocation from './BasketAllocation';

interface BasketWithStrategies extends Omit<Basket, 'strategies'> {
  strategies?: Strategy[]; // Make strategies optional initially
  strategyCount: number;
  totalPnL: number;
  lastExecution?: string;
}

const TabbedBasketManager: React.FC = () => {
  const { showSuccess, showError } = useToast();
  const [baskets, setBaskets] = useState<BasketWithStrategies[]>([]);
  const [selectedBasket, setSelectedBasket] = useState<BasketWithStrategies | null>(null);
  const [loading, setLoading] = useState(true);
  const [strategiesLoading, setStrategiesLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showStrategyWizard, setShowStrategyWizard] = useState(false);
  const [showEditStrategyDialog, setShowEditStrategyDialog] = useState(false);
  const [editingStrategy, setEditingStrategy] = useState<Strategy | null>(null);
  const [loadingEditStrategy, setLoadingEditStrategy] = useState(false);
  const [activeTab, setActiveTab] = useState<'details' | 'performance' | 'allocation'>('details');
  const [updatingBasket, setUpdatingBasket] = useState<string | null>(null);
  const [updatingStrategy, setUpdatingStrategy] = useState<string | null>(null);
  const [deleteConfirmDialog, setDeleteConfirmDialog] = useState<{
    isOpen: boolean;
    basket: BasketWithStrategies | null;
  }>({ isOpen: false, basket: null });

  const [deleteStrategyConfirmDialog, setDeleteStrategyConfirmDialog] = useState<{
    isOpen: boolean;
    strategy: Strategy | null;
  }>({ isOpen: false, strategy: null });

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

  // Load strategies when a basket is selected (with comprehensive debug logging)
  useEffect(() => {
    let isCancelled = false;

    const loadBasketStrategies = async (basketId: string) => {
      console.log('🔍 [DEBUG] Strategy loading triggered for TabbedBasketManager:', {
        basketId,
        timestamp: new Date().toISOString(),
        hasSelectedBasket: !!selectedBasket,
        selectedBasketId: selectedBasket?.basket_id
      });

      if (isCancelled) {
        console.log('⏹️ [DEBUG] Strategy loading cancelled before start');
        return;
      }

      try {
        console.log('⏳ [DEBUG] Setting loading state and clearing errors...');
        setStrategiesLoading(true);

        console.log('🌐 [DEBUG] Making API call to strategyService.getBasketStrategies...', {
          endpoint: `/options/baskets/${basketId}/strategies`,
          basketId
        });

        const strategies = await strategyService.getBasketStrategies(basketId);

        console.log('✅ [DEBUG] API call successful! Received strategies:', {
          strategiesCount: strategies.length,
          firstStrategyKeys: strategies.length > 0 ? Object.keys(strategies[0]) : [],
          firstStrategyFull: strategies.length > 0 ? strategies[0] : null,
          strategiesData: strategies.map(s => ({
            fullObject: s,
            objectKeys: Object.keys(s),
            id: s.strategyId,
            name: s.strategyName,
            type: s.strategyType,
            status: s.status,
            legs: s.legs
          }))
        });

        if (isCancelled) {
          console.log('⏹️ [DEBUG] Strategy loading cancelled after API call');
          return;
        }

        // Update the selected basket with fetched strategies (prevent infinite loop)
        setSelectedBasket(prev => {
          if (!prev || prev.basket_id !== basketId) {
            console.log('⚠️ [DEBUG] Basket mismatch, not updating:', {
              prevBasketId: prev?.basket_id,
              targetBasketId: basketId
            });
            return prev;
          }

          const updatedBasket = {
            ...prev,
            strategies: strategies,
            strategyCount: strategies.length
          };

          console.log('📊 [DEBUG] Successfully updated basket with strategies:', {
            basketId: basketId,
            strategiesCount: strategies.length,
            hasStrategies: strategies.length > 0,
            updatedBasket: {
              id: updatedBasket.basket_id,
              name: updatedBasket.basket_name,
              strategiesCount: updatedBasket.strategyCount
            }
          });

          return updatedBasket;
        });

        // Also update the basket in the baskets list
        setBaskets(prev =>
          prev.map(basket =>
            basket.basket_id === basketId
              ? { ...basket, strategies: strategies, strategyCount: strategies.length }
              : basket
          )
        );

        console.log('🎉 [DEBUG] Strategy loading completed successfully!');
      } catch (error: any) {
        console.error('❌ [DEBUG] Strategy loading failed with error:', error);
        console.error('❌ [DEBUG] Comprehensive error analysis:', {
          errorMessage: error.message,
          errorStack: error.stack,
          responseData: error.response?.data,
          responseStatus: error.response?.status,
          responseHeaders: error.response?.headers,
          requestConfig: error.config,
          basketId,
          timestamp: new Date().toISOString()
        });

        if (!isCancelled) {
          const errorMessage = error.response?.data?.message || error.message || 'Unknown error occurred';
          showError(`Failed to load strategies: ${errorMessage}`);
          console.log('🔴 [DEBUG] Error state set in UI:', errorMessage);
        } else {
          console.log('⏹️ [DEBUG] Error occurred but request was cancelled, not setting error state');
        }
      } finally {
        if (!isCancelled) {
          setStrategiesLoading(false);
          console.log('✨ [DEBUG] Loading state cleared');
        } else {
          console.log('⏹️ [DEBUG] Request cancelled, not clearing loading state');
        }
      }
    };

    // Main trigger logic with enhanced debugging
    if (selectedBasket?.basket_id) {
      console.log('🚀 [DEBUG] UseEffect triggered - basket selected:', {
        basketId: selectedBasket.basket_id,
        basketName: selectedBasket.basket_name,
        currentStrategyCount: selectedBasket.strategyCount,
        hasStrategiesArray: Array.isArray(selectedBasket.strategies),
        useEffectTrigger: 'selectedBasket?.basket_id',
        dependencyValue: selectedBasket.basket_id
      });
      loadBasketStrategies(selectedBasket.basket_id);
    } else {
      console.log('📝 [DEBUG] UseEffect triggered - no basket selected:', {
        selectedBasket: selectedBasket,
        basketId: selectedBasket?.basket_id,
        reason: !selectedBasket ? 'No selected basket' : 'Basket has no ID'
      });
      setStrategiesLoading(false);
    }

    return () => {
      console.log('🧹 [DEBUG] Cleaning up strategy loading effect');
      isCancelled = true;
    };
  }, [selectedBasket?.basket_id, showError]);

  const loadBaskets = async () => {
    try {
      console.log('🔄 [DEBUG] Loading baskets in TabbedBasketManager...');
      setLoading(true);

      const basketsData = await basketService.getBaskets();
      console.log('📦 [DEBUG] Raw baskets data received:', {
        count: basketsData.length,
        baskets: basketsData.map(b => ({
          id: b.basket_id,
          name: b.basket_name,
          hasStrategies: !!b.strategies,
          strategiesCount: b.strategies?.length || 0
        }))
      });

      // Enhance baskets with additional data and ensure strategies is properly handled
      const enhancedBaskets: BasketWithStrategies[] = basketsData.map(basket => ({
        ...basket,
        strategies: basket.strategies || [], // Ensure strategies is always an array
        strategyCount: basket.strategies?.length || 0,
        totalPnL: Math.random() * 2000 - 500, // Mock data
        lastExecution: Math.random() > 0.5 ? new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString() : undefined
      }));

      console.log('✨ [DEBUG] Enhanced baskets created:', {
        count: enhancedBaskets.length,
        baskets: enhancedBaskets.map(b => ({
          id: b.basket_id,
          name: b.basket_name,
          strategiesCount: b.strategyCount,
          hasStrategiesArray: Array.isArray(b.strategies)
        }))
      });

      setBaskets(enhancedBaskets);

      // Auto-select first basket if available
      if (enhancedBaskets.length > 0 && !selectedBasket) {
        console.log('🎯 [DEBUG] Auto-selecting first basket:', enhancedBaskets[0].basket_id);
        setSelectedBasket(enhancedBaskets[0]);
      } else {
        console.log('📝 [DEBUG] No auto-selection:', {
          basketsCount: enhancedBaskets.length,
          hasSelectedBasket: !!selectedBasket
        });
      }

    } catch (error: any) {
      console.error('❌ [DEBUG] Failed to load baskets:', error);
      showError('Failed to load baskets. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Handle basket status toggle (enable/disable)
  const handleBasketStatusToggle = async (basket: BasketWithStrategies) => {
    const newStatus = basket.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE';
    try {
      setUpdatingBasket(basket.basket_id);
      await basketService.updateBasketStatus(basket.basket_id, newStatus);

      // Update local state
      setBaskets(prev =>
        prev.map(b =>
          b.basket_id === basket.basket_id
            ? { ...b, status: newStatus }
            : b
        )
      );

      // Update selected basket if it's the one being updated
      if (selectedBasket?.basket_id === basket.basket_id) {
        setSelectedBasket(prev => prev ? { ...prev, status: newStatus } : null);
      }

      showSuccess(`Basket ${newStatus.toLowerCase()} successfully`);
    } catch (error: any) {
      showError(error.message || 'Failed to update basket status');
    } finally {
      setUpdatingBasket(null);
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

  const handleAddStrategy = async (createResult: any) => {
    try {
      if (!selectedBasket || !createResult.success) {
        if (!createResult.success) {
          throw new Error(createResult.message || 'Failed to create strategy');
        }
        return;
      }

      console.log('🔄 [DEBUG] Handling strategy creation UI updates:', {
        basketId: selectedBasket.basket_id,
        createResult
      });

      // Extract the real strategy data from API response
      const realStrategyData = createResult.createdStrategy;

      if (!realStrategyData) {
        throw new Error('No strategy data received from API');
      }

      // Transform the backend strategy to frontend format using our existing utility
      const { transformStrategyFields } = await import('../../utils/transformStrategyFields');
      const newStrategy = transformStrategyFields(realStrategyData);

      console.log('✅ [DEBUG] Real strategy data transformed:', {
        originalData: realStrategyData,
        transformedStrategy: newStrategy,
        strategyId: newStrategy.strategyId,
        strategyName: newStrategy.strategyName
      });

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

      console.log('✅ [DEBUG] Strategy creation UI state updated successfully');

    } catch (error: any) {
      console.error('❌ [DEBUG] Failed to handle strategy creation UI:', error);
      showError(error.message || 'Failed to add strategy. Please try again.');
    }
  };

  const handleEditStrategy = async (strategy: Strategy) => {
    try {
      console.log('🔍 [DEBUG] Starting strategy edit for:', {
        fullStrategy: strategy,
        strategyId: strategy.strategyId,
        strategyName: strategy.strategyName,
        objectKeys: Object.keys(strategy),
        timestamp: new Date().toISOString()
      });

      setLoadingEditStrategy(true);
      setEditingStrategy(null);

      // Use the standard strategyId property
      const strategyId = strategy.strategyId;

      if (!strategyId) {
        throw new Error('Strategy ID not found. Available properties: ' + Object.keys(strategy).join(', '));
      }

      // Fetch full strategy details from API
      console.log('🌐 [DEBUG] Fetching strategy details from API...');
      const fullStrategyData = await strategyService.getStrategy(strategyId);

      console.log('✅ [DEBUG] Strategy details fetched successfully:', {
        strategyId: fullStrategyData.strategyId,
        strategyName: fullStrategyData.strategyName,
        legsCount: Array.isArray(fullStrategyData.legs) ? fullStrategyData.legs.length : fullStrategyData.legs,
        hasConfig: !!fullStrategyData.config,
        fullData: fullStrategyData
      });

      // Set the editing strategy with full data
      setEditingStrategy(fullStrategyData);
      setShowEditStrategyDialog(true);

    } catch (error: any) {
      console.error('❌ [DEBUG] Failed to fetch strategy for editing:', error);
      showError(error.message || 'Failed to load strategy for editing. Please try again.');
    } finally {
      setLoadingEditStrategy(false);
    }
  };

  const handleUpdateStrategy = async (updateResult: any) => {
    try {
      if (!editingStrategy || !updateResult.success) {
        if (!updateResult.success) {
          throw new Error(updateResult.message || 'Failed to update strategy');
        }
        return;
      }

      console.log('🔄 [DEBUG] Handling strategy update UI changes:', {
        strategyId: editingStrategy.strategyId,
        updateResult
      });

      // Instead of local state merging, refresh complete strategy list from API
      // This ensures we get fresh data including updated TP/SL values
      if (selectedBasket) {
        console.log('🔄 [DEBUG] Refreshing strategy list to get updated data...');

        try {
          const strategies = await strategyService.getBasketStrategies(selectedBasket.basket_id);

          // Update selected basket with fresh strategies
          setSelectedBasket(prev => prev ? {
            ...prev,
            strategies: strategies,
            strategyCount: strategies.length
          } : null);

          // Update baskets list with fresh strategies
          setBaskets(prev =>
            prev.map(basket =>
              basket.basket_id === selectedBasket.basket_id
                ? { ...basket, strategies: strategies, strategyCount: strategies.length }
                : basket
            )
          );

          console.log('✅ [DEBUG] Strategy list refreshed with fresh data from API');
        } catch (refreshError) {
          console.error('❌ [DEBUG] Failed to refresh strategies after update:', refreshError);
          // Don't throw - the update was successful, just the refresh failed
        }
      }

      // Clean up edit state
      setShowEditStrategyDialog(false);
      setEditingStrategy(null);

      console.log('✅ [DEBUG] Strategy UI state updated successfully');

    } catch (error: any) {
      console.error('❌ [DEBUG] Failed to handle strategy update UI:', error);
      showError(error.message || 'Failed to update strategy. Please try again.');
    }
  };

  // Handle strategy status toggle (enable/disable)
  const handleStrategyStatusToggle = async (strategy: Strategy) => {
    const newStatus: 'ACTIVE' | 'PAUSED' | 'COMPLETED' = strategy.status === 'ACTIVE' ? 'PAUSED' : 'ACTIVE';
    try {
      setUpdatingStrategy(strategy.strategyId);
      await strategyService.updateStrategyStatus(strategy.strategyId, newStatus);

      // Update local state
      const updatedStrategies = selectedBasket?.strategies?.map(s =>
        s.strategyId === strategy.strategyId
          ? { ...s, status: newStatus as Strategy['status'] }
          : s
      ) || [];

      // Update selected basket
      if (selectedBasket) {
        setSelectedBasket(prev => prev ? { ...prev, strategies: updatedStrategies } : null);
      }

      // Update baskets list
      setBaskets(prev => prev.map(basket =>
        basket.basket_id === selectedBasket?.basket_id
          ? { ...basket, strategies: updatedStrategies }
          : basket
      ));

      showSuccess(`Strategy ${newStatus.toLowerCase()} successfully`);
    } catch (error: any) {
      showError(error.message || 'Failed to update strategy status');
    } finally {
      setUpdatingStrategy(null);
    }
  };

  const handleDeleteStrategy = (strategy: Strategy) => {
    // Show confirmation dialog
    setDeleteStrategyConfirmDialog({
      isOpen: true,
      strategy: strategy
    });
  };

  const confirmDeleteStrategy = async () => {
    if (!deleteStrategyConfirmDialog.strategy) return;

    try {
      setLoadingEditStrategy(true);

      // Delete the strategy
      await strategyService.deleteStrategy(deleteStrategyConfirmDialog.strategy.strategyId);

      showSuccess(`Strategy "${deleteStrategyConfirmDialog.strategy.strategyName}" deleted successfully`);

      // Refresh the strategy list
      if (selectedBasket) {
        const strategies = await strategyService.getBasketStrategies(selectedBasket.basket_id);

        // Update selected basket with refreshed strategies
        setSelectedBasket(prev => prev ? {
          ...prev,
          strategies: strategies,
          strategyCount: strategies.length
        } : null);

        // Update baskets list
        setBaskets(prev => prev.map(basket =>
          basket.basket_id === selectedBasket.basket_id
            ? { ...basket, strategies: strategies, strategyCount: strategies.length }
            : basket
        ));
      }

      // Close the confirmation dialog
      setDeleteStrategyConfirmDialog({ isOpen: false, strategy: null });
    } catch (error) {
      console.error('Error deleting strategy:', error);
      showError(error instanceof Error ? error.message : 'Failed to delete strategy');
    } finally {
      setLoadingEditStrategy(false);
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
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleBasketStatusToggle(basket);
                          }}
                          disabled={updatingBasket === basket.basket_id}
                          className={`opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded transition-colors ${
                            basket.status === 'ACTIVE'
                              ? 'text-orange-600 hover:text-orange-700 hover:bg-orange-50 dark:hover:bg-orange-900/20'
                              : 'text-green-600 hover:text-green-700 hover:bg-green-50 dark:hover:bg-green-900/20'
                          } disabled:opacity-50`}
                          title={basket.status === 'ACTIVE' ? 'Disable' : 'Enable'}
                        >
                          {updatingBasket === basket.basket_id ? (
                            <RefreshCw className="h-3 w-3 animate-spin" />
                          ) : (
                            <Power className="h-3 w-3" />
                          )}
                        </button>
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
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {selectedBasket ? (selectedBasket.basket_name || 'Unnamed Basket') : 'Select a Basket'}
                  </h3>
                  {selectedBasket && (
                    <Badge
                      variant={selectedBasket.status === 'ACTIVE' ? 'success' : selectedBasket.status === 'PAUSED' ? 'warning' : 'default'}
                    >
                      {selectedBasket.status}
                    </Badge>
                  )}
                </div>
              </div>
              {selectedBasket ? (
                <div className="flex flex-wrap items-center gap-2 mt-2">
                  <span className="text-sm text-gray-600 dark:text-gray-300">
                    {selectedBasket.strategies?.length || 0} strategies
                  </span>
                </div>
              ) : (
                <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                  Choose a basket from the left panel to view details
                </p>
              )}
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
                  Strategies
                </button>
                <button
                  onClick={() => setActiveTab('allocation')}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeTab === 'allocation'
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  Broker Allocation
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
                {/* Strategies Tab */}
                <div className={activeTab === 'details' ? 'block' : 'hidden'}>
                  {/* Strategies Section */}
                  <Card>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <CardTitle>Strategies</CardTitle>
                          <Badge variant="info" size="sm">
                            {selectedBasket.strategies?.length || 0}
                          </Badge>
                        </div>
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
                        {strategiesLoading ? (
                          <div className="flex items-center justify-center py-8">
                            <div className="text-center">
                              <Activity className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-2" />
                              <p className="text-sm text-gray-600">Loading strategies...</p>
                            </div>
                          </div>
                        ) : selectedBasket.strategies && selectedBasket.strategies.length > 0 ? (
                          <div className="space-y-4">
                            {selectedBasket.strategies.map(strategy => (
                              <StrategyCard
                                key={strategy.strategyId}
                                strategy={strategy}
                                onEdit={handleEditStrategy}
                                onDelete={handleDeleteStrategy}
                                onStatusToggle={handleStrategyStatusToggle}
                                isLoading={loadingEditStrategy}
                                isUpdating={updatingStrategy === strategy.strategyId}
                              />
                            ))}
                          </div>
                        ) : (
                          <div className="text-center py-8">
                            <div className="text-sm font-medium text-gray-500 mb-4">Details</div>
                            <h3 className="text-lg font-medium mb-2">No Strategies Yet</h3>
                            <p className="text-gray-600 mb-4">Use the "Add Strategy" button above to start building this basket</p>
                          </div>
                        )}
                    </CardContent>
                  </Card>
                </div>

                {/* Broker Allocation Tab */}
                <div className={activeTab === 'allocation' ? 'block' : 'hidden'}>
                  <BasketAllocation
                    basket={{
                      ...selectedBasket,
                      strategies: selectedBasket.strategies || []
                    }}
                    onBack={() => setActiveTab('details')}
                    onAllocationComplete={() => {
                      showSuccess('Broker allocation updated successfully!');
                      setActiveTab('details');
                    }}
                  />
                </div>

                {/* Performance Tab */}
                <div className={activeTab === 'performance' ? 'block' : 'hidden'}>
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
                </div>
              </div>
            ) : (
              /* Empty State */
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="text-sm font-medium text-gray-500 mb-6">No baskets</div>
                  <h3 className="text-xl font-semibold mb-8">Welcome to Basket Management</h3>
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

      {showEditStrategyDialog && selectedBasket && editingStrategy && (
        <StrategyWizardDialog
          basketId={selectedBasket.basket_id}
          editingStrategy={editingStrategy}
          onClose={() => {
            setShowEditStrategyDialog(false);
            setEditingStrategy(null);
          }}
          onSubmit={handleUpdateStrategy}
        />
      )}

      {/* Delete Basket Confirmation Dialog */}
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

      {/* Delete Strategy Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteStrategyConfirmDialog.isOpen}
        onClose={() => setDeleteStrategyConfirmDialog({ isOpen: false, strategy: null })}
        onConfirm={confirmDeleteStrategy}
        title="Delete Strategy"
        message={`Are you sure you want to delete the strategy "${deleteStrategyConfirmDialog.strategy?.strategyName || 'this strategy'}"? This action cannot be undone. All strategy configurations and data will be permanently removed.`}
        confirmText="Delete Strategy"
        cancelText="Keep Strategy"
        variant="danger"
        icon={<Trash2 className="h-6 w-6 text-red-600" />}
      />
    </>
  );
};

export default TabbedBasketManager;