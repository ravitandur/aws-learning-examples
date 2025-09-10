import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import { X, Plus, Trash2, Copy } from 'lucide-react';

interface StrategyLeg {
  id: string;
  index: string;
  optionType: 'CE' | 'PE';
  actionType: 'BUY' | 'SELL';
  strikePrice: number;
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
    instrumentMovePercentage: number;
    stopLossMovePercentage: number;
  };
}

interface StrategyWizardDialogProps {
  basketId: string;
  onClose: () => void;
  onSubmit: (strategyData: any) => void;
}

const StrategyWizardDialog: React.FC<StrategyWizardDialogProps> = ({ 
  basketId, 
  onClose, 
  onSubmit 
}) => {
  
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
    reEntryReExecute: false
  });

  const [legs, setLegs] = useState<StrategyLeg[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // ATM strike price calculation
  const getATMStrike = (index: string): number => {
    const atmValues = {
      'NIFTY': 21000,
      'BANKNIFTY': 45000,
      'FINNIFTY': 19500
    };
    return atmValues[index as keyof typeof atmValues] || 21000;
  };

  // Generate default strike price options (using ATM Point method)
  const generateStrikeOptions = (index: string): { value: string; label: string }[] => {
    const atmStrike = getATMStrike(index);
    const options = [];
    
    // ITM options (10 below ATM)
    for (let i = 10; i >= 1; i--) {
      const strike = atmStrike - (i * 50);
      options.push({ value: strike.toString(), label: `ITM${i} (${strike})` });
    }
    
    // ATM option
    options.push({ value: atmStrike.toString(), label: `ATM (${atmStrike})` });
    
    // OTM options (10 above ATM)
    for (let i = 1; i <= 10; i++) {
      const strike = atmStrike + (i * 50);
      options.push({ value: strike.toString(), label: `OTM${i} (${strike})` });
    }
    
    return options;
  };

  // Generate ATM percentage-based options
  const generatePercentageOptions = (index: string): { value: string; label: string }[] => {
    const atmStrike = getATMStrike(index);
    const options = [];
    
    // Negative percentages (below ATM)
    for (let i = -10; i < 0; i += 0.25) {
      const percentage = i.toFixed(2);
      const strike = Math.round(atmStrike * (1 + i / 100));
      options.push({ value: strike.toString(), label: `ATM${percentage}% (${strike})` });
    }
    
    // ATM (0%)
    options.push({ value: atmStrike.toString(), label: `ATM (${atmStrike})` });
    
    // Positive percentages (above ATM)
    for (let i = 0.25; i <= 10; i += 0.25) {
      const percentage = i.toFixed(2);
      const strike = Math.round(atmStrike * (1 + i / 100));
      options.push({ value: strike.toString(), label: `ATM+${percentage}% (${strike})` });
    }
    
    return options;
  };

  // Generate strike options based on selection method for a specific position
  const generatePositionStrikeOptions = (index: string, selectionMethod: string): { value: string; label: string }[] => {
    switch (selectionMethod) {
      case 'ATM_PERCENT':
        return generatePercentageOptions(index);
      case 'ATM_POINT':
      default:
        return generateStrikeOptions(index);
    }
  };

  // Add new position with default values
  const addPosition = () => {
    const atmStrike = getATMStrike(strategyIndex);
    const newLeg: StrategyLeg = {
      id: `leg-${Date.now()}`,
      index: strategyIndex,
      optionType: 'CE',
      actionType: 'BUY',
      strikePrice: atmStrike,
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
        instrumentMovePercentage: 0,
        stopLossMovePercentage: 0
      }
    };
    setLegs(prev => [...prev, newLeg]);
    setError(null);
  };

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

    setIsSubmitting(true);
    setError(null);

    try {
      const strategyData = {
        name: strategyName,
        index: strategyIndex,
        config: strategyConfig,
        legs: legs.map(leg => ({
          index: leg.index,
          optionType: leg.optionType,
          actionType: leg.actionType,
          strikePrice: leg.strikePrice,
          totalLots: leg.totalLots,
          expiryType: leg.expiryType,
          selectionMethod: leg.selectionMethod
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="w-full max-w-6xl">
        <Card className="h-[85vh] flex flex-col">
          <CardHeader className="flex-shrink-0 flex flex-row items-center justify-between pb-4 border-b">
            <CardTitle className="text-xl font-semibold">Strategy Creator</CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </CardHeader>

          <CardContent className="flex-1 overflow-hidden p-0">
            <div className="h-full flex flex-col">
              
              {/* Initial Layout - Strategy Name and Add Position Button */}
              <div className="bg-gray-50 dark:bg-gray-700/50 px-4 py-4 border-b border-gray-200 dark:border-gray-600">
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-200 mb-3">Strategy Creator</h4>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-end">
                  {/* Strategy Name - Column 1 */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                      Strategy Name
                    </label>
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
                      <span className="ml-3 text-sm text-gray-600 dark:text-gray-400">
                        {legs.length} position{legs.length !== 1 ? 's' : ''} added
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Header Section - Index and Checkboxes (Show only after first position) */}
              {legs.length > 0 && (
                <div className="bg-gray-50 dark:bg-gray-700/50 px-4 py-4 border-b border-gray-200 dark:border-gray-600">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-200 mb-3">Strategy Settings</h4>
                  
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
                          // Update all existing legs to use new index and recalculate strikes
                          const atmStrike = getATMStrike(e.target.value);
                          setLegs(prev => prev.map(leg => ({ 
                            ...leg, 
                            index: e.target.value,
                            strikePrice: atmStrike
                          })));
                        }}
                        options={[
                          { value: 'NIFTY', label: 'NIFTY' },
                          { value: 'BANKNIFTY', label: 'BANKNIFTY' },
                          { value: 'FINNIFTY', label: 'FINNIFTY' }
                        ]}
                        className="h-9 w-40"
                      />
                    </div>

                    {/* Trading Options Checkboxes - Right Side */}
                    <div className="flex items-center gap-6">
                      {/* Wait & Trade */}
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={strategyConfig.waitAndTrade}
                          onChange={(e) => setStrategyConfig(prev => ({ ...prev, waitAndTrade: e.target.checked }))}
                          className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
                        />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-200">Wait & Trade</span>
                      </label>

                      {/* Move SL to Cost */}
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={strategyConfig.moveSlToCost}
                          onChange={(e) => setStrategyConfig(prev => ({ ...prev, moveSlToCost: e.target.checked }))}
                          className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
                        />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-200">Move SL to Cost</span>
                      </label>

                      {/* Re Entry/Re Execute */}
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={strategyConfig.reEntryReExecute}
                          onChange={(e) => setStrategyConfig(prev => ({ ...prev, reEntryReExecute: e.target.checked }))}
                          className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
                        />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-200">Re Entry/Re Execute</span>
                      </label>
                    </div>
                  </div>
                </div>
              )}

              {/* Error Message */}
              {error && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3 mx-4 mt-4 rounded-lg">
                  <span className="text-sm text-red-800 dark:text-red-200">{error}</span>
                </div>
              )}

              {/* Positions List */}
              {legs.length > 0 && (
                <div className="flex-1 overflow-y-auto px-4 py-4">
                  <div className="space-y-4">
                    {legs.map((leg, index) => (
                    <div
                      key={leg.id}
                      className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden hover:shadow-md transition-shadow"
                    >
                      <div className="p-4">
                        {/* Position Header */}
                        <div className="flex items-center justify-between mb-4">
                          <h5 className="text-sm font-medium text-gray-900 dark:text-white">
                            Position {index + 1}
                          </h5>
                          <div className="flex items-center gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => copyPosition(leg.id)}
                              className="h-7 w-7 p-0"
                            >
                              <Copy className="h-3 w-3" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => removePosition(leg.id)}
                              className="h-7 w-7 p-0 text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
                            >
                              <Trash2 className="h-3 w-3" />
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
                                const atmStrike = getATMStrike(leg.index);
                                setLegs(prev => prev.map(l => 
                                  l.id === leg.id ? { 
                                    ...l, 
                                    selectionMethod: newMethod,
                                    strikePrice: atmStrike // Reset to ATM when method changes
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
                              value={leg.strikePrice.toString()}
                              onChange={(e) => {
                                const newStrikePrice = parseInt(e.target.value);
                                setLegs(prev => prev.map(l => 
                                  l.id === leg.id ? { ...l, strikePrice: newStrikePrice } : l
                                ));
                              }}
                              options={generatePositionStrikeOptions(leg.index, leg.selectionMethod)}
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
                          
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            
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
                                      setLegs(prev => prev.map(l => 
                                        l.id === leg.id ? { 
                                          ...l, 
                                          stopLoss: { ...l.stopLoss, type: e.target.value as 'POINTS' | 'PERCENTAGE' | 'RANGE' }
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
                                      setLegs(prev => prev.map(l => 
                                        l.id === leg.id ? { 
                                          ...l, 
                                          targetProfit: { ...l.targetProfit, type: e.target.value as 'POINTS' | 'PERCENTAGE' }
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
                                  <Input
                                    type="number"
                                    min="0"
                                    step="0.1"
                                    value={leg.trailingStopLoss.instrumentMovePercentage}
                                    onChange={(e) => {
                                      const value = parseFloat(e.target.value) || 0;
                                      setLegs(prev => prev.map(l => 
                                        l.id === leg.id ? { 
                                          ...l, 
                                          trailingStopLoss: { ...l.trailingStopLoss, instrumentMovePercentage: value }
                                        } : l
                                      ));
                                    }}
                                    placeholder="Instrument move %"
                                    className="h-8 text-sm"
                                  />
                                  <Input
                                    type="number"
                                    min="0"
                                    step="0.1"
                                    value={leg.trailingStopLoss.stopLossMovePercentage}
                                    onChange={(e) => {
                                      const value = parseFloat(e.target.value) || 0;
                                      setLegs(prev => prev.map(l => 
                                        l.id === leg.id ? { 
                                          ...l, 
                                          trailingStopLoss: { ...l.trailingStopLoss, stopLossMovePercentage: value }
                                        } : l
                                      ));
                                    }}
                                    placeholder="Stop loss move %"
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
                <div className="bg-gray-50 dark:bg-gray-700/50 px-4 py-4 border-t border-gray-200 dark:border-gray-600">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-200 mb-3">Strategy Configuration</h4>
                  
                  <div className="space-y-4">
                    {/* Range Breakout Checkbox */}
                    <div>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={strategyConfig.rangeBreakout}
                          onChange={(e) => setStrategyConfig(prev => ({ ...prev, rangeBreakout: e.target.checked }))}
                          className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
                        />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-200">Range Breakout</span>
                      </label>
                    </div>

                    {/* Entry Time and Exit Time in same row */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Entry Time */}
                      <div className="space-y-2">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                          Entry Time
                        </label>
                        <div className="grid grid-cols-2 gap-2">
                          <Select
                            value={strategyConfig.entryTimeHour}
                            onChange={(e) => setStrategyConfig(prev => ({ ...prev, entryTimeHour: e.target.value }))}
                            options={Array.from({ length: 24 }, (_, i) => ({ 
                              value: i.toString().padStart(2, '0'), 
                              label: i.toString().padStart(2, '0') 
                            }))}
                            className="text-sm"
                          />
                          <Select
                            value={strategyConfig.entryTimeMinute}
                            onChange={(e) => setStrategyConfig(prev => ({ ...prev, entryTimeMinute: e.target.value }))}
                            options={Array.from({ length: 60 }, (_, i) => ({ 
                              value: i.toString().padStart(2, '0'), 
                              label: i.toString().padStart(2, '0') 
                            }))}
                            className="text-sm"
                          />
                        </div>
                        
                        {/* Range Breakout Time - Show below entry time when checkbox is selected */}
                        {strategyConfig.rangeBreakout && (
                          <div className="mt-2">
                            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                              Range Exit Time
                            </label>
                            <div className="grid grid-cols-2 gap-2">
                              <Select
                                value={strategyConfig.rangeBreakoutTimeHour}
                                onChange={(e) => setStrategyConfig(prev => ({ ...prev, rangeBreakoutTimeHour: e.target.value }))}
                                options={Array.from({ length: 24 }, (_, i) => ({ 
                                  value: i.toString().padStart(2, '0'), 
                                  label: i.toString().padStart(2, '0') 
                                }))}
                                className="text-sm"
                              />
                              <Select
                                value={strategyConfig.rangeBreakoutTimeMinute}
                                onChange={(e) => setStrategyConfig(prev => ({ ...prev, rangeBreakoutTimeMinute: e.target.value }))}
                                options={Array.from({ length: 60 }, (_, i) => ({ 
                                  value: i.toString().padStart(2, '0'), 
                                  label: i.toString().padStart(2, '0') 
                                }))}
                                className="text-sm"
                              />
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Exit Time */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                          Exit Time
                        </label>
                        <div className="grid grid-cols-2 gap-2">
                          <Select
                            value={strategyConfig.exitTimeHour}
                            onChange={(e) => setStrategyConfig(prev => ({ ...prev, exitTimeHour: e.target.value }))}
                            options={Array.from({ length: 24 }, (_, i) => ({ 
                              value: i.toString().padStart(2, '0'), 
                              label: i.toString().padStart(2, '0') 
                            }))}
                            className="text-sm"
                          />
                          <Select
                            value={strategyConfig.exitTimeMinute}
                            onChange={(e) => setStrategyConfig(prev => ({ ...prev, exitTimeMinute: e.target.value }))}
                            options={Array.from({ length: 60 }, (_, i) => ({ 
                              value: i.toString().padStart(2, '0'), 
                              label: i.toString().padStart(2, '0') 
                            }))}
                            className="text-sm"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>

          {/* Action Buttons - Fixed at Bottom */}
          <div className="flex items-center gap-3 p-6 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={isSubmitting}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={legs.length === 0 || isSubmitting}
              className="flex-1 disabled:opacity-50"
            >
              {isSubmitting ? 'Adding Strategy...' : `Create Strategy (${legs.length} position${legs.length !== 1 ? 's' : ''})`}
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default StrategyWizardDialog;