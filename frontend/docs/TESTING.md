# Testing Strategy & Documentation

## 🧪 **Industry-Standard Testing Framework**

This document outlines the comprehensive testing strategy for the Quantleap Options Trading Platform frontend, following enterprise-grade testing practices used by top financial institutions.

## 📋 **Table of Contents**

1. [Testing Philosophy](#testing-philosophy)
2. [Test Architecture](#test-architecture)
3. [Test Suite Organization](#test-suite-organization)
4. [Running Tests](#running-tests)
5. [Writing Tests](#writing-tests)
6. [CI/CD Integration](#cicd-integration)
7. [Coverage Requirements](#coverage-requirements)
8. [Best Practices](#best-practices)

## 🎯 **Testing Philosophy**

### **Test Pyramid**
```
         /\
        /  \  E2E Tests (Few)
       /____\
      /      \  Integration Tests (Some)
     /________\
    /          \ Unit Tests (Many)
   /____________\
```

### **Coverage Standards**
- **Unit Tests**: >95% for critical business logic (strike parsers, transformations)
- **Service Tests**: >85% for API integrations and data transformations
- **Component Tests**: >80% for UI components and user interactions
- **Integration Tests**: Key user workflows and data flow

## 🏗️ **Test Architecture**

### **Directory Structure**
```
src/
├── test/
│   ├── setup.ts                 # Global test configuration
│   ├── utils/
│   │   └── test-utils.tsx       # Testing utilities & helpers
│   ├── __mocks__/
│   │   └── api.ts              # API service mocks
│   └── suites/
│       ├── utils/              # Utility function tests
│       ├── services/           # Service layer tests
│       ├── components/         # Component tests
│       └── integration/        # Integration tests
├── components/
│   └── ui/__tests__/           # Component-specific tests
└── utils/
    └── strategy/
        └── *.test.ts          # Co-located utility tests
```

## 📊 **Test Suite Organization**

### **1. Utility Tests** (`src/test/suites/utils/`)
**Purpose**: Test pure functions and helper utilities
**Coverage**: >95% (Critical business logic)

```typescript
// Example: Strike value parsing
describe("Strike Value Parser", () => {
  test("ATM+5% transforms to 5", () => {
    expect(parseStrikeValue("ATM+5%", "ATM_PERCENT")).toBe(5);
  });
});
```

### **2. Service Tests** (`src/test/suites/services/`)
**Purpose**: Test API integrations and data transformations
**Coverage**: >85%

```typescript
// Example: Strategy transformation service
describe("Strategy Transformation Service", () => {
  test("transforms frontend data to backend format", () => {
    const result = strategyTransformationService.transformToBackend(mockData);
    expect(result.legs[0].strike).toBe(5);
  });
});
```

### **3. Component Tests** (`src/test/suites/components/`)
**Purpose**: Test React components and user interactions
**Coverage**: >80%

```typescript
// Example: Strategy wizard component
describe("StrategyWizardDialog", () => {
  test("creates strategy with valid data", async () => {
    renderWithRouter(<StrategyWizardDialog />);
    await fillForm({ strategyName: "Test Strategy" });
    await clickButton("Create Strategy");
    expectToastMessage("Strategy created successfully");
  });
});
```

### **4. Integration Tests** (`src/test/suites/integration/`)
**Purpose**: Test complete user workflows and data flow
**Coverage**: Key user journeys

```typescript
// Example: End-to-end strategy creation
describe("Strategy Creation Workflow", () => {
  test("complete workflow from creation to validation", async () => {
    // Test complete user journey
  });
});
```

## 🚀 **Running Tests**

### **Quick Commands**
```bash
# Run all tests
npm run test:all

# Run specific test suites
npm run test:utils          # Utility functions only
npm run test:services       # Service layer only
npm run test:components     # React components only
npm run test:integration    # Integration tests only

# Development workflows
npm run test:watch          # Watch mode for development
npm run test:coverage       # Generate coverage report
npm run test:verbose        # Detailed test output
npm run test:ci             # CI/CD optimized (coverage + verbose)

# Maintenance
npm run test:update         # Update snapshots
```

### **Advanced Usage**
```bash
# Custom test runner with options
node scripts/test-runner.js utils --coverage --verbose
node scripts/test-runner.js services --watch
```

### **Test Filtering**
```bash
# Run specific test files
npm test -- --testPathPattern=strikeValueParser
npm test -- --testNamePattern="ATM Points"
```

## ✍️ **Writing Tests**

### **Test Structure Template**
```typescript
/**
 * [Component/Service] Test Suite
 * 
 * Brief description of what this test suite covers
 */

import { screen, waitFor } from '@testing-library/react';
import { renderWithRouter, mockApiResponse } from '../../utils/test-utils';
import { resetAllMocks, setupDefaultMocks } from '../../__mocks__/api';
import ComponentUnderTest from '../../../components/ComponentUnderTest';

describe('ComponentUnderTest', () => {
  beforeEach(() => {
    resetAllMocks();
    setupDefaultMocks();
  });

  describe('Core Functionality', () => {
    test('renders correctly with default props', () => {
      renderWithRouter(<ComponentUnderTest />);
      expect(screen.getByText('Expected Text')).toBeInTheDocument();
    });
    
    test('handles user interactions', async () => {
      renderWithRouter(<ComponentUnderTest />);
      // Test implementation
    });
  });

  describe('Error Handling', () => {
    test('displays error message on API failure', () => {
      // Test error scenarios
    });
  });

  describe('Edge Cases', () => {
    test('handles empty data gracefully', () => {
      // Test edge cases
    });
  });
});
```

### **Testing Utilities**

#### **Custom Render Functions**
```typescript
import { renderWithRouter, renderWithAuth } from '@test/utils/test-utils';

// For components that use routing
renderWithRouter(<Component />);

// For components that need authentication
renderWithAuth(<Component />, mockAuthContext);
```

#### **Common Testing Patterns**
```typescript
// Wait for async operations
await waitForLoadingToFinish();

// Test form interactions
await fillForm({ email: 'test@example.com', password: 'password' });
await selectOption('Index', 'NIFTY');
await clickButton('Submit');

// Test toast notifications
await expectToastMessage('Success message');

// Mock API responses
mockApiClient.post.mockResolvedValue(mockApiResponse(successData));
```

## 🔄 **CI/CD Integration**

### **GitHub Actions Workflow**
Our CI/CD pipeline (`/.github/workflows/test.yml`) includes:

1. **Multi-Node Testing** (Node 18.x, 20.x)
2. **Progressive Test Execution**:
   - Linting & Type Checking
   - Unit Tests (utils)
   - Service Tests
   - Component Tests  
   - Integration Tests
   - Complete Coverage Report
3. **Build Verification**
4. **Security Audit**
5. **Deployment Readiness Check**

### **Coverage Reporting**
- **Codecov Integration**: Automatic coverage uploads
- **HTML Reports**: Detailed coverage visualization
- **Threshold Enforcement**: Pipeline fails if coverage drops below standards

## 📊 **Coverage Requirements**

### **Global Thresholds**
- **Branches**: 80%
- **Functions**: 80%
- **Lines**: 80%
- **Statements**: 80%

### **Critical Module Thresholds**
- **`src/utils/strategy/`**: 95% (Business-critical logic)
- **`src/services/`**: 85% (API integrations)

### **Coverage Reports**
```bash
# Generate coverage report
npm run test:coverage

# View HTML report
open coverage/lcov-report/index.html
```

## 🏆 **Best Practices**

### **1. Test Naming Convention**
```typescript
// ✅ Good: Descriptive and specific
test('transforms ATM+5% to numeric value 5 for backend API')

// ❌ Bad: Vague and unclear  
test('parsing works')
```

### **2. Test Organization**
```typescript
// ✅ Good: Grouped by functionality
describe('Strike Value Parser', () => {
  describe('ATM Points Method', () => {
    test('handles OTM values correctly')
    test('handles ITM values correctly') 
    test('handles ATM value correctly')
  });
  
  describe('ATM Percent Method', () => {
    // Related tests
  });
});
```

### **3. Mock Strategy**
```typescript
// ✅ Good: Mock external dependencies, test your code
jest.mock('../../../services/api', () => mockApiClient);

// ✅ Good: Reset mocks between tests
beforeEach(() => {
  resetAllMocks();
});
```

### **4. Test Data Management**
```typescript
// ✅ Good: Use factory functions for test data
const createMockStrategy = (overrides = {}) => ({
  ...defaultStrategyData,
  ...overrides,
});
```

### **5. Async Testing**
```typescript
// ✅ Good: Proper async/await usage
test('creates strategy successfully', async () => {
  await user.click(submitButton);
  await waitFor(() => {
    expect(screen.getByText('Success')).toBeInTheDocument();
  });
});
```

## 🎯 **Testing Standards Comparison**

| Feature | Our Implementation | Industry Standard | Status |
|---------|------------------|------------------|--------|
| **Test Coverage** | >80% global, >95% critical | >75% typical | ✅ Exceeds |
| **Test Organization** | Suite-based structure | Feature-based | ✅ Matches |
| **CI/CD Integration** | Multi-stage pipeline | Automated testing | ✅ Matches |
| **Mock Strategy** | Service-level mocks | API mocking | ✅ Matches |
| **Coverage Reporting** | HTML + LCOV + Codecov | Standard reporters | ✅ Matches |

## 📝 **Writing Your First Test**

1. **Identify the component/function to test**
2. **Determine the test type** (unit/service/component/integration)
3. **Place in appropriate suite directory**
4. **Use the test template above**
5. **Follow the testing patterns**
6. **Run and verify coverage**

## 🚨 **Common Pitfalls to Avoid**

- ❌ Testing implementation details instead of behavior
- ❌ Not testing error conditions and edge cases
- ❌ Creating tests that depend on other tests
- ❌ Not cleaning up mocks between tests
- ❌ Testing external libraries instead of your code
- ❌ Ignoring accessibility in component tests

## 📈 **Monitoring Test Health**

### **Coverage Trends**
Monitor coverage trends over time to ensure quality doesn't regress.

### **Test Performance**
Track test execution time and optimize slow tests.

### **Flaky Tests**
Identify and fix non-deterministic test failures.

---

This testing framework ensures our options trading platform maintains the highest quality standards expected in financial technology, with comprehensive coverage and enterprise-grade testing practices.