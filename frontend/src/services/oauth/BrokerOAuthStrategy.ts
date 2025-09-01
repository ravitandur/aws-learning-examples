/**
 * Abstract OAuth Strategy for Broker-Specific Implementations
 * Each broker extends this class to implement their specific OAuth flow
 */

import {
  OAuthInitParams,
  OAuthCallbackParams,
  AuthResult,
  TokenResult,
  AuthStatus,
  BrokerOAuthConfig
} from '../../types/oauth';

/**
 * Abstract base class for broker-specific OAuth strategies
 */
export abstract class BrokerOAuthStrategy {
  protected config: BrokerOAuthConfig;
  protected apiBaseUrl: string;

  constructor(config: BrokerOAuthConfig, apiBaseUrl: string) {
    this.config = config;
    this.apiBaseUrl = apiBaseUrl;
  }

  /**
   * Get broker configuration
   */
  getConfig(): BrokerOAuthConfig {
    return this.config;
  }

  /**
   * Initiate OAuth authentication flow
   * This method handles the broker-specific OAuth initiation
   */
  abstract initiateAuth(params: OAuthInitParams): Promise<AuthResult>;

  /**
   * Handle OAuth callback from broker
   * Process the callback parameters and exchange for tokens
   */
  abstract handleCallback(clientId: string, params: OAuthCallbackParams): Promise<TokenResult>;

  /**
   * Get current OAuth authentication status
   * Check if user has valid tokens for this broker
   */
  abstract getAuthStatus(clientId: string): Promise<AuthStatus>;

  /**
   * Refresh OAuth token (optional - only if broker supports it)
   */
  async refreshToken?(clientId: string): Promise<TokenResult>;

  /**
   * Revoke OAuth token (optional - only if broker supports it)
   */
  async revokeToken?(clientId: string): Promise<boolean>;

  /**
   * Validate OAuth callback parameters
   * Check if the callback contains required parameters for this broker
   */
  protected validateCallbackParams(params: OAuthCallbackParams): boolean {
    // Basic validation - subclasses can override for broker-specific validation
    return !params.error;
  }

  /**
   * Generate callback URL for this broker
   */
  protected generateCallbackUrl(baseUrl: string): string {
    return `${baseUrl}/oauth/callback`;
  }

  /**
   * Handle OAuth errors in a consistent way
   */
  protected handleOAuthError(error: any, operation: string): never {
    const errorMessage = error?.response?.data?.message || 
                        error?.message || 
                        `${operation} failed for ${this.config.brokerName}`;
    
    console.error(`OAuth ${operation} error for ${this.config.brokerName}:`, error);
    throw new Error(errorMessage);
  }

  /**
   * Create standardized auth result
   */
  protected createAuthResult(
    success: boolean, 
    oauthUrl?: string, 
    state?: string, 
    error?: string
  ): AuthResult {
    return {
      success,
      oauthUrl,
      state,
      error,
      expiresIn: success ? 300 : undefined, // 5 minutes default for state expiry
      message: success ? 'OAuth URL generated successfully' : error
    };
  }

  /**
   * Create standardized token result
   */
  protected createTokenResult(
    success: boolean,
    data?: any,
    error?: string
  ): TokenResult {
    return {
      success,
      data,
      error,
      message: success ? 'Token obtained successfully' : error
    };
  }

  /**
   * Create standardized auth status
   */
  protected createAuthStatus(
    hasToken: boolean,
    isValid: boolean,
    expiresAt?: string,
    lastLogin?: string,
    error?: string
  ): AuthStatus {
    return {
      hasToken,
      isValid,
      expiresAt,
      lastLogin,
      requiresLogin: !isValid,
      tokenType: this.config.tokenType,
      error
    };
  }

  /**
   * Check if this strategy supports token refresh
   */
  supportsRefresh(): boolean {
    return this.config.expiryType === 'refresh' && !!this.refreshToken;
  }

  /**
   * Check if this strategy requires daily authentication
   */
  requiresDailyAuth(): boolean {
    return this.config.requiresDaily;
  }

  /**
   * Get popup dimensions for this broker
   */
  getPopupDimensions(): { width: number; height: number } {
    return this.config.popupDimensions || { width: 500, height: 600 };
  }
}