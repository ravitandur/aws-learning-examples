import optionsApiClient from './optionsApiClient';
import { Basket, CreateBasket, UpdateBasket, Strategy, ApiResponse } from '../types';

class BasketService {
  /**
   * Get all baskets for the authenticated user
   */
  async getBaskets(): Promise<Basket[]> {
    try {
      const response = await optionsApiClient.get<ApiResponse<Basket[]>>('/options/baskets');

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to fetch baskets');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch baskets');
    }
  }

  /**
   * Get a specific basket by ID
   */
  async getBasket(basketId: string): Promise<Basket> {
    try {
      const response = await optionsApiClient.get<ApiResponse<Basket>>(`/options/baskets/${basketId}`);

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to fetch basket');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch basket');
    }
  }

  /**
   * Create a new basket
   */
  async createBasket(basketData: CreateBasket): Promise<Basket> {
    try {
      const response = await optionsApiClient.post<ApiResponse<Basket>>(
        '/options/baskets',
        basketData
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
      const response = await optionsApiClient.put<ApiResponse<Basket>>(
        `/options/baskets/${basketId}`,
        updates
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
   * Delete a basket
   */
  async deleteBasket(basketId: string): Promise<void> {
    try {
      const response = await optionsApiClient.delete<ApiResponse>(
        `/options/baskets/${basketId}`
      );

      if (!response.success) {
        throw new Error(response.message || 'Failed to delete basket');
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to delete basket');
    }
  }

  /**
   * Get available strategies for baskets
   */
  async getAvailableStrategies(): Promise<Strategy[]> {
    try {
      const response = await optionsApiClient.get<ApiResponse<Strategy[]>>('/options/strategies');

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
}

const basketService = new BasketService();
export default basketService;
export { BasketService };