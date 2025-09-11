/**
 * Test Setup Configuration
 * 
 * Global test configuration and setup for Jest
 * Following industry standards for React/TypeScript testing
 */

import '@testing-library/jest-dom';

declare global {
  namespace NodeJS {
    interface Global {
      console: Console;
    }
  }
}

// Global test configuration
global.console = {
  ...console,
  // Suppress console.log in tests unless needed for debugging
  log: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
};

// Mock environment variables for tests
process.env.REACT_APP_DEBUG = 'false';
process.env.REACT_APP_API_URL_DEV = 'https://test-api.example.com/dev';
process.env.REACT_APP_OPTIONS_API_URL_DEV = 'https://test-options-api.example.com/dev';

// Mock IntersectionObserver for component tests
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  disconnect: jest.fn(),
  unobserve: jest.fn(),
}));

// Mock ResizeObserver for component tests
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  disconnect: jest.fn(),
  unobserve: jest.fn(),
}));

// Mock matchMedia for responsive tests
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock scrollTo for component tests
window.scrollTo = jest.fn();

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
});

// Custom matchers for better testing experience
expect.extend({
  toHaveBeenCalledWithObject(received, expected) {
    const pass = received.mock.calls.some(call => 
      call.some(arg => 
        typeof arg === 'object' && 
        Object.keys(expected).every(key => arg[key] === expected[key])
      )
    );
    
    return {
      message: () => 
        `expected ${received} to have been called with object ${JSON.stringify(expected)}`,
      pass,
    };
  },
});