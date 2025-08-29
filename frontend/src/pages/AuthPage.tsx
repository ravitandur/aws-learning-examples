import React, { useState } from 'react';
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
      <div className="max-w-sm mx-auto mt-20">
        <LoadingSpinner message="Authenticating..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 via-purple-600 to-purple-800 flex items-center justify-center py-4">
      <div className="w-full max-w-md px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            Quantleap Analytics
          </h1>
          <p className="text-xl text-white/90">
            Algorithmic Trading Platform for Indian Markets
          </p>
        </div>

        {/* Registration Success Message */}
        {registrationSuccess && (
          <div className="mb-6">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-green-800 mb-1">
                    <strong>Registration Successful!</strong>
                  </p>
                  <p className="text-sm text-green-700">
                    Your account has been created successfully. Please sign in to continue to your dashboard.
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
          <div className="mt-6 text-center">
            <div className="bg-white rounded-lg shadow-md p-4">
              <p className="text-sm font-medium text-gray-700 mb-2">
                <strong>Why Quantleap Analytics?</strong>
              </p>
              <div className="text-sm text-gray-600 space-y-1">
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
            <p className="text-sm text-white/80">
              Already have an account?{' '}
              <button
                className="text-white underline font-semibold hover:text-white/90"
                onClick={switchToLogin}
              >
                Sign In Here
              </button>
            </p>
          </div>
        )}

        {/* Footer */}
        <div className="text-center mt-8">
          <p className="text-sm text-white/70">
            Module 2: User Authentication & Broker Management
          </p>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;