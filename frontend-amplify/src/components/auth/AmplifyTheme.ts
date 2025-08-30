import type { Theme } from '@aws-amplify/ui-react';

export const amplifyTheme: Theme = {
  name: 'quantleap-theme',
  tokens: {
    colors: {
      font: {
        primary: { value: '#111827' },
        secondary: { value: '#6b7280' },
        tertiary: { value: '#9ca3af' },
      },
      brand: {
        primary: {
          10: { value: '#eff6ff' },
          20: { value: '#dbeafe' },
          40: { value: '#93c5fd' },
          60: { value: '#3b82f6' },
          80: { value: '#1d4ed8' },
          90: { value: '#1e40af' },
          100: { value: '#1e3a8a' },
        },
      },
      background: {
        primary: { value: '#ffffff' },
        secondary: { value: '#f9fafb' },
      },
      border: {
        primary: { value: '#d1d5db' },
        focus: { value: '#3b82f6' },
      },
    },
    fonts: {
      default: {
        variable: { value: 'Inter, system-ui, sans-serif' },
      },
    },
    radii: {
      small: { value: '0.375rem' },
      medium: { value: '0.5rem' },
    },
    space: {
      xs: { value: '0.25rem' },
      small: { value: '0.5rem' },
      medium: { value: '1rem' },
      large: { value: '1.5rem' },
      xl: { value: '2rem' },
    },
  },
};