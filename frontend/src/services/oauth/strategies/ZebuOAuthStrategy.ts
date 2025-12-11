/**
 * Zebu MYNT OAuth Strategy Implementation
 * Handles Zebu MYNT API specific OAuth flow
 * Documentation: https://api.zebuetrade.com/OAuth/
 */

import { BrokerOAuthStrategy } from '../BrokerOAuthStrategy';
import {
  OAuthInitParams,
  OAuthCallbackParams,
  AuthResult,
  TokenResult,
  AuthStatus,
  BrokerOAuthConfig
} from '../../../types/oauth';
import brokerService from '../../brokerService';

/**
 * Zebu MYNT OAuth strategy
 * Implements popup-based OAuth flow with refreshable bearer tokens
 *
 * OAuth Flow:
 * 1. User redirected to: https://go.mynt.in/OAuthlogin/authorize/oauth?client_id={api_key}
 * 2. User logs in and authorizes
 * 3. Redirect to callback URL with authorization code
 * 4. Exchange code for access_token via backend
 * 5. Access token can be refreshed (1 hour validity)
 */
export class ZebuOAuthStrategy extends BrokerOAuthStrategy {
  constructor(config: BrokerOAuthConfig, apiBaseUrl: string) {
    super(config, apiBaseUrl);
  }

  /**
   * Initiate Zebu OAuth flow
   */
  async initiateAuth(params: OAuthInitParams): Promise<AuthResult> {
    try {
      console.log('Initiating Zebu OAuth for client:', params.clientId);

      // Call backend to get Zebu OAuth URL
      const response = await brokerService.initiateOAuthLogin(params.clientId);

      if (!response.data) {
        throw new Error('No response data from OAuth initiation');
      }

      const { oauth_url, state } = response.data;

      if (!oauth_url) {
        throw new Error('OAuth URL not received from backend');
      }

      // Store OAuth state data in localStorage for callback
      this.storeOAuthState(params.clientId, state);

      // Zebu OAuth URL - redirect_uri is handled by frontend
      const callbackUrl = encodeURIComponent(this.generateCallbackUrl(window.location.origin));
      const fullOAuthUrl = `${oauth_url}&redirect_uri=${callbackUrl}`;

      return this.createAuthResult(true, fullOAuthUrl, state);
    } catch (error: any) {
      console.error('Zebu OAuth initiation failed:', error);
      return this.createAuthResult(false, undefined, undefined, error.message);
    }
  }

  /**
   * Handle Zebu OAuth callback
   */
  async handleCallback(clientId: string, params: OAuthCallbackParams): Promise<TokenResult> {
    try {
      console.log('Handling Zebu OAuth callback for client:', clientId);

      // Validate callback parameters
      if (!this.validateZebuCallback(params)) {
        throw new Error('Invalid callback parameters received from Zebu');
      }

      // Zebu returns 'code' instead of 'request_token'
      const code = params.code || params.request_token;
      const { state } = params;

      // Validate state parameter
      const storedState = this.getStoredOAuthState(clientId);

      // Use stored state if not in callback (some OAuth providers don't return state)
      const finalState = state || storedState || '';

      if (storedState && state && state !== storedState) {
        console.error('State mismatch:', { stored: storedState, received: state, clientId });
        throw new Error('State parameter mismatch - potential security issue');
      }

      console.log('OAuth callback validation:', {
        clientId,
        hasStoredState: !!storedState,
        hasReceivedState: !!state,
        finalState: finalState,
        statesMatch: !storedState || !state || storedState === state
      });

      // Exchange authorization code for access token via backend
      const response = await brokerService.handleOAuthCallback(clientId, code!, finalState);

      // Clean up stored state
      this.clearOAuthState(clientId);

      if (response.success && response.data) {
        return this.createTokenResult(true, response.data);
      } else {
        throw new Error(response.message || 'Token exchange failed');
      }
    } catch (error: any) {
      console.error('Zebu OAuth callback handling failed:', error);
      // Clean up stored state on error
      this.clearOAuthState(clientId);
      return this.createTokenResult(false, undefined, error.message);
    }
  }

  /**
   * Get Zebu OAuth authentication status
   */
  async getAuthStatus(clientId: string): Promise<AuthStatus> {
    try {
      console.log('Getting Zebu OAuth status for client:', clientId);

      const response = await brokerService.getOAuthStatus(clientId);

      if (response.data) {
        const { has_token, is_valid, expires_at, last_login } = response.data;
        return this.createAuthStatus(has_token, is_valid, expires_at, last_login);
      } else {
        return this.createAuthStatus(false, false);
      }
    } catch (error: any) {
      console.error('Failed to get Zebu OAuth status:', error);
      return this.createAuthStatus(false, false, undefined, undefined, error.message);
    }
  }

  /**
   * Validate Zebu-specific callback parameters
   */
  private validateZebuCallback(params: OAuthCallbackParams): boolean {
    // Check for error from OAuth provider
    if (params.error) {
      const errorDesc = params.error_description || 'OAuth authentication failed';
      throw new Error(`OAuth error: ${errorDesc}`);
    }

    // Zebu returns 'code' as authorization code
    const code = params.code || params.request_token;
    if (!code) {
      throw new Error('No authorization code received from Zebu. Please try again.');
    }

    return true;
  }

  /**
   * Store OAuth state in localStorage
   */
  private storeOAuthState(clientId: string, state: string): void {
    localStorage.setItem('oauth_client_id', clientId);
    localStorage.setItem('oauth_state', state);
    localStorage.setItem('oauth_broker', 'zebu');
  }

  /**
   * Get stored OAuth state from localStorage
   */
  private getStoredOAuthState(clientId: string): string | null {
    const storedClientId = localStorage.getItem('oauth_client_id');
    const storedBroker = localStorage.getItem('oauth_broker');

    // Validate that the stored state matches the current request
    if (storedClientId !== clientId || storedBroker !== 'zebu') {
      return null;
    }

    return localStorage.getItem('oauth_state');
  }

  /**
   * Clear OAuth state from localStorage
   */
  private clearOAuthState(clientId: string): void {
    localStorage.removeItem('oauth_client_id');
    localStorage.removeItem('oauth_state');
    localStorage.removeItem('oauth_broker');
  }

  /**
   * Refresh Zebu access token using refresh token
   */
  async refreshToken(clientId: string): Promise<TokenResult> {
    try {
      console.log('Refreshing Zebu token for client:', clientId);

      // Call backend refresh endpoint
      const response = await brokerService.refreshOAuthToken(clientId);

      if (response.success && response.data) {
        return this.createTokenResult(true, response.data);
      } else {
        throw new Error(response.message || 'Token refresh failed');
      }
    } catch (error: any) {
      console.error('Zebu token refresh failed:', error);
      return this.createTokenResult(false, undefined, error.message);
    }
  }

  /**
   * Zebu doesn't support explicit token revocation
   */
  async revokeToken(clientId: string): Promise<boolean> {
    console.warn('Zebu does not support explicit token revocation');
    return false;
  }

  /**
   * Get Zebu-specific popup dimensions
   */
  getPopupDimensions(): { width: number; height: number } {
    return { width: 500, height: 650 }; // Optimized for Zebu login form
  }

  /**
   * Zebu does not require daily authentication (tokens are refreshable)
   */
  requiresDailyAuth(): boolean {
    return false;
  }

  /**
   * Zebu supports token refresh
   */
  supportsRefresh(): boolean {
    return true;
  }
}
