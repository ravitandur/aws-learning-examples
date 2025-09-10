import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import { X, Plus, Trash2, Copy } from 'lucide-react';
import strategyService from '../../services/strategyService';
import { FrontendStrategyData } from '../../services/strategyTransformationService';

interface StrategyLeg {
  id: string;
  index: string;
  optionType: 'CE' | 'PE';
  actionType: 'BUY' | 'SELL';
  strikePrice: string;
  totalLots: number;
  expiryType: 'weekly' | 'monthly';
  selectionMethod: 'ATM_POINT' | 'ATM_PERCENT' | 'CLOSEST_PREMIUM' | 'CLOSEST_STRADDLE_PREMIUM';
  
  // Premium selection fields for CLOSEST_PREMIUM method
  premiumOperator?: 'CP_EQUAL' | 'CP_GREATER_EQUAL' | 'CP_LESS_EQUAL';
  premiumValue?: number;
  
  // Straddle premium fields for CLOSEST_STRADDLE_PREMIUM method
  straddlePremiumOperator?: 'CP_EQUAL' | 'CP_GREATER_EQUAL' | 'CP_LESS_EQUAL';
  straddlePremiumPercentage?: number;
  
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
    moveSlToCost: false,
    // New trading type configuration
    tradingType: 'INTRADAY' as 'INTRADAY' | 'POSITIONAL',
    intradayExitMode: 'SAME_DAY' as 'SAME_DAY' | 'NEXT_DAY_BTST',
    positionalEntryDays: 2, // Independent entry days for positional
    positionalExitDays: 0, // Independent exit days for positional
    targetProfit: {
      type: 'TOTAL_MTM' as const,
      value: 0
    },
    mtmStopLoss: {
      type: 'TOTAL_MTM' as const,
      value: 0
    }
  });

  const [legs, setLegs] = useState<StrategyLeg[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

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

  // Generate straddle premium percentage options (5% to 60% in steps of 5%)
  const generateStraddlePremiumPercentageOptions = (): { value: string; label: string }[] => {
    const options = [];
    for (let i = 5; i <= 60; i += 5) {
      options.push({ value: i.toString(), label: `${i}%` });
    }
    return options;
  };

  // Get expiry text based on legs selection (defaults to weekly if no legs or all weekly)
  const getExpiryText = (): string => {
    if (legs.length === 0) return 'weekly';
    
    // If any leg has monthly expiry, show monthly, otherwise show weekly
    const hasMonthlyExpiry = legs.some(leg => leg.expiryType === 'monthly');
    return hasMonthlyExpiry ? 'monthly' : 'weekly';
  };

  // Get maximum slider range based on expiry type
  const getMaxSliderRange = (): number => {
    const hasMonthlyExpiry = legs.some(leg => leg.expiryType === 'monthly');
    return hasMonthlyExpiry ? 24 : 4;
  };

  // Get default values for positional sliders based on expiry type
  const getDefaultPositionalValues = () => {
    return {
      entryDays: 4,
      exitDays: 0 // Always 0 for exit
    };
  };


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
      
      // Default premium selection values
      premiumOperator: 'CP_EQUAL',
      premiumValue: 0,
      
      // Default straddle premium values
      straddlePremiumOperator: 'CP_EQUAL',
      straddlePremiumPercentage: 5,
      
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

  // Submit handler with strategy service integration
  const handleSubmit = async () => {
    const validationError = validateInputs();
    if (validationError) {
      setError(validationError);
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      // Prepare strategy data in frontend format
      const strategyData: FrontendStrategyData = {
        basketId,
        strategyName: strategyName.trim(),
        index: strategyIndex,
        config: strategyConfig,
        legs: legs.map(leg => ({
          id: leg.id,
          index: leg.index,
          optionType: leg.optionType,
          actionType: leg.actionType,
          strikePrice: leg.strikePrice,
          totalLots: leg.totalLots,
          expiryType: leg.expiryType,
          selectionMethod: leg.selectionMethod,
          premiumOperator: leg.premiumOperator,
          premiumValue: leg.premiumValue,
          straddlePremiumOperator: leg.straddlePremiumOperator,
          straddlePremiumPercentage: leg.straddlePremiumPercentage,
          stopLoss: leg.stopLoss,
          targetProfit: leg.targetProfit,
          trailingStopLoss: leg.trailingStopLoss,
          waitAndTrade: leg.waitAndTrade,
          reEntry: leg.reEntry,
          reExecute: leg.reExecute
        }))
      };

      // Use strategy service to create strategy (includes data transformation)
      const result = await strategyService.createStrategy(basketId, strategyData);

      if (result.success) {
        // Call the parent onSubmit handler with the result
        await onSubmit(result);
        // Close dialog on success
        onClose();
      } else {
        throw new Error(result.message || 'Failed to create strategy');
      }
    } catch (error: any) {
      console.error('Strategy creation error:', error);
      setError(error.message || 'Failed to create strategy. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-2 sm:p-4 z-50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="strategy-dialog-title"
    >
      <div 
        ref={dialogRef}
        tabIndex={-1}
        className="w-full max-w-5xl h-full sm:h-[95vh] flex flex-col"
      >
        <Card className="flex flex-col bg-white/95 dark:bg-gray-900/95 backdrop-blur-md border border-white/20 dark:border-gray-700/20 rounded-none sm:rounded-2xl shadow-2xl overflow-hidden h-full">
          {/* Fixed Header */}
          <CardHeader className="flex-shrink-0 flex flex-row items-center justify-between pb-4 px-4 sm:px-6 border-b border-gray-200/50 dark:border-gray-700/50">
            <h2 
              id="strategy-dialog-title"
              className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white tracking-tight"
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

          {/* Content Area */}
          <CardContent className="flex-1 flex flex-col overflow-hidden p-0">
            {/* Strategy Name and Add Position Button - Always Visible */}
            <div className="flex-shrink-0 bg-gray-50 dark:bg-gray-700/50 px-4 py-4 border-b border-gray-200 dark:border-gray-600">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-end">
                  <div>
                    <Input
                      type="text"
                      value={strategyName}
                      onChange={(e) => setStrategyName(e.target.value)}
                      placeholder="Enter strategy name"
                      className="h-9"
                    />
                  </div>
                  <div>
                    <Button
                      onClick={addPosition}
                      leftIcon={<Plus className="h-4 w-4" />}
                      className="bg-blue-600 hover:bg-blue-700 text-white h-9"
                    >
                      Add Position
                    </Button>
                  </div>
                </div>
              </div>

              {/* Header Section - Index and Checkboxes (Show only after first position) */}
              {legs.length > 0 && (
                <div className="flex-shrink-0 bg-white dark:bg-gray-800 mx-4 my-4 rounded-xl shadow-lg border border-gray-200/50 dark:border-gray-600/50 p-5">
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

                    {/* Positions Counter - Middle */}
                    <div className="flex-1 text-center">
                      <span className="text-sm text-gray-600 dark:text-gray-300">
                        <span className="font-bold text-blue-600 dark:text-blue-400">{legs.length}</span> position{legs.length !== 1 ? 's' : ''} added
                      </span>
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

            {/* Scrollable Content Area - Positions Only */}
            <div className="flex-1 overflow-y-auto">
              {/* Positions Content */}
              {legs.length > 0 && (
                <div className="mx-4 mb-6 space-y-4">
                    {legs.map((leg, index) => (
                    <div key={leg.id} className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200/50 dark:border-gray-600/50 p-6">
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

                          {/* Strike Selection, Premium Selection, or Straddle Premium Selection */}
                          {leg.selectionMethod === 'CLOSEST_PREMIUM' ? (
                            // Premium Selection UI
                            <div className="col-span-2 grid grid-cols-2 gap-2">
                              {/* Premium Operator */}
                              <div>
                                <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                                  Premium Operator
                                </label>
                                <Select
                                  value={leg.premiumOperator || 'CP_EQUAL'}
                                  onChange={(e) => {
                                    const newOperator = e.target.value as 'CP_EQUAL' | 'CP_GREATER_EQUAL' | 'CP_LESS_EQUAL';
                                    setLegs(prev => prev.map(l => 
                                      l.id === leg.id ? { ...l, premiumOperator: newOperator } : l
                                    ));
                                  }}
                                  options={[
                                    { value: 'CP_EQUAL', label: 'CP ~' },
                                    { value: 'CP_GREATER_EQUAL', label: 'CP >=' },
                                    { value: 'CP_LESS_EQUAL', label: 'CP <=' }
                                  ]}
                                  className="h-9 text-sm"
                                />
                              </div>
                              
                              {/* Premium Value */}
                              <div>
                                <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                                  Premium Value
                                </label>
                                <Input
                                  type="number"
                                  min="0"
                                  step="0.1"
                                  value={leg.premiumValue || 0}
                                  onChange={(e) => {
                                    const newValue = parseFloat(e.target.value) || 0;
                                    setLegs(prev => prev.map(l => 
                                      l.id === leg.id ? { ...l, premiumValue: newValue } : l
                                    ));
                                  }}
                                  placeholder="Enter premium"
                                  className="h-9 text-sm"
                                />
                              </div>
                            </div>
                          ) : leg.selectionMethod === 'CLOSEST_STRADDLE_PREMIUM' ? (
                            // Straddle Premium Selection UI
                            <div className="col-span-2 grid grid-cols-2 gap-2">
                              {/* Straddle Premium Operator */}
                              <div>
                                <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                                  Premium Operator
                                </label>
                                <Select
                                  value={leg.straddlePremiumOperator || 'CP_EQUAL'}
                                  onChange={(e) => {
                                    const newOperator = e.target.value as 'CP_EQUAL' | 'CP_GREATER_EQUAL' | 'CP_LESS_EQUAL';
                                    setLegs(prev => prev.map(l => 
                                      l.id === leg.id ? { ...l, straddlePremiumOperator: newOperator } : l
                                    ));
                                  }}
                                  options={[
                                    { value: 'CP_EQUAL', label: 'CP ~' },
                                    { value: 'CP_GREATER_EQUAL', label: 'CP >=' },
                                    { value: 'CP_LESS_EQUAL', label: 'CP <=' }
                                  ]}
                                  className="h-9 text-sm"
                                />
                              </div>
                              
                              {/* Straddle Premium Percentage */}
                              <div>
                                <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                                  Premium %
                                </label>
                                <Select
                                  value={(leg.straddlePremiumPercentage || 5).toString()}
                                  onChange={(e) => {
                                    const newPercentage = parseInt(e.target.value);
                                    setLegs(prev => prev.map(l => 
                                      l.id === leg.id ? { ...l, straddlePremiumPercentage: newPercentage } : l
                                    ));
                                  }}
                                  options={generateStraddlePremiumPercentageOptions()}
                                  className="h-9 text-sm"
                                />
                              </div>
                            </div>
                          ) : (
                            // Regular Strike Price Selection
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
                          )}

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
              )}

              {/* Footer Section - Strategy Configuration (Only show after first position) */}
              {legs.length > 0 && (
                <div className="flex-shrink-0 bg-white dark:bg-gray-800 mx-4 mb-4 rounded-xl shadow-lg border border-gray-200/50 dark:border-gray-600/50 p-6">
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

                          {/* Positional Entry Days Slider - Show as second row when Positional is selected */}
                          {strategyConfig.tradingType === 'POSITIONAL' && (
                            <div className="pt-4 border-t border-gray-200/50 dark:border-gray-600/50">

                              <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                  <span className="text-xs text-gray-500 dark:text-gray-400">
                                    {strategyConfig.positionalEntryDays} trading days before {getExpiryText()} expiry (excluding holidays)
                                  </span>
                                  <span className="text-xs font-medium text-blue-600 dark:text-blue-400">
                                    {strategyConfig.positionalEntryDays} {strategyConfig.positionalEntryDays === 1 ? 'day' : 'days'}
                                  </span>
                                </div>
                                <div className="relative">
                                  <input
                                    type="range"
                                    min="0"
                                    max={getMaxSliderRange()}
                                    value={getMaxSliderRange() - strategyConfig.positionalEntryDays}
                                    onChange={(e) => setStrategyConfig(prev => ({ 
                                      ...prev, 
                                      positionalEntryDays: getMaxSliderRange() - parseInt(e.target.value) 
                                    }))}
                                    className="w-full h-2 bg-gray-200 dark:bg-gray-600 rounded-lg appearance-none cursor-pointer slider"
                                    style={{
                                      background: `linear-gradient(to right, #e5e7eb 0%, #e5e7eb ${((getMaxSliderRange() - strategyConfig.positionalEntryDays) / getMaxSliderRange()) * 100}%, #3b82f6 ${((getMaxSliderRange() - strategyConfig.positionalEntryDays) / getMaxSliderRange()) * 100}%, #3b82f6 100%)`
                                    }}
                                  />
                                  <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
                                    <span>{getMaxSliderRange()} days</span>
                                    <span>0 days</span>
                                  </div>
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
                          
                          {/* Intraday Exit Mode - Show as first row when Intraday is selected */}
                          {strategyConfig.tradingType === 'INTRADAY' && (
                            <div className="pb-3 border-b border-gray-200/50 dark:border-gray-600/50">
                              <div className="flex items-center gap-4">
                                <label className="flex items-center gap-2 cursor-pointer">
                                  <input
                                    type="radio"
                                    name="intradayExitMode"
                                    value="SAME_DAY"
                                    checked={strategyConfig.intradayExitMode === 'SAME_DAY'}
                                    onChange={(e) => setStrategyConfig(prev => ({ 
                                      ...prev, 
                                      intradayExitMode: e.target.value as 'SAME_DAY' | 'NEXT_DAY_BTST' 
                                    }))}
                                    className="text-blue-600 focus:ring-blue-500"
                                  />
                                  <span className="text-sm text-gray-700 dark:text-gray-200">Same Day</span>
                                </label>
                                <label className="flex items-center gap-2 cursor-pointer">
                                  <input
                                    type="radio"
                                    name="intradayExitMode"
                                    value="NEXT_DAY_BTST"
                                    checked={strategyConfig.intradayExitMode === 'NEXT_DAY_BTST'}
                                    onChange={(e) => setStrategyConfig(prev => ({ 
                                      ...prev, 
                                      intradayExitMode: e.target.value as 'SAME_DAY' | 'NEXT_DAY_BTST' 
                                    }))}
                                    className="text-blue-600 focus:ring-blue-500"
                                  />
                                  <span className="text-sm text-gray-700 dark:text-gray-200">Next Day (BTST/STBT)</span>
                                </label>
                              </div>
                            </div>
                          )}

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

                          {/* Positional Exit Days Slider - Show as second row when Positional is selected */}
                          {strategyConfig.tradingType === 'POSITIONAL' && (
                            <div className="pt-4 border-t border-gray-200/50 dark:border-gray-600/50">

                              <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                  <span className="text-xs text-gray-500 dark:text-gray-400">
                                    {strategyConfig.positionalExitDays} trading days before {getExpiryText()} expiry (excluding holidays)
                                  </span>
                                  <span className="text-xs font-medium text-blue-600 dark:text-blue-400">
                                    {strategyConfig.positionalExitDays} {strategyConfig.positionalExitDays === 1 ? 'day' : 'days'}
                                  </span>
                                </div>
                                <div className="relative">
                                  <input
                                    type="range"
                                    min="0"
                                    max={getMaxSliderRange()}
                                    value={getMaxSliderRange() - strategyConfig.positionalExitDays}
                                    onChange={(e) => setStrategyConfig(prev => ({ 
                                      ...prev, 
                                      positionalExitDays: getMaxSliderRange() - parseInt(e.target.value) 
                                    }))}
                                    className="w-full h-2 bg-gray-200 dark:bg-gray-600 rounded-lg appearance-none cursor-pointer slider"
                                    style={{
                                      background: `linear-gradient(to right, #e5e7eb 0%, #e5e7eb ${((getMaxSliderRange() - strategyConfig.positionalExitDays) / getMaxSliderRange()) * 100}%, #3b82f6 ${((getMaxSliderRange() - strategyConfig.positionalExitDays) / getMaxSliderRange()) * 100}%, #3b82f6 100%)`
                                    }}
                                  />
                                  <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
                                    <span>{getMaxSliderRange()} days</span>
                                    <span>0 days</span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Trading Type Configuration */}
                    <div className="bg-white/90 dark:bg-gray-800/90 rounded-xl shadow-lg border border-gray-200/50 dark:border-gray-600/50 p-5">
                      <div className="space-y-4">
                        {/* Trading Type Toggle */}
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-200">
                              Trading Type
                            </label>
                          </div>
                          <div className="flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
                            <button
                              type="button"
                              onClick={() => setStrategyConfig(prev => ({ 
                                ...prev, 
                                tradingType: 'INTRADAY',
                                // Reset conditional values when switching
                                intradayExitMode: 'SAME_DAY'
                              }))}
                              className={`px-4 py-2 text-sm font-medium rounded-md transition-all duration-200 ${
                                strategyConfig.tradingType === 'INTRADAY'
                                  ? 'bg-blue-600 text-white shadow-sm' 
                                  : 'text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                              }`}
                            >
                              Intraday
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                const defaults = getDefaultPositionalValues();
                                setStrategyConfig(prev => ({ 
                                  ...prev, 
                                  tradingType: 'POSITIONAL',
                                  // Reset conditional values when switching
                                  positionalEntryDays: defaults.entryDays,
                                  positionalExitDays: defaults.exitDays
                                }));
                              }}
                              className={`px-4 py-2 text-sm font-medium rounded-md transition-all duration-200 ${
                                strategyConfig.tradingType === 'POSITIONAL'
                                  ? 'bg-blue-600 text-white shadow-sm' 
                                  : 'text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                              }`}
                            >
                              Positional
                            </button>
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
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Type</label>
                              <Select
                                value={strategyConfig.targetProfit.type}
                                onChange={(e) => {
                                  const newType = e.target.value as 'TOTAL_MTM' | 'COMBINED_PREMIUM_PERCENT';
                                  setStrategyConfig(prev => ({ 
                                    ...prev, 
                                    targetProfit: { 
                                      type: newType as any,
                                      value: prev.targetProfit.value
                                    }
                                  }));
                                }}
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
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Type</label>
                              <Select
                                value={strategyConfig.mtmStopLoss.type}
                                onChange={(e) => {
                                  const newType = e.target.value as 'TOTAL_MTM' | 'COMBINED_PREMIUM_PERCENT';
                                  setStrategyConfig(prev => ({ 
                                    ...prev, 
                                    mtmStopLoss: { 
                                      type: newType as any,
                                      value: prev.mtmStopLoss.value
                                    }
                                  }));
                                }}
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
            
            {/* Sticky Footer Actions */}
            <div className="flex-shrink-0 sticky bottom-0 bg-white/95 dark:bg-gray-900/95 backdrop-blur-md border-t border-gray-200/50 dark:border-gray-700/50 p-4">
              <div className="flex items-center justify-between gap-3">
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
                    className="min-w-[80px]"
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleSubmit}
                    disabled={isSubmitting || legs.length === 0}
                    className="bg-blue-600 hover:bg-blue-700 text-white min-w-[120px]"
                  >
                    {isSubmitting ? 'Creating...' : 'Create Strategy'}
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default StrategyWizardDialog;