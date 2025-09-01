import React, { useEffect, useState } from 'react';
import { RefreshCw, CheckCircle, XCircle } from 'lucide-react';
import { useOAuth } from '../../context/OAuthContext';
import { getBrokerConfig } from '../../config/brokerConfigs';

const OAuthCallback: React.FC = () => {
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [message, setMessage] = useState('Processing OAuth callback...');
  const [details, setDetails] = useState<string>('');
  const [brokerName, setBrokerName] = useState<string>('');
  const { handleCallback } = useOAuth();

  useEffect(() => {
    const processCallback = async () => {
      try {
        // Extract parameters from URL
        const urlParams = new URLSearchParams(window.location.search);
        const requestToken = urlParams.get('request_token');
        const state = urlParams.get('state');
        const status = urlParams.get('status');
        const error = urlParams.get('error');
        const errorDescription = urlParams.get('error_description');

        // Get broker details from localStorage (stored during OAuth initiation)
        const clientId = localStorage.getItem('oauth_client_id');
        const storedState = localStorage.getItem('oauth_state');
        const storedBroker = localStorage.getItem('oauth_broker');
        
        if (!clientId || !storedBroker) {
          throw new Error('OAuth session not found. Please restart the OAuth process.');
        }

        setBrokerName(storedBroker);
        setMessage(`Processing ${storedBroker} OAuth callback...`);

        // Check for OAuth error parameters
        if (error || status === 'error') {
          const errorMsg = errorDescription || error || 'OAuth authentication was cancelled or failed';
          throw new Error(errorMsg);
        }
        
        // Validate required parameters based on broker
        if (!requestToken && storedBroker.toLowerCase() === 'zerodha') {
          throw new Error(`No request token received from ${storedBroker}. Please try again.`);
        }
        
        // Use stored state if no state in URL (Zerodha doesn't return state in callback)
        const finalState = state || storedState;
        
        // Basic state validation
        if (storedState && state && state !== storedState) {
          throw new Error('State parameter mismatch - potential security issue');
        }

        setMessage(`Exchanging tokens with ${storedBroker}...`);

        // Use the OAuth context to handle the callback
        const callbackParams: any = {
          request_token: requestToken || undefined,
          state: finalState || undefined
        };
        
        if (status) callbackParams.status = status;
        if (error) callbackParams.error = error;
        if (errorDescription) callbackParams.error_description = errorDescription;
        
        const result = await handleCallback(storedBroker, clientId, callbackParams);

        if (result.success) {
          setStatus('success');
          setMessage('OAuth authentication successful!');
          
          // Get broker-specific success details
          const expiryInfo = result.data?.valid_until || result.data?.expires_at;
          if (expiryInfo) {
            setDetails(`Valid until: ${new Date(expiryInfo).toLocaleString()}`);
          }
          
          // Clean up localStorage
          localStorage.removeItem('oauth_client_id');
          localStorage.removeItem('oauth_state');
          localStorage.removeItem('oauth_broker');
          
          // Send success message to parent window (for popup approach)
          if (window.opener) {
            window.opener.postMessage({
              type: `${storedBroker.toUpperCase()}_OAUTH_SUCCESS`,
              clientId,
              data: result.data
            }, window.location.origin);
            
            // Auto-close popup after 2 seconds
            setTimeout(() => {
              window.close();
            }, 2000);
          } else {
            // For redirect approach, redirect to broker page after 3 seconds
            setTimeout(() => {
              window.location.href = '/brokers';
            }, 3000);
          }
        } else {
          throw new Error(result.error || 'Token exchange failed');
        }
        
      } catch (error: any) {
        console.error('OAuth callback error:', error);
        
        setStatus('error');
        setMessage('OAuth authentication failed');
        setDetails(error.message || 'Unknown error occurred');
        
        const storedBroker = localStorage.getItem('oauth_broker') || 'OAuth';
        
        // Clean up localStorage on error
        localStorage.removeItem('oauth_client_id');
        localStorage.removeItem('oauth_state');
        localStorage.removeItem('oauth_broker');
        
        // Send error message to parent window
        if (window.opener) {
          window.opener.postMessage({
            type: `${storedBroker.toUpperCase()}_OAUTH_ERROR`,
            error: error.message || 'OAuth authentication failed'
          }, window.location.origin);
          
          // Keep popup open longer on error for debugging (30 seconds)
          setTimeout(() => {
            window.close();
          }, 30000);
        }
      }
    };

    processCallback();
  }, [handleCallback]);

  const getStatusIcon = () => {
    switch (status) {
      case 'processing':
        return <RefreshCw className="w-12 h-12 animate-spin text-blue-600" />;
      case 'success':
        return <CheckCircle className="w-12 h-12 text-green-600" />;
      case 'error':
        return <XCircle className="w-12 h-12 text-red-600" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'processing':
        return 'text-blue-600';
      case 'success':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="mb-6">
            <div className="mx-auto w-16 h-16 flex items-center justify-center">
              {getStatusIcon()}
            </div>
          </div>
          
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
            {brokerName ? `${brokerName.charAt(0).toUpperCase() + brokerName.slice(1)} OAuth` : 'OAuth'}
          </h2>
          
          <div className="space-y-3">
            <p className={`text-lg font-medium ${getStatusColor()}`}>
              {message}
            </p>
            
            {details && (
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {details}
              </p>
            )}
            
            {status === 'processing' && (
              <p className="text-xs text-gray-500 dark:text-gray-500">
                Please wait while we complete your authentication...
              </p>
            )}
            
            {status === 'success' && window.opener && (
              <p className="text-xs text-gray-500 dark:text-gray-500">
                This window will close automatically in a few seconds.
              </p>
            )}
            
            {status === 'success' && !window.opener && (
              <p className="text-xs text-gray-500 dark:text-gray-500">
                Redirecting you back to the brokers page...
              </p>
            )}
            
            {status === 'error' && (
              <div className="mt-4">
                <p className="text-xs text-gray-500 dark:text-gray-500 mb-3">
                  {window.opener 
                    ? 'This window will close automatically, or you can close it manually.' 
                    : 'Please go back to the brokers page and try again.'
                  }
                </p>
                {!window.opener && (
                  <button
                    onClick={() => window.location.href = '/brokers'}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Back to Brokers
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OAuthCallback;