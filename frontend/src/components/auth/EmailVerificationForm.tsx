import React, { useState } from 'react';
import { Mail, CheckCircle, RefreshCw, ArrowLeft } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorAlert from '../common/ErrorAlert';

interface EmailVerificationFormProps {
  email: string;
  onBack: () => void;
  onVerificationSuccess: () => void;
}

const EmailVerificationForm: React.FC<EmailVerificationFormProps> = ({
  email,
  onBack,
  onVerificationSuccess,
}) => {
  const { verifyEmail, resendVerification, isLoading, error, clearError } = useAuth();
  const [confirmationCode, setConfirmationCode] = useState('');
  const [isVerified, setIsVerified] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    
    if (!confirmationCode.trim()) {
      return;
    }

    try {
      await verifyEmail(email, confirmationCode.trim());
      setIsVerified(true);
      
      // Automatically proceed after showing success message
      setTimeout(() => {
        onVerificationSuccess();
      }, 2000);
    } catch (error) {
      // Error is handled by context
      console.error('Email verification failed:', error);
    }
  };

  const handleResendCode = async () => {
    clearError();
    setResendSuccess(false);

    try {
      await resendVerification(email, 'email');
      setResendSuccess(true);
      
      // Clear success message after 5 seconds
      setTimeout(() => {
        setResendSuccess(false);
      }, 5000);
    } catch (error) {
      // Error is handled by context
      console.error('Failed to resend verification code:', error);
    }
  };

  if (isVerified) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-8 w-full max-w-md text-center">
          <div className="mb-6">
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-2">Email Verified Successfully!</h2>
            <p className="text-gray-600 dark:text-gray-300">
              Your email address has been verified. You can now access all features of your account.
            </p>
          </div>
          
          <div className="text-sm text-gray-500 dark:text-gray-400">
            Redirecting you to sign in...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-8 w-full max-w-md">
        <div className="text-center mb-6">
          <Mail className="w-12 h-12 text-blue-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-2">Verify Your Email</h2>
          <p className="text-gray-600 dark:text-gray-300 text-sm">
            We've sent a verification code to
          </p>
          <p className="text-blue-600 dark:text-blue-400 font-medium text-sm mt-1">{email}</p>
        </div>

        {error && <ErrorAlert message={error} onClose={clearError} />}
        
        {resendSuccess && (
          <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
            <p className="text-sm text-green-700 dark:text-green-300">
              Verification code has been resent to your email.
            </p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="confirmationCode" className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
              Verification Code
            </label>
            <input
              type="text"
              id="confirmationCode"
              value={confirmationCode}
              onChange={(e) => setConfirmationCode(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter 6-digit code"
              maxLength={6}
              pattern="[0-9]*"
              inputMode="numeric"
              required
            />
          </div>

          <button
            type="submit"
            disabled={isLoading || !confirmationCode.trim()}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {isLoading ? (
              <>
                <LoadingSpinner size="sm" />
                <span className="ml-2">Verifying...</span>
              </>
            ) : (
              'Verify Email'
            )}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
            Didn't receive the code?
          </p>
          <button
            onClick={handleResendCode}
            disabled={isLoading}
            className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium text-sm flex items-center justify-center mx-auto disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-4 h-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
            Resend Code
          </button>
        </div>

        <div className="mt-8 text-center">
          <button
            onClick={onBack}
            disabled={isLoading}
            className="text-gray-600 dark:text-gray-300 hover:text-gray-700 dark:hover:text-gray-200 font-medium text-sm flex items-center justify-center mx-auto disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to Sign In
          </button>
        </div>
      </div>
    </div>
  );
};

export default EmailVerificationForm;