/**
 * OAuth Context for Centralized State Management
 * Manages OAuth state across all brokers in the application
 */

import React, { createContext, useContext, useReducer, ReactNode, useCallback, useEffect } from 'react';
import { OAuthService } from '../services/oauth/OAuthService';
import { ZerodhaOAuthStrategy } from '../services/oauth/strategies/ZerodhaOAuthStrategy';
import { ZebuOAuthStrategy } from '../services/oauth/strategies/ZebuOAuthStrategy';
import {
  AuthStatus,
  OAuthInitParams,
  OAuthCallbackParams,
  TokenResult,
  AuthResult,
  OAuthEvent
} from '../types/oauth';
import { zerodhaConfig, zebuConfig } from '../config/brokerConfigs';

/**
 * OAuth state interface
 */
interface OAuthState {
  authStatuses: Map<string, AuthStatus>; // key: `${brokerName}-${clientId}`
  operations: Map<string, 'pending' | 'success' | 'error'>; // ongoing operations
  errors: Map<string, string>; // operation errors
  isInitialized: boolean;
}

/**
 * OAuth context value interface
 */
interface OAuthContextValue {
  // State
  authStatuses: Map<string, AuthStatus>;
  isInitialized: boolean;
  
  // Actions
  initiateAuth: (params: OAuthInitParams) => Promise<AuthResult>;
  handleCallback: (brokerName: string, clientId: string, params: OAuthCallbackParams) => Promise<TokenResult>;
  getAuthStatus: (brokerName: string, clientId: string) => Promise<AuthStatus>;
  refreshAuthStatus: (brokerName: string, clientId: string) => Promise<void>;
  refreshToken: (brokerName: string, clientId: string) => Promise<TokenResult>;
  clearError: (brokerName: string, clientId: string) => void;
  
  // Utilities
  isOperationPending: (brokerName: string, clientId: string) => boolean;
  getOperationError: (brokerName: string, clientId: string) => string | undefined;
  supportsOAuth: (brokerName: string) => boolean;
  requiresDailyAuth: (brokerName: string) => boolean;
}

/**
 * OAuth action types
 */
type OAuthAction =
  | { type: 'SET_INITIALIZED'; payload: boolean }
  | { type: 'SET_AUTH_STATUS'; payload: { key: string; status: AuthStatus } }
  | { type: 'SET_OPERATION_STATUS'; payload: { key: string; status: 'pending' | 'success' | 'error' } }
  | { type: 'SET_ERROR'; payload: { key: string; error: string } }
  | { type: 'CLEAR_ERROR'; payload: { key: string } }
  | { type: 'CLEAR_OPERATION'; payload: { key: string } };

/**
 * OAuth state reducer
 */
function oauthReducer(state: OAuthState, action: OAuthAction): OAuthState {
  switch (action.type) {
    case 'SET_INITIALIZED':
      return {
        ...state,
        isInitialized: action.payload
      };

    case 'SET_AUTH_STATUS':
      const newAuthStatuses = new Map(state.authStatuses);
      newAuthStatuses.set(action.payload.key, action.payload.status);
      return {
        ...state,
        authStatuses: newAuthStatuses
      };

    case 'SET_OPERATION_STATUS':
      const newOperations = new Map(state.operations);
      if (action.payload.status === 'pending') {
        newOperations.set(action.payload.key, action.payload.status);
      } else {
        newOperations.delete(action.payload.key);
      }
      return {
        ...state,
        operations: newOperations
      };

    case 'SET_ERROR':
      const newErrors = new Map(state.errors);
      newErrors.set(action.payload.key, action.payload.error);
      return {
        ...state,
        errors: newErrors
      };

    case 'CLEAR_ERROR':
      const clearedErrors = new Map(state.errors);
      clearedErrors.delete(action.payload.key);
      return {
        ...state,
        errors: clearedErrors
      };

    case 'CLEAR_OPERATION':
      const clearedOperations = new Map(state.operations);
      clearedOperations.delete(action.payload.key);
      return {
        ...state,
        operations: clearedOperations
      };

    default:
      return state;
  }
}

/**
 * Initial OAuth state
 */
const initialState: OAuthState = {
  authStatuses: new Map(),
  operations: new Map(),
  errors: new Map(),
  isInitialized: false
};

/**
 * OAuth context
 */
