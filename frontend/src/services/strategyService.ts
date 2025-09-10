import optionsApiClient from './optionsApiClient';
import strategyTransformationService, { FrontendStrategyData, BackendStrategyData } from './strategyTransformationService';
import { ApiResponse, Strategy } from '../types';

interface StrategyCreationResponse {
  success: boolean;
  data: any;
  message: string;
  warnings?: string[];
}

interface StrategyExecutionStatus {
  status: 'ACTIVE' | 'PAUSED' | 'INACTIVE' | 'COMPLETED' | 'ERROR';
  lastExecution?: string;
  nextExecution?: string;
  executionCount: number;
  performance?: {
    totalReturn: number;
    successRate: number;
    averageReturn: number;
  };
}

class StrategyService {
  /**
   * Create a new strategy in a basket using the transformation service
   */
  async createStrategy(basketId: string, strategyData: FrontendStrategyData): Promise<StrategyCreationResponse> {
    try {
      // Perform advanced validation first
      const validation = await strategyTransformationService.validateFrontendDataAdvanced(strategyData);
      
      if (!validation.isValid) {
        const errorMessage = `Validation failed: ${validation.errors.join(', ')}`;
        if (validation.warnings.length > 0) {
          console.warn('Strategy validation warnings:', validation.warnings);
        }
        throw new Error(errorMessage);
      }
      
      // Show warnings to user (non-blocking)
      if (validation.warnings.length > 0) {
        console.warn('Strategy creation warnings:', validation.warnings);
      }
      
      // Transform frontend data to backend format
      const backendPayload = strategyTransformationService.createApiPayload(basketId, strategyData);
      
      // Make API call to create strategy
      const response = await optionsApiClient.post<ApiResponse<any>>(
        `/options/baskets/${basketId}/strategies`,
        backendPayload
      );

      if (!response.success) {
        throw new Error(response.message || 'Failed to create strategy');
      }

      return {
        success: true,
        data: response.data,
        message: response.message || 'Strategy created successfully',
        warnings: validation.warnings.length > 0 ? validation.warnings : undefined
      };
    } catch (error: any) {
      // Enhanced error handling with transformation details
      if (error.message?.includes('Validation failed')) {
        throw new Error(error.message);
      }
      
      const apiError = error.response?.data?.message || error.message;
      throw new Error(`Failed to create strategy: ${apiError}`);
    }
  }

