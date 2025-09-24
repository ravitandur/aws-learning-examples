import optionsApiClient from './optionsApiClient';
import { BasketBrokerAllocation, CreateAllocation, UpdateAllocation, ApiResponse } from '../types';

class AllocationService {
  /**
   * Get all allocations for a specific basket
   */
  async getBasketAllocations(basketId: string): Promise<BasketBrokerAllocation[]> {
    try {
      const response = await optionsApiClient.get<ApiResponse<{
        allocations: BasketBrokerAllocation[];
        total_brokers: number;
        active_brokers: number;
        total_lot_multiplier: number;
      }>>(
        `/options/baskets/${basketId}/allocations`
      );

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to fetch basket allocations');
      }

      // Backend returns allocations nested in data.allocations
      return response.data.allocations || [];
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch basket allocations');
    }
  }

  /**
   * Get all allocations for the authenticated user across all baskets
   */
  async getAllAllocations(): Promise<BasketBrokerAllocation[]> {
    try {
      const response = await optionsApiClient.get<ApiResponse<{
        allocations: BasketBrokerAllocation[];
        summary: {
          total_allocations: number;
          active_allocations: number;
          total_baskets: number;
          unique_brokers: number;
          broker_breakdown: any[];
        };
      }>>(
        '/options/allocations'
      );

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to fetch allocations');
      }

      // Backend returns allocations nested in data.allocations
      return response.data.allocations || [];
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch allocations');
    }
  }

  /**
   * Get specific allocation by basket, broker, and client
   */
  async getAllocation(
    basketId: string, 
    brokerId: string, 
    clientId: string
  ): Promise<BasketBrokerAllocation> {
    try {
      const response = await optionsApiClient.get<ApiResponse<BasketBrokerAllocation>>(
        `/options/baskets/${basketId}/allocations/${brokerId}/${clientId}`
      );

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to fetch allocation');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch allocation');
    }
  }

  /**
   * Create new allocations for a basket
   */
  async createBasketAllocations(basketId: string, allocationData: CreateAllocation): Promise<BasketBrokerAllocation[]> {
    try {
      const response = await optionsApiClient.post<ApiResponse<{
        allocations: BasketBrokerAllocation[];
        total_brokers: number;
        active_brokers: number;
        total_lot_multiplier: number;
      }>>(
        `/options/baskets/${basketId}/allocations`,
        allocationData
      );

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to create allocations');
      }

      // Backend returns allocations nested in data.allocations
      return response.data.allocations || [];
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to create allocations');
    }
  }

  /**
   * Update a specific allocation
   */
  async updateAllocation(
    basketId: string,
    allocationId: string,
    updates: UpdateAllocation
  ): Promise<{ success: true; allocation_id: string; message: string }> {
    try {
      const response = await optionsApiClient.put<ApiResponse<{ allocation_id: string }>>(
        `/options/baskets/${basketId}/allocations/${allocationId}`,
        updates
      );

      if (!response.success) {
        throw new Error(response.message || 'Failed to update allocation');
      }

      // Backend returns simple success response with allocation_id
      return {
        success: true,
        allocation_id: response.data?.allocation_id || allocationId,
        message: response.message || 'Allocation updated successfully'
      };
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to update allocation');
    }
  }

  /**
   * Delete a specific allocation
   */
  async deleteAllocation(basketId: string, allocationId: string): Promise<void> {
    try {
      const response = await optionsApiClient.delete<ApiResponse>(
        `/options/baskets/${basketId}/allocations/${allocationId}`
      );

      if (!response.success) {
        throw new Error(response.message || 'Failed to delete allocation');
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to delete allocation');
    }
  }

  /**
   * Delete all allocations for a basket
   */
  async deleteBasketAllocations(basketId: string): Promise<void> {
    try {
      const response = await optionsApiClient.delete<ApiResponse>(
        `/options/baskets/${basketId}/allocations`
      );

      if (!response.success) {
        throw new Error(response.message || 'Failed to delete basket allocations');
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to delete basket allocations');
    }
  }

  /**
   * Get allocation summary for a basket
   */
  async getBasketAllocationSummary(basketId: string): Promise<{
    totalAllocations: number;
    totalLotMultiplier: number;
    activeAllocations: number;
    brokerBreakdown: {
      broker_id: string;
      client_count: number;
      total_multiplier: number;
    }[];
  }> {
    try {
      const response = await optionsApiClient.get<ApiResponse<{
        totalAllocations: number;
        totalLotMultiplier: number;
        activeAllocations: number;
        brokerBreakdown: {
          broker_id: string;
          client_count: number;
          total_multiplier: number;
        }[];
      }>>(`/options/baskets/${basketId}/allocations/summary`);

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to fetch allocation summary');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch allocation summary');
    }
  }

  /**
   * Validate allocation data before creation
   */
  validateAllocationData(allocationData: CreateAllocation): {
    isValid: boolean;
    errors: string[];
  } {
    const errors: string[] = [];

    if (!allocationData.allocations || allocationData.allocations.length === 0) {
      errors.push('At least one allocation is required');
      return { isValid: false, errors };
    }

    // Check each allocation
    allocationData.allocations.forEach((allocation, index) => {
      if (!allocation.broker_id || allocation.broker_id.trim() === '') {
        errors.push(`Allocation ${index + 1}: Broker ID is required`);
      }

      if (!allocation.client_id || allocation.client_id.trim() === '') {
        errors.push(`Allocation ${index + 1}: Client ID is required`);
      }

      if (!allocation.lot_multiplier || allocation.lot_multiplier < 1) {
        errors.push(`Allocation ${index + 1}: Lot multiplier must be at least 1`);
      }

      if (allocation.lot_multiplier && allocation.lot_multiplier > 250) {
        errors.push(`Allocation ${index + 1}: Lot multiplier cannot exceed 250`);
      }
    });

    // Check for duplicate broker-client combinations
    const combinations = new Set<string>();
    allocationData.allocations.forEach((allocation, index) => {
      const key = `${allocation.broker_id}-${allocation.client_id}`;
      if (combinations.has(key)) {
        errors.push(`Duplicate allocation for ${allocation.broker_id} - ${allocation.client_id}`);
      }
      combinations.add(key);
    });

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Calculate total lot multiplier for allocations
   */
  calculateTotalMultiplier(allocations: BasketBrokerAllocation[]): number {
    return allocations.reduce((total, allocation) => {
      return allocation.status === 'ACTIVE' ? total + allocation.lot_multiplier : total;
    }, 0);
  }

  /**
   * Get broker breakdown from allocations
   */
  getBrokerBreakdown(allocations: BasketBrokerAllocation[]): {
    broker_id: string;
    client_count: number;
    total_multiplier: number;
    allocations: BasketBrokerAllocation[];
  }[] {
    const brokerMap = new Map<string, {
      broker_id: string;
      client_count: number;
      total_multiplier: number;
      allocations: BasketBrokerAllocation[];
    }>();

    allocations.forEach(allocation => {
      const key = allocation.broker_id;
      
      if (!brokerMap.has(key)) {
        brokerMap.set(key, {
          broker_id: allocation.broker_id,
          client_count: 0,
          total_multiplier: 0,
          allocations: []
        });
      }

      const broker = brokerMap.get(key)!;
      broker.client_count += 1;
      broker.allocations.push(allocation);
      
      if (allocation.status === 'ACTIVE') {
        broker.total_multiplier += allocation.lot_multiplier;
      }
    });

    return Array.from(brokerMap.values());
  }
}

const allocationService = new AllocationService();
export default allocationService;
export { AllocationService };