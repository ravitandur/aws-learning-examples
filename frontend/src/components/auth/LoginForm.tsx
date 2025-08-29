import React, { useState } from 'react';
import {
  Eye,
  EyeOff,
  User,
} from 'lucide-react';
import { UserLogin } from '../../types';
import { validatePhoneNumber, validateEmail, formatPhoneForInput } from '../../utils/validation';
import ErrorAlert from '../common/ErrorAlert';

interface LoginFormProps {
  onSubmit: (credentials: UserLogin) => Promise<void>;
  onRegisterClick: () => void;
  onForgotPasswordClick?: () => void;
  isLoading?: boolean;
  error?: string | null;
  onClearError?: () => void;
}

const LoginForm: React.FC<LoginFormProps> = ({
  onSubmit,
  onRegisterClick,
  onForgotPasswordClick,
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
    <div className="bg-white rounded-lg shadow-lg p-8 w-full max-w-md mx-auto">
      <h1 className="text-3xl font-bold text-center text-gray-900 mb-2">
        Sign In
      </h1>
      
      <p className="text-center text-gray-600 mb-6">
        Welcome back to Quantleap Analytics
      </p>

      {error && (
        <div className="mb-4">
          <ErrorAlert message={error} onClose={onClearError} />
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Email or Phone Number *
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <User className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              value={formData.username}
              onChange={handleInputChange('username')}
              className={`block w-full pl-10 pr-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                fieldErrors.username
                  ? 'border-red-300 text-red-900 placeholder-red-300'
                  : 'border-gray-300 text-gray-900 placeholder-gray-500'
              }`}
              placeholder="user@example.com or +919876543210"
              required
            />
          </div>
          <p className={`mt-1 text-xs ${
            fieldErrors.username ? 'text-red-600' : 'text-gray-500'
          }`}>
            {getUsernameHelperText()}
          </p>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Password *
          </label>
          <div className="relative">
            <input
              type={showPassword ? 'text' : 'password'}
              value={formData.password}
              onChange={handleInputChange('password')}
              className={`block w-full pr-10 pl-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                fieldErrors.password
                  ? 'border-red-300 text-red-900 placeholder-red-300'
                  : 'border-gray-300 text-gray-900 placeholder-gray-500'
              }`}
              required
            />
            <button
              type="button"
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? (
                <EyeOff className="h-5 w-5 text-gray-400" />
              ) : (
                <Eye className="h-5 w-5 text-gray-400" />
              )}
            </button>
          </div>
          {fieldErrors.password && (
            <p className="mt-1 text-xs text-red-600">{fieldErrors.password}</p>
          )}
        </div>

        <div className="text-right mb-4">
          <button
            type="button"
            onClick={onForgotPasswordClick}
            className="text-sm text-blue-600 hover:text-blue-500"
          >
            Forgot password?
          </button>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium py-2 px-4 rounded-lg transition-colors mb-4"
        >
          {isLoading ? 'Signing In...' : 'Sign In'}
        </button>

        <p className="text-center text-sm text-gray-600">
          Don't have an account?{' '}
          <button
            type="button"
            onClick={onRegisterClick}
            className="text-blue-600 hover:text-blue-500 font-medium"
          >
            Create Account
          </button>
        </p>
      </form>
    </div>
  );
};

export default LoginForm;