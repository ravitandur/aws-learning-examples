import optionsApiClient from './optionsApiClient';
import { Basket, CreateBasket, UpdateBasket, StrategyMetadata, ApiResponse } from '../types';
import { transformBasket } from '../utils/transformStrategyFields';
import allocationService from './allocationService';

class BasketService {
  /**
   * Get all baskets for the authenticated user
   */
  async getBaskets(): Promise<Basket[]> {
    try {
      const response = await optionsApiClient.get<ApiResponse<any[]>>('/options/baskets');

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to fetch baskets');
      }

      // Transform backend data to frontend format
      return response.data.map(transformBasket);
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch baskets');
    }
  }

  /**
   * Get a specific basket by ID
   */
  async getBasket(basketId: string): Promise<Basket> {
    try {
      const response = await optionsApiClient.get<ApiResponse<any>>(`/options/baskets/${basketId}`);

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to fetch basket');
      }

      // Transform backend data to frontend format
      return transformBasket(response.data);
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch basket');
    }
  }

  /**
   * Create a new basket
   */
  async createBasket(basketData: CreateBasket): Promise<Basket> {
    try {
      // Send data directly - no transformation needed since types match backend
      const apiPayload = {
        name: basketData.basket_name,
        description: basketData.description,
        strategies: basketData.strategies,
        initial_capital: basketData.initial_capital
      };

      const response = await optionsApiClient.post<ApiResponse<Basket>>(
        '/options/baskets',
        apiPayload
      );

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to create basket');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to create basket');
    }
  }

  /**
   * Update a specific basket
   */
  async updateBasket(basketId: string, updates: UpdateBasket): Promise<Basket> {
    try {
      // Send data directly - no transformation needed since types match backend
      const apiPayload: any = {};
      if (updates.basket_name !== undefined) apiPayload.name = updates.basket_name;
      if (updates.description !== undefined) apiPayload.description = updates.description;
      if (updates.strategies !== undefined) apiPayload.strategies = updates.strategies;
      if (updates.status !== undefined) apiPayload.status = updates.status;

      const response = await optionsApiClient.put<ApiResponse<Basket>>(
        `/options/baskets/${basketId}`,
        apiPayload
      );

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to update basket');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to update basket');
    }
  }

  /**
   * Delete a basket (with validation to prevent deletion if allocations exist)
   */
  async deleteBasket(basketId: string): Promise<void> {
    try {
      // Validation: Check for existing allocations before deletion
      try {
        const allocations = await allocationService.getBasketAllocations(basketId);
        if (allocations.length > 0) {
          throw new Error(
            `Cannot delete basket. Please delete all ${allocations.length} broker allocation${allocations.length === 1 ? '' : 's'} first.`
          );
        }
      } catch (error: any) {
        // If it's our validation error, re-throw it
        if (error.message.includes('Cannot delete basket')) {
          throw error;
        }
        // If it's a 404 or other error (no allocations found), continue with deletion
        console.log('No allocations found for basket or allocation check failed:', basketId);
      }

      // Delete the basket only if validation passes
      const response = await optionsApiClient.delete<ApiResponse>(
        `/options/baskets/${basketId}`
      );

      if (!response.success) {
        throw new Error(response.message || 'Failed to delete basket');
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.message || error.message || 'Failed to delete basket');
    }
  }

  /**
   * Get available strategies for baskets
   */
  async getAvailableStrategies(): Promise<StrategyMetadata[]> {
    try {
      const response = await optionsApiClient.get<ApiResponse<StrategyMetadata[]>>('/options/strategies');

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to fetch strategies');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch strategies');
    }
  }

  /**
   * Associate strategies with a basket
   */
  async associateStrategies(basketId: string, strategyIds: string[]): Promise<Basket> {
    try {
      const response = await optionsApiClient.post<ApiResponse<Basket>>(
        `/options/baskets/${basketId}/strategies`,
        { strategyIds }
      );

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to associate strategies');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to associate strategies');
    }
  }

  /**
   * Remove strategies from a basket
   */
  async removeStrategies(basketId: string, strategyIds: string[]): Promise<Basket> {
    try {
      const response = await optionsApiClient.delete<ApiResponse<Basket>>(
        `/options/baskets/${basketId}/strategies`,
        { data: { strategyIds } }
      );

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to remove strategies');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to remove strategies');
    }
  }


  /**
   * Get basket execution status
   */
  async getBasketStatus(basketId: string): Promise<{
    status: 'ACTIVE' | 'PAUSED' | 'INACTIVE';
    lastExecution?: string;
    nextExecution?: string;
    executionCount: number;
  }> {
    try {
      const response = await optionsApiClient.get<ApiResponse<{
        status: 'ACTIVE' | 'PAUSED' | 'INACTIVE';
        lastExecution?: string;
        nextExecution?: string;
        executionCount: number;
      }>>(`/options/baskets/${basketId}/status`);

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to fetch basket status');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch basket status');
    }
  }

  /**
   * Start/Resume basket execution
   */
  async startBasket(basketId: string): Promise<void> {
    try {
      const response = await optionsApiClient.post<ApiResponse>(
        `/options/baskets/${basketId}/start`
      );

      if (!response.success) {
        throw new Error(response.message || 'Failed to start basket');
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to start basket');
    }
  }

  /**
   * Pause basket execution
   */
  async pauseBasket(basketId: string): Promise<void> {
    try {
      const response = await optionsApiClient.post<ApiResponse>(
        `/options/baskets/${basketId}/pause`
      );

      if (!response.success) {
        throw new Error(response.message || 'Failed to pause basket');
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to pause basket');
    }
  }

  /**
   * Stop basket execution
   */
  async stopBasket(basketId: string): Promise<void> {
    try {
      const response = await optionsApiClient.post<ApiResponse>(
        `/options/baskets/${basketId}/stop`
      );

      if (!response.success) {
        throw new Error(response.message || 'Failed to stop basket');
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to stop basket');
    }
  }

  /**
   * Update basket status (enable/disable)
   */
  async updateBasketStatus(basketId: string, status: 'ACTIVE' | 'INACTIVE' | 'PAUSED'): Promise<Basket> {
    try {
      const response = await optionsApiClient.put<ApiResponse<Basket>>(
        `/options/baskets/${basketId}`,
        { status }
      );

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to update basket status');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to update basket status');
    }
  }

}

const basketService = new BasketService();
export default basketService;
export { BasketService };