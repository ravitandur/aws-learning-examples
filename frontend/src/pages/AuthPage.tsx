import React, { useState, useEffect } from 'react';
import { Turtle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import LoginForm from '../components/auth/LoginForm';
import RegisterForm from '../components/auth/RegisterForm';
import ForgotPasswordForm from '../components/auth/ForgotPasswordForm';
import ResetPasswordForm from '../components/auth/ResetPasswordForm';
import EmailVerificationForm from '../components/auth/EmailVerificationForm';
import LoadingSpinner from '../components/common/LoadingSpinner';

const AuthPage: React.FC = () => {
  const { login, register, forgotPassword, resetPassword, isLoading, error, clearError, isAuthenticated } = useAuth() as any;
  const [authMode, setAuthMode] = useState<'login' | 'register' | 'forgot-password' | 'reset-password' | 'verify-email'>('login');
  
  const [registrationSuccess, setRegistrationSuccess] = useState(false);
  const [forgotPasswordSuccess, setForgotPasswordSuccess] = useState(false);
  const [resetPasswordSuccess, setResetPasswordSuccess] = useState(false);
  const [pendingVerificationEmail, setPendingVerificationEmail] = useState<string>('');
  const [pendingResetEmail, setPendingResetEmail] = useState<string>('');

  const handleLogin = async (credentials: any) => {
    try {
      await login(credentials);
    } catch (error) {
      // Error is handled by AuthContext
    }
  };

  const handleRegister = async (userData: any) => {
    try {
      const response = await register(userData);
      
      // Check if email verification is required
      if (response?.email_verification_required === true) {
        // After successful registration, redirect to verification
        setPendingVerificationEmail(userData.email);
        setAuthMode('verify-email');
      } else {
        // If no verification needed, show success and go to login
        setRegistrationSuccess(true);
        setAuthMode('login');
      }
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
    setForgotPasswordSuccess(false);
    setResetPasswordSuccess(false);
    setPendingVerificationEmail('');
    setPendingResetEmail('');
    setAuthMode('login');
  };

  const switchToForgotPassword = () => {
    clearError();
    setRegistrationSuccess(false);
    setForgotPasswordSuccess(false);
    setResetPasswordSuccess(false);
    setAuthMode('forgot-password');
  };

  const switchToResetPassword = () => {
    clearError();
    setAuthMode('reset-password');
  };

  const handleVerificationSuccess = () => {
    // After successful email verification, show success message and go to login
    setRegistrationSuccess(true);
    setPendingVerificationEmail('');
    setAuthMode('login');
  };

  const handleForgotPasswordSubmit = async (email: string) => {
    try {
      await forgotPassword(email);
      setPendingResetEmail(email);
      setForgotPasswordSuccess(true);
    } catch (error) {
      // Error is handled by AuthContext
    }
  };

  const handleResetPasswordSubmit = async (email: string, code: string, newPassword: string) => {
    try {
      await resetPassword(email, code, newPassword);
      setResetPasswordSuccess(true);
    } catch (error) {
      // Error is handled by AuthContext
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-sm mx-auto mt-20">
        <LoadingSpinner message="Authenticating..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center py-4">
      <div className="w-full max-w-md px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Turtle className="h-12 w-12 text-blue-600 mr-3" />
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Quantleap Analytics
            </h1>
          </div>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            Algorithmic Trading Platform for Indian Markets
          </p>
        </div>

        {/* Registration Success Message */}
        {registrationSuccess && (
          <div className="mb-6">
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-green-800 dark:text-green-200 mb-1">
                    <strong>Registration Successful!</strong>
                  </p>
                  <p className="text-sm text-green-700 dark:text-green-300">
                    Your account has been created and email verified successfully. You can now sign in to continue to your dashboard.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Auth Forms */}
        {authMode === 'login' ? (
          <LoginForm
            onSubmit={handleLogin}
            onRegisterClick={switchToRegister}
            onForgotPasswordClick={switchToForgotPassword}
            isLoading={isLoading}
            error={error}
            onClearError={clearError}
          />
        ) : authMode === 'register' ? (
          <RegisterForm
            onSubmit={handleRegister}
            isLoading={isLoading}
            error={error}
            onClearError={clearError}
          />
        ) : authMode === 'verify-email' ? (
          <EmailVerificationForm
            email={pendingVerificationEmail}
            onBack={switchToLogin}
            onVerificationSuccess={handleVerificationSuccess}
          />
        ) : authMode === 'reset-password' ? (
          <ResetPasswordForm
            email={pendingResetEmail}
            onSubmit={handleResetPasswordSubmit}
            onBackToForgotPassword={resetPasswordSuccess ? switchToLogin : switchToForgotPassword}
            isLoading={isLoading}
            error={error}
            onClearError={clearError}
            success={resetPasswordSuccess}
          />
        ) : (
          <ForgotPasswordForm
            onSubmit={handleForgotPasswordSubmit}
            onBackToLogin={switchToLogin}
            onContinueToReset={switchToResetPassword}
            isLoading={isLoading}
            error={error}
            onClearError={clearError}
            success={forgotPasswordSuccess}
          />
        )}

        {/* Additional Info for Register Form */}
        {authMode === 'register' && (
          <div className="mt-6 text-center">
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-md p-4">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                <strong>Why Quantleap Analytics?</strong>
              </p>
              <div className="text-sm text-gray-600 dark:text-gray-300 space-y-1">
                <p>• Secure AWS-based infrastructure</p>
                <p>• Indian market specialized algorithms</p>
                <p>• Zerodha integration for seamless trading</p>
                <p>• Advanced risk management tools</p>
              </div>
            </div>
          </div>
        )}

        {/* Switch Auth Mode */}
        {authMode === 'register' && (
          <div className="mt-4 text-center">
            <p className="text-sm text-gray-600 dark:text-gray-300">
              Already have an account?{' '}
              <button
                className="text-blue-600 dark:text-blue-400 underline font-semibold hover:text-blue-700 dark:hover:text-blue-300"
                onClick={switchToLogin}
              >
                Sign In Here
              </button>
            </p>
          </div>
        )}

        {/* Footer */}
        <div className="text-center mt-8">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Module 2: User Authentication & Broker Management
          </p>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;