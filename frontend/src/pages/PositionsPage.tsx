/**
 * Positions Page
 * Displays current positions with real-time P&L and square-off functionality
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  RefreshCw,
  TrendingUp,
  TrendingDown,
  XCircle,
  Target,
  DollarSign,
  BarChart2,
  ArrowUpRight,
  ArrowDownRight,
  AlertTriangle,
} from 'lucide-react';
import tradingService from '../services/tradingService';
import {
  Position,
  TradingMode,
  PositionFilters,
  formatCurrency,
  formatPercentage,
  getPnLColor,
  getPositionSide,
} from '../types/trading';

const PositionsPage: React.FC = () => {
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // Filters
  const [modeFilter, setModeFilter] = useState<TradingMode | ''>('');
  const [showClosedPositions, setShowClosedPositions] = useState(false);

  // Summary
  const [summary, setSummary] = useState({
    totalPnl: 0,
    totalDayPnl: 0,
    openPositions: 0,
  });

  // Square-off dialog
  const [squareOffPosition, setSquareOffPosition] = useState<Position | null>(null);
  const [squareOffLoading, setSquareOffLoading] = useState(false);

  const fetchPositions = useCallback(async () => {
    try {
      setError(null);
      const filters: PositionFilters = {};
      if (modeFilter) filters.tradingMode = modeFilter;
      if (!showClosedPositions) filters.status = 'OPEN';

      const [positionsData, summaryData] = await Promise.all([
        tradingService.getPositions(filters),
        tradingService.getPositionSummary(filters),
      ]);

      setPositions(positionsData);
      setSummary(summaryData);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch positions');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [modeFilter, showClosedPositions]);

  useEffect(() => {
    fetchPositions();
    // Auto-refresh every 30 seconds for live positions
    const interval = setInterval(fetchPositions, 30000);
    return () => clearInterval(interval);
  }, [fetchPositions]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchPositions();
  };

  const handleSquareOff = async () => {
    if (!squareOffPosition) return;

    setSquareOffLoading(true);
    try {
      await tradingService.squareOffPosition(squareOffPosition.positionId);
      setSquareOffPosition(null);
      fetchPositions();
    } catch (err: any) {
      setError(err.message || 'Failed to square off position');
    } finally {
      setSquareOffLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Positions</h1>
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-2 text-gray-600 dark:text-gray-400">Loading positions...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Positions</h1>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <XCircle className="h-5 w-5 text-red-600" />
            <span className="text-red-800 dark:text-red-200">{error}</span>
          </div>
        </div>
      )}

      {/* P&L Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total P&L</p>
              <p className={`text-2xl font-bold ${getPnLColor(summary.totalPnl)}`}>
                {formatCurrency(summary.totalPnl)}
              </p>
            </div>
            <div className={`p-3 rounded-full ${summary.totalPnl >= 0 ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30'}`}>
              {summary.totalPnl >= 0 ? (
                <TrendingUp className="w-6 h-6 text-green-600 dark:text-green-400" />
              ) : (
                <TrendingDown className="w-6 h-6 text-red-600 dark:text-red-400" />
              )}
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Day P&L</p>
              <p className={`text-2xl font-bold ${getPnLColor(summary.totalDayPnl)}`}>
                {formatCurrency(summary.totalDayPnl)}
              </p>
            </div>
            <div className={`p-3 rounded-full ${summary.totalDayPnl >= 0 ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30'}`}>
              <DollarSign className={`w-6 h-6 ${summary.totalDayPnl >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`} />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Open Positions</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {summary.openPositions}
              </p>
            </div>
            <div className="p-3 rounded-full bg-blue-100 dark:bg-blue-900/30">
              <BarChart2 className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Trading Mode
            </label>
            <select
              value={modeFilter}
              onChange={(e) => setModeFilter(e.target.value as TradingMode | '')}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="">All Modes</option>
              <option value="PAPER">Paper Trading</option>
              <option value="LIVE">Live Trading</option>
            </select>
          </div>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showClosedPositions}
              onChange={(e) => setShowClosedPositions(e.target.checked)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">Show Closed Positions</span>
          </label>
        </div>
      </div>

      {/* Positions Grid */}
      {positions.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="text-center py-12">
            <BarChart2 className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No positions</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              You don't have any {showClosedPositions ? '' : 'open '}positions.
            </p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {positions.map((position) => (
            <div
              key={position.positionId}
              className="bg-white dark:bg-gray-800 rounded-lg shadow p-4"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${position.quantity >= 0 ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30'}`}>
                    {position.quantity >= 0 ? (
                      <ArrowUpRight className="w-5 h-5 text-green-600 dark:text-green-400" />
                    ) : (
                      <ArrowDownRight className="w-5 h-5 text-red-600 dark:text-red-400" />
                    )}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      {position.symbol}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {position.exchange} • {position.brokerId}
                    </p>
                  </div>
                </div>
                <span
                  className={`px-2 py-1 text-xs font-medium rounded-full ${
                    position.tradingMode === 'LIVE'
                      ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
                  }`}
                >
                  {position.tradingMode}
                </span>
              </div>

              {/* Position Details */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Quantity</p>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {Math.abs(position.quantity)} ({getPositionSide(position.quantity)})
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Avg Price</p>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {formatCurrency(
                      position.quantity >= 0
                        ? position.averageBuyPrice
                        : position.averageSellPrice
                    )}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">LTP</p>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {formatCurrency(position.lastPrice)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Value</p>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {formatCurrency(position.value)}
                  </p>
                </div>
              </div>

              {/* P&L */}
              <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">P&L</p>
                  <div className="flex items-center gap-2">
                    <span className={`text-lg font-bold ${getPnLColor(position.pnl)}`}>
                      {formatCurrency(position.pnl)}
                    </span>
                    <span className={`text-sm ${getPnLColor(position.pnlPercentage)}`}>
                      ({formatPercentage(position.pnlPercentage)})
                    </span>
                  </div>
                </div>
                {position.status === 'OPEN' && position.quantity !== 0 && (
                  <button
                    onClick={() => setSquareOffPosition(position)}
                    className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700"
                  >
                    <Target className="w-4 h-4" />
                    Square Off
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Square Off Confirmation Dialog */}
      {squareOffPosition && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg max-w-md w-full p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-full bg-red-100 dark:bg-red-900/30">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Confirm Square Off
              </h3>
            </div>

            <p className="text-gray-600 dark:text-gray-300 mb-4">
              Are you sure you want to square off your position in{' '}
              <span className="font-semibold">{squareOffPosition.symbol}</span>?
            </p>

            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-6">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500 dark:text-gray-400">Quantity</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {Math.abs(squareOffPosition.quantity)}
                </span>
              </div>
              <div className="flex justify-between text-sm mt-2">
                <span className="text-gray-500 dark:text-gray-400">Current P&L</span>
                <span className={`font-medium ${getPnLColor(squareOffPosition.pnl)}`}>
                  {formatCurrency(squareOffPosition.pnl)}
                </span>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setSquareOffPosition(null)}
                disabled={squareOffLoading}
                className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
              >
                Cancel
              </button>
              <button
                onClick={handleSquareOff}
                disabled={squareOffLoading}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                {squareOffLoading ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Target className="w-4 h-4" />
                )}
                Square Off
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PositionsPage;
