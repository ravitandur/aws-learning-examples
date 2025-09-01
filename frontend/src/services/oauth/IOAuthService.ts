/**
 * OAuth Service Interface
 * Defines the contract for OAuth operations across all brokers
 */

import {
  OAuthInitParams,
  OAuthCallbackParams,
  AuthResult,
  TokenResult,
  AuthStatus
} from '../../types/oauth';

/**
 * Main OAuth service interface
 * All OAuth implementations must implement this interface
 */
export interface IOAuthService {
  /**
   * Initiate OAuth flow for a specific broker
   */
  initiateAuth(params: OAuthInitParams): Promise<AuthResult>;

  /**
   * Handle OAuth callback from broker
   */
  handleCallback(brokerName: string, clientId: string, params: OAuthCallbackParams): Promise<TokenResult>;

  /**
   * Get current OAuth status for a broker account
   */
  getAuthStatus(brokerName: string, clientId: string): Promise<AuthStatus>;

  /**
   * Refresh OAuth token (if supported by broker)
   */
  refreshToken?(brokerName: string, clientId: string): Promise<TokenResult>;

  /**
   * Revoke OAuth token (if supported by broker)
   */
  revokeToken?(brokerName: string, clientId: string): Promise<boolean>;

  /**
   * Check if broker supports OAuth
   */
  supportsOAuth(brokerName: string): boolean;

  /**
   * Check if broker supports token refresh
   */
  supportsRefresh(brokerName: string): boolean;
}

/**
 * OAuth service configuration
 */
export interface OAuthServiceConfig {
  baseApiUrl: string;
  callbackBaseUrl: string;
  defaultTimeout: number;
}