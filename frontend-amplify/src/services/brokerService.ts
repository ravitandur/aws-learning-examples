import apiClient from './apiClient';
import type { BrokerAccount, CreateBrokerAccount, UpdateBrokerAccount, ApiResponse } from '../types';

class BrokerService {
  /**
   * Create a new broker account
   */
  async createBrokerAccount(accountData: CreateBrokerAccount): Promise<BrokerAccount> {
    try {
      const response = await apiClient.post<ApiResponse<BrokerAccount>>(
        '/broker-accounts',
        accountData
      );

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to create broker account');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to create broker account');
    }
  }

  /**
   * Get all broker accounts for the authenticated user
   */
  async getBrokerAccounts(): Promise<BrokerAccount[]> {
    try {
      const response = await apiClient.get<ApiResponse<BrokerAccount[]>>('/broker-accounts');

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to fetch broker accounts');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch broker accounts');
    }
  }

  /**
   * Update a specific broker account
   */
  async updateBrokerAccount(
    brokerAccountId: string, 
    updates: UpdateBrokerAccount
  ): Promise<BrokerAccount> {
    try {
      const response = await apiClient.put<ApiResponse<BrokerAccount>>(
        `/broker-accounts/${brokerAccountId}`,
        updates
      );

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to update broker account');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to update broker account');
    }
  }

  /**
   * Delete a specific broker account
   */
  async deleteBrokerAccount(brokerAccountId: string): Promise<void> {
    try {
      const response = await apiClient.delete<ApiResponse>(
        `/broker-accounts/${brokerAccountId}`
      );

      if (!response.success) {
        throw new Error(response.message || 'Failed to delete broker account');
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to delete broker account');
    }
  }

  /**
   * Test connection to a broker account
   */
  async testConnection(brokerAccountId: string): Promise<{ connected: boolean; message: string }> {
    try {
      const response = await apiClient.post<ApiResponse<{ connected: boolean; message: string }>>(
        `/broker-accounts/${brokerAccountId}/test-connection`
      );

      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to test connection');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to test connection');
    }
  }
}

const brokerService = new BrokerService();
export default brokerService;