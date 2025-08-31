import React, { useState, useEffect } from 'react';
import { X, Eye, EyeOff } from 'lucide-react';
import { BrokerAccount, UpdateBrokerAccount } from '../../types';
import ErrorAlert from '../common/ErrorAlert';

interface EditBrokerAccountFormProps {
  open: boolean;
  account: BrokerAccount | null;
  onClose: () => void;
  onSubmit: (clientId: string, updateData: UpdateBrokerAccount) => Promise<void>;
  isLoading?: boolean;
  error?: string | null;
  onClearError?: () => void;
}

const EditBrokerAccountForm: React.FC<EditBrokerAccountFormProps> = ({
  open,
  account,
  onClose,
  onSubmit,
  isLoading = false,
  error,
  onClearError,
}) => {
  const [formData, setFormData] = useState<UpdateBrokerAccount>({
    api_key: '',
    api_secret: '',
    capital: 0,
    description: '',
  });
  
  const [showApiSecret, setShowApiSecret] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof UpdateBrokerAccount, string>>>({});

  useEffect(() => {
    if (account) {
      setFormData({
        api_key: '',
        api_secret: '',
        capital: account.capital || 0,
        description: account.description || '',
      });
    }
  }, [account]);

  const handleInputChange = (field: keyof UpdateBrokerAccount) => (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    let value: string | number = event.target.value;
    
    if (field === 'capital') {
      value = parseFloat(value) || 0;
    }
    
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));

    if (fieldErrors[field]) {
      setFieldErrors(prev => ({
        ...prev,
        [field]: undefined,
      }));
    }

    if (error && onClearError) {
      onClearError();
    }
  };

  const validateForm = (): boolean => {
    const errors: Partial<Record<keyof UpdateBrokerAccount, string>> = {};

    if (formData.capital !== undefined && formData.capital <= 0) {
      errors.capital = 'Capital must be greater than 0';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!account || !validateForm()) {
      return;
    }

    const updateData: UpdateBrokerAccount = {};
    
    if (formData.api_key?.trim()) {
      updateData.api_key = formData.api_key.trim();
    }
    
    if (formData.api_secret?.trim()) {
      updateData.api_secret = formData.api_secret.trim();
    }
    
    if (formData.capital !== undefined && formData.capital > 0) {
      updateData.capital = formData.capital;
    }
    
    if (formData.description !== undefined) {
      updateData.description = formData.description.trim();
    }

    if (Object.keys(updateData).length === 0) {
      setFieldErrors({ api_key: 'At least one field must be updated' });
      return;
    }

    try {
      await onSubmit(account.client_id, updateData);
      handleClose();
    } catch (error) {
      // Error handling is managed by parent
    }
  };

  const handleClose = () => {
    setFormData({
      api_key: '',
      api_secret: '',
      capital: account?.capital || 0,
      description: account?.description || '',
    });
    setFieldErrors({});
    if (onClearError) {
      onClearError();
    }
    onClose();
  };

  if (!open || !account) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Edit Broker Account
          </h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {error && (
            <div className="mb-4">
              <ErrorAlert message={error} onClose={onClearError} />
            </div>
          )}

          {/* Read-only account info */}
          <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">Account Information</h3>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">Broker:</span>
                <span className="text-gray-900 dark:text-white capitalize">{account.broker_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">Client ID:</span>
                <span className="text-gray-900 dark:text-white">{account.client_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">Group:</span>
                <span className="text-gray-900 dark:text-white">{account.group}</span>
              </div>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
              These fields cannot be modified after account creation.
            </p>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                Capital *
              </label>
              <input
                type="number"
                min="1"
                step="0.01"
                value={formData.capital}
                onChange={handleInputChange('capital')}
                className={`block w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                  fieldErrors.capital
                    ? 'border-red-300 dark:border-red-600'
                    : 'border-gray-300 dark:border-gray-600'
                }`}
                placeholder="100000"
              />
              {fieldErrors.capital && (
                <p className="mt-1 text-xs text-red-600">{fieldErrors.capital}</p>
              )}
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={handleInputChange('description')}
                rows={3}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none"
                placeholder="Optional description for this account"
              />
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                API Key
              </label>
              <input
                type="text"
                value={formData.api_key}
                onChange={handleInputChange('api_key')}
                className={`block w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                  fieldErrors.api_key
                    ? 'border-red-300 dark:border-red-600'
                    : 'border-gray-300 dark:border-gray-600'
                }`}
                placeholder="Leave empty to keep current API key"
              />
              {fieldErrors.api_key && (
                <p className="mt-1 text-xs text-red-600">{fieldErrors.api_key}</p>
              )}
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                API Secret
              </label>
              <div className="relative">
                <input
                  type={showApiSecret ? 'text' : 'password'}
                  value={formData.api_secret}
                  onChange={handleInputChange('api_secret')}
                  className={`block w-full px-3 py-2 pr-10 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                    fieldErrors.api_secret
                      ? 'border-red-300 dark:border-red-600'
                      : 'border-gray-300 dark:border-gray-600'
                  }`}
                  placeholder="Leave empty to keep current API secret"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowApiSecret(!showApiSecret)}
                >
                  {showApiSecret ? (
                    <EyeOff className="h-5 w-5 text-gray-400" />
                  ) : (
                    <Eye className="h-5 w-5 text-gray-400" />
                  )}
                </button>
              </div>
              {fieldErrors.api_secret && (
                <p className="mt-1 text-xs text-red-600">{fieldErrors.api_secret}</p>
              )}
            </div>

            <div className="flex gap-3 justify-end">
              <button
                type="button"
                onClick={handleClose}
                className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium rounded-lg transition-colors"
              >
                {isLoading ? 'Updating...' : 'Update Account'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default EditBrokerAccountForm;