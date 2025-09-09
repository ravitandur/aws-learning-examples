import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import { 
  ArrowLeft, TrendingUp, TrendingDown, BarChart3, 
  Clock, Activity, Target, Shield,
  RefreshCw, Users
} from 'lucide-react';
import { Basket, BasketBrokerAllocation } from '../../types';

interface BasketPerformanceProps {
  basket: Basket & {
    allocations: BasketBrokerAllocation[];
    stats: {
      totalPnL: number;
      executionCount: number;
      lastExecution?: string;
      avgExecutionTime: number;
      successRate: number;
    };
    revolutionaryFeatures: {
      gsi2Optimized: boolean;
      multibrokerEnabled: boolean;
      timingPrecision: number;
      weekendProtected: boolean;
    };
  };
  onBack: () => void;
}

interface PerformanceData {
  dailyPnL: { date: string; pnl: number; executions: number }[];
  brokerPerformance: { 
    broker_id: string; 
    pnl: number; 
    executions: number; 
    successRate: number;
    avgExecutionTime: number;
  }[];
  strategyBreakdown: {
    strategyId: string;
    strategyName: string;
    pnl: number;
    executions: number;
    successRate: number;
  }[];
  revolutionaryMetrics: {
    gsi2QueryReduction: number;
    timingAccuracy: number;
    weekendBlocksCount: number;
    multiBrokerAdvantage: number;
  };
}

