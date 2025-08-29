import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Alert,
  Chip,
} from '@mui/material';
import {
  AccountBalance as AccountBalanceIcon,
  TrendingUp as TrendingUpIcon,
  Person as PersonIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { formatPhoneNumber } from '../utils/validation';
import brokerService from '../services/brokerService';

interface DashboardProps {
  onNavigate: (page: string) => void;
}

const Dashboard: React.FC<DashboardProps> = ({ onNavigate }) => {
  const { user } = useAuth();
  const [brokerAccountCount, setBrokerAccountCount] = useState<number>(0);

  useEffect(() => {
    const fetchBrokerAccounts = async () => {
      try {
        const accounts = await brokerService.getBrokerAccounts();
        setBrokerAccountCount(accounts.length);
      } catch (error) {
        console.error('Failed to fetch broker accounts for dashboard:', error);
        setBrokerAccountCount(0);
      }
    };

    fetchBrokerAccounts();
  }, []);

  const quickStats = [
    {
      title: 'Broker Accounts',
      value: brokerAccountCount.toString(),
      subtitle: 'Connected accounts',
      icon: <AccountBalanceIcon sx={{ fontSize: 40 }} />,
      color: '#1976d2',
    },
    {
      title: 'Active Strategies',
      value: '0', // TODO: Implement in future modules
      subtitle: 'Running algorithms',
      icon: <TrendingUpIcon sx={{ fontSize: 40 }} />,
      color: '#2e7d32',
    },
    {
      title: 'P&L Today',
      value: '₹0.00', // TODO: Implement in future modules
      subtitle: 'Trading profit/loss',
      icon: <TrendingUpIcon sx={{ fontSize: 40 }} />,
      color: '#ed6c02',
    },
  ];

  const getWelcomeMessage = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <Box>
      {/* Welcome Section */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          {getWelcomeMessage()}, {user?.fullName?.split(' ')[0]}! 👋
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Welcome to your algorithmic trading dashboard. Monitor your strategies, manage broker accounts, and track performance.
        </Typography>
      </Box>

      {/* User Profile Summary */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box display="flex" alignItems="center" sx={{ mb: 2 }}>
            <PersonIcon sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6">Profile Summary</Typography>
          </Box>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Typography variant="body2" color="textSecondary">
                Full Name
              </Typography>
              <Typography variant="body1">{user?.fullName}</Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="body2" color="textSecondary">
                Email
              </Typography>
              <Typography variant="body1">{user?.email}</Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="body2" color="textSecondary">
                Phone Number
              </Typography>
              <Typography variant="body1">
                {user?.phoneNumber && formatPhoneNumber(user.phoneNumber)}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="body2" color="textSecondary">
                State
              </Typography>
              <Chip label={user?.state} color="primary" variant="outlined" size="small" />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Quick Stats */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {quickStats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={4} key={index}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography variant="h4" component="div" gutterBottom>
                      {stat.value}
                    </Typography>
                    <Typography variant="h6" color="textSecondary">
                      {stat.title}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      {stat.subtitle}
                    </Typography>
                  </Box>
                  <Box sx={{ color: stat.color }}>
                    {stat.icon}
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Getting Started Section */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Getting Started
          </Typography>
          
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>Welcome to Quantleap Analytics!</strong> You've successfully set up your account. 
              Now let's connect your broker account to start algorithmic trading.
            </Typography>
          </Alert>

          <Box>
            <Typography variant="body1" gutterBottom>
              <strong>Next Steps:</strong>
            </Typography>
            <Box component="ol" sx={{ pl: 2, mb: 2 }}>
              <Box component="li" sx={{ mb: 1 }}>
                <Typography variant="body2">
                  Connect your Zerodha account to enable trading
                </Typography>
              </Box>
              <Box component="li" sx={{ mb: 1 }}>
                <Typography variant="body2">
                  Test your broker connection to ensure everything works
                </Typography>
              </Box>
              <Box component="li" sx={{ mb: 1 }}>
                <Typography variant="body2" color="textSecondary">
                  Set up your first trading strategy (Module 3 - Coming soon)
                </Typography>
              </Box>
              <Box component="li">
                <Typography variant="body2" color="textSecondary">
                  Monitor and optimize your portfolio (Module 4 - Coming soon)
                </Typography>
              </Box>
            </Box>

            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => onNavigate('brokers')}
              size="large"
            >
              Connect Broker Account
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Dashboard;