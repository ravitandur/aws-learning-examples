import React, { useState, useRef, useEffect, useCallback } from 'react';
import { MoreHorizontal, Edit, Trash2, Wifi, WifiOff, Copy, Check, AlertCircle } from 'lucide-react';
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
  onOAuthUpdate?: () => void;
  isLoading?: boolean;
  error?: string | null;
}

const BrokerAccountCard: React.FC<BrokerAccountCardProps> = ({
  account,
  onEdit,
  onDelete,
  onTest,
  isTestingConnection = false,
  onOAuthUpdate,
  isLoading = false,
  error = null,
}) => {
  const [showMenu, setShowMenu] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const menuButtonRef = useRef<HTMLButtonElement>(null);
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

  // Click outside detection for dropdown menu
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node) &&
          menuButtonRef.current && !menuButtonRef.current.contains(event.target as Node)) {
        setShowMenu(false);
      }
    };

    if (showMenu) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showMenu]);

  // Keyboard navigation for menu
  const handleMenuKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Escape') {
      setShowMenu(false);
      menuButtonRef.current?.focus();
    }
  };

  // Copy to clipboard functionality
  const copyToClipboard = useCallback(async (text: string, field: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  }, []);

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
  };

  // Skeleton loading component
  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 animate-pulse"
           role="status" aria-label="Loading broker account">
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-32 mb-2"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-48 mb-1"></div>
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-40"></div>
          </div>
          <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
        <div className="mb-4">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-20 mb-3"></div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-16"></div>
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <div className="flex-1 h-10 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
        </div>
      </div>
    );
  }

  return (
    <article 
      className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 sm:p-6 relative transition-all duration-200 hover:shadow-lg focus-within:ring-2 focus-within:ring-blue-500 focus-within:ring-opacity-50"
      aria-labelledby={`broker-${account.client_id}-title`}
      aria-describedby={`broker-${account.client_id}-status`}
    >
      {/* Error state */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg" role="alert">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400 flex-shrink-0" />
            <span className="text-sm text-red-800 dark:text-red-200">{error}</span>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1 min-w-0">
          <h3 id={`broker-${account.client_id}-title`} className="text-lg font-semibold text-gray-900 dark:text-white capitalize truncate">
            {account.broker_name}
          </h3>
          <div className="flex items-center gap-2 mt-1">
            <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
              Client ID: {account.client_id}
            </p>
            <button
              onClick={() => copyToClipboard(account.client_id, 'client_id')}
              className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
              title="Copy Client ID"
              aria-label="Copy Client ID to clipboard"
            >
              {copiedField === 'client_id' ? (
                <Check className="w-3 h-3 text-green-600" />
              ) : (
                <Copy className="w-3 h-3 text-gray-400 hover:text-gray-600" />
              )}
            </button>
          </div>
          {account.description && (
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-1 line-clamp-2">
              {account.description}
            </p>
          )}
        </div>
        
        <div className="relative">
          <button
            ref={menuButtonRef}
            onClick={() => setShowMenu(!showMenu)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                setShowMenu(!showMenu);
              }
            }}
            className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 transition-colors"
            aria-expanded={showMenu}
            aria-haspopup="menu"
            aria-label="More options"
          >
            <MoreHorizontal className="w-5 h-5 text-gray-500" />
          </button>
          
          {showMenu && (
            <div 
              ref={menuRef}
              className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-700 rounded-lg shadow-lg border border-gray-200 dark:border-gray-600 z-10 animate-in slide-in-from-top-2 duration-200"
              role="menu"
              aria-orientation="vertical"
              onKeyDown={handleMenuKeyDown}
            >
              <button
                onClick={() => {
                  onEdit(account);
                  setShowMenu(false);
                }}
                className="flex items-center w-full px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:bg-gray-50 dark:focus:bg-gray-600 first:rounded-t-lg transition-colors"
                role="menuitem"
                tabIndex={-1}
              >
                <Edit className="w-4 h-4 mr-2" aria-hidden="true" />
                Edit
              </button>
              <button
                onClick={() => {
                  setShowDeleteDialog(true);
                  setShowMenu(false);
                }}
                className="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 focus:outline-none focus:bg-red-50 dark:focus:bg-red-900/20 last:rounded-b-lg transition-colors"
                role="menuitem"
                tabIndex={-1}
              >
                <Trash2 className="w-4 h-4 mr-2" aria-hidden="true" />
                Delete
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Status */}
      <div className="mb-4">
        <span 
          id={`broker-${account.client_id}-status`}
          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor()}`}
          role="status"
          aria-label={`Account status: ${account.account_status}`}
        >
          {account.account_status === 'enabled' ? (
            <Wifi className="w-3 h-3 mr-1" aria-hidden="true" />
          ) : (
            <WifiOff className="w-3 h-3 mr-1" aria-hidden="true" />
          )}
          <span className="capitalize">{account.account_status}</span>
        </span>
        
        {/* Account details */}
        <div className="mt-3 space-y-2">
          <div className="flex justify-between items-center text-sm">
            <span className="text-gray-500 dark:text-gray-400">Capital:</span>
            <div className="flex items-center gap-2">
              <span className="text-gray-900 dark:text-white font-medium tabular-nums">
                ₹{account.capital?.toLocaleString('en-IN') || '0'}
              </span>
              <button
                onClick={() => copyToClipboard(account.capital?.toString() || '0', 'capital')}
                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                title="Copy Capital Amount"
                aria-label="Copy capital amount to clipboard"
              >
                {copiedField === 'capital' ? (
                  <Check className="w-3 h-3 text-green-600" />
                ) : (
                  <Copy className="w-3 h-3 text-gray-400 hover:text-gray-600" />
                )}
              </button>
            </div>
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
      <div className="flex flex-col sm:flex-row gap-2">
        {brokerSupportsOAuth && (
          <OAuthButton
            brokerAccount={account}
            onAuthSuccess={handleOAuthSuccess}
            onAuthError={handleOAuthError}
            disabled={account.account_status !== 'enabled'}
            className="sm:flex-1"
          />
        )}
        
        <button
          onClick={() => onTest(account.client_id)}
          disabled={isTestingConnection || account.account_status !== 'enabled'}
          className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 dark:disabled:bg-blue-800 text-white text-sm font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800"
          aria-label="Test broker connection"
        >
          {isTestingConnection ? (
            <span className="flex items-center justify-center gap-2">
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" aria-hidden="true"></div>
              Testing...
            </span>
          ) : (
            'Test Connection'
          )}
        </button>
      </div>

      {/* Delete Confirmation Dialog */}
      {showDeleteDialog && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-dialog-title"
          aria-describedby="delete-dialog-description"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setShowDeleteDialog(false);
            }
          }}
        >
          <div 
            className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4 animate-in zoom-in-95 duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-red-100 dark:bg-red-900/20 rounded-full">
                <AlertCircle className="h-6 w-6 text-red-600 dark:text-red-400" />
              </div>
              <h3 id="delete-dialog-title" className="text-lg font-semibold text-gray-900 dark:text-white">
                Delete Broker Account
              </h3>
            </div>
            <p id="delete-dialog-description" className="text-gray-600 dark:text-gray-300 mb-6 leading-relaxed">
              Are you sure you want to delete broker account <strong>"{account.client_id}"</strong>? This action cannot be undone and will permanently remove all associated data.
            </p>
            <div className="flex flex-col-reverse sm:flex-row gap-3 sm:justify-end">
              <button
                onClick={() => setShowDeleteDialog(false)}
                className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800"
                autoFocus
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  onDelete(account.client_id);
                  setShowDeleteDialog(false);
                }}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 focus:bg-red-700 text-white rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800"
              >
                Delete Account
              </button>
            </div>
          </div>
        </div>
      )}
    </article>
  );
};

export default BrokerAccountCard;