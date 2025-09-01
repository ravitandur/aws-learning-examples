/**
 * Generic OAuth Button Component
 * Works with any broker using the OAuth context and strategy pattern
 */

import React, { useState, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';
import { useOAuth } from '../../context/OAuthContext';
import { OAuthButtonProps, AuthStatus } from '../../types/oauth';
import { getBrokerConfig, getPopupDimensions } from '../../config/brokerConfigs';

/**
 * Generic OAuth button that works with any broker
 */
export const OAuthButton: React.FC<OAuthButtonProps> = ({
  brokerAccount,
  onAuthSuccess,
  onAuthError,
  disabled = false,
  className = ''
}) => {
  const {
    authStatuses,
    initiateAuth,
    getAuthStatus,
    refreshAuthStatus,
    isOperationPending,
    getOperationError,
    supportsOAuth,
    clearError
  } = useOAuth();

  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null);
  const [oauthError, setOauthError] = useState<string | null>(null);

  const brokerName = brokerAccount.broker_name;
  const clientId = brokerAccount.client_id;
  const cacheKey = `${brokerName.toLowerCase()}-${clientId}`;

  // Get auth status from context or fetch it
  useEffect(() => {
    const contextStatus = authStatuses.get(cacheKey);
    if (contextStatus) {
      setAuthStatus(contextStatus);
    } else {
      // Fetch status if not in context
      loadAuthStatus();
    }
  }, [authStatuses, cacheKey]);

  // Clear any stale OAuth state on component mount
  useEffect(() => {
    const storedClientId = localStorage.getItem('oauth_client_id');
    const storedBroker = localStorage.getItem('oauth_broker');
    
    // If there's stale OAuth state for a different client or broker, clear it
    if (storedClientId !== clientId || storedBroker !== brokerName.toLowerCase()) {
      localStorage.removeItem('oauth_client_id');
      localStorage.removeItem('oauth_state');
      localStorage.removeItem('oauth_broker');
      console.log('Cleared stale OAuth state for different client/broker');
    }
  }, [clientId, brokerName]);

  // Update error from context
  useEffect(() => {
    const contextError = getOperationError(brokerName, clientId);
    setOauthError(contextError || null);
  }, [getOperationError, brokerName, clientId]);

  /**
   * Load OAuth authentication status
   */
  const loadAuthStatus = async () => {
    try {
      const status = await getAuthStatus(brokerName, clientId);
      setAuthStatus(status);
    } catch (error: any) {
      console.error('Failed to load OAuth status:', error);
      setOauthError(error.message);
    }
  };

  /**
   * Handle OAuth authentication
   */
  const handleOAuthLogin = async () => {
    if (!supportsOAuth(brokerName)) {
      const errorMsg = `OAuth login is not supported for ${brokerName} accounts`;
      setOauthError(errorMsg);
      onAuthError?.(errorMsg);
      return;
    }

    // Don't proceed if already connected
    if (isConnected) {
      console.log('OAuth already connected, ignoring click');
      return;
    }

    // Clear any existing errors and stale OAuth state
    clearError(brokerName, clientId);
    setOauthError(null);
    
    // Clear any stale OAuth state from localStorage
    localStorage.removeItem('oauth_client_id');
    localStorage.removeItem('oauth_state');
    localStorage.removeItem('oauth_broker');

    try {
      // Step 1: Initiate OAuth flow
      const loginResponse = await initiateAuth({
        brokerName,
        clientId,
        callbackUrl: `${window.location.origin}/oauth/callback`
      });

      if (!loginResponse.success || !loginResponse.oauthUrl) {
        throw new Error(loginResponse.error || 'No OAuth URL received');
      }

      // Step 2: Open OAuth popup
      const config = getBrokerConfig(brokerName);
      const popupDimensions = getPopupDimensions(brokerName);
      
      const popup = window.open(
        loginResponse.oauthUrl,
        `${brokerName}-oauth`,
        `width=${popupDimensions.width},height=${popupDimensions.height},scrollbars=yes,resizable=yes`
      );

      if (!popup) {
        throw new Error('Popup blocked. Please allow popups and try again.');
      }

      // Step 3: Listen for postMessage from callback
      const handleMessage = (event: MessageEvent) => {
        // Security check - ensure message is from our origin
        if (event.origin !== window.location.origin) {
          console.warn('Ignoring message from unknown origin:', event.origin);
          return;
        }

        console.log('Received OAuth message:', event.data);

        if (event.data.type === `${brokerName.toUpperCase()}_OAUTH_SUCCESS`) {
          console.log('OAuth success received for', brokerName);
          
          // Update auth status
          refreshAuthStatus(brokerName, clientId);
          
          // Call success handler
          onAuthSuccess?.(event.data.data);
          
          // Clean up listener
          window.removeEventListener('message', handleMessage);
          
        } else if (event.data.type === `${brokerName.toUpperCase()}_OAUTH_ERROR`) {
          console.log('OAuth error received for', brokerName, event.data.error);
          const errorMsg = event.data.error || 'OAuth authentication failed';
          setOauthError(errorMsg);
          onAuthError?.(errorMsg);
          
          // Clean up listener
          window.removeEventListener('message', handleMessage);
        }
      };

      // Add message event listener
      window.addEventListener('message', handleMessage);

      // Step 4: Monitor popup closure (fallback)
      const checkClosed = setInterval(() => {
        if (popup.closed) {
          clearInterval(checkClosed);
          console.log('OAuth popup closed for', brokerName);
          
          // Remove message listener if popup was closed manually
          window.removeEventListener('message', handleMessage);
          
          // Note: Don't show error if user just cancelled
        }
      }, 1000);

      // Timeout after 10 minutes
      setTimeout(() => {
        clearInterval(checkClosed);
        window.removeEventListener('message', handleMessage);
        
        if (!popup.closed) {
          popup.close();
        }
        
        // Only show timeout error if still loading
        if (isOperationPending(brokerName, clientId)) {
          const timeoutError = 'OAuth login timed out. Please try again.';
          setOauthError(timeoutError);
          onAuthError?.(timeoutError);
        }
      }, 600000); // 10 minutes

    } catch (error: any) {
      console.error('OAuth initiation error:', error);
      const errorMsg = error.message || 'Failed to initiate OAuth login';
      setOauthError(errorMsg);
      onAuthError?.(errorMsg);
    }
  };

  /**
   * Dismiss OAuth error
   */
  const dismissError = () => {
    setOauthError(null);
    clearError(brokerName, clientId);
  };

  // Don't render if broker doesn't support OAuth
  if (!supportsOAuth(brokerName)) {
    return null;
  }

  const isLoading = isOperationPending(brokerName, clientId);
  const isConnected = authStatus?.hasToken && authStatus?.isValid;
  const isDisabled = disabled || isLoading || isConnected || brokerAccount.account_status !== 'enabled';

  const buttonClass = `
    flex-1 px-4 py-2 text-sm font-medium rounded-lg transition-colors
    ${isConnected 
      ? 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-300 cursor-not-allowed'
      : isDisabled
        ? 'bg-orange-300 dark:bg-orange-800 text-white cursor-not-allowed'
        : 'bg-orange-600 hover:bg-orange-700 text-white'
    }
    ${className}
  `;

  const getButtonText = (): string => {
    if (isLoading) {
      return 'Connecting...';
    }
    
    if (isConnected) {
      return 'OAuth Connected';
    }
    
    return 'Connect OAuth';
  };

  return (
    <div className="space-y-2">
      {/* OAuth Error */}
      {oauthError && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-600 dark:text-red-400">{oauthError}</p>
          <button
            onClick={dismissError}
            className="text-xs text-red-500 hover:text-red-700 mt-1 underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* OAuth Button */}
      <button
        onClick={handleOAuthLogin}
        disabled={isDisabled}
        className={buttonClass}
        title={isConnected ? 'OAuth is already connected' : `Connect ${brokerName} OAuth`}
      >
        {isLoading && <RefreshCw className="w-4 h-4 mr-2 animate-spin" />}
        {getButtonText()}
      </button>
    </div>
  );
};