import React, { useState } from 'react';
import { MoreHorizontal, Edit, Trash2, Wifi, WifiOff } from 'lucide-react';
import { BrokerAccount } from '../../types';
import { OAuthButton } from '../oauth/OAuthButton';
import { OAuthStatusDisplay } from '../oauth/OAuthStatusDisplay';
import { useOAuth } from '../../context/OAuthContext';
import { supportsOAuth } from '../../config/brokerConfigs';

interface BrokerAccountCardProps {
  account: BrokerAccount;
  onEdit: (account: BrokerAccount) => void;
  onDelete: (clientId: string) => void;
  onTest: (clientId: string) => void;
  isTestingConnection?: boolean;
  onOAuthUpdate?: () => void; // Callback to refresh account data
}

const BrokerAccountCard: React.FC<BrokerAccountCardProps> = ({
  account,
  onEdit,
  onDelete,
  onTest,
  isTestingConnection = false,
  onOAuthUpdate,
}) => {
  const [showMenu, setShowMenu] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const { supportsOAuth: contextSupportsOAuth } = useOAuth();

  const getStatusColor = () => {
    switch (account.account_status) {
      case 'enabled':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'disabled':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
    }
  };

  // Check if this broker supports OAuth
  const brokerSupportsOAuth = supportsOAuth(account.broker_name) && contextSupportsOAuth(account.broker_name);

  // Handle OAuth success
  const handleOAuthSuccess = (data: any) => {
    console.log('OAuth authentication successful:', data);
    onOAuthUpdate?.();
  };

  // Handle OAuth error
  const handleOAuthError = (error: string) => {
    console.error('OAuth authentication failed:', error);
    // Error is already displayed by OAuthButton component
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 relative">
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white capitalize">
            {account.broker_name}
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Client ID: {account.client_id}
          </p>
          {account.description && (
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
              {account.description}
            </p>
          )}
        </div>
        
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <MoreHorizontal className="w-5 h-5 text-gray-500" />
          </button>
          
          {showMenu && (
            <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-700 rounded-lg shadow-lg border border-gray-200 dark:border-gray-600 z-10">
              <button
                onClick={() => {
                  onEdit(account);
                  setShowMenu(false);
                }}
                className="flex items-center w-full px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600"
              >
                <Edit className="w-4 h-4 mr-2" />
                Edit
              </button>
              <button
                onClick={() => {
                  setShowDeleteDialog(true);
                  setShowMenu(false);
                }}
                className="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Status */}
      <div className="mb-4">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor()}`}>
          {account.account_status === 'enabled' ? <Wifi className="w-3 h-3 mr-1" /> : <WifiOff className="w-3 h-3 mr-1" />}
          {account.account_status}
        </span>
        
        {/* Account details */}
        <div className="mt-3 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-500 dark:text-gray-400">Capital:</span>
            <span className="text-gray-900 dark:text-white font-medium">₹{account.capital?.toLocaleString()}</span>
          </div>
          {brokerSupportsOAuth && (
            <OAuthStatusDisplay 
              brokerAccount={account}
              className="mt-2"
            />
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        {brokerSupportsOAuth && (
          <OAuthButton
            brokerAccount={account}
            onAuthSuccess={handleOAuthSuccess}
            onAuthError={handleOAuthError}
            disabled={account.account_status !== 'enabled'}
            className=""
          />
        )}
        
        <button
          onClick={() => onTest(account.client_id)}
          disabled={isTestingConnection}
          className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-sm font-medium rounded-lg transition-colors"
        >
          {isTestingConnection ? 'Testing...' : 'Test Connection'}
        </button>
      </div>

      {/* Delete Confirmation Dialog */}
      {showDeleteDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md mx-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Delete Broker Account
            </h3>
            <p className="text-gray-600 dark:text-gray-300 mb-6">
              Are you sure you want to delete broker account "{account.client_id}"? This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowDeleteDialog(false)}
                className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  onDelete(account.client_id);
                  setShowDeleteDialog(false);
                }}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BrokerAccountCard;