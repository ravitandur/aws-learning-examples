import apiClient from './apiClient';
import { UserLogin, UserRegistration, AuthTokens, User, ApiResponse, EmailVerificationResponse } from '../types';

class AuthService {
  /**
   * Register a new user
   */
  async register(userData: UserRegistration): Promise<ApiResponse<{ user_id: string }>> {
    try {
      const response = await apiClient.post<ApiResponse<{ user_id: string }>>(
        '/auth/register',
        userData
      );
      return response;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Registration failed');
    }
  }

  /**
   * Login user and get JWT tokens
   */
  async login(credentials: UserLogin): Promise<{ tokens: AuthTokens; user: User }> {
    try {
      const response = await apiClient.post<{
        message: string;
        user_id: string;
        user_attributes: any;
        tokens: {
          access_token: string;
          id_token: string;
          refresh_token: string;
          token_type: string;
          expires_in: number;
        }
      }>('/auth/login', credentials);

      if (!response.tokens) {
        throw new Error(response.message || 'Login failed');
      }

      const tokens: AuthTokens = {
        accessToken: response.tokens.access_token,
        idToken: response.tokens.id_token,
        refreshToken: response.tokens.refresh_token,
        expiresIn: response.tokens.expires_in,
      };

      // Store tokens in API client
      apiClient.setTokens(tokens);

      // Store user profile from login response
      const user = this.storeUserProfile(response.user_attributes, response.user_id);

      return { tokens, user };
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Login failed');
    }
  }

  /**
   * Get user profile information
   */
  async getUserProfile(): Promise<User> {
    try {
      // For now, we'll extract user info from stored login data
      // In the future, we can create a separate profile endpoint
      const storedUserData = localStorage.getItem('user_profile');
      if (storedUserData) {
        return JSON.parse(storedUserData);
      }
      
      throw new Error('No user profile found. Please login again.');
    } catch (error: any) {
      throw new Error('Failed to fetch user profile');
    }
  }

  /**
   * Store user profile data
   */
  storeUserProfile(userData: any, userId: string): User {
    const user: User = {
      id: userId,
      email: userData.email || '',
      phoneNumber: userData.phone_number || '',
      fullName: userData.name || '',
      state: userData.state || '',
      createdAt: new Date().toISOString(),
    };
    
    localStorage.setItem('user_profile', JSON.stringify(user));
    return user;
  }

  /**
   * Update user profile
   */
  async updateProfile(updates: Partial<Pick<User, 'fullName' | 'state'>>): Promise<User> {
    try {
      const response = await apiClient.put<ApiResponse<User>>('/auth/profile', updates);
      
      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to update profile');
      }

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to update profile');
    }
  }

  /**
   * Verify email address with confirmation code
   */
  async verifyEmail(email: string, confirmationCode: string): Promise<EmailVerificationResponse> {
    try {
      const response = await apiClient.post<EmailVerificationResponse>('/auth/verify-email', {
        email: email.toLowerCase().trim(),
        confirmation_code: confirmationCode,
      });
      return response as EmailVerificationResponse;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Email verification failed');
    }
  }

  /**
   * Resend verification code for email or phone
   */
  async resendVerification(email: string, verificationType: 'email' | 'phone'): Promise<ApiResponse> {
    try {
      const response = await apiClient.post<ApiResponse>('/auth/resend-verification', {
        email: email.toLowerCase().trim(),
        verification_type: verificationType,
      });
      return response;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to resend verification code');
    }
  }

  /**
   * Request password reset
   */
  async forgotPassword(email: string): Promise<ApiResponse> {
    try {
      const response = await apiClient.post<ApiResponse>('/auth/forgot-password', {
        email: email.toLowerCase().trim(),
      });
      return response;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to send reset instructions');
    }
  }

  /**
   * Reset password with verification code
   */
  async resetPassword(email: string, code: string, newPassword: string): Promise<ApiResponse> {
    try {
      const response = await apiClient.post<ApiResponse>('/auth/reset-password', {
        email: email.toLowerCase().trim(),
        verification_code: code,
        new_password: newPassword,
      });
      return response;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to reset password');
    }
  }

  /**
   * Confirm forgot password (for Cognito flow)
   */
  async confirmForgotPassword(email: string, confirmationCode: string, newPassword: string): Promise<ApiResponse> {
    try {
      const response = await apiClient.post<ApiResponse>('/auth/confirm-forgot-password', {
        email: email.toLowerCase().trim(),
        confirmation_code: confirmationCode,
        new_password: newPassword,
      });
      return response;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to confirm password reset');
    }
  }

  /**
   * Logout user
   */
  logout(): void {
    apiClient.clearTokens();
  }

  /**
   * Check if user is currently authenticated
   */
  isAuthenticated(): boolean {
    return apiClient.isAuthenticated();
  }

  /**
   * Get stored tokens
   */
  getTokens(): AuthTokens | null {
    return apiClient.getTokens();
  }

  /**
   * Validate Indian phone number format
   */
  static validatePhoneNumber(phone: string): boolean {
    const phoneRegex = /^\+91[6-9]\d{9}$/;
    return phoneRegex.test(phone);
  }

  /**
   * Format phone number for display
   */
  static formatPhoneNumber(phone: string): string {
    if (phone.startsWith('+91')) {
      const number = phone.substring(3);
      return `+91 ${number.substring(0, 5)} ${number.substring(5)}`;
    }
    return phone;
  }
}

const authService = new AuthService();
export default authService;