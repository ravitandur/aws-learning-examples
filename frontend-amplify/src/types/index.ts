// User Types
export interface User {
  id: string;
  email: string;
  phoneNumber: string;
  fullName: string;
  state: string;
  createdAt: string;
}

export interface UserRegistration {
  phone_number: string;
  email: string;
  full_name: string;
  state: string;
  password: string;
}

export interface UserLogin {
  username: string;
  password: string;
}

export interface AuthTokens {
  accessToken: string;
  idToken: string;
  refreshToken: string;
  expiresIn: number;
}

// Broker Account Types
export interface BrokerAccount {
  broker_account_id: string;
  user_id: string;
  broker_name: string;
  account_name: string;
  account_type: string;
  account_status: 'active' | 'inactive' | 'pending';
  created_at: string;
  updated_at: string;
  has_credentials?: boolean;
  metadata?: {
    exchanges_enabled: string[];
    products_enabled: string[];
  };
}

export interface CreateBrokerAccount {
  broker_name: string;
  account_name: string;
  api_key: string;
  api_secret: string;
  account_status: 'active' | 'inactive' | 'pending';
}

export interface UpdateBrokerAccount {
  api_key?: string;
  api_secret?: string;
}

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message: string;
  errors?: string[];
}

// Email Verification Response Type
export interface EmailVerificationResponse {
  message: string;
  verified: boolean;
  account_status: string;
  email_verified?: boolean;
}

// Auth Context Types
export interface AuthContextType {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: UserLogin) => Promise<void>;
  register: (userData: UserRegistration) => Promise<ApiResponse<any>>;
  logout: () => void;
  forgotPassword: (email: string) => Promise<void>;
  resetPassword: (email: string, code: string, newPassword: string) => Promise<void>;
  verifyEmail: (email: string, confirmationCode: string) => Promise<void>;
  resendVerification: (email: string, verificationType: 'email' | 'phone') => Promise<void>;
  clearError: () => void;
}