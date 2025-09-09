import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Badge from '../ui/Badge';
import { 
  X, Zap, Plus, Minus, Target, AlertCircle, 
  TrendingUp, TrendingDown, Activity, Calendar,
  Eye, Settings
} from 'lucide-react';

interface StrategyLeg {
  id: string;
  instrument: 'CALL' | 'PUT';
  action: 'BUY' | 'SELL';
  strike: number;
  expiry: string;
  quantity: number;
  premium?: number;
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
  const [currentStep, setCurrentStep] = useState<'basic' | 'legs' | 'preview'>('basic');
  const [strategyName, setStrategyName] = useState('');
  const [strategyType, setStrategyType] = useState('CUSTOM');
  const [legs, setLegs] = useState<StrategyLeg[]>([
    {
      id: '1',
      instrument: 'CALL',
      action: 'BUY',
      strike: 0,
      expiry: '',
      quantity: 1
    }
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Strategy templates
  const strategyTemplates = [
    {
      type: 'IRON_CONDOR',
      name: 'Iron Condor',
      description: '4-leg strategy with limited risk and reward',
      legs: [
        { instrument: 'PUT' as const, action: 'SELL' as const, strike: 18000, quantity: 1 },
        { instrument: 'PUT' as const, action: 'BUY' as const, strike: 17800, quantity: 1 },
        { instrument: 'CALL' as const, action: 'SELL' as const, strike: 18200, quantity: 1 },
        { instrument: 'CALL' as const, action: 'BUY' as const, strike: 18400, quantity: 1 }
      ]
    },
    {
      type: 'BULL_CALL_SPREAD',
      name: 'Bull Call Spread',
      description: '2-leg bullish strategy',
      legs: [
        { instrument: 'CALL' as const, action: 'BUY' as const, strike: 18000, quantity: 1 },
        { instrument: 'CALL' as const, action: 'SELL' as const, strike: 18100, quantity: 1 }
      ]
    },
    {
      type: 'STRADDLE',
      name: 'Straddle',
      description: '2-leg volatility strategy',
      legs: [
        { instrument: 'CALL' as const, action: 'BUY' as const, strike: 18000, quantity: 1 },
        { instrument: 'PUT' as const, action: 'BUY' as const, strike: 18000, quantity: 1 }
      ]
    }
  ];

  const addLeg = () => {
    const newLeg: StrategyLeg = {
      id: String(legs.length + 1),
      instrument: 'CALL',
      action: 'BUY',
      strike: 0,
      expiry: '',
      quantity: 1
    };
    setLegs(prev => [...prev, newLeg]);
  };

  const removeLeg = (legId: string) => {
    if (legs.length > 1) {
      setLegs(prev => prev.filter(leg => leg.id !== legId));
    }
  };

  const updateLeg = (legId: string, field: keyof StrategyLeg, value: any) => {
    setLegs(prev => 
      prev.map(leg => 
        leg.id === legId ? { ...leg, [field]: value } : leg
      )
    );
  };

  const applyTemplate = (template: typeof strategyTemplates[0]) => {
    setStrategyType(template.type);
    setStrategyName(template.name);
    setLegs(template.legs.map((leg, index) => ({
      id: String(index + 1),
      instrument: leg.instrument,
      action: leg.action,
      strike: leg.strike,
      expiry: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 1 week from now
      quantity: leg.quantity
    })));
  };

  const validateBasicInfo = () => {
    return strategyName.trim().length > 0;
  };

  const validateLegs = () => {
    return legs.every(leg => 
      leg.strike > 0 && 
      leg.expiry !== '' && 
      leg.quantity > 0
    );
  };

  const handleSubmit = async () => {
    if (!validateBasicInfo() || !validateLegs()) {
      setError('Please fill in all required fields');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const strategyData = {
        name: strategyName.trim(),
        type: strategyType,
        legs: legs.map(leg => ({
          instrument: leg.instrument,
          action: leg.action,
          strike: leg.strike,
          expiry: leg.expiry,
          quantity: leg.quantity,
          premium: leg.premium
        }))
      };

      await onSubmit(strategyData);
      
    } catch (error: any) {
      console.error('Failed to create strategy:', error);
      setError(error.message || 'Failed to create strategy. Please try again.');
      setIsSubmitting(false);
    }
  };

  const getActionColor = (action: string) => {
    return action === 'BUY' ? 'text-green-600' : 'text-red-600';
  };

  const getInstrumentIcon = (instrument: string) => {
    return instrument === 'CALL' ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />;
  };

  const calculateNetPremium = () => {
    return legs.reduce((total, leg) => {
      const premium = leg.premium || 0;
      const multiplier = leg.action === 'BUY' ? -1 : 1;
      return total + (premium * leg.quantity * multiplier);
    }, 0);
  };

  const renderBasicStep = () => (
    <div className="space-y-6">
      
      {/* Strategy Name */}
      <div>
        <label className="block text-sm font-medium mb-2">
          Strategy Name *
        </label>
        <Input
          value={strategyName}
          onChange={(e) => setStrategyName(e.target.value)}
          placeholder="e.g., NIFTY Iron Condor Weekly"
          className="w-full"
          autoFocus
        />
      </div>

      {/* Strategy Type */}
      <div>
        <label className="block text-sm font-medium mb-2">
          Strategy Type
        </label>
        <select
          value={strategyType}
          onChange={(e) => setStrategyType(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700"
        >
          <option value="CUSTOM">Custom Strategy</option>
          <option value="IRON_CONDOR">Iron Condor</option>
          <option value="BULL_CALL_SPREAD">Bull Call Spread</option>
          <option value="BEAR_PUT_SPREAD">Bear Put Spread</option>
          <option value="STRADDLE">Straddle</option>
          <option value="STRANGLE">Strangle</option>
          <option value="BUTTERFLY">Butterfly</option>
        </select>
      </div>

      {/* Templates */}
      <div>
        <label className="block text-sm font-medium mb-3">
          Quick Templates
        </label>
        <div className="grid grid-cols-1 gap-3">
          {strategyTemplates.map(template => (
            <Card 
              key={template.type}
              className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              onClick={() => applyTemplate(template)}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">{template.name}</h4>
                    <p className="text-sm text-gray-600">{template.description}</p>
                  </div>
                  <Badge variant="info" size="sm">
                    {template.legs.length} legs
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );

  const renderLegsStep = () => (
    <div className="space-y-6">
      
      {/* Legs Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">Strategy Legs ({legs.length})</h3>
        <Button
          onClick={addLeg}
          leftIcon={<Plus className="h-4 w-4" />}
          size="sm"
        >
          Add Leg
        </Button>
      </div>

      {/* Legs List */}
      <div className="space-y-4">
        {legs.map((leg, index) => (
          <Card key={leg.id} className="border-l-4 border-l-blue-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <span className="font-medium">Leg {index + 1}</span>
                  {getInstrumentIcon(leg.instrument)}
                  <Badge 
                    variant={leg.action === 'BUY' ? 'success' : 'danger'} 
                    size="sm"
                  >
                    {leg.action}
                  </Badge>
                  <Badge variant="default" size="sm">
                    {leg.instrument}
                  </Badge>
                </div>
                {legs.length > 1 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeLeg(leg.id)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <Minus className="h-4 w-4" />
                  </Button>
                )}
              </div>

              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                
                {/* Instrument */}
                <div>
                  <label className="block text-xs font-medium mb-1">Instrument</label>
                  <select
                    value={leg.instrument}
                    onChange={(e) => updateLeg(leg.id, 'instrument', e.target.value)}
                    className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700"
                  >
                    <option value="CALL">Call</option>
                    <option value="PUT">Put</option>
                  </select>
                </div>

                {/* Action */}
                <div>
                  <label className="block text-xs font-medium mb-1">Action</label>
                  <select
                    value={leg.action}
                    onChange={(e) => updateLeg(leg.id, 'action', e.target.value)}
                    className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700"
                  >
                    <option value="BUY">Buy</option>
                    <option value="SELL">Sell</option>
                  </select>
                </div>

                {/* Strike */}
                <div>
                  <label className="block text-xs font-medium mb-1">Strike</label>
                  <Input
                    type="number"
                    value={leg.strike || ''}
                    onChange={(e) => updateLeg(leg.id, 'strike', parseInt(e.target.value) || 0)}
                    placeholder="18000"
                    className="text-sm"
                  />
                </div>

                {/* Expiry */}
                <div>
                  <label className="block text-xs font-medium mb-1">Expiry</label>
                  <Input
                    type="date"
                    value={leg.expiry}
                    onChange={(e) => updateLeg(leg.id, 'expiry', e.target.value)}
                    className="text-sm"
                  />
                </div>

                {/* Quantity */}
                <div>
                  <label className="block text-xs font-medium mb-1">Quantity</label>
                  <Input
                    type="number"
                    value={leg.quantity || ''}
                    onChange={(e) => updateLeg(leg.id, 'quantity', parseInt(e.target.value) || 1)}
                    min="1"
                    className="text-sm"
                  />
                </div>
              </div>

              {/* Optional Premium */}
              <div className="mt-3">
                <label className="block text-xs font-medium mb-1">Premium (Optional)</label>
                <Input
                  type="number"
                  step="0.01"
                  value={leg.premium || ''}
                  onChange={(e) => updateLeg(leg.id, 'premium', parseFloat(e.target.value) || undefined)}
                  placeholder="0.00"
                  className="w-32 text-sm"
                />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderPreviewStep = () => (
    <div className="space-y-6">
      
      {/* Strategy Summary */}
      <Card className="bg-blue-50 dark:bg-blue-900/20 border-blue-200">
        <CardContent className="p-4">
          <div className="flex items-center gap-3 mb-3">
            <Target className="h-6 w-6 text-blue-600" />
            <div>
              <h3 className="text-lg font-medium">{strategyName}</h3>
              <Badge variant="info">{strategyType}</Badge>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600">{legs.length}</div>
              <div className="text-sm text-gray-600">Legs</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">
                ₹{calculateNetPremium().toFixed(2)}
              </div>
              <div className="text-sm text-gray-600">Net Premium</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">
                {legs.reduce((sum, leg) => sum + leg.quantity, 0)}
              </div>
              <div className="text-sm text-gray-600">Total Qty</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Legs Summary */}
      <div>
        <h4 className="font-medium mb-3">Strategy Breakdown</h4>
        <div className="space-y-2">
          {legs.map((leg, index) => (
            <div 
              key={leg.id}
              className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium">Leg {index + 1}</span>
                <div className="flex items-center gap-2">
                  <span className={`font-medium ${getActionColor(leg.action)}`}>
                    {leg.action}
                  </span>
                  <span>{leg.quantity}x</span>
                  <span className="font-medium">{leg.instrument}</span>
                  <span>@ {leg.strike}</span>
                </div>
              </div>
              <div className="text-sm text-gray-600">
                Exp: {new Date(leg.expiry).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Risk Disclaimer */}
      <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
          <div>
            <h4 className="font-medium text-yellow-800 dark:text-yellow-200">
              Risk Disclaimer
            </h4>
            <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
              Options trading involves substantial risk. Please ensure you understand 
              the risks before executing this strategy. Past performance is not indicative 
              of future results.
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl mx-4 max-h-[90vh] flex flex-col">
        <Card className="border-0 shadow-none flex-1 flex flex-col">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5" />
                Strategy Wizard
              </CardTitle>
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
            
            {/* Step Indicator */}
            <div className="flex items-center gap-4 mt-4">
              {[
                { key: 'basic', label: 'Basic Info', icon: Settings },
                { key: 'legs', label: 'Configure Legs', icon: Activity },
                { key: 'preview', label: 'Preview', icon: Eye }
              ].map((step, index) => {
                const Icon = step.icon;
                const isCurrent = currentStep === step.key;
                const isCompleted = 
                  (step.key === 'basic' && (currentStep === 'legs' || currentStep === 'preview')) ||
                  (step.key === 'legs' && currentStep === 'preview');
                
                return (
                  <div key={step.key} className="flex items-center gap-2">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      isCurrent ? 'bg-blue-600 text-white' :
                      isCompleted ? 'bg-green-600 text-white' :
                      'bg-gray-200 dark:bg-gray-700 text-gray-500'
                    }`}>
                      <Icon className="h-4 w-4" />
                    </div>
                    <span className={`text-sm ${
                      isCurrent ? 'font-medium text-blue-600' :
                      isCompleted ? 'text-green-600' :
                      'text-gray-500'
                    }`}>
                      {step.label}
                    </span>
                    {index < 2 && (
                      <div className={`w-8 h-0.5 ${
                        isCompleted ? 'bg-green-600' : 'bg-gray-300 dark:bg-gray-600'
                      }`} />
                    )}
                  </div>
                );
              })}
            </div>
          </CardHeader>

          <CardContent className="flex-1 overflow-y-auto">
            
            {/* Error Message */}
            {error && (
              <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg mb-4">
                <AlertCircle className="h-4 w-4 text-red-600" />
                <span className="text-sm text-red-800 dark:text-red-200">{error}</span>
              </div>
            )}

            {/* Step Content */}
            {currentStep === 'basic' && renderBasicStep()}
            {currentStep === 'legs' && renderLegsStep()}
            {currentStep === 'preview' && renderPreviewStep()}
          </CardContent>

          {/* Footer */}
          <div className="p-6 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <Button
                variant="outline"
                onClick={() => {
                  if (currentStep === 'legs') setCurrentStep('basic');
                  else if (currentStep === 'preview') setCurrentStep('legs');
                }}
                disabled={currentStep === 'basic' || isSubmitting}
              >
                Previous
              </Button>

              <div className="flex items-center gap-3">
                <Button
                  variant="outline"
                  onClick={onClose}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                
                {currentStep === 'preview' ? (
                  <Button
                    onClick={handleSubmit}
                    disabled={isSubmitting || !validateBasicInfo() || !validateLegs()}
                    leftIcon={<Target className="h-4 w-4" />}
                  >
                    {isSubmitting ? 'Adding Strategy...' : 'Add Strategy'}
                  </Button>
                ) : (
                  <Button
                    onClick={() => {
                      if (currentStep === 'basic' && validateBasicInfo()) {
                        setCurrentStep('legs');
                      } else if (currentStep === 'legs' && validateLegs()) {
                        setCurrentStep('preview');
                      } else {
                        setError('Please complete all required fields');
                      }
                    }}
                    disabled={
                      (currentStep === 'basic' && !validateBasicInfo()) ||
                      (currentStep === 'legs' && !validateLegs())
                    }
                  >
                    Next
                  </Button>
                )}
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default StrategyWizardDialog;