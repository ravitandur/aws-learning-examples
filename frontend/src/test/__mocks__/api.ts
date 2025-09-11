/**
 * API Mocks for Testing
 * 
 * Mock implementations of API services for testing
 * Following industry standards for API mocking
 */

import { jest } from '@jest/globals';

// Mock API Client
export const mockApiClient = {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  patch: jest.fn(),
};

// Mock Strategy Service
export const mockStrategyService = {
  createStrategy: jest.fn(),
  getBasketStrategies: jest.fn(),
  getStrategy: jest.fn(),
  updateStrategy: jest.fn(),
  deleteStrategy: jest.fn(),
  getStrategyStatus: jest.fn(),
  startStrategy: jest.fn(),
  pauseStrategy: jest.fn(),
  stopStrategy: jest.fn(),
  getStrategyAnalytics: jest.fn(),
  cloneStrategy: jest.fn(),
  getStrategyHistory: jest.fn(),
  validateStrategyData: jest.fn(),
  getStrategyTemplates: jest.fn(),
};

// Mock Auth Service
export const mockAuthService = {
  login: jest.fn(),
  register: jest.fn(),
  logout: jest.fn(),
  refreshToken: jest.fn(),
  forgotPassword: jest.fn(),
  resetPassword: jest.fn(),
  verifyEmail: jest.fn(),
  resendVerification: jest.fn(),
};

// Mock Broker Service
export const mockBrokerService = {
  getBrokers: jest.fn(),
  addBroker: jest.fn(),
  updateBroker: jest.fn(),
  deleteBroker: jest.fn(),
  testConnection: jest.fn(),
  syncPositions: jest.fn(),
};

// Common API Response Builders
export const buildSuccessResponse = <T>(data: T) => ({
  success: true,
  data,
  message: 'Success',
});

export const buildErrorResponse = (message: string, code = 400) => ({
  success: false,
  data: null,
  message,
  code,
});

// Mock API Responses for Strategy Creation
export const mockStrategyResponses = {
  createSuccess: buildSuccessResponse({
    strategyId: 'strategy-123',
    name: 'Test Strategy',
    status: 'CREATED',
  }),
  
  createValidationError: buildErrorResponse(
    'Validation failed: Strategy name is required'
  ),
  
  getStrategiesSuccess: buildSuccessResponse([
    {
      id: 'strategy-1',
      name: 'Iron Condor Strategy',
      status: 'ACTIVE',
      legs: 4,
      createdAt: '2025-01-01T09:00:00Z',
    },
    {
      id: 'strategy-2', 
      name: 'Long Straddle Strategy',
      status: 'PAUSED',
      legs: 2,
      createdAt: '2025-01-02T09:00:00Z',
    },
  ]),
  
  getStrategySuccess: buildSuccessResponse({
    id: 'strategy-123',
    name: 'Test Strategy',
    underlying: 'NIFTY',
    legs: [
      {
        option_type: 'CALL',
        action: 'BUY',
        strike: 5,
        lots: 1,
        selection_method: 'ATM_PERCENT',
      },
    ],
  }),
};

// Mock Basket Responses
export const mockBasketResponses = {
  getBasketsSuccess: buildSuccessResponse([
    {
      id: 'basket-1',
      name: 'Conservative Basket',
      strategiesCount: 3,
      status: 'ACTIVE',
    },
    {
      id: 'basket-2',
      name: 'Aggressive Basket', 
      strategiesCount: 5,
      status: 'PAUSED',
    },
  ]),
};

// Mock Authentication Responses
export const mockAuthResponses = {
  loginSuccess: buildSuccessResponse({
    user: {
      id: 'user-123',
      email: 'test@example.com',
      name: 'Test User',
    },
    token: 'jwt-token-123',
    refreshToken: 'refresh-token-123',
  }),
  
  loginError: buildErrorResponse('Invalid credentials'),
  
  registerSuccess: buildSuccessResponse({
    message: 'Registration successful. Please verify your email.',
  }),
  
  registerError: buildErrorResponse('Email already exists'),
};

// Setup default mock implementations
export const setupDefaultMocks = () => {
  // Strategy Service Defaults
  mockStrategyService.createStrategy.mockResolvedValue(
    mockStrategyResponses.createSuccess
  );
  
  mockStrategyService.getBasketStrategies.mockResolvedValue(
    mockStrategyResponses.getStrategiesSuccess.data
  );
  
  mockStrategyService.validateStrategyData.mockReturnValue({
    isValid: true,
    errors: [],
  });
  
  // Auth Service Defaults
  mockAuthService.login.mockResolvedValue(mockAuthResponses.loginSuccess);
  mockAuthService.register.mockResolvedValue(mockAuthResponses.registerSuccess);
  
  // API Client Defaults
  mockApiClient.post.mockResolvedValue(mockStrategyResponses.createSuccess);
  mockApiClient.get.mockResolvedValue(mockStrategyResponses.getStrategiesSuccess);
  mockApiClient.put.mockResolvedValue(buildSuccessResponse({}));
  mockApiClient.delete.mockResolvedValue(buildSuccessResponse({}));
};

// Reset all mocks (call this in beforeEach)
export const resetAllMocks = () => {
  Object.values(mockStrategyService).forEach(mock => mock.mockReset());
  Object.values(mockAuthService).forEach(mock => mock.mockReset());
  Object.values(mockBrokerService).forEach(mock => mock.mockReset());
  Object.values(mockApiClient).forEach(mock => mock.mockReset());
};