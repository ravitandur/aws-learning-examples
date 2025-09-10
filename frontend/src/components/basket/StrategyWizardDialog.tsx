import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/Table';
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
  const [selectionMethod, setSelectionMethod] = useState<'ATM_POINT' | 'ATM_PERCENT' | 'CLOSEST_PREMIUM' | 'CLOSEST_STRADDLE_PREMIUM'>('ATM_POINT');
  
  const [strategyName, setStrategyName] = useState('');
  const [formData, setFormData] = useState({
    index: 'NIFTY',
    optionType: 'CE' as 'CE' | 'PE',
    actionType: 'BUY' as 'BUY' | 'SELL',
    strikePrice: '',
    totalLots: '1',
    expiryType: 'weekly' as 'weekly' | 'monthly'
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

  // Generate strike price options for new positions (based on selection method)
  const generateStrikeOptions = (index: string): { value: string; label: string }[] => {
    const atmStrike = getATMStrike(index);
    const options = [];
    
    if (selectionMethod === 'ATM_PERCENT') {
      // ATM Percent method: ATM + 0.25% to 10% on top, ATM - 0.25% to -10% on bottom
      // Add positive percentages (above ATM) - +10% to +0.25%
      for (let i = 10; i >= 0.25; i -= 0.25) {
        const strike = Math.round(atmStrike * (1 + i / 100));
        options.push({ value: strike.toString(), label: `ATM+${i}%` });
      }
      
      // Add ATM (middle)
      options.push({ value: atmStrike.toString(), label: 'ATM' });
      
      // Add negative percentages (below ATM) - -0.25% to -10%
      for (let i = 0.25; i <= 10; i += 0.25) {
        const strike = Math.round(atmStrike * (1 - i / 100));
        options.push({ value: strike.toString(), label: `ATM-${i}%` });
      }
    } else {
      // Default ATM Point method: OTM/ITM labels
      const strikeInterval = index === 'BANKNIFTY' ? 100 : 50;
      
      // Add OTM options (above ATM) - OTM10 to OTM1
      for (let i = 10; i >= 1; i--) {
        const strike = atmStrike + (i * strikeInterval);
        options.push({ value: strike.toString(), label: `OTM${i}` });
      }
      
      // Add ATM (middle)
      options.push({ value: atmStrike.toString(), label: 'ATM' });
      
      // Add ITM options (below ATM) - ITM1 to ITM10
      for (let i = 1; i <= 10; i++) {
        const strike = atmStrike - (i * strikeInterval);
        options.push({ value: strike.toString(), label: `ITM${i}` });
      }
    }
    
    return options;
  };

  // Generate strike price options for individual positions based on their selection method
  const generatePositionStrikeOptions = (index: string, positionSelectionMethod: 'ATM_POINT' | 'ATM_PERCENT' | 'CLOSEST_PREMIUM' | 'CLOSEST_STRADDLE_PREMIUM'): { value: string; label: string }[] => {
    const atmStrike = getATMStrike(index);
    const options = [];
    
    if (positionSelectionMethod === 'ATM_PERCENT') {
      // ATM Percent method: ATM + 0.25% to 10% on top, ATM - 0.25% to -10% on bottom
      // Add positive percentages (above ATM) - +10% to +0.25%
      for (let i = 10; i >= 0.25; i -= 0.25) {
        const strike = Math.round(atmStrike * (1 + i / 100));
        options.push({ value: strike.toString(), label: `ATM+${i}%` });
      }
      
      // Add ATM (middle)
      options.push({ value: atmStrike.toString(), label: 'ATM' });
      
      // Add negative percentages (below ATM) - -0.25% to -10%
      for (let i = 0.25; i <= 10; i += 0.25) {
        const strike = Math.round(atmStrike * (1 - i / 100));
        options.push({ value: strike.toString(), label: `ATM-${i}%` });
      }
    } else {
      // Default ATM Point method: OTM/ITM labels
      const strikeInterval = index === 'BANKNIFTY' ? 100 : 50;
      
      // Add OTM options (above ATM) - OTM10 to OTM1
      for (let i = 10; i >= 1; i--) {
        const strike = atmStrike + (i * strikeInterval);
        options.push({ value: strike.toString(), label: `OTM${i}` });
      }
      
      // Add ATM (middle)
      options.push({ value: atmStrike.toString(), label: 'ATM' });
      
      // Add ITM options (below ATM) - ITM1 to ITM10
      for (let i = 1; i <= 10; i++) {
        const strike = atmStrike - (i * strikeInterval);
        options.push({ value: strike.toString(), label: `ITM${i}` });
      }
    }
    
    return options;
  };

  // Initialize strike price when index changes
  React.useEffect(() => {
    if (!formData.strikePrice) {
      setFormData(prev => ({ ...prev, strikePrice: getATMStrike(prev.index).toString() }));
    }
  }, [formData.index]);

  // Reset strike price when selection method changes
  React.useEffect(() => {
    setFormData(prev => ({ ...prev, strikePrice: getATMStrike(prev.index).toString() }));
  }, [selectionMethod, formData.index]);

  const validateInputs = (): string | null => {
    if (!formData.index || !formData.optionType || !formData.actionType) {
      return 'Please select all required fields';
    }
    
    if (!formData.strikePrice) {
      return 'Please select a strike price';
    }
    
    if (parseInt(formData.totalLots) < 1) {
      return 'Total lots must be at least 1';
    }
    
    return null;
  };

  const addPosition = () => {
    const validationError = validateInputs();
    if (validationError) {
      setError(validationError);
      return;
    }

    const newLeg: StrategyLeg = {
      id: `leg-${Date.now()}`,
      index: formData.index,
      optionType: formData.optionType,
      actionType: formData.actionType,
      strikePrice: parseInt(formData.strikePrice),
      totalLots: parseInt(formData.totalLots),
      expiryType: formData.expiryType,
      selectionMethod: selectionMethod
    };

    setLegs(prev => [...prev, newLeg]);
    setError(null);
    
    // Reset form for next leg
    setFormData(prev => ({
      ...prev,
      optionType: 'CE',
      actionType: 'BUY',
      totalLots: '1'
    }));
  };

  const removeLeg = (id: string) => {
    setLegs(prev => prev.filter(leg => leg.id !== id));
  };

  const copyLeg = (leg: StrategyLeg) => {
    const copiedLeg: StrategyLeg = {
      ...leg,
      id: `leg-${Date.now()}`
    };
    setLegs(prev => [...prev, copiedLeg]);
  };

  const handleSubmit = async () => {
    if (!strategyName.trim()) {
      setError('Please enter a strategy name');
      return;
    }

    if (legs.length === 0) {
      setError('Please add at least one position');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const strategyData = {
        name: strategyName.trim(),
        basketId,
        selectionMethod,
        legs: legs.map(leg => ({
          index: leg.index,
          optionType: leg.optionType,
          actionType: leg.actionType,
          strikePrice: leg.strikePrice,
          totalLots: leg.totalLots,
          expiryType: leg.expiryType
        }))
      };

      await onSubmit(strategyData);
      
    } catch (error: any) {
      console.error('Failed to create strategy:', error);
      setError(error.message || 'Failed to create strategy. Please try again.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-5xl h-[85vh] flex flex-col">
        <Card className="border-0 shadow-none h-full flex flex-col">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <CardTitle className="text-2xl font-bold">Add Strategy</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                disabled={isSubmitting}
                className="h-8 w-8 p-0"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>

          <CardContent className="flex-1 overflow-y-auto space-y-6 px-6 py-6">
            
            {/* Strategy Name Input */}
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-200">
                Strategy Name *
              </label>
              <Input
                value={strategyName}
                onChange={(e) => setStrategyName(e.target.value)}
                placeholder="e.g., NIFTY Iron Condor Weekly"
                className="w-full"
                autoFocus
              />
              <p className="text-xs text-gray-500 mt-1">
                Enter a descriptive name for your strategy
              </p>
            </div>

            {/* Selection Method Radio Buttons */}
            <div>
              <label className="block text-sm font-medium mb-3 text-gray-700 dark:text-gray-200">
                Selection Method
              </label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { value: 'ATM_POINT', label: 'ATM Point' },
                  { value: 'ATM_PERCENT', label: 'ATM Percent' },
                  { value: 'CLOSEST_PREMIUM', label: 'Closest Premium' },
                  { value: 'CLOSEST_STRADDLE_PREMIUM', label: 'Closest Straddle Premium' }
                ].map((method) => (
                  <label key={method.value} className="flex items-center gap-2 cursor-pointer p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                    <input
                      type="radio"
                      name="selectionMethod"
                      value={method.value}
                      checked={selectionMethod === method.value}
                      onChange={(e) => setSelectionMethod(e.target.value as any)}
                      className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
                    />
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{method.label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Position Configuration Form */}
            <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-200">
                    Index Selection
                  </label>
                  <Select
                    value={formData.index}
                    onChange={(e) => {
                      const newIndex = e.target.value;
                      setFormData(prev => ({
                        ...prev,
                        index: newIndex,
                        strikePrice: getATMStrike(newIndex).toString()
                      }));
                    }}
                    options={[
                      { value: 'NIFTY', label: 'NIFTY' },
                      { value: 'BANKNIFTY', label: 'BANKNIFTY' },
                      { value: 'FINNIFTY', label: 'FINNIFTY' }
                    ]}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-200">
                    Option Type
                  </label>
                  <Select
                    value={formData.optionType}
                    onChange={(e) => setFormData(prev => ({ ...prev, optionType: e.target.value as 'CE' | 'PE' }))}
                    options={[
                      { value: 'CE', label: 'CE' },
                      { value: 'PE', label: 'PE' }
                    ]}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-200">
                    Action Type
                  </label>
                  <Select
                    value={formData.actionType}
                    onChange={(e) => setFormData(prev => ({ ...prev, actionType: e.target.value as 'BUY' | 'SELL' }))}
                    options={[
                      { value: 'BUY', label: 'BUY' },
                      { value: 'SELL', label: 'SELL' }
                    ]}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-200">
                    Strike Price
                  </label>
                  <Select
                    value={formData.strikePrice}
                    onChange={(e) => setFormData(prev => ({ ...prev, strikePrice: e.target.value }))}
                    options={generateStrikeOptions(formData.index)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-200">
                    Total Lots
                  </label>
                  <Input
                    type="number"
                    min="1"
                    value={formData.totalLots}
                    onChange={(e) => setFormData(prev => ({ ...prev, totalLots: e.target.value }))}
                    placeholder="1"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-200">
                    Expiry Type
                  </label>
                  <Select
                    value={formData.expiryType}
                    onChange={(e) => setFormData(prev => ({ ...prev, expiryType: e.target.value as 'weekly' | 'monthly' }))}
                    options={[
                      { value: 'weekly', label: 'Weekly' },
                      { value: 'monthly', label: 'Monthly' }
                    ]}
                  />
                </div>
              </div>

              {/* Error Message */}
              {error && (
                <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <span className="text-sm text-red-800 dark:text-red-200">{error}</span>
                </div>
              )}

              {/* Add Position Button */}
              <div className="mt-6">
                <Button onClick={addPosition} className="flex items-center gap-2">
                  <Plus className="h-4 w-4" />
                  Add Position
                </Button>
              </div>
            </div>

            {/* Strategy Positions - Row Wizard Format */}
            {legs.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
                  Strategy Positions ({legs.length})
                </h3>
                <div className="space-y-3">
                  {legs.map((leg, index) => (
                    <div
                      key={leg.id}
                      className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                    >
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-gray-500 dark:text-gray-400">
                          Position {index + 1}
                        </span>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => copyLeg(leg)}
                            className="h-8 w-8 p-0 text-gray-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20"
                            title="Copy position"
                          >
                            <Copy className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeLeg(leg.id)}
                            className="h-8 w-8 p-0 text-gray-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                            title="Delete position"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>

                      <div className="space-y-4">
                        {/* Selection Method Radio Buttons */}
                        <div>
                          <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                            Selection Method
                          </label>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                            {[
                              { value: 'ATM_POINT', label: 'ATM Point' },
                              { value: 'ATM_PERCENT', label: 'ATM Percent' },
                              { value: 'CLOSEST_PREMIUM', label: 'Closest Premium' },
                              { value: 'CLOSEST_STRADDLE_PREMIUM', label: 'Closest Straddle Premium' }
                            ].map((method) => (
                              <label key={method.value} className="flex items-center gap-1 cursor-pointer p-2 border border-gray-200 dark:border-gray-700 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors text-xs">
                                <input
                                  type="radio"
                                  name={`selectionMethod-${leg.id}`}
                                  value={method.value}
                                  checked={leg.selectionMethod === method.value}
                                  onChange={(e) => {
                                    const newSelectionMethod = e.target.value as 'ATM_POINT' | 'ATM_PERCENT' | 'CLOSEST_PREMIUM' | 'CLOSEST_STRADDLE_PREMIUM';
                                    setLegs(prev => prev.map(l => 
                                      l.id === leg.id ? { ...l, selectionMethod: newSelectionMethod } : l
                                    ));
                                  }}
                                  className="h-3 w-3 text-blue-600 border-gray-300 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
                                />
                                <span className="text-xs font-medium text-gray-700 dark:text-gray-300">{method.label}</span>
                              </label>
                            ))}
                          </div>
                        </div>

                        {/* Other fields in grid */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
                          
                          {/* Index Display */}
                          <div>
                            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                              Index
                            </label>
                            <div className="px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded-md text-sm font-medium">
                              {leg.index}
                            </div>
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

                          {/* Switchable Transaction Type */}
                          <div>
                            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                              Transaction
                            </label>
                            <Select
                              value={leg.actionType}
                              onChange={(e) => {
                                const newActionType = e.target.value as 'BUY' | 'SELL';
                                setLegs(prev => prev.map(l => 
                                  l.id === leg.id ? { ...l, actionType: newActionType } : l
                                ));
                              }}
                              options={[
                                { value: 'BUY', label: 'BUY' },
                                { value: 'SELL', label: 'SELL' }
                              ]}
                              className="h-9 text-sm"
                            />
                          </div>

                          {/* Strike Selection */}
                          <div>
                            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                              Strike
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

                          {/* Switchable Call Type */}
                          <div>
                            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                              Option Type
                            </label>
                            <Select
                              value={leg.optionType}
                              onChange={(e) => {
                                const newOptionType = e.target.value as 'CE' | 'PE';
                                setLegs(prev => prev.map(l => 
                                  l.id === leg.id ? { ...l, optionType: newOptionType } : l
                                ));
                              }}
                              options={[
                                { value: 'CE', label: 'CE' },
                                { value: 'PE', label: 'PE' }
                              ]}
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
                      </div>

                      {/* Position Summary */}
                      <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-600">
                        <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-300">
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                            leg.actionType === 'BUY'
                              ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400'
                              : 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400'
                          }`}>
                            {leg.actionType}
                          </span>
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                            leg.optionType === 'CE' 
                              ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                              : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                          }`}>
                            {leg.optionType}
                          </span>
                          <span className="font-mono font-medium">{leg.strikePrice}</span>
                          <span>{leg.totalLots} lot{leg.totalLots !== 1 ? 's' : ''}</span>
                          <span className="capitalize">{leg.expiryType}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
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