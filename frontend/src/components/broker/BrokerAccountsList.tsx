import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Grid,
  Alert,
  Snackbar,
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
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
      <Box>
        <ErrorAlert message={error} onClose={() => setError(null)} />
        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Button variant="outlined" onClick={fetchBrokerAccounts}>
            Retry
          </Button>
        </Box>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Typography variant="h5" component="h2">
          Broker Accounts
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setAddFormOpen(true)}
        >
          Add Broker Account
        </Button>
      </Box>

      {accounts.length === 0 ? (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            No broker accounts connected
          </Typography>
          <Typography>
            Connect your trading account to start executing algorithmic strategies.
            Your credentials will be stored securely and encrypted.
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setAddFormOpen(true)}
            sx={{ mt: 2 }}
          >
            Add Your First Broker Account
          </Button>
        </Alert>
      ) : (
        <Grid container spacing={3}>
          {accounts.map((account) => (
            <Grid item xs={12} sm={6} md={4} key={account.broker_account_id}>
              <BrokerAccountCard
                account={account}
                onEdit={handleEditAccount}
                onDelete={handleDeleteAccount}
                onTest={handleTestConnection}
                isTestingConnection={testingAccountId === account.broker_account_id}
              />
            </Grid>
          ))}
        </Grid>
      )}

      <AddBrokerAccountForm
        open={addFormOpen}
        onClose={() => setAddFormOpen(false)}
        onSubmit={handleAddAccount}
        isLoading={isAddingAccount}
        error={addError}
        onClearError={() => setAddError(null)}
      />

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default BrokerAccountsList;