const OAuthContext = createContext<OAuthContextValue | undefined>(undefined);

/**
 * OAuth service instance (singleton)
 */
let oauthService: OAuthService | null = null;

/**
 * Get or create OAuth service instance
 */
function getOAuthService(): OAuthService {
  if (!oauthService) {
    const config = {
      baseApiUrl: process.env.REACT_APP_API_URL_DEV || '',
      callbackBaseUrl: window.location.origin,
      defaultTimeout: 30000
    };

    oauthService = new OAuthService(config);
    
    // Register broker strategies
    oauthService.registerStrategy('zerodha', new ZerodhaOAuthStrategy(zerodhaConfig, config.baseApiUrl));
    oauthService.registerStrategy('zebu', new ZebuOAuthStrategy(zebuConfig, config.baseApiUrl));

    // TODO: Register other broker strategies when implemented
    // oauthService.registerStrategy('angel', new AngelOneOAuthStrategy(angelOneConfig, config.baseApiUrl));
    // oauthService.registerStrategy('finvasia', new FinvasiaOAuthStrategy(finvasiaConfig, config.baseApiUrl));
  }

  return oauthService;
}

/**
 * OAuth Provider Props
 */
interface OAuthProviderProps {
  children: ReactNode;
}

/**
 * OAuth Provider Component
 */
