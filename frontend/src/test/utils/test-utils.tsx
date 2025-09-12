/**
 * Test Utilities
 * 
 * Custom render functions and utilities for testing React components
 * Following React Testing Library best practices
 */

import React, { ReactElement } from 'react';
import { render, RenderOptions, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';

// Custom render function with providers
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  initialEntries?: string[];
}

export const renderWithRouter = (
  ui: ReactElement,
  options?: CustomRenderOptions
) => {
  const { initialEntries = ['/'], ...renderOptions } = options || {};

  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <BrowserRouter>
      {children}
    </BrowserRouter>
  );

  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

// Mock Authentication Context Provider for tests
export const mockAuthContext = {
  isAuthenticated: true,
  user: {
    id: 'test-user-id',
    email: 'test@example.com',
    name: 'Test User',
  },
  login: () => Promise.resolve(),
  logout: () => Promise.resolve(),
  loading: false,
};

export const renderWithAuth = (
  ui: ReactElement,
  authContext = mockAuthContext,
  options?: CustomRenderOptions
) => {
  const AuthWrapper = ({ children }: { children: React.ReactNode }) => (
    <BrowserRouter>
      {/* Mock AuthContext.Provider */}
      {children}
    </BrowserRouter>
  );

  return render(ui, { wrapper: AuthWrapper, ...options });
};

// Utility functions for common testing patterns
export const waitForLoadingToFinish = () => 
  waitFor(() => {
    return !screen.queryByText(/loading/i);
  });

export const expectToastMessage = async (message: string | RegExp) => {
  await waitFor(() => {
    return screen.getByText(message);
  });
};

export const fillForm = async (formData: Record<string, string>) => {
  const user = userEvent.setup();
  
  for (const [field, value] of Object.entries(formData)) {
    const input = screen.getByLabelText(new RegExp(field, 'i'));
    await user.clear(input);
    await user.type(input, value);
  }
};

export const selectOption = async (labelText: string | RegExp, optionText: string) => {
  const user = userEvent.setup();
  const select = screen.getByLabelText(labelText);
  await user.selectOptions(select, optionText);
};

export const clickButton = async (buttonText: string | RegExp) => {
  const user = userEvent.setup();
  const button = screen.getByRole('button', { name: buttonText });
  await user.click(button);
};

// Mock API responses for testing
export const mockApiResponse = function<T>(data: T, success = true) {
  return {
    success,
    data,
    message: success ? 'Success' : 'Error',
  };
};

export const mockStrategyData = {
  basketId: 'test-basket-id',
  strategyName: 'Test Strategy',
  index: 'NIFTY',
  config: {
    entryTimeHour: '09',
    entryTimeMinute: '15',
    exitTimeHour: '15',
    exitTimeMinute: '30',
    rangeBreakout: false,
    rangeBreakoutTimeHour: '09',
    rangeBreakoutTimeMinute: '30',
    moveSlToCost: false,
    productType: 'NRML' as const,
    tradingType: 'INTRADAY' as const,
    intradayExitMode: 'SAME_DAY' as const,
    entryTradingDaysBeforeExpiry: 4,
    exitTradingDaysBeforeExpiry: 0,
    targetProfit: { type: 'TOTAL_MTM' as const, value: 0 },
    mtmStopLoss: { type: 'TOTAL_MTM' as const, value: 0 },
  },
  legs: [
    {
      id: 'leg-1',
      index: 'NIFTY',
      optionType: 'CE' as const,
      actionType: 'BUY' as const,
      strikePrice: 'ATM',
      totalLots: 1,
      expiryType: 'weekly' as const,
      selectionMethod: 'ATM_POINTS' as const,
      premiumOperator: 'CLOSEST' as const,
      premiumValue: 0,
      straddlePremiumOperator: 'CLOSEST' as const,
      straddlePremiumPercentage: 5,
      stopLoss: { enabled: false, type: 'PERCENTAGE' as const, value: 0 },
      targetProfit: { enabled: false, type: 'PERCENTAGE' as const, value: 0 },
      trailingStopLoss: { enabled: false, type: 'POINTS' as const, instrumentMoveValue: 0, stopLossMoveValue: 0 },
      waitAndTrade: { enabled: false, type: 'PERCENTAGE' as const, value: 0 },
      reEntry: { enabled: false, type: 'SL_REENTRY' as const, count: 1 },
      reExecute: { enabled: false, type: 'TP_REEXEC' as const, count: 1 },
    },
  ],
};

// Re-export everything from @testing-library/react
export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';