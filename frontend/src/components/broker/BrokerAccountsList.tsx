import React, { useState, useEffect } from 'react';
import { Plus } from 'lucide-react';
import { BrokerAccount, CreateBrokerAccount } from '../../types';
import brokerService from '../../services/brokerService';
import BrokerAccountCard from './BrokerAccountCard';
import AddBrokerAccountForm from './AddBrokerAccountForm';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorAlert from '../common/ErrorAlert';

const BrokerAccountsList: React.FC = () => {
  const [accounts, setAccounts] = useState<BrokerAccount[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addFormOpen, setAddFormOpen] = useState(false);
  const [isAddingAccount, setIsAddingAccount] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);
  const [testingAccountId, setTestingAccountId] = useState<string | null>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  useEffect(() => {
    fetchBrokerAccounts();
  }, []);

  const fetchBrokerAccounts = async () => {
    try {
      setIsLoading(true);
      const fetchedAccounts = await brokerService.getBrokerAccounts();
      setAccounts(fetchedAccounts);
      setError(null);
    } catch (error) {
      console.error('Failed to fetch broker accounts:', error);
      setError(error instanceof Error ? error.message : 'Failed to fetch broker accounts');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddAccount = async (accountData: CreateBrokerAccount) => {
    try {
      setIsAddingAccount(true);
      setAddError(null);
      
      const newAccount = await brokerService.createBrokerAccount(accountData);
      setAccounts(prev => [...prev, newAccount]);
      
      setSnackbar({
        open: true,
        message: `${accountData.broker_name} account added successfully!`,
        severity: 'success',
      });
      
      setAddFormOpen(false);
    } catch (error) {
      console.error('Failed to add broker account:', error);
      setAddError(error instanceof Error ? error.message : 'Failed to add broker account');
      throw error; // Re-throw so form doesn't close
    } finally {
      setIsAddingAccount(false);
    }
  };

  const handleEditAccount = (account: BrokerAccount) => {
    // TODO: Implement edit functionality
    console.log('Edit account:', account);
    setSnackbar({
      open: true,
      message: 'Edit functionality coming soon!',
      severity: 'error',
    });
  };

  const handleDeleteAccount = async (accountId: string) => {
    try {
      await brokerService.deleteBrokerAccount(accountId);
      setAccounts(prev => prev.filter(acc => acc.broker_account_id !== accountId));
      
      setSnackbar({
        open: true,
        message: 'Broker account removed successfully!',
        severity: 'success',
      });
    } catch (error) {
      console.error('Failed to delete broker account:', error);
      setSnackbar({
        open: true,
        message: error instanceof Error ? error.message : 'Failed to remove broker account',
        severity: 'error',
      });
    }
  };

  const handleTestConnection = async (accountId: string) => {
    try {
      setTestingAccountId(accountId);
      const result = await brokerService.testBrokerConnection(accountId);
      
      if (result.success && result.data?.status === 'connected') {
        setSnackbar({
          open: true,
          message: 'Connection test successful!',
          severity: 'success',
        });
      } else {
        setSnackbar({
          open: true,
          message: result.data?.details || 'Connection test failed',
          severity: 'error',
        });
      }
    } catch (error) {
      console.error('Connection test failed:', error);
      setSnackbar({
        open: true,
        message: error instanceof Error ? error.message : 'Connection test failed',
        severity: 'error',
      });
    } finally {
      setTestingAccountId(null);
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  if (isLoading) {
    return <LoadingSpinner message="Loading broker accounts..." />;
  }

  if (error) {
    return (
      <div>
        <ErrorAlert message={error} onClose={() => setError(null)} />
        <div className="mt-4 text-center">
          <button 
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            onClick={fetchBrokerAccounts}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Broker Accounts
        </h2>
        <button
          className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
          onClick={() => setAddFormOpen(true)}
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Broker Account
        </button>
      </div>

      {accounts.length === 0 ? (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-800 dark:text-blue-200 mb-2">
            No broker accounts connected
          </h3>
          <p className="text-blue-700 dark:text-blue-300 mb-4">
            Connect your trading account to start executing algorithmic strategies.
            Your credentials will be stored securely and encrypted.
          </p>
          <button
            className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
            onClick={() => setAddFormOpen(true)}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Your First Broker Account
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {accounts.map((account) => (
            <BrokerAccountCard
              key={account.broker_account_id}
              account={account}
              onEdit={handleEditAccount}
              onDelete={handleDeleteAccount}
              onTest={handleTestConnection}
              isTestingConnection={testingAccountId === account.broker_account_id}
            />
          ))}
        </div>
      )}

      <AddBrokerAccountForm
        open={addFormOpen}
        onClose={() => setAddFormOpen(false)}
        onSubmit={handleAddAccount}
        isLoading={isAddingAccount}
        error={addError}
        onClearError={() => setAddError(null)}
      />

      {/* Toast notification */}
      {snackbar.open && (
        <div className="fixed bottom-4 right-4 z-50">
          <div className={`rounded-lg shadow-lg p-4 max-w-sm ${
            snackbar.severity === 'success'
              ? 'bg-green-50 border border-green-200 text-green-800'
              : 'bg-red-50 border border-red-200 text-red-800'
          }`}>
            <div className="flex">
              <div className="flex-1">
                <p className="text-sm font-medium">{snackbar.message}</p>
              </div>
              <button
                className="ml-3 flex-shrink-0"
                onClick={handleCloseSnackbar}
              >
                <span className="sr-only">Close</span>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BrokerAccountsList;