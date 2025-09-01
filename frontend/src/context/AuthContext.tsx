import React, { createContext, useContext, useEffect, useReducer, ReactNode } from 'react';
import { User, AuthTokens, UserLogin, UserRegistration, AuthContextType, ApiResponse } from '../types';
import authService from '../services/authService';

// Auth State Type
interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// Auth Actions
type AuthAction =
  | { type: 'AUTH_START' }
  | { type: 'AUTH_SUCCESS'; payload: { user: User; tokens: AuthTokens } }
  | { type: 'AUTH_FAILURE'; payload: string }
  | { type: 'AUTH_LOGOUT' }
  | { type: 'SET_USER'; payload: User }
  | { type: 'CLEAR_ERROR' }
  | { type: 'CLEAR_LOADING' };

// Initial State
const initialState: AuthState = {
  user: null,
  tokens: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

// Auth Reducer
const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'AUTH_START':
      return {
        ...state,
        isLoading: true,
        error: null,
      };

    case 'AUTH_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        tokens: action.payload.tokens,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };

    case 'AUTH_FAILURE':
      return {
        ...state,
        user: null,
        tokens: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
      };

    case 'AUTH_LOGOUT':
      return {
        ...state,
        user: null,
        tokens: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      };

    case 'SET_USER':
      return {
        ...state,
        user: action.payload,
        isLoading: false,
      };

    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
        isLoading: false,
      };

    case 'CLEAR_LOADING':
      return {
        ...state,
        isLoading: false,
      };

    default:
      return state;
  }
};

// Extended AuthContext type
interface ExtendedAuthContextType extends AuthContextType {
  updateProfile: (updates: Partial<Pick<User, 'fullName' | 'state'>>) => Promise<void>;
}

// Create Context
const AuthContext = createContext<ExtendedAuthContextType | undefined>(undefined);

// Auth Provider Props
interface AuthProviderProps {
  children: ReactNode;
}

// Auth Provider Component
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Initialize auth state on app load
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const tokens = authService.getTokens();
        
        if (tokens && authService.isAuthenticated()) {
          // Try to get user profile
          const user = await authService.getUserProfile();
          dispatch({ type: 'AUTH_SUCCESS', payload: { user, tokens } });
        } else {
          dispatch({ type: 'AUTH_LOGOUT' });
        }
      } catch (error) {
        console.error('Auth initialization failed:', error);
        authService.logout();
        dispatch({ type: 'AUTH_LOGOUT' });
      }
    };

    initializeAuth();
  }, []);

  // Listen for unauthorized events from API client
  useEffect(() => {
    const handleUnauthorized = () => {
      dispatch({ type: 'AUTH_LOGOUT' });
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, []);

  // Login function
  const login = async (credentials: UserLogin): Promise<void> => {
    try {
      dispatch({ type: 'AUTH_START' });
      
      const { tokens, user } = await authService.login(credentials);
      
      dispatch({ type: 'AUTH_SUCCESS', payload: { user, tokens } });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage });
      throw error;
    }
  };

  // Register function
  const register = async (userData: UserRegistration): Promise<ApiResponse<any>> => {
    try {
      dispatch({ type: 'AUTH_START' });
      
      const response = await authService.register(userData);
      
      if (response.success) {
        // Clear loading state so AuthPage can show verification form
        dispatch({ type: 'CLEAR_LOADING' });
        return response;
      } else {
        throw new Error(response.message || 'Registration failed');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Registration failed';
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage });
      throw error;
    }
  };

  // Logout function
  const logout = (): void => {
    authService.logout();
    dispatch({ type: 'AUTH_LOGOUT' });
  };

  // Update user profile
  const updateProfile = async (updates: Partial<Pick<User, 'fullName' | 'state'>>): Promise<void> => {
    try {
      const updatedUser = await authService.updateProfile(updates);
      dispatch({ type: 'SET_USER', payload: updatedUser });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Profile update failed';
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage });
      throw error;
    }
  };

  // Forgot password function
  const forgotPassword = async (email: string): Promise<void> => {
    try {
      dispatch({ type: 'AUTH_START' });
      
      const response = await authService.forgotPassword(email);
      
      if (!response.success) {
        throw new Error(response.message || 'Failed to send reset instructions');
      }
      
      // Clear loading state without changing auth status
      dispatch({ type: 'CLEAR_ERROR' });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to send reset instructions';
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage });
      throw error;
    }
  };

  // Reset password function
  const resetPassword = async (email: string, code: string, newPassword: string): Promise<void> => {
    try {
      dispatch({ type: 'AUTH_START' });
      
      const response = await authService.confirmForgotPassword(email, code, newPassword);
      
      if (!response.success) {
        throw new Error(response.message || 'Failed to reset password');
      }
      
      // Clear loading state without changing auth status
      dispatch({ type: 'CLEAR_ERROR' });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to reset password';
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage });
      throw error;
    }
  };

  // Verify email function
  const verifyEmail = async (email: string, confirmationCode: string): Promise<void> => {
    try {
      dispatch({ type: 'AUTH_START' });
      
      const response = await authService.verifyEmail(email, confirmationCode);
      
      // Backend returns {verified: true} for success, not {success: true}
      if (!response.verified && !response.message?.includes('verified successfully')) {
        throw new Error(response.message || 'Email verification failed');
      }
      
      // Clear loading state after successful email verification
      dispatch({ type: 'CLEAR_ERROR' });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Email verification failed';
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage });
      throw error;
    }
  };

  // Resend verification code function
  const resendVerification = async (email: string, verificationType: 'email' | 'phone'): Promise<void> => {
    try {
      dispatch({ type: 'AUTH_START' });
      
      const response = await authService.resendVerification(email, verificationType);
      
      if (!response.success) {
        throw new Error(response.message || 'Failed to resend verification code');
      }
      
      // Clear loading state without changing auth status
      dispatch({ type: 'CLEAR_ERROR' });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to resend verification code';
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage });
      throw error;
    }
  };

  // Clear error
  const clearError = (): void => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const value: ExtendedAuthContextType = {
    user: state.user,
    tokens: state.tokens,
    isAuthenticated: state.isAuthenticated,
    isLoading: state.isLoading,
    error: state.error,
    login,
    register,
    logout,
    forgotPassword,
    resetPassword,
    updateProfile,
    verifyEmail,
    resendVerification,
    clearError,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};