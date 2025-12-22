/**
 * Today's Execution Timeline Page
 * Shows all strategies executing today with entry/exit times and countdown
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  RefreshCw,
  Clock,
  PlayCircle,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Calendar,
  TrendingUp,
  Timer,
  Activity,
  Pause,
  ChevronRight,
} from 'lucide-react';
import tradingService from '../services/tradingService';
import { ExecutionTimelineItem } from '../types/trading';

// Countdown Timer Component
const CountdownTimer: React.FC<{ targetTime: string; type: 'ENTRY' | 'EXIT' }> = ({
  targetTime,
  type,
}) => {
  const [timeLeft, setTimeLeft] = useState<number>(0);

  useEffect(() => {
    const calculateTimeLeft = () => {
      const now = new Date();
      const target = new Date();
      const [hours, minutes] = targetTime.split(':').map(Number);
      target.setHours(hours, minutes, 0, 0);

      const diff = target.getTime() - now.getTime();
      return Math.max(0, Math.floor(diff / 1000));
    };

    setTimeLeft(calculateTimeLeft());
    const interval = setInterval(() => {
      setTimeLeft(calculateTimeLeft());
    }, 1000);

    return () => clearInterval(interval);
  }, [targetTime]);

  const formatTime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hrs > 0) {
      return `${hrs}h ${mins}m ${secs}s`;
    } else if (mins > 0) {
      return `${mins}m ${secs}s`;
    }
    return `${secs}s`;
  };

  if (timeLeft <= 0) {
    return (
      <span className="text-green-600 dark:text-green-400 font-medium">
        {type === 'ENTRY' ? 'Entry time!' : 'Exit time!'}
      </span>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <Timer className={`w-4 h-4 ${type === 'ENTRY' ? 'text-blue-500' : 'text-orange-500'}`} />
      <span className={`font-mono ${type === 'ENTRY' ? 'text-blue-600 dark:text-blue-400' : 'text-orange-600 dark:text-orange-400'}`}>
        {formatTime(timeLeft)}
      </span>
      <span className="text-xs text-gray-500 dark:text-gray-400">
        to {type.toLowerCase()}
      </span>
    </div>
  );
};

// Execution Status Badge
const ExecutionStatusBadge: React.FC<{ status: ExecutionTimelineItem['status'] }> = ({ status }) => {
  const configs: Record<ExecutionTimelineItem['status'], { icon: React.ReactNode; bg: string; text: string; label: string }> = {
    PENDING: {
      icon: <Clock className="w-3 h-3" />,
      bg: 'bg-gray-100 dark:bg-gray-700',
      text: 'text-gray-700 dark:text-gray-300',
      label: 'Pending',
    },
    EXECUTING: {
      icon: <Activity className="w-3 h-3 animate-pulse" />,
      bg: 'bg-blue-100 dark:bg-blue-900/30',
      text: 'text-blue-700 dark:text-blue-300',
      label: 'Executing',
    },
    EXECUTED: {
      icon: <CheckCircle className="w-3 h-3" />,
      bg: 'bg-green-100 dark:bg-green-900/30',
      text: 'text-green-700 dark:text-green-300',
      label: 'Executed',
    },
    FAILED: {
      icon: <XCircle className="w-3 h-3" />,
      bg: 'bg-red-100 dark:bg-red-900/30',
      text: 'text-red-700 dark:text-red-300',
      label: 'Failed',
    },
    SKIPPED: {
      icon: <Pause className="w-3 h-3" />,
      bg: 'bg-yellow-100 dark:bg-yellow-900/30',
      text: 'text-yellow-700 dark:text-yellow-300',
      label: 'Skipped',
    },
  };

  const config = configs[status];

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full ${config.bg} ${config.text}`}>
      {config.icon}
      {config.label}
    </span>
  );
};

const TodayPage: React.FC = () => {
  const [executions, setExecutions] = useState<ExecutionTimelineItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  // Summary
  const [summary, setSummary] = useState({
    pending: 0,
    executing: 0,
    completed: 0,
    failed: 0,
  });

  const fetchExecutions = useCallback(async () => {
    try {
      setError(null);
      const [executionsData, summaryData] = await Promise.all([
        tradingService.getTodayExecutions(),
        tradingService.getTodayExecutionSummary(),
      ]);

      // Sort by entry time
      const sorted = executionsData.sort((a, b) => {
        const timeA = a.entryTime.split(':').map(Number);
        const timeB = b.entryTime.split(':').map(Number);
        return (timeA[0] * 60 + timeA[1]) - (timeB[0] * 60 + timeB[1]);
      });

      setExecutions(sorted);
      setSummary(summaryData);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch executions');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchExecutions();
    // Auto-refresh every minute
    const interval = setInterval(fetchExecutions, 60000);
    return () => clearInterval(interval);
  }, [fetchExecutions]);

  // Update current time every second
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchExecutions();
  };

  const formatTime = (time: string) => {
    const [hours, minutes] = time.split(':').map(Number);
    const period = hours >= 12 ? 'PM' : 'AM';
    const displayHours = hours % 12 || 12;
    return `${displayHours}:${minutes.toString().padStart(2, '0')} ${period}`;
  };

  const isTimePassed = (time: string) => {
    const [hours, minutes] = time.split(':').map(Number);
    const now = currentTime;
    const targetMinutes = hours * 60 + minutes;
    const currentMinutes = now.getHours() * 60 + now.getMinutes();
    return currentMinutes >= targetMinutes;
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Today's Timeline</h1>
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-2 text-gray-600 dark:text-gray-400">Loading timeline...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Today's Timeline</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {currentTime.toLocaleDateString('en-IN', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm text-gray-500 dark:text-gray-400">Current Time</p>
            <p className="text-lg font-mono font-bold text-gray-900 dark:text-white">
              {currentTime.toLocaleTimeString('en-IN', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
              })}
            </p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <XCircle className="h-5 w-5 text-red-600" />
            <span className="text-red-800 dark:text-red-200">{error}</span>
          </div>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700">
              <Clock className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Pending</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white">{summary.pending}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
              <PlayCircle className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Executing</p>
              <p className="text-xl font-bold text-blue-600 dark:text-blue-400">{summary.executing}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900/30">
              <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Completed</p>
              <p className="text-xl font-bold text-green-600 dark:text-green-400">{summary.completed}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-red-100 dark:bg-red-900/30">
              <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Failed</p>
              <p className="text-xl font-bold text-red-600 dark:text-red-400">{summary.failed}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Timeline */}
      {executions.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="text-center py-12">
            <Calendar className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No executions today</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              You don't have any strategies scheduled for today.
            </p>
          </div>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Execution Timeline</h2>
          </div>
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {executions.map((execution, index) => (
              <div
                key={`${execution.strategyId}-${index}`}
                className={`p-4 ${
                  execution.status === 'EXECUTING'
                    ? 'bg-blue-50 dark:bg-blue-900/10'
                    : ''
                }`}
              >
                <div className="flex items-start gap-4">
                  {/* Timeline indicator */}
                  <div className="flex flex-col items-center">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        execution.status === 'EXECUTED'
                          ? 'bg-green-100 dark:bg-green-900/30'
                          : execution.status === 'EXECUTING'
                          ? 'bg-blue-100 dark:bg-blue-900/30'
                          : execution.status === 'FAILED'
                          ? 'bg-red-100 dark:bg-red-900/30'
                          : 'bg-gray-100 dark:bg-gray-700'
                      }`}
                    >
                      {execution.status === 'EXECUTED' && (
                        <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                      )}
                      {execution.status === 'EXECUTING' && (
                        <Activity className="w-5 h-5 text-blue-600 dark:text-blue-400 animate-pulse" />
                      )}
                      {execution.status === 'FAILED' && (
                        <XCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
                      )}
                      {execution.status === 'PENDING' && (
                        <Clock className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      )}
                      {execution.status === 'SKIPPED' && (
                        <Pause className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
                      )}
                    </div>
                    {index < executions.length - 1 && (
                      <div className="w-0.5 h-full min-h-[40px] bg-gray-200 dark:bg-gray-700 mt-2" />
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-semibold text-gray-900 dark:text-white">
                          {execution.strategyName}
                        </h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                          {execution.underlying} • {execution.strategyType}
                        </p>
                      </div>
                      <ExecutionStatusBadge status={execution.status} />
                    </div>

                    {/* Time details */}
                    <div className="mt-3 flex flex-wrap items-center gap-4">
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${isTimePassed(execution.entryTime) ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'}`} />
                        <span className="text-sm text-gray-600 dark:text-gray-300">
                          Entry: <span className="font-medium">{formatTime(execution.entryTime)}</span>
                        </span>
                      </div>
                      {execution.exitTime && (
                        <>
                          <ChevronRight className="w-4 h-4 text-gray-400" />
                          <div className="flex items-center gap-2">
                            <div className={`w-2 h-2 rounded-full ${isTimePassed(execution.exitTime) ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'}`} />
                            <span className="text-sm text-gray-600 dark:text-gray-300">
                              Exit: <span className="font-medium">{formatTime(execution.exitTime)}</span>
                            </span>
                          </div>
                        </>
                      )}
                    </div>

                    {/* Countdown */}
                    {execution.status === 'PENDING' && (
                      <div className="mt-3">
                        <CountdownTimer targetTime={execution.entryTime} type="ENTRY" />
                      </div>
                    )}
                    {execution.status === 'EXECUTING' && execution.exitTime && (
                      <div className="mt-3">
                        <CountdownTimer targetTime={execution.exitTime} type="EXIT" />
                      </div>
                    )}

                    {/* Broker Allocations */}
                    {execution.brokerAllocations && execution.brokerAllocations.length > 0 && (
                      <div className="mt-4 flex flex-wrap gap-2">
                        {execution.brokerAllocations.map((alloc, i) => (
                          <span
                            key={i}
                            className="inline-flex items-center px-2 py-1 text-xs font-medium rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                          >
                            {alloc.brokerId}: {alloc.lots} lots
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Trading Mode */}
                    <div className="mt-3">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                          execution.tradingMode === 'LIVE'
                            ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                            : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
                        }`}
                      >
                        {execution.tradingMode} Trading
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TodayPage;
