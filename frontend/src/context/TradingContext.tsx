/**
 * Trading Context
 * Provides real-time trading state management with WebSocket integration
 */

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from 'react';
import { useWebSocket, WebSocketMessage, SubscriptionChannel } from '../hooks/useWebSocket';
import { Order, Position } from '../types/trading';

// Context state interface
interface TradingState {
  orders: Order[];
  positions: Position[];
  totalPnl: number;
  totalDayPnl: number;
  isLoading: boolean;
  lastUpdate: Date | null;
}

// Context value interface
interface TradingContextValue extends TradingState {
  // Connection state
  isConnected: boolean;
  connectionState: string;

  // Actions
  refreshOrders: () => Promise<void>;
  refreshPositions: () => Promise<void>;
  subscribeToUpdates: (channels?: SubscriptionChannel[]) => void;
  unsubscribeFromUpdates: (channels?: SubscriptionChannel[]) => void;

  // Callbacks for pages to register
  onOrderUpdate: (callback: (order: Order) => void) => () => void;
  onPositionUpdate: (callback: (position: Position) => void) => () => void;
  onPnlUpdate: (callback: (pnl: { totalPnl: number; totalDayPnl: number }) => void) => () => void;
}

// Create context
const TradingContext = createContext<TradingContextValue | undefined>(undefined);

// Provider props
interface TradingProviderProps {
  children: ReactNode;
}

// Transform snake_case to camelCase for orders
const transformOrder = (order: any): Order => ({
  orderId: order.order_id || order.orderId,
  brokerOrderId: order.broker_order_id || order.brokerOrderId,
  symbol: order.symbol,
  exchange: order.exchange,
  transactionType: order.transaction_type || order.transactionType,
  orderType: order.order_type || order.orderType,
  quantity: order.quantity,
  price: order.price,
  triggerPrice: order.trigger_price || order.triggerPrice,
  productType: order.product_type || order.productType || 'NRML',
  status: order.status,
  filledQuantity: order.filled_quantity || order.filledQuantity || 0,
  fillPrice: order.fill_price || order.fillPrice,
  rejectionReason: order.rejection_reason || order.rejectionReason,
  tradingMode: order.trading_mode || order.tradingMode || 'PAPER',
  brokerId: order.broker_id || order.brokerId,
  clientId: order.client_id || order.clientId,
  strategyId: order.strategy_id || order.strategyId,
  basketId: order.basket_id || order.basketId,
  legId: order.leg_id || order.legId,
  executionType: order.execution_type || order.executionType || 'MANUAL',
  placedAt: order.placed_at || order.placedAt,
  updatedAt: order.updated_at || order.updatedAt,
});

// Transform snake_case to camelCase for positions
const transformPosition = (pos: any): Position => ({
  positionId: pos.position_id || pos.positionId,
  symbol: pos.symbol,
  exchange: pos.exchange,
  productType: pos.product_type || pos.productType || 'NRML',
  quantity: pos.quantity,
  buyQuantity: pos.buy_quantity || pos.buyQuantity || 0,
  sellQuantity: pos.sell_quantity || pos.sellQuantity || 0,
  averageBuyPrice: pos.average_buy_price || pos.averageBuyPrice || 0,
  averageSellPrice: pos.average_sell_price || pos.averageSellPrice || 0,
  lastPrice: pos.last_price || pos.lastPrice || 0,
  pnl: pos.pnl || 0,
  pnlPercentage: pos.pnl_percentage || pos.pnlPercentage || 0,
  dayChange: pos.day_change || pos.dayChange || 0,
  dayChangePercentage: pos.day_change_percentage || pos.dayChangePercentage,
  value: pos.value || 0,
  tradingMode: pos.trading_mode || pos.tradingMode || 'PAPER',
  brokerId: pos.broker_id || pos.brokerId,
  clientId: pos.client_id || pos.clientId,
  strategyId: pos.strategy_id || pos.strategyId,
  basketId: pos.basket_id || pos.basketId,
  status: pos.status || 'OPEN',
  openedAt: pos.opened_at || pos.openedAt,
  closedAt: pos.closed_at || pos.closedAt,
  updatedAt: pos.updated_at || pos.updatedAt,
});

