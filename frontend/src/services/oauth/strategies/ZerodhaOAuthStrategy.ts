/**
 * Zerodha OAuth Strategy Implementation
 * Handles Zerodha Kite Connect specific OAuth flow
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
 * Zerodha Kite Connect OAuth strategy
 * Implements popup-based OAuth flow with daily session tokens
 */
export class ZerodhaOAuthStrategy extends BrokerOAuthStrategy {
  constructor(config: BrokerOAuthConfig, apiBaseUrl: string) {
    super(config, apiBaseUrl);
  }

  /**
   * Initiate Zerodha OAuth flow
   */
  async initiateAuth(params: OAuthInitParams): Promise<AuthResult> {
    try {
      console.log('Initiating Zerodha OAuth for client:', params.clientId);

      // Call backend to get Zerodha OAuth URL
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

      // Prepare the OAuth URL with callback
      const callbackUrl = encodeURIComponent(this.generateCallbackUrl(window.location.origin));
      const fullOAuthUrl = `${oauth_url}&redirect_uri=${callbackUrl}`;

      return this.createAuthResult(true, fullOAuthUrl, state);
    } catch (error: any) {
      console.error('Zerodha OAuth initiation failed:', error);
      return this.createAuthResult(false, undefined, undefined, error.message);
    }
  }

  /**
   * Handle Zerodha OAuth callback
   */
  async handleCallback(clientId: string, params: OAuthCallbackParams): Promise<TokenResult> {
    try {
      console.log('Handling Zerodha OAuth callback for client:', clientId);

      // Validate callback parameters
      if (!this.validateZerodhaCallback(params)) {
        throw new Error('Invalid callback parameters received from Zerodha');
      }

      const { request_token, state } = params;

      // Validate state parameter
      const storedState = this.getStoredOAuthState(clientId);
      if (storedState && state && state !== storedState) {
        console.error('State mismatch:', { stored: storedState, received: state, clientId });
        throw new Error('State parameter mismatch - potential security issue');
      }
      
      // Log for debugging
      console.log('OAuth callback validation:', { 
        clientId, 
        hasStoredState: !!storedState, 
        hasReceivedState: !!state, 
        statesMatch: !storedState || !state || storedState === state 
      });

      // Exchange request token for access token via backend
      const response = await brokerService.handleOAuthCallback(clientId, request_token!, state || '');
      
      // Clean up stored state
      this.clearOAuthState(clientId);

      if (response.success && response.data) {
        return this.createTokenResult(true, response.data);
      } else {
        throw new Error(response.message || 'Token exchange failed');
      }
    } catch (error: any) {
      console.error('Zerodha OAuth callback handling failed:', error);
      // Clean up stored state on error
      this.clearOAuthState(clientId);
      return this.createTokenResult(false, undefined, error.message);
    }
  }

  /**
   * Get Zerodha OAuth authentication status
   */
  async getAuthStatus(clientId: string): Promise<AuthStatus> {
    try {
      console.log('Getting Zerodha OAuth status for client:', clientId);

      const response = await brokerService.getOAuthStatus(clientId);
      
      if (response.data) {
        const { has_token, is_valid, expires_at, last_login } = response.data;
        return this.createAuthStatus(has_token, is_valid, expires_at, last_login);
      } else {
        return this.createAuthStatus(false, false);
      }
    } catch (error: any) {
      console.error('Failed to get Zerodha OAuth status:', error);
      return this.createAuthStatus(false, false, undefined, undefined, error.message);
    }
  }

  /**
   * Validate Zerodha-specific callback parameters
   */
  private validateZerodhaCallback(params: OAuthCallbackParams): boolean {
    // Check for error status from Zerodha
    if (params.status === 'error') {
      throw new Error('OAuth authentication was cancelled or failed');
    }

    // Zerodha must provide request_token
    if (!params.request_token) {
      throw new Error('No request token received from Zerodha. Please try again.');
    }

    return true;
  }

  /**
   * Store OAuth state in localStorage
   */
  private storeOAuthState(clientId: string, state: string): void {
    localStorage.setItem('oauth_client_id', clientId);
    localStorage.setItem('oauth_state', state);
    localStorage.setItem('oauth_broker', 'zerodha');
  }

  /**
   * Get stored OAuth state from localStorage
   */
  private getStoredOAuthState(clientId: string): string | null {
    const storedClientId = localStorage.getItem('oauth_client_id');
    const storedBroker = localStorage.getItem('oauth_broker');
    
    // Validate that the stored state matches the current request
    if (storedClientId !== clientId || storedBroker !== 'zerodha') {
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
   * Zerodha doesn't support token refresh - tokens expire daily
   */
  async refreshToken(clientId: string): Promise<TokenResult> {
    return this.createTokenResult(
      false, 
      undefined, 
      'Zerodha tokens cannot be refreshed - please re-authenticate'
    );
  }

  /**
   * Zerodha doesn't support explicit token revocation
   */
  async revokeToken(clientId: string): Promise<boolean> {
    console.warn('Zerodha does not support explicit token revocation');
    return false;
  }

  /**
   * Get Zerodha-specific popup dimensions
   */
  getPopupDimensions(): { width: number; height: number } {
    return { width: 600, height: 700 }; // Optimized for Zerodha login form
  }

  /**
   * Zerodha requires daily authentication (tokens expire at 6 AM IST)
   */
  requiresDailyAuth(): boolean {
    return true;
  }

  /**
   * Zerodha does not support token refresh
   */
  supportsRefresh(): boolean {
    return false;
  }
}