export const OAuthProvider: React.FC<OAuthProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(oauthReducer, initialState);

  // Initialize OAuth service
  useEffect(() => {
    getOAuthService();
    dispatch({ type: 'SET_INITIALIZED', payload: true });
  }, []);

  /**
   * Generate cache key for broker account
   */
  const getCacheKey = useCallback((brokerName: string, clientId: string): string => {
    return `${brokerName.toLowerCase()}-${clientId}`;
  }, []);

  /**
   * Initiate OAuth authentication
   */
  const initiateAuth = useCallback(async (params: OAuthInitParams): Promise<AuthResult> => {
    const service = getOAuthService();
    const key = getCacheKey(params.brokerName, params.clientId);

    try {
      dispatch({ type: 'SET_OPERATION_STATUS', payload: { key, status: 'pending' } });
      dispatch({ type: 'CLEAR_ERROR', payload: { key } });

      const result = await service.initiateAuth(params);

      if (result.success) {
        dispatch({ type: 'SET_OPERATION_STATUS', payload: { key, status: 'success' } });
      } else {
        dispatch({ type: 'SET_OPERATION_STATUS', payload: { key, status: 'error' } });
        dispatch({ type: 'SET_ERROR', payload: { key, error: result.error || 'Auth initiation failed' } });
      }

      return result;
    } catch (error: any) {
      dispatch({ type: 'SET_OPERATION_STATUS', payload: { key, status: 'error' } });
      dispatch({ type: 'SET_ERROR', payload: { key, error: error.message } });
      throw error;
    }
  }, [getCacheKey]);

  /**
   * Handle OAuth callback
   */
  const handleCallback = useCallback(async (
    brokerName: string, 
    clientId: string, 
    params: OAuthCallbackParams
  ): Promise<TokenResult> => {
    const service = getOAuthService();
    const key = getCacheKey(brokerName, clientId);

    try {
      dispatch({ type: 'SET_OPERATION_STATUS', payload: { key, status: 'pending' } });
      dispatch({ type: 'CLEAR_ERROR', payload: { key } });

      const result = await service.handleCallback(brokerName, clientId, params);

      if (result.success) {
        dispatch({ type: 'SET_OPERATION_STATUS', payload: { key, status: 'success' } });
        
        // Update auth status after successful token exchange
        const authStatus = await service.getAuthStatus(brokerName, clientId);
        dispatch({ type: 'SET_AUTH_STATUS', payload: { key, status: authStatus } });
      } else {
        dispatch({ type: 'SET_OPERATION_STATUS', payload: { key, status: 'error' } });
        dispatch({ type: 'SET_ERROR', payload: { key, error: result.error || 'Callback handling failed' } });
      }

      return result;
    } catch (error: any) {
      dispatch({ type: 'SET_OPERATION_STATUS', payload: { key, status: 'error' } });
      dispatch({ type: 'SET_ERROR', payload: { key, error: error.message } });
      throw error;
    }
  }, [getCacheKey]);

  /**
   * Get OAuth authentication status
   */
  const getAuthStatus = useCallback(async (brokerName: string, clientId: string): Promise<AuthStatus> => {
    const service = getOAuthService();
    const key = getCacheKey(brokerName, clientId);

    try {
      const status = await service.getAuthStatus(brokerName, clientId);
      dispatch({ type: 'SET_AUTH_STATUS', payload: { key, status } });
      return status;
    } catch (error: any) {
      const errorStatus: AuthStatus = {
        hasToken: false,
        isValid: false,
        requiresLogin: true,
        error: error.message
      };
      dispatch({ type: 'SET_AUTH_STATUS', payload: { key, status: errorStatus } });
      return errorStatus;
    }
  }, [getCacheKey]);

  /**
   * Refresh authentication status
   */
  const refreshAuthStatus = useCallback(async (brokerName: string, clientId: string): Promise<void> => {
    await getAuthStatus(brokerName, clientId);
  }, [getAuthStatus]);

  /**
   * Refresh OAuth token
   */
  const refreshToken = useCallback(async (brokerName: string, clientId: string): Promise<TokenResult> => {
    const service = getOAuthService();
    const key = getCacheKey(brokerName, clientId);

    try {
      dispatch({ type: 'SET_OPERATION_STATUS', payload: { key, status: 'pending' } });
      dispatch({ type: 'CLEAR_ERROR', payload: { key } });

      const result = await service.refreshToken!(brokerName, clientId);

      if (result.success) {
        dispatch({ type: 'SET_OPERATION_STATUS', payload: { key, status: 'success' } });
        
        // Update auth status after successful token refresh
        const authStatus = await service.getAuthStatus(brokerName, clientId);
        dispatch({ type: 'SET_AUTH_STATUS', payload: { key, status: authStatus } });
      } else {
        dispatch({ type: 'SET_OPERATION_STATUS', payload: { key, status: 'error' } });
        dispatch({ type: 'SET_ERROR', payload: { key, error: result.error || 'Token refresh failed' } });
      }

      return result;
    } catch (error: any) {
      dispatch({ type: 'SET_OPERATION_STATUS', payload: { key, status: 'error' } });
      dispatch({ type: 'SET_ERROR', payload: { key, error: error.message } });
      throw error;
    }
  }, [getCacheKey]);

  /**
   * Clear operation error
   */
  const clearError = useCallback((brokerName: string, clientId: string): void => {
    const key = getCacheKey(brokerName, clientId);
    dispatch({ type: 'CLEAR_ERROR', payload: { key } });
  }, [getCacheKey]);

  /**
   * Check if operation is pending
   */
  const isOperationPending = useCallback((brokerName: string, clientId: string): boolean => {
    const key = getCacheKey(brokerName, clientId);
    return state.operations.get(key) === 'pending';
  }, [state.operations, getCacheKey]);

  /**
   * Get operation error
   */
  const getOperationError = useCallback((brokerName: string, clientId: string): string | undefined => {
    const key = getCacheKey(brokerName, clientId);
    return state.errors.get(key);
  }, [state.errors, getCacheKey]);

  /**
   * Check if broker supports OAuth
   */
  const supportsOAuth = useCallback((brokerName: string): boolean => {
    const service = getOAuthService();
    return service.supportsOAuth(brokerName);
  }, []);

  /**
   * Check if broker requires daily authentication
   */
  const requiresDailyAuth = useCallback((brokerName: string): boolean => {
    const service = getOAuthService();
    return service.requiresDailyAuth(brokerName);
  }, []);

  const value: OAuthContextValue = {
    // State
    authStatuses: state.authStatuses,
    isInitialized: state.isInitialized,
    
    // Actions
    initiateAuth,
    handleCallback,
    getAuthStatus,
    refreshAuthStatus,
    refreshToken,
    clearError,
    
    // Utilities
    isOperationPending,
    getOperationError,
    supportsOAuth,
    requiresDailyAuth
  };

  return (
    <OAuthContext.Provider value={value}>
      {children}
    </OAuthContext.Provider>
  );
};

/**
 * Custom hook to use OAuth context
 */
export const useOAuth = (): OAuthContextValue => {
  const context = useContext(OAuthContext);
  if (context === undefined) {
    throw new Error('useOAuth must be used within an OAuthProvider');
  }
  return context;
};