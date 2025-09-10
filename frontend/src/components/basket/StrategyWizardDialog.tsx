import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import { X, Plus, Trash2, Copy, ChevronDown, ChevronUp } from 'lucide-react';

interface StrategyLeg {
  id: string;
  index: string;
  optionType: 'CE' | 'PE';
  actionType: 'BUY' | 'SELL';
  strikePrice: string;
  totalLots: number;
  expiryType: 'weekly' | 'monthly';
  selectionMethod: 'ATM_POINT' | 'ATM_PERCENT' | 'CLOSEST_PREMIUM' | 'CLOSEST_STRADDLE_PREMIUM';
  
  // Risk Management Fields
  stopLoss: {
    enabled: boolean;
    type: 'POINTS' | 'PERCENTAGE' | 'RANGE';
    value: number;
  };
  targetProfit: {
    enabled: boolean;
    type: 'POINTS' | 'PERCENTAGE';
    value: number;
  };
  trailingStopLoss: {
    enabled: boolean;
    type: 'POINTS' | 'PERCENTAGE';
    instrumentMoveValue: number;
    stopLossMoveValue: number;
  };
  waitAndTrade: {
    enabled: boolean;
    type: 'POINTS' | 'PERCENTAGE';
    value: number;
  };
  reEntry: {
    enabled: boolean;
    type: 'SL_REENTRY' | 'SL_RECOST' | 'SL_REEXEC';
    count: number; // 1 to 5
  };
  reExecute: {
    enabled: boolean;
    type: 'TP_REEXEC';
    count: number; // 1 to 5
  };
}

interface StrategyWizardDialogProps {
  basketId: string;
  onClose: () => void;
  onSubmit: (strategyData: any) => void;
}

// Stable ID counter for better performance
let legIdCounter = 0;
const generateStableId = () => `leg-${++legIdCounter}-${Date.now()}`;

