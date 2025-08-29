import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Alert,
  Paper,
} from '@mui/material';
import { useAuth } from '../context/AuthContext';
import LoginForm from '../components/auth/LoginForm';
import RegisterForm from '../components/auth/RegisterForm';
import LoadingSpinner from '../components/common/LoadingSpinner';

const AuthPage: React.FC = () => {
  const { login, register, isLoading, error, clearError } = useAuth() as any;
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [registrationSuccess, setRegistrationSuccess] = useState(false);

  const handleLogin = async (credentials: any) => {
    try {
      await login(credentials);
    } catch (error) {
      // Error is handled by AuthContext
    }
  };

  const handleRegister = async (userData: any) => {
    try {
      await register(userData);
      setRegistrationSuccess(true);
      setAuthMode('login');
    } catch (error) {
      // Error is handled by AuthContext
    }
  };

  const switchToRegister = () => {
    clearError();
    setRegistrationSuccess(false);
    setAuthMode('register');
  };

  const switchToLogin = () => {
    clearError();
    setRegistrationSuccess(false);
    setAuthMode('login');
  };

  if (isLoading) {
    return (
      <Container maxWidth="sm" sx={{ mt: 8 }}>
        <LoadingSpinner message="Authenticating..." />
      </Container>
    );
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        py: 4,
      }}
    >
      <Container maxWidth="sm">
        {/* Header */}
        <Box textAlign="center" sx={{ mb: 4 }}>
          <Typography variant="h3" component="h1" sx={{ color: 'white', mb: 1, fontWeight: 'bold' }}>
            Quantleap Analytics
          </Typography>
          <Typography variant="h6" sx={{ color: 'rgba(255,255,255,0.9)' }}>
            Algorithmic Trading Platform for Indian Markets
          </Typography>
        </Box>

        {/* Registration Success Message */}
        {registrationSuccess && (
          <Box sx={{ mb: 3 }}>
            <Alert severity="success">
              <Typography variant="body2" gutterBottom>
                <strong>Registration Successful!</strong>
              </Typography>
              <Typography variant="body2">
                Your account has been created successfully. Please sign in to continue to your dashboard.
              </Typography>
            </Alert>
          </Box>
        )}

        {/* Auth Forms */}
        {authMode === 'login' ? (
          <LoginForm
            onSubmit={handleLogin}
            onRegisterClick={switchToRegister}
            isLoading={isLoading}
            error={error}
            onClearError={clearError}
          />
        ) : (
          <RegisterForm
            onSubmit={handleRegister}
            isLoading={isLoading}
            error={error}
            onClearError={clearError}
          />
        )}

        {/* Additional Info for Register Form */}
        {authMode === 'register' && (
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                <strong>Why Quantleap Analytics?</strong>
              </Typography>
              <Typography variant="body2" color="textSecondary">
                • Secure AWS-based infrastructure<br />
                • Indian market specialized algorithms<br />
                • Zerodha integration for seamless trading<br />
                • Advanced risk management tools
              </Typography>
            </Paper>
          </Box>
        )}

        {/* Switch Auth Mode */}
        {authMode === 'register' && (
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.8)' }}>
              Already have an account?{' '}
              <Box
                component="span"
                sx={{
                  color: 'white',
                  textDecoration: 'underline',
                  cursor: 'pointer',
                  fontWeight: 'bold',
                }}
                onClick={switchToLogin}
              >
                Sign In Here
              </Box>
            </Typography>
          </Box>
        )}

        {/* Footer */}
        <Box textAlign="center" sx={{ mt: 4 }}>
          <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
            Module 2: User Authentication & Broker Management
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default AuthPage;