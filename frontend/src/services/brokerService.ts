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
    clientId: string, 
    updates: UpdateBrokerAccount
  ): Promise<BrokerAccount> {
    try {
      const response = await apiClient.put<ApiResponse<BrokerAccount>>(
        `/broker-accounts/${clientId}`,
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
  async deleteBrokerAccount(clientId: string): Promise<void> {
    try {
      const response = await apiClient.delete<ApiResponse>(
        `/broker-accounts/${clientId}`
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
  async testBrokerConnection(clientId: string): Promise<ApiResponse<{
    status: 'connected' | 'failed';
    details?: string;
  }>> {
    try {
      const response = await apiClient.post<ApiResponse<{
        status: 'connected' | 'failed';
        details?: string;
      }>>(`/broker-accounts/${clientId}/verify`);

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
      },
      {
        id: 'angel',
        name: 'Angel One',
        description: 'Leading financial services company',
        website: 'https://angelone.in'
      },
      {
        id: 'finvasia',
        name: 'Finvasia',
        description: 'Zero brokerage trading platform',
        website: 'https://finvasia.com'
      },
      {
        id: 'zebu',
        name: 'Zebu',
        description: 'Technology-driven stockbroking',
        website: 'https://zebu.in'
      }
    ];
  }

  /**
   * OAuth operations for broker authentication
   */
  async initiateOAuthLogin(clientId: string): Promise<ApiResponse<{
    oauth_url: string;
    state: string;
    expires_in: number;
  }>> {
    try {
      const response = await apiClient.post<ApiResponse<{
        oauth_url: string;
        state: string;
        expires_in: number;
      }>>(`/broker-accounts/${clientId}/oauth/login`);

      return response;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to initiate OAuth login');
    }
  }

  async handleOAuthCallback(clientId: string, requestToken: string, state: string): Promise<ApiResponse<{
    token_expires_at: string;
    login_time: string;
    valid_until: string;
  }>> {
    try {
      const response = await apiClient.post<ApiResponse<{
        token_expires_at: string;
        login_time: string;
        valid_until: string;
      }>>(`/broker-accounts/${clientId}/oauth/callback`, {
        request_token: requestToken,
        state: state
      });

      return response;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to handle OAuth callback');
    }
  }

  async getOAuthStatus(clientId: string): Promise<ApiResponse<{
    has_token: boolean;
    is_valid: boolean;
    expires_at?: string;
    last_login?: string;
    requires_login: boolean;
  }>> {
    try {
      const response = await apiClient.get<ApiResponse<{
        has_token: boolean;
        is_valid: boolean;
        expires_at?: string;
        last_login?: string;
        requires_login: boolean;
      }>>(`/broker-accounts/${clientId}/oauth/status`);

      return response;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to get OAuth status');
    }
  }

  /**
   * Refresh OAuth token for brokers that support token refresh (e.g., Zebu)
   */
  async refreshOAuthToken(clientId: string): Promise<ApiResponse<{
    token_expires_at: string;
    login_time: string;
  }>> {
    try {
      const response = await apiClient.post<ApiResponse<{
        token_expires_at: string;
        login_time: string;
      }>>(`/broker-accounts/${clientId}/oauth/refresh`);

      return response;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to refresh OAuth token');
    }
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
          apiKeyLabel: 'API Key',
          apiSecretLabel: 'API Secret'
        };
      case 'zebu':
        return {
          title: 'Zebu MYNT OAuth Setup',
          steps: [
            '1. Log in to go.mynt.in',
            '2. Register an OAuth application',
            '3. Set redirect URL: http://localhost:3000/oauth/callback',
            '4. Copy Client ID and Client Secret from your OAuth app',
            '5. Add credentials below to enable OAuth login'
          ],
          apiKeyLabel: 'API Key (Client ID)',
          apiSecretLabel: 'API Secret (Client Secret)'
        };
      case 'angel':
        return {
          title: 'Angel One SmartAPI Setup',
          steps: [
            '1. Log in to Angel One SmartAPI portal',
            '2. Create a new app to get API credentials',
            '3. Copy API Key and Secret',
            '4. Note: You will also need TOTP for login'
          ],
          apiKeyLabel: 'API Key',
          apiSecretLabel: 'API Secret'
        };
      case 'finvasia':
        return {
          title: 'Finvasia Shoonya Setup',
          steps: [
            '1. Log in to Finvasia/Shoonya',
            '2. Request API access from support',
            '3. Get your Vendor Code and App Key',
            '4. Copy credentials below'
          ],
          apiKeyLabel: 'Vendor Code',
          apiSecretLabel: 'App Key'
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