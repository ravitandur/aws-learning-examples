/**
 * Trading Service
 * API service for order and position management
 */

import apiClient from './apiClient';
import {
  Order,
  Position,
  PlaceOrderRequest,
  ModifyOrderRequest,
  SquareOffRequest,
  OrderResponse,
  OrderListResponse,
  PositionListResponse,
  SquareOffResponse,
  TodayExecutionsResponse,
  OrderFilters,
  PositionFilters,
  ExecutionTimelineItem,
} from '../types/trading';

// Transform snake_case to camelCase for orders
const transformOrder = (order: any): Order => ({
  orderId: order.order_id,
  brokerOrderId: order.broker_order_id,
  symbol: order.symbol,
  exchange: order.exchange,
  transactionType: order.transaction_type,
  orderType: order.order_type,
  quantity: order.quantity,
  price: order.price,
  triggerPrice: order.trigger_price,
  productType: order.product_type || 'NRML',
  status: order.status,
  filledQuantity: order.filled_quantity || 0,
  fillPrice: order.fill_price,
  rejectionReason: order.rejection_reason,
  tradingMode: order.trading_mode || 'PAPER',
  brokerId: order.broker_id,
  clientId: order.client_id,
  strategyId: order.strategy_id,
  basketId: order.basket_id,
  legId: order.leg_id,
  executionType: order.execution_type || 'MANUAL',
  placedAt: order.placed_at,
  updatedAt: order.updated_at,
});

// Transform snake_case to camelCase for positions
const transformPosition = (pos: any): Position => ({
  positionId: pos.position_id,
  symbol: pos.symbol,
  exchange: pos.exchange,
  productType: pos.product_type || 'NRML',
  quantity: pos.quantity,
  buyQuantity: pos.buy_quantity || 0,
  sellQuantity: pos.sell_quantity || 0,
  averageBuyPrice: pos.average_buy_price || 0,
  averageSellPrice: pos.average_sell_price || 0,
  lastPrice: pos.last_price || 0,
  pnl: pos.pnl || 0,
  pnlPercentage: pos.pnl_percentage || 0,
  dayChange: pos.day_change || 0,
  dayChangePercentage: pos.day_change_percentage,
  value: pos.value || 0,
  tradingMode: pos.trading_mode || 'PAPER',
  brokerId: pos.broker_id,
  clientId: pos.client_id,
  strategyId: pos.strategy_id,
  basketId: pos.basket_id,
  status: pos.status || 'OPEN',
  openedAt: pos.opened_at,
  closedAt: pos.closed_at,
  updatedAt: pos.updated_at,
});

// Transform snake_case to camelCase for execution timeline
const transformExecution = (exec: any): ExecutionTimelineItem => ({
  strategyId: exec.strategy_id,
  basketId: exec.basket_id,
  strategyName: exec.strategy_name,
  underlying: exec.underlying,
  strategyType: exec.strategy_type,
  executionDate: exec.execution_date,
  entryTime: exec.entry_time,
  exitTime: exec.exit_time,
  // Map execution_status to status (PENDING, EXECUTING, EXECUTED, FAILED, SKIPPED)
  status: exec.execution_status || 'PENDING',
  executionStatus: exec.execution_status,
  tradingMode: exec.trading_mode || 'PAPER',
  brokerAllocations: (exec.broker_allocations || []).map((alloc: any) => ({
    brokerId: alloc.broker_id,
    clientId: alloc.client_id,
    lots: alloc.lots,
  })),
  countdown: exec.countdown,
});

// Transform camelCase to snake_case for requests
const transformOrderRequest = (request: PlaceOrderRequest): any => ({
  symbol: request.symbol,
  exchange: request.exchange,
  transaction_type: request.transactionType,
  order_type: request.orderType,
  quantity: request.quantity,
  price: request.price,
  trigger_price: request.triggerPrice,
  product_type: request.productType || 'NRML',
  trading_mode: request.tradingMode || 'PAPER',
  broker_id: request.brokerId,
  client_id: request.clientId,
  strategy_id: request.strategyId,
  basket_id: request.basketId,
  leg_id: request.legId,
  execution_type: request.executionType || 'MANUAL',
  tag: request.tag,
});

