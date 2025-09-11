/**
 * Test Suite Index
 * 
 * Centralized exports for all test suites
 * Allows for organized test execution and imports
 */

// Export test suite runners
export * from './utils/strikeValueParser.test';
export * from './services/strategyTransformationService.test';

// Test suite metadata for reporting
export const TEST_SUITES = {
  UTILS: {
    name: 'Utility Functions',
    description: 'Tests for utility functions and helper methods',
    files: [
      'utils/strikeValueParser.test.ts',
    ],
  },
  SERVICES: {
    name: 'Service Layer',
    description: 'Tests for API services and business logic',
    files: [
      'services/strategyTransformationService.test.ts',
    ],
  },
  COMPONENTS: {
    name: 'React Components',
    description: 'Tests for UI components and user interactions',
    files: [
      // Component tests will be added here
    ],
  },
  INTEGRATION: {
    name: 'Integration Tests',
    description: 'End-to-end workflow and integration tests',
    files: [
      // Integration tests will be added here
    ],
  },
} as const;

export type TestSuiteType = keyof typeof TEST_SUITES;