const StrategyWizardDialog: React.FC<StrategyWizardDialogProps> = ({ 
  basketId, 
  onClose, 
  onSubmit 
}) => {
  const dialogRef = useRef<HTMLDivElement>(null);
  const [strategyName, setStrategyName] = useState('');
  const [strategyIndex, setStrategyIndex] = useState('NIFTY');
  const [strategyConfig, setStrategyConfig] = useState({
    entryTimeHour: '09',
    entryTimeMinute: '15',
    exitTimeHour: '15',
    exitTimeMinute: '30',
    rangeBreakout: false,
    rangeBreakoutTimeHour: '09',
    rangeBreakoutTimeMinute: '30',
    waitAndTrade: false,
    moveSlToCost: false,
    reEntryReExecute: false,
    targetProfit: {
      type: 'TOTAL_MTM', // 'TOTAL_MTM' | 'COMBINED_PREMIUM_PERCENT'
      value: 0
    },
    mtmStopLoss: {
      type: 'TOTAL_MTM', // 'TOTAL_MTM' | 'COMBINED_PREMIUM_PERCENT'  
      value: 0
    }
  });

  const [legs, setLegs] = useState<StrategyLeg[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [expandedRiskSections, setExpandedRiskSections] = useState<Record<string, boolean>>({});

  // Focus management for accessibility
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    if (dialogRef.current) {
      dialogRef.current.focus();
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose]);

  // Generate default strike price options (using ATM Point method)
  const generateStrikeOptions = (): { value: string; label: string }[] => {
    const options = [];
    
    // ITM options (10 below ATM)
    for (let i = 10; i >= 1; i--) {
      options.push({ value: `ITM${i}`, label: `ITM${i}` });
    }
    
    // ATM option
    options.push({ value: 'ATM', label: 'ATM' });
    
    // OTM options (10 above ATM)
    for (let i = 1; i <= 10; i++) {
      options.push({ value: `OTM${i}`, label: `OTM${i}` });
    }
    
    return options;
  };

  // Generate ATM percentage-based options
  const generatePercentageOptions = (): { value: string; label: string }[] => {
    const options = [];
    
    // Negative percentages (below ATM)
    for (let i = -10; i < 0; i += 0.25) {
      const percentage = i.toFixed(2);
      options.push({ value: `ATM${percentage}%`, label: `ATM${percentage}%` });
    }
    
    // ATM (0%)
    options.push({ value: 'ATM', label: 'ATM' });
    
    // Positive percentages (above ATM)
    for (let i = 0.25; i <= 10; i += 0.25) {
      const percentage = i.toFixed(2);
      options.push({ value: `ATM+${percentage}%`, label: `ATM+${percentage}%` });
    }
    
    return options;
  };

  // Generate strike options based on selection method for a specific position
  const generatePositionStrikeOptions = (selectionMethod: string): { value: string; label: string }[] => {
    switch (selectionMethod) {
      case 'ATM_PERCENT':
        return generatePercentageOptions();
      case 'ATM_POINT':
      default:
        return generateStrikeOptions();
    }
  };

  // Optimized leg update function with useCallback
  const updateLeg = useCallback((legId: string, updates: Partial<StrategyLeg>) => {
    setLegs(prev => prev.map(leg => 
      leg.id === legId ? { ...leg, ...updates } : leg
    ));
  }, []);

  // Optimized add position with stable IDs
  const addPosition = useCallback(() => {
    const newLeg: StrategyLeg = {
      id: generateStableId(),
      index: strategyIndex,
      optionType: 'CE',
      actionType: 'BUY',
      strikePrice: 'ATM',
      totalLots: 1,
      expiryType: 'weekly',
      selectionMethod: 'ATM_POINT',
      
      // Default risk management values
      stopLoss: {
        enabled: false,
        type: 'POINTS',
        value: 0
      },
      targetProfit: {
        enabled: false,
        type: 'POINTS',
        value: 0
      },
      trailingStopLoss: {
        enabled: false,
        type: 'POINTS',
        instrumentMoveValue: 0,
        stopLossMoveValue: 0
      },
      waitAndTrade: {
        enabled: false,
        type: 'POINTS',
        value: 0
      },
      reEntry: {
        enabled: false,
        type: 'SL_REENTRY',
        count: 1
      },
      reExecute: {
        enabled: false,
        type: 'TP_REEXEC',
        count: 1
      }
    };
    setLegs(prev => [...prev, newLeg]);
    setError(null);
  }, [strategyIndex]);

  // Remove position
  const removePosition = (legId: string) => {
    setLegs(prev => prev.filter(leg => leg.id !== legId));
  };

  // Copy position
  const copyPosition = (legId: string) => {
    const legToCopy = legs.find(leg => leg.id === legId);
    if (legToCopy) {
      const newLeg = { ...legToCopy, id: `leg-${Date.now()}` };
      setLegs(prev => [...prev, newLeg]);
    }
  };

  // Validation
  const validateInputs = (): string | null => {
    if (!strategyName.trim()) {
      return 'Please enter a strategy name';
    }
    
    if (legs.length === 0) {
      return 'Please add at least one position';
    }

    return null;
  };

  // Submit handler
  const handleSubmit = async () => {
    const validationError = validateInputs();
    if (validationError) {
      setError(validationError);
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      const strategyData = {
        basketId,
        strategyName: strategyName.trim(),
        index: strategyIndex,
        config: strategyConfig,
        legs: legs.map(leg => ({
          index: leg.index,
          optionType: leg.optionType,
          actionType: leg.actionType,
          strikePrice: leg.strikePrice,
          totalLots: leg.totalLots,
          expiryType: leg.expiryType,
          selectionMethod: leg.selectionMethod,
          stopLoss: leg.stopLoss,
          targetProfit: leg.targetProfit,
          trailingStopLoss: leg.trailingStopLoss,
          waitAndTrade: leg.waitAndTrade,
          reEntry: leg.reEntry,
          reExecute: leg.reExecute
        }))
      };

      await onSubmit(strategyData);
    } catch (error: any) {
      setError(error.message || 'Failed to create strategy. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="strategy-dialog-title"
    >
      <div 
        ref={dialogRef}
        tabIndex={-1}
        className="w-full max-w-5xl"
      >
        <Card className="h-[90vh] flex flex-col bg-white/95 dark:bg-gray-900/95 backdrop-blur-md border border-white/20 dark:border-gray-700/20 rounded-2xl shadow-2xl overflow-hidden">
          <CardHeader className="flex-shrink-0 flex flex-row items-center justify-between pb-4 border-b border-gray-200/50 dark:border-gray-700/50">
            <h2 
              id="strategy-dialog-title"
              className="text-xl font-semibold text-gray-900 dark:text-white tracking-tight"
            >
              Strategy Creator
            </h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-10 w-10 p-0 rounded-xl hover:bg-gray-100/80 dark:hover:bg-gray-700/80 transition-all duration-200"
              aria-label="Close dialog"
            >
              <X className="h-5 w-5" />
            </Button>
          </CardHeader>

          <CardContent className="flex-1 overflow-hidden p-0">
            <div className="h-full flex flex-col">
              
              {/* Initial Layout - Strategy Name and Add Position Button */}
              <div className="bg-gray-50 dark:bg-gray-700/50 px-4 py-4 border-b border-gray-200 dark:border-gray-600">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-end">
                  {/* Strategy Name - Column 1 */}
                  <div>
                    <Input
                      type="text"
                      value={strategyName}
                      onChange={(e) => setStrategyName(e.target.value)}
                      placeholder="Enter strategy name"
                      className="h-9"
                    />
                  </div>

                  {/* Add Position Button - Column 2 */}
                  <div>
                    <Button
                      onClick={addPosition}
                      leftIcon={<Plus className="h-4 w-4" />}
                      className="bg-blue-600 hover:bg-blue-700 text-white h-9"
                    >
                      Add Position
                    </Button>
                    {legs.length > 0 && (
                      <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                        {legs.length} position{legs.length !== 1 ? 's' : ''} added
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Header Section - Index and Checkboxes (Show only after first position) */}
              {legs.length > 0 && (
                <div className="bg-gray-50 dark:bg-gray-700/50 px-4 py-4 border-b border-gray-200 dark:border-gray-600">
                  {/* Index and Checkboxes Row */}
                  <div className="flex items-end justify-between gap-4">
                    {/* Index Selection - Left Side */}
                    <div className="flex-shrink-0">
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                        Index (applies to all positions)
                      </label>
                      <Select
                        value={strategyIndex}
                        onChange={(e) => {
                          setStrategyIndex(e.target.value);
                          // Update all existing legs to use new index
                          setLegs(prev => prev.map(leg => ({ 
                            ...leg, 
                            index: e.target.value
                          })));
                        }}
                        options={[
                          { value: 'NIFTY', label: 'NIFTY' },
                          { value: 'BANKNIFTY', label: 'BANKNIFTY' },
                          { value: 'FINNIFTY', label: 'FINNIFTY' }
                        ]}
                        className="min-w-[120px]"
                      />
                    </div>

                    {/* Trading Checkboxes - Right Side */}
                    <div className="flex items-end gap-4">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={strategyConfig.moveSlToCost}
                          onChange={(e) => setStrategyConfig(prev => ({ ...prev, moveSlToCost: e.target.checked }))}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-200">Move SL to Cost</span>
                      </label>
                    </div>
                  </div>
                </div>
              )}

              {/* Scrollable Positions Content */}
              {legs.length > 0 && (
                <div className="flex-1 overflow-y-auto">
                  <div className="p-4 space-y-4">
                    {legs.map((leg, index) => (
                    <div key={leg.id} className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-4">
                      <div className="space-y-4">
                        {/* Position Header with Actions */}
                        <div className="flex items-center justify-between">
                          <h5 className="text-sm font-semibold text-gray-900 dark:text-white">
                            Position {index + 1}
                          </h5>
                          <div className="flex items-center gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => copyPosition(leg.id)}
                              className="h-8 w-8 p-0 text-blue-600 hover:bg-blue-50"
                            >
                              <Copy className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => removePosition(leg.id)}
                              className="h-8 w-8 p-0 text-red-600 hover:bg-red-50"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>

                        {/* Position Configuration Grid */}
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-7 gap-4">
                          
                          {/* Selection Method */}
                          <div>
                            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                              Selection Method
                            </label>
                            <Select
                              value={leg.selectionMethod}
                              onChange={(e) => {
                                const newMethod = e.target.value as StrategyLeg['selectionMethod'];
                                setLegs(prev => prev.map(l => 
                                  l.id === leg.id ? { 
                                    ...l, 
                                    selectionMethod: newMethod,
                                    strikePrice: 'ATM' // Reset to ATM when method changes
                                  } : l
                                ));
                              }}
                              options={[
                                { value: 'ATM_POINT', label: 'ATM Point' },
                                { value: 'ATM_PERCENT', label: 'ATM Percent' },
                                { value: 'CLOSEST_PREMIUM', label: 'Closest Premium' },
                                { value: 'CLOSEST_STRADDLE_PREMIUM', label: 'Closest Straddle' }
                              ]}
                              className="h-9 text-sm"
                            />
                          </div>

                          {/* Strike Selection */}
                          <div>
                            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                              Strike Price
                            </label>
                            <Select
                              value={leg.strikePrice}
                              onChange={(e) => {
                                const newStrikePrice = e.target.value;
                                setLegs(prev => prev.map(l => 
                                  l.id === leg.id ? { ...l, strikePrice: newStrikePrice } : l
                                ));
                              }}
                              options={generatePositionStrikeOptions(leg.selectionMethod)}
                              className="h-9 text-sm"
                            />
                          </div>

                          {/* Option Type Toggle */}
                          <div>
                            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                              Option Type
                            </label>
                            <button
                              type="button"
                              onClick={() => {
                                const newOptionType = leg.optionType === 'CE' ? 'PE' : 'CE';
                                setLegs(prev => prev.map(l => 
                                  l.id === leg.id ? { ...l, optionType: newOptionType } : l
                                ));
                              }}
                              className="w-full px-3 py-2 text-sm font-medium bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors shadow-sm"
                            >
                              {leg.optionType}
                            </button>
                          </div>

                          {/* Action Type Toggle */}
                          <div>
                            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                              Action
                            </label>
                            <button
                              type="button"
                              onClick={() => {
                                const newActionType = leg.actionType === 'BUY' ? 'SELL' : 'BUY';
                                setLegs(prev => prev.map(l => 
                                  l.id === leg.id ? { ...l, actionType: newActionType } : l
                                ));
                              }}
                              className={`w-full px-3 py-2 text-sm font-medium rounded-md hover:opacity-90 transition-all shadow-sm ${
                                leg.actionType === 'BUY' 
                                  ? 'bg-green-600 text-white hover:bg-green-700' 
                                  : 'bg-red-600 text-white hover:bg-red-700'
                              }`}
                            >
                              {leg.actionType}
                            </button>
                          </div>

                          {/* Editable Total Lots */}
                          <div>
                            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                              Lots
                            </label>
                            <Input
                              type="number"
                              min="1"
                              value={leg.totalLots}
                              onChange={(e) => {
                                const newLots = parseInt(e.target.value) || 1;
                                setLegs(prev => prev.map(l => 
                                  l.id === leg.id ? { ...l, totalLots: newLots } : l
                                ));
                              }}
                              className="h-9 text-sm"
                            />
                          </div>

                          {/* Expiry Type */}
                          <div>
                            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                              Expiry
                            </label>
                            <Select
                              value={leg.expiryType}
                              onChange={(e) => {
                                const newExpiryType = e.target.value as 'weekly' | 'monthly';
                                setLegs(prev => prev.map(l => 
                                  l.id === leg.id ? { ...l, expiryType: newExpiryType } : l
                                ));
                              }}
                              options={[
                                { value: 'weekly', label: 'Weekly' },
                                { value: 'monthly', label: 'Monthly' }
                              ]}
                              className="h-9 text-sm"
                            />
                          </div>
                        </div>

                        {/* Risk Management Section */}
                        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
                          <h5 className="text-sm font-medium text-gray-700 dark:text-gray-200 mb-3">Risk Management</h5>
                          
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
                            
                            {/* Stop Loss Configuration */}
                            <div className="space-y-3">
                              <div className="flex items-center space-x-2">
                                <input
                                  type="checkbox"
                                  id={`stopLoss-${leg.id}`}
                                  checked={leg.stopLoss.enabled}
                                  onChange={(e) => {
                                    setLegs(prev => prev.map(l => 
                                      l.id === leg.id ? { 
                                        ...l, 
                                        stopLoss: { ...l.stopLoss, enabled: e.target.checked },
                                        // Disable trailing stop loss if stop loss is disabled
                                        trailingStopLoss: e.target.checked ? l.trailingStopLoss : { ...l.trailingStopLoss, enabled: false }
                                      } : l
                                    ));
                                  }}
                                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                />
                                <label htmlFor={`stopLoss-${leg.id}`} className="text-sm font-medium text-gray-700 dark:text-gray-200">
                                  Stop Loss
                                </label>
                              </div>
                              
                              {leg.stopLoss.enabled && (
                                <div className="space-y-2">
                                  <Select
                                    value={leg.stopLoss.type}
                                    onChange={(e) => {
                                      const newType = e.target.value as 'POINTS' | 'PERCENTAGE' | 'RANGE';
                                      setLegs(prev => prev.map(l => 
                                        l.id === leg.id ? { 
                                          ...l, 
                                          stopLoss: { ...l.stopLoss, type: newType, value: 0 }
                                        } : l
                                      ));
                                    }}
                                    options={[
                                      { value: 'POINTS', label: 'Points' },
                                      { value: 'PERCENTAGE', label: 'Percentage' },
                                      { value: 'RANGE', label: 'Range' }
                                    ]}
                                    className="h-8 text-sm"
                                  />
                                  <Input
                                    type="number"
                                    min="0"
                                    step="0.1"
                                    value={leg.stopLoss.value}
                                    onChange={(e) => {
                                      const value = parseFloat(e.target.value) || 0;
                                      setLegs(prev => prev.map(l => 
                                        l.id === leg.id ? { 
                                          ...l, 
                                          stopLoss: { ...l.stopLoss, value }
                                        } : l
                                      ));
                                    }}
                                    placeholder="Stop loss value"
                                    className="h-8 text-sm"
                                  />
                                </div>
                              )}
                            </div>

                            {/* Target Profit Configuration */}
                            <div className="space-y-3">
                              <div className="flex items-center space-x-2">
                                <input
                                  type="checkbox"
                                  id={`targetProfit-${leg.id}`}
                                  checked={leg.targetProfit.enabled}
                                  onChange={(e) => {
                                    setLegs(prev => prev.map(l => 
                                      l.id === leg.id ? { 
                                        ...l, 
                                        targetProfit: { ...l.targetProfit, enabled: e.target.checked }
                                      } : l
                                    ));
                                  }}
                                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                />
                                <label htmlFor={`targetProfit-${leg.id}`} className="text-sm font-medium text-gray-700 dark:text-gray-200">
                                  Target Profit
                                </label>
                              </div>
                              
                              {leg.targetProfit.enabled && (
                                <div className="space-y-2">
                                  <Select
                                    value={leg.targetProfit.type}
                                    onChange={(e) => {
                                      const newType = e.target.value as 'POINTS' | 'PERCENTAGE';
                                      setLegs(prev => prev.map(l => 
                                        l.id === leg.id ? { 
                                          ...l, 
                                          targetProfit: { ...l.targetProfit, type: newType, value: 0 }
                                        } : l
                                      ));
                                    }}
                                    options={[
                                      { value: 'POINTS', label: 'Points' },
                                      { value: 'PERCENTAGE', label: 'Percentage' }
                                    ]}
                                    className="h-8 text-sm"
                                  />
                                  <Input
                                    type="number"
                                    min="0"
                                    step="0.1"
                                    value={leg.targetProfit.value}
                                    onChange={(e) => {
                                      const value = parseFloat(e.target.value) || 0;
                                      setLegs(prev => prev.map(l => 
                                        l.id === leg.id ? { 
                                          ...l, 
                                          targetProfit: { ...l.targetProfit, value }
                                        } : l
                                      ));
                                    }}
                                    placeholder="Target profit value"
                                    className="h-8 text-sm"
                                  />
                                </div>
                              )}
                            </div>

                            {/* Trailing Stop Loss Configuration */}
                            <div className="space-y-3">
                              <div className="flex items-center space-x-2">
                                <input
                                  type="checkbox"
                                  id={`trailingStopLoss-${leg.id}`}
                                  checked={leg.trailingStopLoss.enabled}
                                  disabled={!leg.stopLoss.enabled}
                                  onChange={(e) => {
                                    setLegs(prev => prev.map(l => 
                                      l.id === leg.id ? { 
                                        ...l, 
                                        trailingStopLoss: { ...l.trailingStopLoss, enabled: e.target.checked }
                                      } : l
                                    ));
                                  }}
                                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:opacity-50"
                                />
                                <label htmlFor={`trailingStopLoss-${leg.id}`} className={`text-sm font-medium ${!leg.stopLoss.enabled ? 'text-gray-400' : 'text-gray-700 dark:text-gray-200'}`}>
                                  Trailing Stop Loss
                                </label>
                              </div>
                              
                              {leg.trailingStopLoss.enabled && leg.stopLoss.enabled && (
                                <div className="space-y-2">
                                  {/* Row 1: Type Selection */}
                                  <Select
                                    value={leg.trailingStopLoss.type}
                                    onChange={(e) => {
                                      const newType = e.target.value as 'POINTS' | 'PERCENTAGE';
                                      setLegs(prev => prev.map(l => 
                                        l.id === leg.id ? { 
                                          ...l, 
                                          trailingStopLoss: { 
                                            ...l.trailingStopLoss, 
                                            type: newType,
                                            instrumentMoveValue: 0,
                                            stopLossMoveValue: 0
                                          }
                                        } : l
                                      ));
                                    }}
                                    options={[
                                      { value: 'POINTS', label: 'Points' },
                                      { value: 'PERCENTAGE', label: 'Percentage' }
                                    ]}
                                    className="h-8 text-sm"
                                  />
                                  
                                  {/* Row 2: Instrument Move Value */}
                                  <Input
                                    type="number"
                                    min="0"
                                    step="0.1"
                                    value={leg.trailingStopLoss.instrumentMoveValue}
                                    onChange={(e) => {
                                      const value = parseFloat(e.target.value) || 0;
                                      setLegs(prev => prev.map(l => 
                                        l.id === leg.id ? { 
                                          ...l, 
                                          trailingStopLoss: { ...l.trailingStopLoss, instrumentMoveValue: value }
                                        } : l
                                      ));
                                    }}
                                    placeholder="Instrument Move by"
                                    className="h-8 text-sm"
                                  />
                                  
                                  {/* Row 3: Stop Loss Move Value */}
                                  <Input
                                    type="number"
                                    min="0"
                                    step="0.1"
                                    value={leg.trailingStopLoss.stopLossMoveValue}
                                    onChange={(e) => {
                                      const value = parseFloat(e.target.value) || 0;
                                      setLegs(prev => prev.map(l => 
                                        l.id === leg.id ? { 
                                          ...l, 
                                          trailingStopLoss: { ...l.trailingStopLoss, stopLossMoveValue: value }
                                        } : l
                                      ));
                                    }}
                                    placeholder="Move StopLoss by"
                                    className="h-8 text-sm"
                                  />
                                </div>
                              )}
                            </div>

                            {/* Wait & Trade Configuration */}
                            <div className="space-y-3">
                              <div className="flex items-center space-x-2">
                                <input
                                  type="checkbox"
                                  id={`waitAndTrade-${leg.id}`}
                                  checked={leg.waitAndTrade.enabled}
                                  onChange={(e) => {
                                    setLegs(prev => prev.map(l => 
                                      l.id === leg.id ? { 
                                        ...l, 
                                        waitAndTrade: { ...l.waitAndTrade, enabled: e.target.checked }
                                      } : l
                                    ));
                                  }}
                                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                />
                                <label htmlFor={`waitAndTrade-${leg.id}`} className="text-sm font-medium text-gray-700 dark:text-gray-200">
                                  Wait & Trade
                                </label>
                              </div>
                              
                              {leg.waitAndTrade.enabled && (
                                <div className="space-y-2">
                                  <Select
                                    value={leg.waitAndTrade.type}
                                    onChange={(e) => {
                                      const newType = e.target.value as 'POINTS' | 'PERCENTAGE';
                                      setLegs(prev => prev.map(l => 
                                        l.id === leg.id ? { 
                                          ...l, 
                                          waitAndTrade: { ...l.waitAndTrade, type: newType, value: 0 }
                                        } : l
                                      ));
                                    }}
                                    options={[
                                      { value: 'POINTS', label: 'Points' },
                                      { value: 'PERCENTAGE', label: 'Percentage' }
                                    ]}
                                    className="h-8 text-sm"
                                  />
                                  <Input
                                    type="number"
                                    min="0"
                                    step="0.1"
                                    value={leg.waitAndTrade.value}
                                    onChange={(e) => {
                                      const value = parseFloat(e.target.value) || 0;
                                      setLegs(prev => prev.map(l => 
                                        l.id === leg.id ? { 
                                          ...l, 
                                          waitAndTrade: { ...l.waitAndTrade, value }
                                        } : l
                                      ));
                                    }}
                                    placeholder="Wait & trade value"
                                    className="h-8 text-sm"
                                  />
                                </div>
                              )}
                            </div>

                            {/* Re Entry Configuration */}
                            <div className="space-y-3">
                              <div className="flex items-center space-x-2">
                                <input
                                  type="checkbox"
                                  id={`reEntry-${leg.id}`}
                                  checked={leg.reEntry.enabled}
                                  onChange={(e) => {
                                    setLegs(prev => prev.map(l => 
                                      l.id === leg.id ? { 
                                        ...l, 
                                        reEntry: { ...l.reEntry, enabled: e.target.checked }
                                      } : l
                                    ));
                                  }}
                                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                />
                                <label htmlFor={`reEntry-${leg.id}`} className="text-sm font-medium text-gray-700 dark:text-gray-200">
                                  Re Entry [SL]
                                </label>
                              </div>
                              
                              {leg.reEntry.enabled && (
                                <div className="space-y-2">
                                  <Select
                                    value={leg.reEntry.type}
                                    onChange={(e) => {
                                      setLegs(prev => prev.map(l => 
                                        l.id === leg.id ? { 
                                          ...l, 
                                          reEntry: { ...l.reEntry, type: e.target.value as 'SL_REENTRY' | 'SL_RECOST' | 'SL_REEXEC' }
                                        } : l
                                      ));
                                    }}
                                    options={[
                                      { value: 'SL_REENTRY', label: 'SL ReEntry' },
                                      { value: 'SL_RECOST', label: 'SL ReCost' },
                                      { value: 'SL_REEXEC', label: 'SL ReExec' }
                                    ]}
                                    className="h-8 text-sm"
                                  />
                                  <Select
                                    value={leg.reEntry.count.toString()}
                                    onChange={(e) => {
                                      const count = parseInt(e.target.value);
                                      setLegs(prev => prev.map(l => 
                                        l.id === leg.id ? { 
                                          ...l, 
                                          reEntry: { ...l.reEntry, count }
                                        } : l
                                      ));
                                    }}
                                    options={[
                                      { value: '1', label: '1' },
                                      { value: '2', label: '2' },
                                      { value: '3', label: '3' },
                                      { value: '4', label: '4' },
                                      { value: '5', label: '5' }
                                    ]}
                                    className="h-8 text-sm"
                                  />
                                </div>
                              )}
                            </div>

                            {/* Re Execute Configuration */}
                            <div className="space-y-3">
                              <div className="flex items-center space-x-2">
                                <input
                                  type="checkbox"
                                  id={`reExecute-${leg.id}`}
                                  checked={leg.reExecute.enabled}
                                  onChange={(e) => {
                                    setLegs(prev => prev.map(l => 
                                      l.id === leg.id ? { 
                                        ...l, 
                                        reExecute: { ...l.reExecute, enabled: e.target.checked }
                                      } : l
                                    ));
                                  }}
                                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                />
                                <label htmlFor={`reExecute-${leg.id}`} className="text-sm font-medium text-gray-700 dark:text-gray-200">
                                  Re Execute [TP]
                                </label>
                              </div>
                              
                              {leg.reExecute.enabled && (
                                <div className="space-y-2">
                                  <Select
                                    value={leg.reExecute.type}
                                    onChange={(e) => {
                                      setLegs(prev => prev.map(l => 
                                        l.id === leg.id ? { 
                                          ...l, 
                                          reExecute: { ...l.reExecute, type: e.target.value as 'TP_REEXEC' }
                                        } : l
                                      ));
                                    }}
                                    options={[
                                      { value: 'TP_REEXEC', label: 'TP ReExec' }
                                    ]}
                                    className="h-8 text-sm"
                                  />
                                  <Select
                                    value={leg.reExecute.count.toString()}
                                    onChange={(e) => {
                                      const count = parseInt(e.target.value);
                                      setLegs(prev => prev.map(l => 
                                        l.id === leg.id ? { 
                                          ...l, 
                                          reExecute: { ...l.reExecute, count }
                                        } : l
                                      ));
                                    }}
                                    options={[
                                      { value: '1', label: '1' },
                                      { value: '2', label: '2' },
                                      { value: '3', label: '3' },
                                      { value: '4', label: '4' },
                                      { value: '5', label: '5' }
                                    ]}
                                    className="h-8 text-sm"
                                  />
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Footer Section - Strategy Configuration (Only show after first position) */}
              {legs.length > 0 && (
                <div className="bg-gradient-to-r from-gray-50/80 to-gray-100/80 dark:from-gray-800/50 dark:to-gray-700/50 px-6 py-6 border-t border-gray-200/30 dark:border-gray-600/30">
                  <div className="space-y-6">
                    {/* Range Breakout Checkbox */}
                    <div>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={strategyConfig.rangeBreakout}
                          onChange={(e) => setStrategyConfig(prev => ({ ...prev, rangeBreakout: e.target.checked }))}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 focus:ring-2"
                        />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-200">Range Breakout</span>
                      </label>
                    </div>

                    {/* Time Configuration Cards */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      {/* Entry Time Card */}
                      <div className="bg-white/90 dark:bg-gray-800/90 rounded-xl shadow-lg border border-gray-200/50 dark:border-gray-600/50 p-5">
                        <div className="space-y-4">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-200">
                              Entry Time
                            </label>
                          </div>
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Hour</label>
                              <Select
                                value={strategyConfig.entryTimeHour}
                                onChange={(e) => setStrategyConfig(prev => ({ ...prev, entryTimeHour: e.target.value }))}
                                options={Array.from({ length: 24 }, (_, i) => ({ 
                                  value: i.toString().padStart(2, '0'), 
                                  label: i.toString().padStart(2, '0') 
                                }))}
                                className="h-10 text-sm rounded-lg"
                              />
                            </div>
                            <div>
                              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Minute</label>
                              <Select
                                value={strategyConfig.entryTimeMinute}
                                onChange={(e) => setStrategyConfig(prev => ({ ...prev, entryTimeMinute: e.target.value }))}
                                options={Array.from({ length: 60 }, (_, i) => ({ 
                                  value: i.toString().padStart(2, '0'), 
                                  label: i.toString().padStart(2, '0') 
                                }))}
                                className="h-10 text-sm rounded-lg"
                              />
                            </div>
                          </div>
                          
                          {/* Range Breakout Time - Show below entry time when checkbox is selected */}
                          {strategyConfig.rangeBreakout && (
                            <div className="pt-4 border-t border-gray-200/50 dark:border-gray-600/50">
                              <div className="flex items-center gap-2 mb-3">
                                <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                                <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300">
                                  Range Exit Time
                                </label>
                              </div>
                              <div className="grid grid-cols-2 gap-3">
                                <div>
                                  <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Hour</label>
                                  <Select
                                    value={strategyConfig.rangeBreakoutTimeHour}
                                    onChange={(e) => setStrategyConfig(prev => ({ ...prev, rangeBreakoutTimeHour: e.target.value }))}
                                    options={Array.from({ length: 24 }, (_, i) => ({ 
                                      value: i.toString().padStart(2, '0'), 
                                      label: i.toString().padStart(2, '0') 
                                    }))}
                                    className="h-9 text-sm rounded-lg"
                                  />
                                </div>
                                <div>
                                  <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Minute</label>
                                  <Select
                                    value={strategyConfig.rangeBreakoutTimeMinute}
                                    onChange={(e) => setStrategyConfig(prev => ({ ...prev, rangeBreakoutTimeMinute: e.target.value }))}
                                    options={Array.from({ length: 60 }, (_, i) => ({ 
                                      value: i.toString().padStart(2, '0'), 
                                      label: i.toString().padStart(2, '0') 
                                    }))}
                                    className="h-9 text-sm rounded-lg"
                                  />
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Exit Time Card */}
                      <div className="bg-white/90 dark:bg-gray-800/90 rounded-xl shadow-lg border border-gray-200/50 dark:border-gray-600/50 p-5">
                        <div className="space-y-4">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-200">
                              Exit Time
                            </label>
                          </div>
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Hour</label>
                              <Select
                                value={strategyConfig.exitTimeHour}
                                onChange={(e) => setStrategyConfig(prev => ({ ...prev, exitTimeHour: e.target.value }))}
                                options={Array.from({ length: 24 }, (_, i) => ({ 
                                  value: i.toString().padStart(2, '0'), 
                                  label: i.toString().padStart(2, '0') 
                                }))}
                                className="h-10 text-sm rounded-lg"
                              />
                            </div>
                            <div>
                              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Minute</label>
                              <Select
                                value={strategyConfig.exitTimeMinute}
                                onChange={(e) => setStrategyConfig(prev => ({ ...prev, exitTimeMinute: e.target.value }))}
                                options={Array.from({ length: 60 }, (_, i) => ({ 
                                  value: i.toString().padStart(2, '0'), 
                                  label: i.toString().padStart(2, '0') 
                                }))}
                                className="h-10 text-sm rounded-lg"
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Risk Management Cards */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      {/* Target Profit Card */}
                      <div className="bg-white/90 dark:bg-gray-800/90 rounded-xl shadow-lg border border-gray-200/50 dark:border-gray-600/50 p-5">
                        <div className="space-y-4">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-200">
                              Target Profit
                            </label>
                          </div>
                          <div className="space-y-3">
                            <div>
                              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Type</label>
                              <Select
                                value={strategyConfig.targetProfit.type}
                                onChange={(e) => setStrategyConfig(prev => ({ 
                                  ...prev, 
                                  targetProfit: { ...prev.targetProfit, type: e.target.value as 'TOTAL_MTM' | 'COMBINED_PREMIUM_PERCENT' }
                                }))}
                                options={[
                                  { value: 'TOTAL_MTM', label: 'Total MTM' },
                                  { value: 'COMBINED_PREMIUM_PERCENT', label: 'Combined Premium %' }
                                ]}
                                className="h-10 text-sm rounded-lg"
                              />
                            </div>
                            <div>
                              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Value</label>
                              <Input
                                type="number"
                                min="0"
                                step="0.1"
                                value={strategyConfig.targetProfit.value}
                                onChange={(e) => setStrategyConfig(prev => ({ 
                                  ...prev, 
                                  targetProfit: { ...prev.targetProfit, value: parseFloat(e.target.value) || 0 }
                                }))}
                                placeholder={strategyConfig.targetProfit.type === 'TOTAL_MTM' ? 'Enter amount' : 'Enter percentage'}
                                className="h-10 text-sm rounded-lg"
                              />
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* MTM Stop Loss Card */}
                      <div className="bg-white/90 dark:bg-gray-800/90 rounded-xl shadow-lg border border-gray-200/50 dark:border-gray-600/50 p-5">
                        <div className="space-y-4">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-red-600 rounded-full"></div>
                            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-200">
                              MTM Stop Loss
                            </label>
                          </div>
                          <div className="space-y-3">
                            <div>
                              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Type</label>
                              <Select
                                value={strategyConfig.mtmStopLoss.type}
                                onChange={(e) => setStrategyConfig(prev => ({ 
                                  ...prev, 
                                  mtmStopLoss: { ...prev.mtmStopLoss, type: e.target.value as 'TOTAL_MTM' | 'COMBINED_PREMIUM_PERCENT' }
                                }))}
                                options={[
                                  { value: 'TOTAL_MTM', label: 'Total MTM' },
                                  { value: 'COMBINED_PREMIUM_PERCENT', label: 'Combined Premium %' }
                                ]}
                                className="h-10 text-sm rounded-lg"
                              />
                            </div>
                            <div>
                              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Value</label>
                              <Input
                                type="number"
                                min="0"
                                step="0.1"
                                value={strategyConfig.mtmStopLoss.value}
                                onChange={(e) => setStrategyConfig(prev => ({ 
                                  ...prev, 
                                  mtmStopLoss: { ...prev.mtmStopLoss, value: parseFloat(e.target.value) || 0 }
                                }))}
                                placeholder={strategyConfig.mtmStopLoss.type === 'TOTAL_MTM' ? 'Enter amount' : 'Enter percentage'}
                                className="h-10 text-sm rounded-lg"
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>

          {/* Footer Actions */}
          <div className="flex-shrink-0 flex items-center justify-between gap-3 p-4 border-t bg-gray-50 dark:bg-gray-700/50">
            {error && (
              <div className="flex-1 text-sm text-red-600 dark:text-red-400">
                {error}
              </div>
            )}
            <div className={`flex items-center gap-3 ${error ? '' : 'ml-auto'}`}>
              <Button
                variant="outline"
                onClick={onClose}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                onClick={handleSubmit}
                disabled={isSubmitting || legs.length === 0}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                {isSubmitting ? 'Creating...' : 'Create Strategy'}
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default StrategyWizardDialog;