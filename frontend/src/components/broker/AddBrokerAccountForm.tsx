import React, { useState } from 'react';
import { X, Eye, EyeOff } from 'lucide-react';
import { CreateBrokerAccount } from '../../types';
import ErrorAlert from '../common/ErrorAlert';

interface AddBrokerAccountFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (accountData: CreateBrokerAccount) => Promise<void>;
  isLoading?: boolean;
  error?: string | null;
  onClearError?: () => void;
}

const AddBrokerAccountForm: React.FC<AddBrokerAccountFormProps> = ({
  open,
  onClose,
  onSubmit,
  isLoading = false,
  error,
  onClearError,
}) => {
  const [formData, setFormData] = useState<CreateBrokerAccount>({
    broker_name: 'Zerodha',
    account_name: '',
    api_key: '',
    api_secret: '',
    account_status: 'active',
  });
  
  const [showApiSecret, setShowApiSecret] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof CreateBrokerAccount, string>>>({});

  const handleInputChange = (field: keyof CreateBrokerAccount) => (
    event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    setFormData(prev => ({
      ...prev,
      [field]: event.target.value,
    }));

    // Clear field error when user starts typing
    if (fieldErrors[field]) {
      setFieldErrors(prev => ({
        ...prev,
        [field]: undefined,
      }));
    }

    // Clear general error
    if (error && onClearError) {
      onClearError();
    }
  };

  const validateForm = (): boolean => {
    const errors: Partial<Record<keyof CreateBrokerAccount, string>> = {};

    if (!formData.account_name.trim()) {
      errors.account_name = 'Account name is required';
    }

    if (!formData.api_key.trim()) {
      errors.api_key = 'API Key is required';
    }

    if (!formData.api_secret.trim()) {
      errors.api_secret = 'API Secret is required';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      await onSubmit(formData);
      // Reset form on success
      setFormData({
        broker_name: 'Zerodha',
        account_name: '',
        api_key: '',
        api_secret: '',
        account_status: 'active',
      });
      setFieldErrors({});
    } catch (error) {
      // Error handling is managed by parent
    }
  };

  const handleClose = () => {
    setFormData({
      broker_name: 'Zerodha',
      account_name: '',
      api_key: '',
      api_secret: '',
      account_status: 'active',
    });
    setFieldErrors({});
    if (onClearError) {
      onClearError();
    }
    onClose();
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Add Broker Account
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

          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                Broker *
              </label>
              <select
                value={formData.broker_name}
                onChange={handleInputChange('broker_name')}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="Zerodha">Zerodha</option>
              </select>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                Account Name *
              </label>
              <input
                type="text"
                value={formData.account_name}
                onChange={handleInputChange('account_name')}
                className={`block w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                  fieldErrors.account_name
                    ? 'border-red-300 dark:border-red-600'
                    : 'border-gray-300 dark:border-gray-600'
                }`}
                placeholder="My Trading Account"
              />
              {fieldErrors.account_name && (
                <p className="mt-1 text-xs text-red-600">{fieldErrors.account_name}</p>
              )}
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                API Key *
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
                placeholder="Your Zerodha API Key"
              />
              {fieldErrors.api_key && (
                <p className="mt-1 text-xs text-red-600">{fieldErrors.api_key}</p>
              )}
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                API Secret *
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
                  placeholder="Your Zerodha API Secret"
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
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg transition-colors"
              >
                {isLoading ? 'Adding...' : 'Add Account'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AddBrokerAccountForm;