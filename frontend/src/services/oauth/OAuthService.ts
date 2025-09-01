/**
 * Main OAuth Service Implementation
 * Coordinates OAuth operations across different brokers using strategy pattern
 */

import {
  IOAuthService,
  OAuthServiceConfig
} from './IOAuthService';
import {
  OAuthInitParams,
  OAuthCallbackParams,
  AuthResult,
  TokenResult,
  AuthStatus
} from '../../types/oauth';
import { BrokerOAuthStrategy } from './BrokerOAuthStrategy';
import { getBrokerConfig, supportsOAuth as brokerSupportsOAuth } from '../../config/brokerConfigs';

/**
 * OAuth service that uses strategy pattern for broker-specific implementations
 */
export class OAuthService implements IOAuthService {
  private strategies: Map<string, BrokerOAuthStrategy> = new Map();
  private config: OAuthServiceConfig;

  constructor(config: OAuthServiceConfig) {
    this.config = config;
  }

  /**
   * Register a broker OAuth strategy
   */
  registerStrategy(brokerName: string, strategy: BrokerOAuthStrategy): void {
    this.strategies.set(brokerName.toLowerCase(), strategy);
  }

  /**
   * Get strategy for a specific broker
   */
  private getStrategy(brokerName: string): BrokerOAuthStrategy {
    const strategy = this.strategies.get(brokerName.toLowerCase());
    if (!strategy) {
      throw new Error(`OAuth strategy not found for broker: ${brokerName}`);
    }
    return strategy;
  }

  /**
   * Initiate OAuth flow for a specific broker
   */
  async initiateAuth(params: OAuthInitParams): Promise<AuthResult> {
    try {
      if (!this.supportsOAuth(params.brokerName)) {
        throw new Error(`OAuth not supported for broker: ${params.brokerName}`);
      }

      const strategy = this.getStrategy(params.brokerName);
      return await strategy.initiateAuth(params);
    } catch (error: any) {
      console.error('OAuth initiation failed:', error);
      return {
        success: false,
        error: error.message || 'Failed to initiate OAuth',
        message: `OAuth initiation failed for ${params.brokerName}`
      };
    }
  }

  /**
   * Handle OAuth callback from broker
   */
  async handleCallback(
    brokerName: string, 
    clientId: string, 
    params: OAuthCallbackParams
  ): Promise<TokenResult> {
    try {
      if (!this.supportsOAuth(brokerName)) {
        throw new Error(`OAuth not supported for broker: ${brokerName}`);
      }

      const strategy = this.getStrategy(brokerName);
      return await strategy.handleCallback(clientId, params);
    } catch (error: any) {
      console.error('OAuth callback handling failed:', error);
      return {
        success: false,
        error: error.message || 'Failed to handle OAuth callback',
        message: `OAuth callback failed for ${brokerName}`
      };
    }
  }

  /**
   * Get current OAuth status for a broker account
   */
  async getAuthStatus(brokerName: string, clientId: string): Promise<AuthStatus> {
    try {
      if (!this.supportsOAuth(brokerName)) {
        return {
          hasToken: false,
          isValid: false,
          requiresLogin: true,
          error: `OAuth not supported for ${brokerName}`
        };
      }

      const strategy = this.getStrategy(brokerName);
      return await strategy.getAuthStatus(clientId);
    } catch (error: any) {
      console.error('OAuth status check failed:', error);
      return {
        hasToken: false,
        isValid: false,
        requiresLogin: true,
        error: error.message || 'Failed to get OAuth status'
      };
    }
  }

  /**
   * Refresh OAuth token (if supported by broker)
   */
  async refreshToken(brokerName: string, clientId: string): Promise<TokenResult> {
    try {
      if (!this.supportsRefresh(brokerName)) {
        throw new Error(`Token refresh not supported for broker: ${brokerName}`);
      }

      const strategy = this.getStrategy(brokerName);
      if (!strategy.refreshToken) {
        throw new Error(`Refresh token method not implemented for: ${brokerName}`);
      }

      return await strategy.refreshToken(clientId);
    } catch (error: any) {
      console.error('OAuth token refresh failed:', error);
      return {
        success: false,
        error: error.message || 'Failed to refresh OAuth token',
        message: `Token refresh failed for ${brokerName}`
      };
    }
  }

  /**
   * Revoke OAuth token (if supported by broker)
   */
  async revokeToken(brokerName: string, clientId: string): Promise<boolean> {
    try {
      if (!this.supportsOAuth(brokerName)) {
        return false;
      }

      const strategy = this.getStrategy(brokerName);
      if (!strategy.revokeToken) {
        console.warn(`Token revocation not supported for: ${brokerName}`);
        return false;
      }

      return await strategy.revokeToken(clientId);
    } catch (error: any) {
      console.error('OAuth token revocation failed:', error);
      return false;
    }
  }

  /**
   * Check if broker supports OAuth
   */
  supportsOAuth(brokerName: string): boolean {
    return brokerSupportsOAuth(brokerName) && this.strategies.has(brokerName.toLowerCase());
  }

  /**
   * Check if broker supports token refresh
   */
  supportsRefresh(brokerName: string): boolean {
    if (!this.supportsOAuth(brokerName)) {
      return false;
    }

    try {
      const strategy = this.getStrategy(brokerName);
      return strategy.supportsRefresh();
    } catch {
      return false;
    }
  }

  /**
   * Get list of registered OAuth brokers
   */
  getRegisteredBrokers(): string[] {
    return Array.from(this.strategies.keys());
  }

  /**
   * Get broker configuration
   */
  getBrokerConfig(brokerName: string) {
    return getBrokerConfig(brokerName);
  }

  /**
   * Check if broker requires daily authentication
   */
  requiresDailyAuth(brokerName: string): boolean {
    if (!this.supportsOAuth(brokerName)) {
      return false;
    }

    try {
      const strategy = this.getStrategy(brokerName);
      return strategy.requiresDailyAuth();
    } catch {
      return false;
    }
  }

  /**
   * Get popup dimensions for broker
   */
  getPopupDimensions(brokerName: string): { width: number; height: number } {
    if (!this.supportsOAuth(brokerName)) {
      return { width: 500, height: 600 };
    }

    try {
      const strategy = this.getStrategy(brokerName);
      return strategy.getPopupDimensions();
    } catch {
      return { width: 500, height: 600 };
    }
  }
}