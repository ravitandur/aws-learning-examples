import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Paper,
  InputAdornment,
  IconButton,
  Link,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  AccountCircle,
} from '@mui/icons-material';
import { UserLogin } from '../../types';
import { validatePhoneNumber, validateEmail, formatPhoneForInput } from '../../utils/validation';
import ErrorAlert from '../common/ErrorAlert';

interface LoginFormProps {
  onSubmit: (credentials: UserLogin) => Promise<void>;
  onRegisterClick: () => void;
  isLoading?: boolean;
  error?: string | null;
  onClearError?: () => void;
}

const LoginForm: React.FC<LoginFormProps> = ({
  onSubmit,
  onRegisterClick,
  isLoading = false,
  error,
  onClearError,
}) => {
  const [formData, setFormData] = useState<UserLogin>({
    username: '',
    password: '',
  });

  const [showPassword, setShowPassword] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof UserLogin, string>>>({});

  const handleInputChange = (field: keyof UserLogin) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    let value = event.target.value;

    // Special formatting for username (could be phone or email)
    if (field === 'username') {
      // If it looks like a phone number, format it
      if (value.match(/^[\d+]/)) {
        value = formatPhoneForInput(value);
      }
    }

    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));

    // Clear field error when user starts typing
    if (fieldErrors[field]) {
      setFieldErrors(prev => ({
        ...prev,
        [field]: undefined,
      }));
    }

    // Clear general error when user makes changes
    if (error && onClearError) {
      onClearError();
    }
  };

  const validateForm = (): boolean => {
    const errors: Partial<Record<keyof UserLogin, string>> = {};

    // Validate username (can be email or phone)
    if (!formData.username) {
      errors.username = 'Email or phone number is required';
    } else {
      const isEmail = formData.username.includes('@');
      const isPhone = formData.username.startsWith('+91');

      if (isEmail) {
        const emailValidation = validateEmail(formData.username);
        if (!emailValidation.isValid) {
          errors.username = emailValidation.error;
        }
      } else if (isPhone) {
        const phoneValidation = validatePhoneNumber(formData.username);
        if (!phoneValidation.isValid) {
          errors.username = phoneValidation.error;
        }
      } else {
        errors.username = 'Please enter a valid email or phone number (+91xxxxxxxxxx)';
      }
    }

    // Validate password
    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      errors.password = 'Password must be at least 6 characters';
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
    } catch (error) {
      // Error handling is managed by parent component
    }
  };

  const getUsernameHelperText = (): string => {
    if (fieldErrors.username) {
      return fieldErrors.username;
    }
    
    if (formData.username.startsWith('+91')) {
      return 'Phone number format: +919876543210';
    } else if (formData.username.includes('@')) {
      return 'Email format: user@example.com';
    }
    
    return 'Enter email or phone number (+91xxxxxxxxxx)';
  };

  return (
    <Paper elevation={3} sx={{ p: 4, maxWidth: 400, mx: 'auto' }}>
      <Typography variant="h4" component="h1" gutterBottom align="center">
        Sign In
      </Typography>
      
      <Typography variant="body2" color="textSecondary" align="center" sx={{ mb: 3 }}>
        Welcome back to Quantleap Analytics
      </Typography>

      {error && (
        <Box sx={{ mb: 2 }}>
          <ErrorAlert message={error} onClose={onClearError} />
        </Box>
      )}

      <Box component="form" onSubmit={handleSubmit} noValidate>
        <TextField
          fullWidth
          margin="normal"
          label="Email or Phone Number"
          value={formData.username}
          onChange={handleInputChange('username')}
          error={!!fieldErrors.username}
          helperText={getUsernameHelperText()}
          required
          placeholder="user@example.com or +919876543210"
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <AccountCircle />
              </InputAdornment>
            ),
          }}
        />

        <TextField
          fullWidth
          margin="normal"
          label="Password"
          type={showPassword ? 'text' : 'password'}
          value={formData.password}
          onChange={handleInputChange('password')}
          error={!!fieldErrors.password}
          helperText={fieldErrors.password}
          required
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  aria-label="toggle password visibility"
                  onClick={() => setShowPassword(!showPassword)}
                  edge="end"
                >
                  {showPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />

        <Box sx={{ textAlign: 'right', mt: 1, mb: 2 }}>
          <Link href="#" variant="body2" color="primary">
            Forgot password?
          </Link>
        </Box>

        <Button
          type="submit"
          fullWidth
          variant="contained"
          size="large"
          disabled={isLoading}
          sx={{ mt: 2, mb: 2 }}
        >
          {isLoading ? 'Signing In...' : 'Sign In'}
        </Button>

        <Typography variant="body2" align="center">
          Don't have an account?{' '}
          <Button variant="text" size="small" onClick={onRegisterClick}>
            Create Account
          </Button>
        </Typography>
      </Box>
    </Paper>
  );
};

export default LoginForm;