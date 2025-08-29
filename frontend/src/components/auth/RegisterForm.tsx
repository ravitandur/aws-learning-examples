import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Paper,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  InputAdornment,
  IconButton,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Person,
  Email,
  Phone,
  LocationOn,
} from '@mui/icons-material';
import { UserRegistration, INDIAN_STATES } from '../../types';
import {
  validatePhoneNumber,
  validateEmail,
  validatePassword,
  validateFullName,
  validateState,
  formatPhoneForInput,
} from '../../utils/validation';
import ErrorAlert from '../common/ErrorAlert';

interface RegisterFormProps {
  onSubmit: (userData: UserRegistration) => Promise<void>;
  isLoading?: boolean;
  error?: string | null;
  onClearError?: () => void;
}

const RegisterForm: React.FC<RegisterFormProps> = ({
  onSubmit,
  isLoading = false,
  error,
  onClearError,
}) => {
  const [formData, setFormData] = useState<UserRegistration>({
    phone_number: '',
    email: '',
    full_name: '',
    state: '',
    password: '',
  });

  const [showPassword, setShowPassword] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof UserRegistration, string>>>({});

  const handleInputChange = (field: keyof UserRegistration) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    let value = event.target.value;

    // Special formatting for phone number
    if (field === 'phone_number') {
      value = formatPhoneForInput(value);
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
    const errors: Partial<Record<keyof UserRegistration, string>> = {};

    // Validate phone number
    const phoneValidation = validatePhoneNumber(formData.phone_number);
    if (!phoneValidation.isValid) {
      errors.phone_number = phoneValidation.error;
    }

    // Validate email
    const emailValidation = validateEmail(formData.email);
    if (!emailValidation.isValid) {
      errors.email = emailValidation.error;
    }

    // Validate full name
    const nameValidation = validateFullName(formData.full_name);
    if (!nameValidation.isValid) {
      errors.full_name = nameValidation.error;
    }

    // Validate state
    const stateValidation = validateState(formData.state);
    if (!stateValidation.isValid) {
      errors.state = stateValidation.error;
    }

    // Validate password
    const passwordValidation = validatePassword(formData.password);
    if (!passwordValidation.isValid) {
      errors.password = passwordValidation.error;
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

  return (
    <Paper elevation={3} sx={{ p: 4, maxWidth: 500, mx: 'auto' }}>
      <Typography variant="h4" component="h1" gutterBottom align="center">
        Create Account
      </Typography>
      
      <Typography variant="body2" color="textSecondary" align="center" sx={{ mb: 3 }}>
        Join Quantleap Analytics algorithmic trading platform
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
          label="Full Name"
          value={formData.full_name}
          onChange={handleInputChange('full_name')}
          error={!!fieldErrors.full_name}
          helperText={fieldErrors.full_name}
          required
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Person />
              </InputAdornment>
            ),
          }}
        />

        <TextField
          fullWidth
          margin="normal"
          label="Phone Number"
          value={formData.phone_number}
          onChange={handleInputChange('phone_number')}
          error={!!fieldErrors.phone_number}
          helperText={fieldErrors.phone_number || 'Format: +919876543210'}
          required
          placeholder="+919876543210"
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Phone />
              </InputAdornment>
            ),
          }}
        />

        <TextField
          fullWidth
          margin="normal"
          label="Email"
          type="email"
          value={formData.email}
          onChange={handleInputChange('email')}
          error={!!fieldErrors.email}
          helperText={fieldErrors.email}
          required
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Email />
              </InputAdornment>
            ),
          }}
        />

        <FormControl fullWidth margin="normal" error={!!fieldErrors.state}>
          <InputLabel>State *</InputLabel>
          <Select
            value={formData.state}
            label="State *"
            onChange={(e) => {
              setFormData(prev => ({ ...prev, state: e.target.value }));
              if (fieldErrors.state) {
                setFieldErrors(prev => ({ ...prev, state: undefined }));
              }
            }}
            startAdornment={
              <InputAdornment position="start">
                <LocationOn />
              </InputAdornment>
            }
          >
            {INDIAN_STATES.map((state) => (
              <MenuItem key={state} value={state}>
                {state}
              </MenuItem>
            ))}
          </Select>
          {fieldErrors.state && (
            <Typography variant="caption" color="error" sx={{ mt: 1, ml: 2 }}>
              {fieldErrors.state}
            </Typography>
          )}
        </FormControl>

        <TextField
          fullWidth
          margin="normal"
          label="Password"
          type={showPassword ? 'text' : 'password'}
          value={formData.password}
          onChange={handleInputChange('password')}
          error={!!fieldErrors.password}
          helperText={fieldErrors.password || 'Must contain uppercase, lowercase, number and special character'}
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

        <Button
          type="submit"
          fullWidth
          variant="contained"
          size="large"
          disabled={isLoading}
          sx={{ mt: 3, mb: 2 }}
        >
          {isLoading ? 'Creating Account...' : 'Create Account'}
        </Button>

        <Typography variant="body2" align="center">
          Already have an account?{' '}
          <Button variant="text" size="small">
            Sign In
          </Button>
        </Typography>
      </Box>
    </Paper>
  );
};

export default RegisterForm;