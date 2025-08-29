import apiClient from './apiClient';
import { BrokerAccount, CreateBrokerAccount, UpdateBrokerAccount, ApiResponse } from '../types';

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
   * Delete a broker account
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
   * Test broker account connection
   */
  async testBrokerConnection(brokerAccountId: string): Promise<ApiResponse<{
    status: 'connected' | 'failed';
    details?: string;
  }>> {
    try {
      const response = await apiClient.post<ApiResponse<{
        status: 'connected' | 'failed';
        details?: string;
      }>>(`/broker-accounts/${brokerAccountId}/verify`);

      return response;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to test broker connection');
    }
  }

  /**
   * Get supported brokers
   */
  static getSupportedBrokers(): Array<{
    id: string;
    name: string;
    description: string;
    website: string;
  }> {
    return [
      {
        id: 'zerodha',
        name: 'Zerodha',
        description: 'India\'s largest stock broker by volume',
        website: 'https://zerodha.com'
      }
      // Future: Add more brokers like Upstox, Angel One, etc.
    ];
  }

  /**
   * Validate API key format for different brokers
   */
  static validateApiKey(brokerName: string, apiKey: string): boolean {
    switch (brokerName.toLowerCase()) {
      case 'zerodha':
        // Zerodha API keys are typically alphanumeric, 15-20 characters
        return /^[a-zA-Z0-9]{15,20}$/.test(apiKey);
      default:
        return apiKey.length > 0;
    }
  }

  /**
   * Validate API secret format for different brokers
   */
  static validateApiSecret(brokerName: string, apiSecret: string): boolean {
    switch (brokerName.toLowerCase()) {
      case 'zerodha':
        // Zerodha API secrets are typically longer alphanumeric strings
        return /^[a-zA-Z0-9]{20,40}$/.test(apiSecret);
      default:
        return apiSecret.length > 0;
    }
  }

  /**
   * Get broker-specific setup instructions
   */
  static getBrokerInstructions(brokerName: string): {
    title: string;
    steps: string[];
    apiKeyLabel: string;
    apiSecretLabel: string;
  } {
    switch (brokerName.toLowerCase()) {
      case 'zerodha':
        return {
          title: 'Zerodha Kite Connect Setup',
          steps: [
            '1. Log in to your Zerodha account',
            '2. Go to Kite Connect developer console',
            '3. Create a new app and get your API key',
            '4. Generate API secret for your app',
            '5. Copy both API key and secret to add here'
          ],
          apiKeyLabel: 'Zerodha API Key',
          apiSecretLabel: 'Zerodha API Secret'
        };
      default:
        return {
          title: 'Broker Setup',
          steps: ['1. Get API credentials from your broker'],
          apiKeyLabel: 'API Key',
          apiSecretLabel: 'API Secret'
        };
    }
  }
}

const brokerService = new BrokerService();
export default brokerService;
export { BrokerService };