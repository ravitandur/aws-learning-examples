import React, { useState } from 'react';
import { ArrowLeft, Mail } from 'lucide-react';
import { validateEmail } from '../../utils/validation';
import ErrorAlert from '../common/ErrorAlert';

interface ForgotPasswordFormProps {
  onSubmit: (email: string) => Promise<void>;
  onBackToLogin: () => void;
  onContinueToReset?: () => void;
  isLoading?: boolean;
  error?: string | null;
  onClearError?: () => void;
  success?: boolean;
}

const ForgotPasswordForm: React.FC<ForgotPasswordFormProps> = ({
  onSubmit,
  onBackToLogin,
  onContinueToReset,
  isLoading = false,
  error,
  onClearError,
  success = false,
}) => {
  const [email, setEmail] = useState('');
  const [fieldError, setFieldError] = useState<string>('');

  const handleEmailChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setEmail(value);

    // Clear field error when user starts typing
    if (fieldError) {
      setFieldError('');
    }

    // Clear general error when user makes changes
    if (error && onClearError) {
      onClearError();
    }
  };

  const validateForm = (): boolean => {
    if (!email.trim()) {
      setFieldError('Email is required');
      return false;
    }

    const emailValidation = validateEmail(email);
    if (!emailValidation.isValid) {
      setFieldError(emailValidation.error || 'Invalid email');
      return false;
    }

    setFieldError('');
    return true;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      await onSubmit(email);
    } catch (error) {
      // Error handling is managed by parent component
    }
  };

  if (success) {
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-8 w-full max-w-md mx-auto">
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
            <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Check Your Email
          </h1>
          <p className="text-gray-600 dark:text-gray-300 mb-6">
            We've sent password reset instructions to <strong>{email}</strong>
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
            If you don't see the email in your inbox, please check your spam folder.
          </p>
          <div className="space-y-3">
            {onContinueToReset && (
              <button
                onClick={onContinueToReset}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
              >
                Continue to Enter Code
              </button>
            )}
            <button
              onClick={onBackToLogin}
              className="inline-flex items-center justify-center w-full text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300 font-medium"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Sign In
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-8 w-full max-w-md mx-auto">
      <div className="mb-6">
        <button
          onClick={onBackToLogin}
          className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300 font-medium mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Sign In
        </button>
        
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Reset Password
        </h1>
        <p className="text-gray-600 dark:text-gray-300">
          Enter your email address and we'll send you instructions to reset your password.
        </p>
      </div>

      {error && (
        <div className="mb-4">
          <ErrorAlert message={error} onClose={onClearError} />
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
            Email Address *
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Mail className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="email"
              value={email}
              onChange={handleEmailChange}
              className={`block w-full pl-10 pr-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 ${
                fieldError
                  ? 'border-red-300 dark:border-red-600'
                  : 'border-gray-300 dark:border-gray-600'
              }`}
              placeholder="Enter your email address"
              required
            />
          </div>
          {fieldError && (
            <p className="mt-1 text-xs text-red-600 dark:text-red-400">{fieldError}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 dark:disabled:bg-blue-800 text-white font-medium py-2 px-4 rounded-lg transition-colors"
        >
          {isLoading ? 'Sending Reset Instructions...' : 'Send Reset Instructions'}
        </button>
      </form>

      <div className="mt-6 text-center">
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Remember your password?{' '}
          <button
            onClick={onBackToLogin}
            className="text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300 font-medium"
          >
            Sign In
          </button>
        </p>
      </div>
    </div>
  );
};

export default ForgotPasswordForm;