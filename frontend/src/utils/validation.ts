import { INDIAN_STATES } from '../types';

// Phone number validation for Indian numbers
export const validatePhoneNumber = (phone: string): { isValid: boolean; error?: string } => {
  const phoneRegex = /^\+91[6-9]\d{9}$/;
  
  if (!phone) {
    return { isValid: false, error: 'Phone number is required' };
  }
  
  if (!phone.startsWith('+91')) {
    return { isValid: false, error: 'Phone number must start with +91' };
  }
  
  if (phone.length !== 13) {
    return { isValid: false, error: 'Phone number must be 13 digits including +91' };
  }
  
  if (!phoneRegex.test(phone)) {
    return { isValid: false, error: 'Invalid Indian phone number format' };
  }
  
  return { isValid: true };
};

// Email validation
export const validateEmail = (email: string): { isValid: boolean; error?: string } => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  
  if (!email) {
    return { isValid: false, error: 'Email is required' };
  }
  
  if (!emailRegex.test(email)) {
    return { isValid: false, error: 'Invalid email format' };
  }
  
  return { isValid: true };
};

// Password validation
export const validatePassword = (password: string): { isValid: boolean; error?: string } => {
  if (!password) {
    return { isValid: false, error: 'Password is required' };
  }
  
  if (password.length < 8) {
    return { isValid: false, error: 'Password must be at least 8 characters long' };
  }
  
  if (!/(?=.*[a-z])/.test(password)) {
    return { isValid: false, error: 'Password must contain at least one lowercase letter' };
  }
  
  if (!/(?=.*[A-Z])/.test(password)) {
    return { isValid: false, error: 'Password must contain at least one uppercase letter' };
  }
  
  if (!/(?=.*\d)/.test(password)) {
    return { isValid: false, error: 'Password must contain at least one number' };
  }
  
  if (!/(?=.*[!@#$%^&*(),.?":{}|<>])/.test(password)) {
    return { isValid: false, error: 'Password must contain at least one special character' };
  }
  
  return { isValid: true };
};

// Full name validation
export const validateFullName = (name: string): { isValid: boolean; error?: string } => {
  if (!name) {
    return { isValid: false, error: 'Full name is required' };
  }
  
  if (name.trim().length < 2) {
    return { isValid: false, error: 'Full name must be at least 2 characters long' };
  }
  
  if (!/^[a-zA-Z\s]+$/.test(name)) {
    return { isValid: false, error: 'Full name can only contain letters and spaces' };
  }
  
  return { isValid: true };
};

// Indian state validation
export const validateState = (state: string): { isValid: boolean; error?: string } => {
  if (!state) {
    return { isValid: false, error: 'State is required' };
  }
  
  if (!INDIAN_STATES.includes(state as any)) {
    return { isValid: false, error: 'Please select a valid Indian state' };
  }
  
  return { isValid: true };
};

// API key validation for different brokers
export const validateApiKey = (brokerName: string, apiKey: string): { isValid: boolean; error?: string } => {
  if (!apiKey) {
    return { isValid: false, error: 'API key is required' };
  }
  
  switch (brokerName.toLowerCase()) {
    case 'zerodha':
      if (!/^[a-zA-Z0-9]{15,20}$/.test(apiKey)) {
        return { isValid: false, error: 'Zerodha API key should be 15-20 alphanumeric characters' };
      }
      break;
    default:
      if (apiKey.length < 8) {
        return { isValid: false, error: 'API key must be at least 8 characters long' };
      }
  }
  
  return { isValid: true };
};

// API secret validation for different brokers
export const validateApiSecret = (brokerName: string, apiSecret: string): { isValid: boolean; error?: string } => {
  if (!apiSecret) {
    return { isValid: false, error: 'API secret is required' };
  }
  
  switch (brokerName.toLowerCase()) {
    case 'zerodha':
      if (!/^[a-zA-Z0-9]{20,40}$/.test(apiSecret)) {
        return { isValid: false, error: 'Zerodha API secret should be 20-40 alphanumeric characters' };
      }
      break;
    default:
      if (apiSecret.length < 16) {
        return { isValid: false, error: 'API secret must be at least 16 characters long' };
      }
  }
  
  return { isValid: true };
};

// Format phone number for display
export const formatPhoneNumber = (phone: string): string => {
  if (phone.startsWith('+91')) {
    const number = phone.substring(3);
    return `+91 ${number.substring(0, 5)} ${number.substring(5)}`;
  }
  return phone;
};

// Format phone number for input (remove spaces and ensure +91 prefix)
export const formatPhoneForInput = (phone: string): string => {
  let cleaned = phone.replace(/\s+/g, '');
  
  if (cleaned.startsWith('91') && cleaned.length === 12) {
    cleaned = '+' + cleaned;
  } else if (cleaned.startsWith('9') && cleaned.length === 10) {
    cleaned = '+91' + cleaned;
  } else if (!cleaned.startsWith('+91') && cleaned.length === 10) {
    cleaned = '+91' + cleaned;
  }
  
  return cleaned;
};