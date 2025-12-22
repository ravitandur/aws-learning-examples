/**
 * Trading Types
 * Type definitions for orders, positions, and trading operations
 */

// Order Types
export type OrderType = 'MARKET' | 'LIMIT' | 'SL' | 'SL-M';
export type TransactionType = 'BUY' | 'SELL';
export type OrderStatus = 'PENDING' | 'PLACED' | 'OPEN' | 'FILLED' | 'PARTIALLY_FILLED' | 'CANCELLED' | 'REJECTED' | 'EXPIRED';
export type TradingMode = 'PAPER' | 'LIVE';
export type ProductType = 'MIS' | 'NRML' | 'CNC';
export type ExecutionType = 'ENTRY' | 'EXIT' | 'MANUAL';
export type PositionStatus = 'OPEN' | 'CLOSED' | 'SQUARED_OFF';

// Order Interface
export interface Order {
  orderId: string;
  brokerOrderId?: string;
  symbol: string;
  exchange: string;
  transactionType: TransactionType;
  orderType: OrderType;
  quantity: number;
  price?: number;
  triggerPrice?: number;
  productType: ProductType;
  status: OrderStatus;
  filledQuantity: number;
  fillPrice?: number;
  rejectionReason?: string;
  tradingMode: TradingMode;
  brokerId: string;
  clientId?: string;
  strategyId?: string;
  basketId?: string;
  legId?: string;
  executionType: ExecutionType;
  placedAt: string;
  updatedAt: string;
}

// Position Interface
export interface Position {
  positionId: string;
  symbol: string;
  exchange: string;
  productType: ProductType;
  quantity: number;
  buyQuantity: number;
  sellQuantity: number;
  averageBuyPrice: number;
  averageSellPrice: number;
  lastPrice: number;
  pnl: number;
  pnlPercentage: number;
  dayChange: number;
  dayChangePercentage?: number;
  value: number;
  tradingMode: TradingMode;
  brokerId: string;
  clientId?: string;
  strategyId?: string;
  basketId?: string;
  status: PositionStatus;
  openedAt?: string;
  closedAt?: string;
  updatedAt?: string;
}

// Today's Execution Timeline Item
export interface ExecutionTimelineItem {
  strategyId: string;
  basketId: string;
  strategyName: string;
  underlying: string;
  strategyType: string;
  executionDate: string;
  entryTime: string;
  exitTime?: string;
  status: 'PENDING' | 'EXECUTING' | 'EXECUTED' | 'FAILED' | 'SKIPPED';
  executionStatus: 'AWAITING_ENTRY' | 'ENTRY_PLACED' | 'ENTRY_FILLED' | 'AWAITING_EXIT' | 'EXIT_PLACED' | 'EXIT_FILLED' | 'COMPLETED';
  tradingMode: TradingMode;
  brokerAllocations: BrokerAllocation[];
  countdown?: {
    type: 'ENTRY' | 'EXIT';
    secondsRemaining: number;
  };
}

// Broker Allocation
export interface BrokerAllocation {
  brokerId: string;
  clientId: string;
  lots: number;
}

// Order Placement Request
export interface PlaceOrderRequest {
  symbol: string;
  exchange: string;
  transactionType: TransactionType;
  orderType: OrderType;
  quantity: number;
  price?: number;
  triggerPrice?: number;
  productType?: ProductType;
  tradingMode?: TradingMode;
  brokerId?: string;
  clientId?: string;
  strategyId?: string;
  basketId?: string;
  legId?: string;
  executionType?: ExecutionType;
  tag?: string;
}

// Order Modification Request
export interface ModifyOrderRequest {
  quantity?: number;
  price?: number;
  triggerPrice?: number;
  orderType?: OrderType;
}

// Square Off Request
export interface SquareOffRequest {
  quantity?: number;  // Optional - defaults to full position
  orderType?: OrderType;
  price?: number;  // Required for LIMIT orders
}

// API Responses
export interface OrderResponse {
  success: boolean;
  order?: {
    orderId: string;
    brokerOrderId?: string;
    status: OrderStatus;
    message?: string;
    placedAt: string;
  };
  message?: string;
  error?: string;
}

export interface OrderListResponse {
  success: boolean;
  orders: Order[];
  count: number;
}

export interface PositionListResponse {
  success: boolean;
  positions: Position[];
  count: number;
  summary: {
    totalPnl: number;
    totalDayPnl: number;
    openPositions: number;
  };
}

export interface SquareOffResponse {
  success: boolean;
  message: string;
  order?: {
    orderId: string;
    brokerOrderId?: string;
    status: OrderStatus;
    quantity: number;
  };
  remainingQuantity: number;
}

export interface TodayExecutionsResponse {
  success: boolean;
  executions: ExecutionTimelineItem[];
  count: number;
  summary: {
    pending: number;
    executing: number;
    completed: number;
    failed: number;
  };
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: 'order_update' | 'position_update' | 'pnl_update' | 'execution_update';
  data: Order | Position | PnLUpdate | ExecutionUpdate;
  timestamp: string;
}

export interface PnLUpdate {
  totalPnl: number;
  totalDayPnl: number;
  positions: {
    symbol: string;
    pnl: number;
    lastPrice: number;
  }[];
}

export interface ExecutionUpdate {
  strategyId: string;
  status: ExecutionTimelineItem['executionStatus'];
  orderId?: string;
  message?: string;
}

// Filter Types
export interface OrderFilters {
  status?: OrderStatus;
  tradingMode?: TradingMode;
  symbol?: string;
  fromDate?: string;
  toDate?: string;
}

export interface PositionFilters {
  tradingMode?: TradingMode;
  brokerId?: string;
  status?: PositionStatus;
}

// Utility Types
export type OrderSide = 'LONG' | 'SHORT';

export const getOrderSide = (transactionType: TransactionType): OrderSide => {
  return transactionType === 'BUY' ? 'LONG' : 'SHORT';
};

export const getPositionSide = (quantity: number): OrderSide => {
  return quantity >= 0 ? 'LONG' : 'SHORT';
};

export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
};

export const formatPercentage = (value: number): string => {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
};

export const getStatusColor = (status: OrderStatus | PositionStatus): string => {
  switch (status) {
    case 'FILLED':
    case 'OPEN':
      return 'text-green-600 dark:text-green-400';
    case 'PENDING':
    case 'PLACED':
      return 'text-yellow-600 dark:text-yellow-400';
    case 'CANCELLED':
    case 'CLOSED':
    case 'SQUARED_OFF':
      return 'text-gray-600 dark:text-gray-400';
    case 'REJECTED':
    case 'EXPIRED':
      return 'text-red-600 dark:text-red-400';
    case 'PARTIALLY_FILLED':
      return 'text-blue-600 dark:text-blue-400';
    default:
      return 'text-gray-600 dark:text-gray-400';
  }
};

export const getPnLColor = (pnl: number): string => {
  if (pnl > 0) return 'text-green-600 dark:text-green-400';
  if (pnl < 0) return 'text-red-600 dark:text-red-400';
  return 'text-gray-600 dark:text-gray-400';
};
