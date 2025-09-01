/**
 * OAuth Status Display Component
 * Shows the current OAuth authentication status for a broker account
 */

import React, { useEffect, useState } from 'react';
import { Shield, ShieldCheck, Clock } from 'lucide-react';
import { useOAuth } from '../../context/OAuthContext';
import { AuthStatus } from '../../types/oauth';
import { BrokerAccount } from '../../types';

interface OAuthStatusDisplayProps {
  brokerAccount: BrokerAccount;
  className?: string;
}

export const OAuthStatusDisplay: React.FC<OAuthStatusDisplayProps> = ({
  brokerAccount,
  className = ''
}) => {
  const { authStatuses, getAuthStatus, supportsOAuth } = useOAuth();
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null);

  const brokerName = brokerAccount.broker_name;
  const clientId = brokerAccount.client_id;
  const cacheKey = `${brokerName.toLowerCase()}-${clientId}`;

  // Get auth status from context or fetch it
  useEffect(() => {
    const contextStatus = authStatuses.get(cacheKey);
    if (contextStatus) {
      setAuthStatus(contextStatus);
    } else if (supportsOAuth(brokerName)) {
      // Fetch status if not in context
      loadAuthStatus();
    }
  }, [authStatuses, cacheKey, supportsOAuth, brokerName]);

  const loadAuthStatus = async () => {
    try {
      const status = await getAuthStatus(brokerName, clientId);
      setAuthStatus(status);
    } catch (error: any) {
      console.error('Failed to load OAuth status:', error);
    }
  };

  // Don't render if broker doesn't support OAuth
  if (!supportsOAuth(brokerName)) {
    return null;
  }

  // Don't render if no status available
  if (!authStatus) {
    return null;
  }

  const getStatusDisplay = () => {
    if (authStatus.hasToken && authStatus.isValid) {
      const expiryDate = authStatus.expiresAt 
        ? new Date(authStatus.expiresAt).toLocaleTimeString('en-IN', {
            hour: '2-digit',
            minute: '2-digit',
            timeZone: 'Asia/Kolkata'
          })
        : 'Unknown';
      
      return (
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500 dark:text-gray-400 flex items-center">
            <ShieldCheck className="w-3 h-3 mr-1 text-green-500" />
            OAuth Session:
          </span>
          <span className="text-green-600 dark:text-green-400 text-xs">
            Active until {expiryDate}
          </span>
        </div>
      );
    } else if (authStatus.hasToken && !authStatus.isValid) {
      return (
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500 dark:text-gray-400 flex items-center">
            <Clock className="w-3 h-3 mr-1 text-yellow-500" />
            OAuth Session:
          </span>
          <span className="text-yellow-600 dark:text-yellow-400 text-xs">
            Expired
          </span>
        </div>
      );
    } else {
      return (
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500 dark:text-gray-400 flex items-center">
            <Shield className="w-3 h-3 mr-1 text-gray-500" />
            OAuth Session:
          </span>
          <span className="text-gray-600 dark:text-gray-400 text-xs">
            Not connected
          </span>
        </div>
      );
    }
  };

  return (
    <div className={className}>
      {getStatusDisplay()}
    </div>
  );
};