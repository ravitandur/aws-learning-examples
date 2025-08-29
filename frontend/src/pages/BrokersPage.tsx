import React from 'react';
import {
  Box,
  Typography,
  Container,
} from '@mui/material';
import BrokerAccountsList from '../components/broker/BrokerAccountsList';

const BrokersPage: React.FC = () => {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Broker Accounts
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Manage your trading accounts and API connections. Your credentials are stored securely
          and encrypted using AWS Secrets Manager.
        </Typography>
      </Box>

      <BrokerAccountsList />
    </Container>
  );
};

export default BrokersPage;