class TradingService {
  private baseUrl: string;

  constructor() {
    // Use options API for trading endpoints
    // API Gateway path: /options/trading/*
    this.baseUrl = `${process.env.REACT_APP_OPTIONS_API_URL_DEV || ''}/options`;
  }

  // ==================== Order Operations ====================

  /**
   * Place a new order
   */
  async placeOrder(request: PlaceOrderRequest): Promise<OrderResponse> {
    try {
      const response = await apiClient.post<any>(
        `${this.baseUrl}/trading/orders`,
        transformOrderRequest(request)
      );

      return {
        success: response.data.success,
        order: response.data.order ? {
          orderId: response.data.order.order_id,
          brokerOrderId: response.data.order.broker_order_id,
          status: response.data.order.status,
          message: response.data.order.message,
          placedAt: response.data.order.placed_at,
        } : undefined,
        message: response.data.message,
        error: response.data.error,
      };
    } catch (error: any) {
      console.error('Error placing order:', error);
      throw error;
    }
  }

  /**
   * Get list of orders with optional filters
   */
  async getOrders(filters?: OrderFilters): Promise<Order[]> {
    try {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.tradingMode) params.append('trading_mode', filters.tradingMode);
      if (filters?.symbol) params.append('symbol', filters.symbol);
      if (filters?.fromDate) params.append('from_date', filters.fromDate);
      if (filters?.toDate) params.append('to_date', filters.toDate);

      const queryString = params.toString();
      const url = `${this.baseUrl}/trading/orders${queryString ? `?${queryString}` : ''}`;

      const response = await apiClient.get<OrderListResponse>(url);
      return (response.orders || []).map(transformOrder);
    } catch (error: any) {
      console.error('Error fetching orders:', error);
      throw error;
    }
  }

  /**
   * Get details of a specific order
   */
  async getOrder(orderId: string): Promise<Order> {
    try {
      const response = await apiClient.get<any>(
        `${this.baseUrl}/trading/orders/${orderId}`
      );
      return transformOrder(response.data.order);
    } catch (error: any) {
      console.error('Error fetching order:', error);
      throw error;
    }
  }

  /**
   * Modify an existing order
   */
  async modifyOrder(orderId: string, modifications: ModifyOrderRequest): Promise<OrderResponse> {
    try {
      const response = await apiClient.put<any>(
        `${this.baseUrl}/trading/orders/${orderId}`,
        {
          quantity: modifications.quantity,
          price: modifications.price,
          trigger_price: modifications.triggerPrice,
          order_type: modifications.orderType,
        }
      );

      return {
        success: response.data.success,
        message: response.data.message,
        error: response.data.error,
      };
    } catch (error: any) {
      console.error('Error modifying order:', error);
      throw error;
    }
  }

  /**
   * Cancel an order
   */
  async cancelOrder(orderId: string): Promise<{ success: boolean; message?: string }> {
    try {
      const response = await apiClient.delete<any>(
        `${this.baseUrl}/trading/orders/${orderId}`
      );

      return {
        success: response.data.success,
        message: response.data.message,
      };
    } catch (error: any) {
      console.error('Error cancelling order:', error);
      throw error;
    }
  }

  // ==================== Position Operations ====================

  /**
   * Get list of positions with optional filters
   */
  async getPositions(filters?: PositionFilters): Promise<Position[]> {
    try {
      const params = new URLSearchParams();
      if (filters?.tradingMode) params.append('trading_mode', filters.tradingMode);
      if (filters?.brokerId) params.append('broker_id', filters.brokerId);
      if (filters?.status) params.append('status', filters.status);

      const queryString = params.toString();
      const url = `${this.baseUrl}/trading/positions${queryString ? `?${queryString}` : ''}`;

      const response = await apiClient.get<PositionListResponse>(url);
      return (response.positions || []).map(transformPosition);
    } catch (error: any) {
      console.error('Error fetching positions:', error);
      throw error;
    }
  }

  /**
   * Get position summary (P&L totals)
   */
  async getPositionSummary(filters?: PositionFilters): Promise<{
    totalPnl: number;
    totalDayPnl: number;
    openPositions: number;
  }> {
    try {
      const params = new URLSearchParams();
      if (filters?.tradingMode) params.append('trading_mode', filters.tradingMode);
      if (filters?.brokerId) params.append('broker_id', filters.brokerId);

      const queryString = params.toString();
      const url = `${this.baseUrl}/trading/positions${queryString ? `?${queryString}` : ''}`;

      const response = await apiClient.get<PositionListResponse>(url);
      const summary = response.summary as any;
      return {
        totalPnl: summary?.totalPnl || summary?.total_pnl || 0,
        totalDayPnl: summary?.totalDayPnl || summary?.total_day_pnl || 0,
        openPositions: summary?.openPositions || summary?.open_positions || 0,
      };
    } catch (error: any) {
      console.error('Error fetching position summary:', error);
      return { totalPnl: 0, totalDayPnl: 0, openPositions: 0 };
    }
  }

  /**
   * Get details of a specific position
   */
  async getPosition(positionId: string): Promise<Position> {
    try {
      const response = await apiClient.get<any>(
        `${this.baseUrl}/trading/positions/${positionId}`
      );
      return transformPosition(response.data.position);
    } catch (error: any) {
      console.error('Error fetching position:', error);
      throw error;
    }
  }

  /**
   * Square off a position
   */
  async squareOffPosition(positionId: string, request?: SquareOffRequest): Promise<SquareOffResponse> {
    try {
      const response = await apiClient.post<any>(
        `${this.baseUrl}/trading/positions/${positionId}/square-off`,
        {
          quantity: request?.quantity,
          order_type: request?.orderType || 'MARKET',
          price: request?.price,
        }
      );

      return {
        success: response.data.success,
        message: response.data.message,
        order: response.data.order ? {
          orderId: response.data.order.order_id,
          brokerOrderId: response.data.order.broker_order_id,
          status: response.data.order.status,
          quantity: response.data.order.quantity,
        } : undefined,
        remainingQuantity: response.data.remaining_quantity || 0,
      };
    } catch (error: any) {
      console.error('Error squaring off position:', error);
      throw error;
    }
  }

  // ==================== Today's Executions ====================

  /**
   * Get today's execution timeline
   */
  async getTodayExecutions(): Promise<ExecutionTimelineItem[]> {
    try {
      const response = await apiClient.get<any>(
        `${this.baseUrl}/trading/today`
      );
      // apiClient.get returns response.data directly, so access executions directly
      return (response.executions || []).map(transformExecution);
    } catch (error: any) {
      console.error('Error fetching today executions:', error);
      throw error;
    }
  }

  /**
   * Get execution summary for today
   */
  async getTodayExecutionSummary(): Promise<{
    pending: number;
    executing: number;
    completed: number;
    failed: number;
  }> {
    try {
      const response = await apiClient.get<TodayExecutionsResponse>(
        `${this.baseUrl}/trading/today`
      );
      const summary = response.summary as any;
      return {
        pending: summary?.pending || 0,
        executing: summary?.executing || 0,
        completed: summary?.completed || 0,
        failed: summary?.failed || 0,
      };
    } catch (error: any) {
      console.error('Error fetching execution summary:', error);
      return { pending: 0, executing: 0, completed: 0, failed: 0 };
    }
  }
}

// Export singleton instance
const tradingService = new TradingService();
export default tradingService;
