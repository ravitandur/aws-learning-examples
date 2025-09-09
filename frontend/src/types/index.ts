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
  user_id: string;
  client_id: string;
  broker_name: 'zerodha' | 'angel' | 'finvasia' | 'zebu';
  group: 'BFW' | 'KOU' | 'PMS';
  capital: number;
  account_status: 'enabled' | 'disabled' | 'pending';
  description: string;
  created_at: string;
  updated_at: string;
  has_credentials: boolean;
  has_oauth_token: boolean;
  token_expires_at?: string;
  last_oauth_login?: string;
  metadata?: {
    exchanges_enabled: string[];
    products_enabled: string[];
  };
}

export interface CreateBrokerAccount {
  broker_name: 'zerodha' | 'angel' | 'finvasia' | 'zebu';
  client_id: string;
  api_key: string;
  api_secret: string;
  capital: number;
  description?: string;
}

export interface UpdateBrokerAccount {
  api_key?: string;
  api_secret?: string;
  capital?: number;
  description?: string;
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

// Indian States
export const INDIAN_STATES = [
  'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
  'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
  'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
  'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana',
  'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
  'Andaman and Nicobar Islands', 'Chandigarh', 'Dadra and Nagar Haveli',
  'Daman and Diu', 'Delhi', 'Jammu and Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry'
] as const;

export type IndianState = typeof INDIAN_STATES[number];

// Basket and Strategy Types for Options Platform
export interface Strategy {
  strategyId: string;
  strategyName: string;
  strategyType: string;
  status: 'ACTIVE' | 'PAUSED' | 'COMPLETED';
  legs: number;
}

export interface Basket {
  basket_id: string;
  basket_name: string;
  description?: string;
  strategies: Strategy[];
  status: 'ACTIVE' | 'PAUSED' | 'INACTIVE';
  created_at: string;
}

export interface CreateBasket {
  basket_name: string;
  description?: string;
  strategies: string[];
  initial_capital: number;
}

export interface UpdateBasket {
  basket_name?: string;
  description?: string;
  strategies?: string[];
  status?: 'ACTIVE' | 'PAUSED' | 'INACTIVE';
}

// Basket-Broker Allocation Types (New Separate System)
export interface BasketBrokerAllocation {
  basket_id: string;
  broker_id: string;
  client_id: string;
  lot_multiplier: number;
  status: 'ACTIVE' | 'INACTIVE';
  created_at: string;
  updated_at: string;
}

export interface CreateAllocation {
  allocations: {
    broker_id: string;
    client_id: string;
    lot_multiplier: number;
  }[];
}

export interface UpdateAllocation {
  lot_multiplier: number;
  status?: 'ACTIVE' | 'INACTIVE';
}