// Provider component
export const TradingProvider: React.FC<TradingProviderProps> = ({ children }) => {
  // State
  const [orders, setOrders] = useState<Order[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [totalPnl, setTotalPnl] = useState(0);
  const [totalDayPnl, setTotalDayPnl] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  // Callback registries
  const [orderCallbacks, setOrderCallbacks] = useState<Set<(order: Order) => void>>(new Set());
  const [positionCallbacks, setPositionCallbacks] = useState<Set<(position: Position) => void>>(
    new Set()
  );
  const [pnlCallbacks, setPnlCallbacks] = useState<
    Set<(pnl: { totalPnl: number; totalDayPnl: number }) => void>
  >(new Set());

  // Handle WebSocket messages
  const handleMessage = useCallback(
    (message: WebSocketMessage) => {
      const { type, data } = message;

      switch (type) {
        case 'order_update': {
          const order = transformOrder(data);
          setOrders((prev) => {
            const index = prev.findIndex((o) => o.orderId === order.orderId);
            if (index >= 0) {
              const updated = [...prev];
              updated[index] = order;
              return updated;
            }
            return [order, ...prev];
          });
          setLastUpdate(new Date());
          orderCallbacks.forEach((cb) => cb(order));
          break;
        }

        case 'position_update': {
          const position = transformPosition(data);
          setPositions((prev) => {
            const index = prev.findIndex((p) => p.positionId === position.positionId);
            if (index >= 0) {
              const updated = [...prev];
              updated[index] = position;
              return updated;
            }
            return [position, ...prev];
          });
          setLastUpdate(new Date());
          positionCallbacks.forEach((cb) => cb(position));
          break;
        }

        case 'pnl_update': {
          const pnl = {
            totalPnl: data.total_pnl ?? data.totalPnl ?? 0,
            totalDayPnl: data.total_day_pnl ?? data.totalDayPnl ?? 0,
          };
          setTotalPnl(pnl.totalPnl);
          setTotalDayPnl(pnl.totalDayPnl);
          setLastUpdate(new Date());
          pnlCallbacks.forEach((cb) => cb(pnl));
          break;
        }

        default:
          // Ignore other message types
          break;
      }
    },
    [orderCallbacks, positionCallbacks, pnlCallbacks]
  );

  // WebSocket connection
  const {
    connectionState,
    isConnected,
    subscribe,
    unsubscribe,
  } = useWebSocket({
    autoConnect: true,
    autoReconnect: true,
    onMessage: handleMessage,
  });

  // Refresh orders from API
  const refreshOrders = useCallback(async () => {
    setIsLoading(true);
    try {
      // Import tradingService dynamically to avoid circular deps
      const tradingService = (await import('../services/tradingService')).default;
      const data = await tradingService.getOrders();
      setOrders(data);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to refresh orders:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Refresh positions from API
  const refreshPositions = useCallback(async () => {
    setIsLoading(true);
    try {
      const tradingService = (await import('../services/tradingService')).default;
      const [positionsData, summaryData] = await Promise.all([
        tradingService.getPositions(),
        tradingService.getPositionSummary(),
      ]);
      setPositions(positionsData);
      setTotalPnl(summaryData.totalPnl);
      setTotalDayPnl(summaryData.totalDayPnl);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to refresh positions:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Subscribe to updates
  const subscribeToUpdates = useCallback(
    (channels: SubscriptionChannel[] = ['orders', 'positions', 'pnl']) => {
      subscribe(channels);
    },
    [subscribe]
  );

  // Unsubscribe from updates
  const unsubscribeFromUpdates = useCallback(
    (channels: SubscriptionChannel[] = ['orders', 'positions', 'pnl']) => {
      unsubscribe(channels);
    },
    [unsubscribe]
  );

  // Register order update callback
  const onOrderUpdate = useCallback((callback: (order: Order) => void) => {
    setOrderCallbacks((prev) => new Set(prev).add(callback));
    return () => {
      setOrderCallbacks((prev) => {
        const next = new Set(prev);
        next.delete(callback);
        return next;
      });
    };
  }, []);

  // Register position update callback
  const onPositionUpdate = useCallback((callback: (position: Position) => void) => {
    setPositionCallbacks((prev) => new Set(prev).add(callback));
    return () => {
      setPositionCallbacks((prev) => {
        const next = new Set(prev);
        next.delete(callback);
        return next;
      });
    };
  }, []);

  // Register P&L update callback
  const onPnlUpdate = useCallback(
    (callback: (pnl: { totalPnl: number; totalDayPnl: number }) => void) => {
      setPnlCallbacks((prev) => new Set(prev).add(callback));
      return () => {
        setPnlCallbacks((prev) => {
          const next = new Set(prev);
          next.delete(callback);
          return next;
        });
      };
    },
    []
  );

  // Auto-subscribe on connect
  useEffect(() => {
    if (isConnected) {
      subscribeToUpdates();
    }
  }, [isConnected, subscribeToUpdates]);

  // Context value
  const value: TradingContextValue = {
    orders,
    positions,
    totalPnl,
    totalDayPnl,
    isLoading,
    lastUpdate,
    isConnected,
    connectionState,
    refreshOrders,
    refreshPositions,
    subscribeToUpdates,
    unsubscribeFromUpdates,
    onOrderUpdate,
    onPositionUpdate,
    onPnlUpdate,
  };

  return <TradingContext.Provider value={value}>{children}</TradingContext.Provider>;
};

// Hook to use trading context
export function useTrading(): TradingContextValue {
  const context = useContext(TradingContext);
  if (context === undefined) {
    throw new Error('useTrading must be used within a TradingProvider');
  }
  return context;
}

export default TradingContext;
