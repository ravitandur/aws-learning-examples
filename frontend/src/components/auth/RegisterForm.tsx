import React, { useState } from 'react';
import {
  Eye,
  EyeOff,
  User,
  Mail,
  Phone,
  MapPin,
} from 'lucide-react';
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
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-8 w-full max-w-lg mx-auto">
      <h1 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-2">
        Create Account
      </h1>
      
      <p className="text-center text-gray-600 dark:text-gray-300 mb-6">
        Join Quantleap Analytics algorithmic trading platform
      </p>

      {error && (
        <div className="mb-4">
          <ErrorAlert message={error} onClose={onClearError} />
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
            Full Name *
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <User className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              value={formData.full_name}
              onChange={handleInputChange('full_name')}
              className={`block w-full pl-10 pr-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 ${
                fieldErrors.full_name
                  ? 'border-red-300 dark:border-red-600'
                  : 'border-gray-300 dark:border-gray-600'
              }`}
              required
            />
          </div>
          {fieldErrors.full_name && (
            <p className="mt-1 text-xs text-red-600 dark:text-red-400">{fieldErrors.full_name}</p>
          )}
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
            Phone Number *
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Phone className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="tel"
              value={formData.phone_number}
              onChange={handleInputChange('phone_number')}
              className={`block w-full pl-10 pr-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 ${
                fieldErrors.phone_number
                  ? 'border-red-300 dark:border-red-600'
                  : 'border-gray-300 dark:border-gray-600'
              }`}
              placeholder="+919876543210"
              required
            />
          </div>
          <p className={`mt-1 text-xs ${
            fieldErrors.phone_number ? 'text-red-600 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'
          }`}>
            {fieldErrors.phone_number || 'Format: +919876543210'}
          </p>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
            Email *
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Mail className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="email"
              value={formData.email}
              onChange={handleInputChange('email')}
              className={`block w-full pl-10 pr-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 ${
                fieldErrors.email
                  ? 'border-red-300 dark:border-red-600'
                  : 'border-gray-300 dark:border-gray-600'
              }`}
              required
            />
          </div>
          {fieldErrors.email && (
            <p className="mt-1 text-xs text-red-600 dark:text-red-400">{fieldErrors.email}</p>
          )}
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
            State *
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MapPin className="h-5 w-5 text-gray-400" />
            </div>
            <select
              value={formData.state}
              onChange={(e) => {
                setFormData(prev => ({ ...prev, state: e.target.value }));
                if (fieldErrors.state) {
                  setFieldErrors(prev => ({ ...prev, state: undefined }));
                }
              }}
              className={`block w-full pl-10 pr-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                fieldErrors.state
                  ? 'border-red-300 dark:border-red-600'
                  : 'border-gray-300 dark:border-gray-600'
              }`}
              required
            >
              <option value="">Select a state</option>
              {INDIAN_STATES.map((state) => (
                <option key={state} value={state}>
                  {state}
                </option>
              ))}
            </select>
          </div>
          {fieldErrors.state && (
            <p className="mt-1 text-xs text-red-600 dark:text-red-400">{fieldErrors.state}</p>
          )}
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
            Password *
          </label>
          <div className="relative">
            <input
              type={showPassword ? 'text' : 'password'}
              value={formData.password}
              onChange={handleInputChange('password')}
              className={`block w-full pr-10 pl-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 ${
                fieldErrors.password
                  ? 'border-red-300 dark:border-red-600'
                  : 'border-gray-300 dark:border-gray-600'
              }`}
              required
            />
            <button
              type="button"
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? (
                <EyeOff className="h-5 w-5 text-gray-400 dark:text-gray-500" />
              ) : (
                <Eye className="h-5 w-5 text-gray-400 dark:text-gray-500" />
              )}
            </button>
          </div>
          <p className={`mt-1 text-xs ${
            fieldErrors.password ? 'text-red-600 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'
          }`}>
            {fieldErrors.password || 'Must contain uppercase, lowercase, number and special character'}
          </p>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 dark:disabled:bg-blue-800 text-white font-medium py-2 px-4 rounded-lg transition-colors mb-4"
        >
          {isLoading ? 'Creating Account...' : 'Create Account'}
        </button>

        <p className="text-center text-sm text-gray-600 dark:text-gray-300">
          Already have an account?{' '}
          <button
            type="button"
            className="text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300 font-medium"
          >
            Sign In
          </button>
        </p>
      </form>
    </div>
  );
};

export default RegisterForm;