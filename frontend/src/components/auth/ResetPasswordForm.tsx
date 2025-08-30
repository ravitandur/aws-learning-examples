import React, { useState } from 'react';
import { ArrowLeft, Lock, Eye, EyeOff, KeyRound } from 'lucide-react';
import { validatePassword } from '../../utils/validation';
import ErrorAlert from '../common/ErrorAlert';

interface ResetPasswordFormProps {
  email: string;
  onSubmit: (email: string, code: string, newPassword: string) => Promise<void>;
  onBackToForgotPassword: () => void;
  isLoading?: boolean;
  error?: string | null;
  onClearError?: () => void;
  success?: boolean;
}

const ResetPasswordForm: React.FC<ResetPasswordFormProps> = ({
  email,
  onSubmit,
  onBackToForgotPassword,
  isLoading = false,
  error,
  onClearError,
  success = false,
}) => {
  const [formData, setFormData] = useState({
    verificationCode: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleInputChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));

    // Clear field error when user starts typing
    if (fieldErrors[field]) {
      setFieldErrors(prev => ({
        ...prev,
        [field]: '',
      }));
    }

    // Clear general error when user makes changes
    if (error && onClearError) {
      onClearError();
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    // Validate verification code
    if (!formData.verificationCode.trim()) {
      errors.verificationCode = 'Verification code is required';
    } else if (!/^\d{6}$/.test(formData.verificationCode.trim())) {
      errors.verificationCode = 'Verification code must be 6 digits';
    }

    // Validate new password
    const passwordValidation = validatePassword(formData.newPassword);
    if (!passwordValidation.isValid) {
      errors.newPassword = passwordValidation.error || 'Invalid password';
    }

    // Validate confirm password
    if (!formData.confirmPassword) {
      errors.confirmPassword = 'Please confirm your password';
    } else if (formData.newPassword !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
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
      await onSubmit(email, formData.verificationCode.trim(), formData.newPassword);
    } catch (error) {
      // Error handling is managed by parent component
    }
  };

  if (success) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-8 w-full max-w-md mx-auto">
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
            <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Password Reset Successful
          </h1>
          <p className="text-gray-600 mb-6">
            Your password has been successfully reset. You can now sign in with your new password.
          </p>
          <button
            onClick={() => {
              // Clear success state and go to login
              if (onBackToForgotPassword) {
                onBackToForgotPassword();
              }
            }}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
          >
            Continue to Sign In
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-8 w-full max-w-md mx-auto">
      <div className="mb-6">
        <button
          onClick={onBackToForgotPassword}
          className="inline-flex items-center text-blue-600 hover:text-blue-500 font-medium mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </button>
        
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Reset Your Password
        </h1>
        <p className="text-gray-600">
          Enter the verification code sent to <strong>{email}</strong> and choose a new password.
        </p>
      </div>

      {error && (
        <div className="mb-4">
          <ErrorAlert message={error} onClose={onClearError} />
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        {/* Verification Code */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Verification Code *
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <KeyRound className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              value={formData.verificationCode}
              onChange={handleInputChange('verificationCode')}
              className={`block w-full pl-10 pr-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                fieldErrors.verificationCode
                  ? 'border-red-300 text-red-900 placeholder-red-300'
                  : 'border-gray-300 text-gray-900 placeholder-gray-500'
              }`}
              placeholder="Enter 6-digit code"
              maxLength={6}
              required
            />
          </div>
          {fieldErrors.verificationCode && (
            <p className="mt-1 text-xs text-red-600">{fieldErrors.verificationCode}</p>
          )}
        </div>

        {/* New Password */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            New Password *
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Lock className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type={showPassword ? 'text' : 'password'}
              value={formData.newPassword}
              onChange={handleInputChange('newPassword')}
              className={`block w-full pl-10 pr-12 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                fieldErrors.newPassword
                  ? 'border-red-300 text-red-900 placeholder-red-300'
                  : 'border-gray-300 text-gray-900 placeholder-gray-500'
              }`}
              placeholder="Enter new password"
              required
            />
            <button
              type="button"
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? (
                <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
              ) : (
                <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
              )}
            </button>
          </div>
          {fieldErrors.newPassword && (
            <p className="mt-1 text-xs text-red-600">{fieldErrors.newPassword}</p>
          )}
          <p className="mt-1 text-xs text-gray-500">
            Password must be at least 8 characters with uppercase, lowercase, number, and special character.
          </p>
        </div>

        {/* Confirm Password */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Confirm New Password *
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Lock className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type={showConfirmPassword ? 'text' : 'password'}
              value={formData.confirmPassword}
              onChange={handleInputChange('confirmPassword')}
              className={`block w-full pl-10 pr-12 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                fieldErrors.confirmPassword
                  ? 'border-red-300 text-red-900 placeholder-red-300'
                  : 'border-gray-300 text-gray-900 placeholder-gray-500'
              }`}
              placeholder="Confirm new password"
              required
            />
            <button
              type="button"
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            >
              {showConfirmPassword ? (
                <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
              ) : (
                <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
              )}
            </button>
          </div>
          {fieldErrors.confirmPassword && (
            <p className="mt-1 text-xs text-red-600">{fieldErrors.confirmPassword}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium py-2 px-4 rounded-lg transition-colors"
        >
          {isLoading ? 'Resetting Password...' : 'Reset Password'}
        </button>
      </form>

      <div className="mt-4 text-center">
        <p className="text-sm text-gray-500">
          Didn't receive the code?{' '}
          <button
            onClick={onBackToForgotPassword}
            className="text-blue-600 hover:text-blue-500 font-medium"
          >
            Try again
          </button>
        </p>
      </div>
    </div>
  );
};

export default ResetPasswordForm;