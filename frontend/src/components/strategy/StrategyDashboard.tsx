import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import Badge from '../ui/Badge';

interface Strategy {
  strategyId: string;
  strategyName: string;
  strategyType: string;
  underlyingSymbol: string;
  status: 'ACTIVE' | 'PAUSED' | 'COMPLETED';
  brokerAllocations: {
    brokerId: string;
    brokerName: string;
    totalLots: number;
  }[];
  performance: {
    pnl: number;
    executionCount: number;
    lastExecution?: string;
  };
  revolutionaryFeatures: {
    gsi2Optimized: boolean;
    multibrokerEnabled: boolean;
    timingPrecision: number;
    weekendProtected: boolean;
  };
}

const StrategyDashboard: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [performanceMetrics, setPerformanceMetrics] = useState({
    totalStrategies: 0,
    activeStrategies: 0,
    totalPnL: 0,
    avgQueryTime: 0,
    weekendBlocks: 0
  });

  useEffect(() => {
    // Mock data - replace with API calls
    setStrategies([
      {
        strategyId: 'strategy-001',
        strategyName: 'Iron Condor Multi-Broker',
        strategyType: 'IRON_CONDOR',
        underlyingSymbol: 'NIFTY',
        status: 'ACTIVE',
        brokerAllocations: [
          { brokerId: 'zerodha', brokerName: 'Zerodha', totalLots: 3 },
          { brokerId: 'angel_one', brokerName: 'Angel One', totalLots: 2 }
        ],
        performance: {
          pnl: 1250.50,
          executionCount: 15,
          lastExecution: '2024-01-15T14:30:00Z'
        },
        revolutionaryFeatures: {
          gsi2Optimized: true,
          multibrokerEnabled: true,
          timingPrecision: 0.2,
          weekendProtected: true
        }
      }
    ]);

    setPerformanceMetrics({
      totalStrategies: 5,
      activeStrategies: 3,
      totalPnL: 3250.75,
      avgQueryTime: 45, // milliseconds
      weekendBlocks: 12 // weekend execution attempts blocked
    });
  }, []);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Revolutionary Performance Metrics */}
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-green-600">
              {performanceMetrics.totalStrategies}
            </div>
            <p className="text-sm text-gray-600">Total Strategies</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-blue-600">
              ₹{performanceMetrics.totalPnL.toFixed(2)}
            </div>
            <p className="text-sm text-gray-600">Total P&L</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-purple-600">
              {performanceMetrics.avgQueryTime}ms
            </div>
            <p className="text-sm text-gray-600">Avg Query Time (GSI2)</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-red-600">
              {performanceMetrics.weekendBlocks}
            </div>
            <p className="text-sm text-gray-600">Weekend Blocks</p>
          </CardContent>
        </Card>
      </div>

      {/* Revolutionary Features Status */}
      <Card className="bg-gradient-to-r from-blue-50 to-purple-50">
        <CardHeader>
          <CardTitle>Features Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-sm font-medium text-gray-500 mb-2">GSI2</div>
              <div className="font-semibold text-green-600">GSI2 Optimization</div>
              <div className="text-sm text-gray-600">99.5% Reduction</div>
            </div>
            <div className="text-center">
              <div className="text-sm font-medium text-gray-500 mb-2">Multi-Broker</div>
              <div className="font-semibold text-blue-600">Multi-Broker</div>
              <div className="text-sm text-gray-600">5 Brokers Active</div>
            </div>
            <div className="text-center">
              <div className="text-sm font-medium text-gray-500 mb-2">Timing</div>
              <div className="font-semibold text-purple-600">0-Second Timing</div>
              <div className="text-sm text-gray-600">Institutional Grade</div>
            </div>
            <div className="text-center">
              <div className="text-sm font-medium text-gray-500 mb-2">Weekend Safe</div>
              <div className="font-semibold text-green-600">Weekend Shield</div>
              <div className="text-sm text-gray-600">100% Protection</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Strategy List */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Active Strategies</h2>
        
        {strategies.map(strategy => (
          <Card key={strategy.strategyId} className="border-l-4 border-l-blue-500">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg">{strategy.strategyName}</CardTitle>
                  <p className="text-sm text-gray-600">
                    {strategy.strategyType} • {strategy.underlyingSymbol}
                  </p>
                </div>
                <Badge 
                  variant={strategy.status === 'ACTIVE' ? 'success' : 'default'}
                >
                  {strategy.status}
                </Badge>
              </div>
            </CardHeader>
            
            <CardContent className="space-y-4">
              {/* Performance Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <div className="text-sm text-gray-600">P&L</div>
                  <div className={`font-semibold ${strategy.performance.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    ₹{strategy.performance.pnl.toFixed(2)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Executions</div>
                  <div className="font-semibold">{strategy.performance.executionCount}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Last Execution</div>
                  <div className="font-semibold text-sm">
                    {strategy.performance.lastExecution ? 
                      new Date(strategy.performance.lastExecution).toLocaleString() : 
                      'Never'
                    }
                  </div>
                </div>
              </div>

              {/* Revolutionary Multi-Broker Allocation */}
              <div>
                <div className="text-sm font-medium text-gray-700 mb-2">
                  Multi-Broker Allocation
                </div>
                <div className="flex flex-wrap gap-2">
                  {strategy.brokerAllocations.map(allocation => (
                    <Badge key={allocation.brokerId} variant="info">
                      {allocation.brokerName}: {allocation.totalLots} lots
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Revolutionary Features Status */}
              <div>
                <div className="text-sm font-medium text-gray-700 mb-2">
                  Active Features
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge 
                    variant={strategy.revolutionaryFeatures.gsi2Optimized ? 'success' : 'default'}
                  >
                    GSI2 Optimized
                  </Badge>
                  <Badge 
                    variant={strategy.revolutionaryFeatures.multibrokerEnabled ? 'info' : 'default'}
                  >
                    Multi-Broker
                  </Badge>
                  <Badge 
                    variant={strategy.revolutionaryFeatures.timingPrecision < 1 ? 'success' : 'default'}
                  >
                    {strategy.revolutionaryFeatures.timingPrecision}s Precision
                  </Badge>
                  <Badge 
                    variant={strategy.revolutionaryFeatures.weekendProtected ? 'success' : 'default'}
                  >
                    Weekend Protected
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default StrategyDashboard;