  /**
   * Get all strategies for a specific basket
   */
  async getBasketStrategies(basketId: string): Promise<Strategy[]> {
    try {
      const response = await optionsApiClient.get<ApiResponse<Strategy[]>>(
        `/options/baskets/${basketId}/strategies`
      );

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to fetch basket strategies');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch basket strategies');
    }
  }

  /**
   * Get detailed information about a specific strategy
   */
  async getStrategy(strategyId: string): Promise<any> {
    try {
      const response = await optionsApiClient.get<ApiResponse<any>>(
        `/options/strategies/${strategyId}`
      );

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to fetch strategy details');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch strategy details');
    }
  }

  /**
   * Update an existing strategy
   */
  async updateStrategy(strategyId: string, updates: Partial<BackendStrategyData>): Promise<any> {
    try {
      const response = await optionsApiClient.put<ApiResponse<any>>(
        `/options/strategies/${strategyId}`,
        updates
      );

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to update strategy');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to update strategy');
    }
  }

  /**
   * Delete a strategy
   */
  async deleteStrategy(strategyId: string): Promise<void> {
    try {
      const response = await optionsApiClient.delete<ApiResponse>(
        `/options/strategies/${strategyId}`
      );

      if (!response.success) {
        throw new Error(response.message || 'Failed to delete strategy');
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to delete strategy');
    }
  }

  /**
   * Get strategy execution status with performance metrics
   */
  async getStrategyStatus(strategyId: string): Promise<StrategyExecutionStatus> {
    try {
      const response = await optionsApiClient.get<ApiResponse<StrategyExecutionStatus>>(
        `/options/strategies/${strategyId}/status`
      );

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to fetch strategy status');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch strategy status');
    }
  }

  /**
   * Start strategy execution
   */
  async startStrategy(strategyId: string): Promise<void> {
    try {
      const response = await optionsApiClient.post<ApiResponse>(
        `/options/strategies/${strategyId}/start`
      );

      if (!response.success) {
        throw new Error(response.message || 'Failed to start strategy');
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to start strategy');
    }
  }

  /**
   * Pause strategy execution
   */
  async pauseStrategy(strategyId: string): Promise<void> {
    try {
      const response = await optionsApiClient.post<ApiResponse>(
        `/options/strategies/${strategyId}/pause`
      );

      if (!response.success) {
        throw new Error(response.message || 'Failed to pause strategy');
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to pause strategy');
    }
  }

  /**
   * Stop strategy execution
   */
  async stopStrategy(strategyId: string): Promise<void> {
    try {
      const response = await optionsApiClient.post<ApiResponse>(
        `/options/strategies/${strategyId}/stop`
      );

      if (!response.success) {
        throw new Error(response.message || 'Failed to stop strategy');
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to stop strategy');
    }
  }

  /**
   * Get strategy performance analytics
   */
  async getStrategyAnalytics(strategyId: string, timeframe: 'day' | 'week' | 'month' = 'week'): Promise<{
    executions: any[];
    performance: {
      totalReturn: number;
      successRate: number;
      averageReturn: number;
      maxDrawdown: number;
      sharpeRatio: number;
    };
    charts: {
      pnlChart: { date: string; value: number }[];
      winRateChart: { date: string; rate: number }[];
    };
  }> {
    try {
      const response = await optionsApiClient.get<ApiResponse<any>>(
        `/options/strategies/${strategyId}/analytics?timeframe=${timeframe}`
      );

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to fetch strategy analytics');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch strategy analytics');
    }
  }

  /**
   * Clone an existing strategy to a different basket
   */
  async cloneStrategy(strategyId: string, targetBasketId: string, newName?: string): Promise<any> {
    try {
      const response = await optionsApiClient.post<ApiResponse<any>>(
        `/options/strategies/${strategyId}/clone`,
        {
          target_basket_id: targetBasketId,
          new_name: newName
        }
      );

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to clone strategy');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to clone strategy');
    }
  }

  /**
   * Get strategy execution history
   */
  async getStrategyHistory(strategyId: string, limit: number = 50): Promise<{
    executions: Array<{
      executionId: string;
      executionDate: string;
      executionType: 'ENTRY' | 'EXIT';
      status: 'SUCCESS' | 'FAILED' | 'PARTIAL';
      totalPnL: number;
      legs: Array<{
        legId: string;
        symbol: string;
        action: string;
        quantity: number;
        price: number;
        pnl: number;
      }>;
    }>;
    summary: {
      totalExecutions: number;
      successfulExecutions: number;
      totalPnL: number;
    };
  }> {
    try {
      const response = await optionsApiClient.get<ApiResponse<any>>(
        `/options/strategies/${strategyId}/history?limit=${limit}`
      );

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to fetch strategy history');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch strategy history');
    }
  }

  /**
   * Validate strategy configuration before creation
   */
  validateStrategyData(strategyData: FrontendStrategyData): { isValid: boolean; errors: string[] } {
    return strategyTransformationService.validateFrontendData(strategyData);
  }

  /**
   * Get strategy templates/presets
   */
  async getStrategyTemplates(): Promise<Array<{
    templateId: string;
    name: string;
    description: string;
    category: 'BULLISH' | 'BEARISH' | 'NEUTRAL' | 'VOLATILITY';
    complexity: 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED';
    defaultConfig: Partial<FrontendStrategyData>;
  }>> {
    try {
      const response = await optionsApiClient.get<ApiResponse<any>>(
        '/options/strategy-templates'
      );

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to fetch strategy templates');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch strategy templates');
    }
  }
}

const strategyService = new StrategyService();
export default strategyService;
export { StrategyService };
export type { StrategyExecutionStatus, StrategyCreationResponse };