const BasketPerformance: React.FC<BasketPerformanceProps> = ({ basket, onBack }) => {
  const [performanceData, setPerformanceData] = useState<PerformanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTimeframe, setSelectedTimeframe] = useState<'1D' | '7D' | '30D' | '90D'>('7D');

  useEffect(() => {
    loadPerformanceData();
  }, [basket.basket_id, selectedTimeframe]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadPerformanceData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Mock performance data - replace with actual API calls
      const mockData: PerformanceData = {
        dailyPnL: generateDailyPnLData(selectedTimeframe),
        brokerPerformance: basket.allocations.map(allocation => ({
          broker_id: allocation.broker_id,
          pnl: Math.random() * 1000 - 200,
          executions: Math.floor(Math.random() * 20) + 5,
          successRate: Math.random() * 20 + 80,
          avgExecutionTime: Math.random() * 50 + 30
        })),
        strategyBreakdown: basket.strategies.map(strategy => ({
          strategyId: strategy.strategyId,
          strategyName: strategy.strategyName,
          pnl: Math.random() * 800 - 150,
          executions: Math.floor(Math.random() * 15) + 3,
          successRate: Math.random() * 15 + 85
        })),
        revolutionaryMetrics: {
          gsi2QueryReduction: 99.5,
          timingAccuracy: 99.8,
          weekendBlocksCount: Math.floor(Math.random() * 20) + 5,
          multiBrokerAdvantage: basket.allocations.length > 1 ? Math.random() * 15 + 10 : 0
        }
      };

      setPerformanceData(mockData);

    } catch (error: any) {
      console.error('Failed to load performance data:', error);
      setError('Failed to load performance data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const generateDailyPnLData = (timeframe: string) => {
    const days = timeframe === '1D' ? 1 : timeframe === '7D' ? 7 : timeframe === '30D' ? 30 : 90;
    const data = [];
    
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      data.push({
        date: date.toISOString().split('T')[0],
        pnl: Math.random() * 200 - 50,
        executions: Math.floor(Math.random() * 5) + 1
      });
    }
    
    return data;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="outline" onClick={onBack} leftIcon={<ArrowLeft className="h-4 w-4" />}>
            Back to Baskets
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Basket Performance Analytics</h1>
            <p className="text-gray-600 dark:text-gray-300">
              {basket.basket_name}
            </p>
          </div>
        </div>
        
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mr-3" />
          <span className="text-gray-600 dark:text-gray-400">Loading performance analytics...</span>
        </div>
      </div>
    );
  }

  if (error || !performanceData) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="outline" onClick={onBack} leftIcon={<ArrowLeft className="h-4 w-4" />}>
            Back to Baskets
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Basket Performance Analytics</h1>
            <p className="text-gray-600 dark:text-gray-300">
              {basket.basket_name}
            </p>
          </div>
        </div>
        
        <Card className="border-red-200 bg-red-50 dark:bg-red-900/20">
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-red-800 dark:text-red-200">{error || 'Failed to load performance data'}</p>
              <Button className="mt-4" onClick={loadPerformanceData}>
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const totalPnL = performanceData.dailyPnL.reduce((sum, day) => sum + day.pnl, 0);
  const totalExecutions = performanceData.dailyPnL.reduce((sum, day) => sum + day.executions, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="outline" onClick={onBack} leftIcon={<ArrowLeft className="h-4 w-4" />}>
            Back to Baskets
          </Button>
          <div>
            <h1 className="text-2xl font-bold">📊 Basket Performance Analytics</h1>
            <p className="text-gray-600 dark:text-gray-300">
              <span className="font-medium">{basket.basket_name}</span> • Revolutionary Features Active
            </p>
          </div>
        </div>
        
        {/* Timeframe Selector */}
        <div className="flex space-x-2">
          {(['1D', '7D', '30D', '90D'] as const).map(timeframe => (
            <Button
              key={timeframe}
              variant={selectedTimeframe === timeframe ? "primary" : "outline"}
              size="sm"
              onClick={() => setSelectedTimeframe(timeframe)}
            >
              {timeframe}
            </Button>
          ))}
        </div>
      </div>

      {/* Revolutionary Features Status */}
      <Card className="border-2 border-blue-500 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Revolutionary Features Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-white dark:bg-gray-800 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {performanceData.revolutionaryMetrics.gsi2QueryReduction}%
              </div>
              <div className="text-sm text-gray-600">GSI2 Query Reduction</div>
              <Badge variant="success" size="sm" className="mt-2">⚡ Active</Badge>
            </div>
            <div className="text-center p-4 bg-white dark:bg-gray-800 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {performanceData.revolutionaryMetrics.timingAccuracy}%
              </div>
              <div className="text-sm text-gray-600">Timing Accuracy</div>
              <Badge variant="success" size="sm" className="mt-2">🎯 0-Second</Badge>
            </div>
            <div className="text-center p-4 bg-white dark:bg-gray-800 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">
                {performanceData.revolutionaryMetrics.weekendBlocksCount}
              </div>
              <div className="text-sm text-gray-600">Weekend Blocks</div>
              <Badge variant="success" size="sm" className="mt-2">🛡️ Protected</Badge>
            </div>
            <div className="text-center p-4 bg-white dark:bg-gray-800 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {performanceData.revolutionaryMetrics.multiBrokerAdvantage.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Multi-Broker Advantage</div>
              <Badge variant={basket.allocations.length > 1 ? "info" : "default"} size="sm" className="mt-2">
                🏦 {basket.allocations.length > 1 ? 'Active' : 'Disabled'}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Key Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className={`text-2xl font-bold ${totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ₹{totalPnL.toFixed(2)}
                </div>
                <div className="text-sm text-gray-600">Total P&L ({selectedTimeframe})</div>
              </div>
              {totalPnL >= 0 ? 
                <TrendingUp className="h-8 w-8 text-green-600" /> : 
                <TrendingDown className="h-8 w-8 text-red-600" />
              }
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-blue-600">{totalExecutions}</div>
                <div className="text-sm text-gray-600">Total Executions</div>
              </div>
              <Activity className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-green-600">{basket.stats.successRate.toFixed(1)}%</div>
                <div className="text-sm text-gray-600">Success Rate</div>
              </div>
              <Target className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-purple-600">{basket.stats.avgExecutionTime.toFixed(0)}ms</div>
                <div className="text-sm text-gray-600">Avg Execution Time</div>
              </div>
              <Clock className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Daily P&L Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Daily P&L Trend ({selectedTimeframe})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {performanceData.dailyPnL.map((day, index) => (
              <div key={day.date} className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700">
                <div className="flex items-center space-x-4">
                  <div className="w-16 text-sm text-gray-600">
                    {new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </div>
                  <div className="flex-1">
                    <div className={`font-semibold ${day.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      ₹{day.pnl.toFixed(2)}
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-sm text-gray-600">{day.executions} executions</div>
                  <div className={`w-20 h-2 rounded ${day.pnl >= 0 ? 'bg-green-200' : 'bg-red-200'}`}>
                    <div 
                      className={`h-full rounded ${day.pnl >= 0 ? 'bg-green-600' : 'bg-red-600'}`}
                      style={{ width: `${Math.min(100, Math.abs(day.pnl) / 100 * 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Multi-Broker Performance */}
      {basket.allocations.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Multi-Broker Performance Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {performanceData.brokerPerformance.map(broker => (
                <div key={broker.broker_id} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <h4 className="font-semibold capitalize">{broker.broker_id}</h4>
                      <Badge variant={broker.pnl >= 0 ? 'success' : 'default'}>
                        {broker.pnl >= 0 ? '+' : ''}₹{broker.pnl.toFixed(2)}
                      </Badge>
                    </div>
                    <div className="text-sm text-gray-600">
                      {broker.executions} executions • {broker.successRate.toFixed(1)}% success
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-sm text-gray-600">Executions</div>
                      <div className="font-semibold">{broker.executions}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Success Rate</div>
                      <div className="font-semibold text-green-600">{broker.successRate.toFixed(1)}%</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Avg Speed</div>
                      <div className="font-semibold text-blue-600">{broker.avgExecutionTime.toFixed(0)}ms</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Strategy Performance Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Strategy Performance Breakdown
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {performanceData.strategyBreakdown.map(strategy => (
              <div key={strategy.strategyId} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div>
                  <div className="font-medium">{strategy.strategyName}</div>
                  <div className="text-sm text-gray-600">{strategy.executions} executions</div>
                </div>
                <div className="text-right">
                  <div className={`font-semibold ${strategy.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    ₹{strategy.pnl.toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-600">{strategy.successRate.toFixed(1)}% success</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Basket Configuration Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Basket Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <div className="text-sm text-gray-600">Status</div>
              <Badge variant={basket.status === 'ACTIVE' ? 'success' : 'default'}>
                {basket.status}
              </Badge>
            </div>
            <div>
              <div className="text-sm text-gray-600">Strategies</div>
              <div className="font-semibold">{basket.strategies.length}</div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Broker Allocations</div>
              <div className="font-semibold">{basket.allocations.length}</div>
            </div>
          </div>
          
          {basket.description && (
            <div>
              <div className="text-sm text-gray-600">Description</div>
              <div className="text-sm">{basket.description}</div>
            </div>
          )}

          <div>
            <div className="text-sm text-gray-600">Broker Allocation Details</div>
            <div className="mt-2 space-y-2">
              {basket.allocations.map(allocation => (
                <div key={`${allocation.broker_id}-${allocation.client_id}`} className="flex items-center justify-between text-sm">
                  <span className="capitalize">{allocation.broker_id} ({allocation.client_id})</span>
                  <Badge variant="info" size="sm">
                    {allocation.lot_multiplier}x multiplier
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex justify-center space-x-4">
        <Button onClick={loadPerformanceData} leftIcon={<RefreshCw className="h-4 w-4" />}>
          Refresh Data
        </Button>
        <Button variant="outline" onClick={onBack}>
          Back to Basket Management
        </Button>
      </div>
    </div>
  );
};

export default BasketPerformance;