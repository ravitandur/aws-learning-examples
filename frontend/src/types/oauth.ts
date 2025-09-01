/**
 * OAuth Types and Interfaces for Broker Integration
 * Supports multiple brokers with different OAuth flows
 */

export type AuthFlowType = 'popup' | 'redirect' | 'embedded';
export type TokenType = 'session' | 'refresh' | 'bearer';
export type ExpiryType = 'daily' | 'fixed' | 'refresh';

/**
 * Configuration for broker-specific OAuth settings
 */
export interface BrokerOAuthConfig {
  brokerName: string;
  displayName: string;
  authFlow: AuthFlowType;
  tokenType: TokenType;
  expiryType: ExpiryType;
  requiresDaily: boolean;
  popupDimensions?: {
    width: number;
    height: number;
  };
  scopes?: string[];
  metadata?: {
    tokenExpiryTime?: string; // e.g., "6:00 AM IST" for Zerodha
    refreshable?: boolean;
    multiStep?: boolean;
  };
}

/**
 * OAuth initialization parameters
 */
export interface OAuthInitParams {
  clientId: string;
  brokerName: string;
  callbackUrl?: string;
  state?: string;
  scopes?: string[];
}

/**
 * OAuth callback parameters received from broker
 */
export interface OAuthCallbackParams {
  request_token?: string;
  authorization_code?: string;
  state?: string;
  error?: string;
  error_description?: string;
  [key: string]: any; // Allow for broker-specific parameters
}

/**
 * OAuth authentication result
 */
export interface AuthResult {
  success: boolean;
  oauthUrl?: string;
  state?: string;
  expiresIn?: number;
  error?: string;
  message?: string;
}

/**
 * Token exchange result
 */
export interface TokenResult {
  success: boolean;
  data?: {
    access_token?: string;
    refresh_token?: string;
    token_type?: string;
    expires_in?: number;
    expires_at?: string;
    scope?: string;
    valid_until?: string;
  };
  error?: string;
  message?: string;
}

/**
 * OAuth status information
 */
export interface AuthStatus {
  hasToken: boolean;
  isValid: boolean;
  expiresAt?: string;
  lastLogin?: string;
  requiresLogin: boolean;
  tokenType?: TokenType;
  error?: string;
}

/**
 * OAuth operation result
 */
export interface OAuthOperation {
  type: 'INIT' | 'CALLBACK' | 'STATUS' | 'REFRESH';
  brokerName: string;
  clientId: string;
  status: 'pending' | 'success' | 'error';
  result?: AuthResult | TokenResult | AuthStatus;
  error?: string;
}

/**
 * OAuth event types for communication between components
 */
export interface OAuthEvent {
  type: 'OAUTH_SUCCESS' | 'OAUTH_ERROR' | 'OAUTH_PROGRESS';
  brokerName: string;
  clientId: string;
  data?: any;
  error?: string;
}

/**
 * OAuth button component props
 */
export interface OAuthButtonProps {
  brokerAccount: {
    client_id: string;
    broker_name: string;
    account_status: string;
  };
  onAuthSuccess?: (result: TokenResult) => void;
  onAuthError?: (error: string) => void;
  disabled?: boolean;
  className?: string;
}

/**
 * OAuth status display props
 */
export interface OAuthStatusProps {
  status: AuthStatus;
  brokerName: string;
  className?: string;
}