/**
 * Broker OAuth Configuration
 * Contains OAuth-specific settings for all supported brokers
 */

import { BrokerOAuthConfig } from '../types/oauth';

/**
 * Zerodha Kite Connect OAuth Configuration
 */
export const zerodhaConfig: BrokerOAuthConfig = {
  brokerName: 'zerodha',
  displayName: 'Zerodha Kite',
  authFlow: 'popup',
  tokenType: 'session',
  expiryType: 'daily',
  requiresDaily: true,
  popupDimensions: {
    width: 600,
    height: 700
  },
  scopes: [],
  metadata: {
    tokenExpiryTime: '6:00 AM IST',
    refreshable: false,
    multiStep: false
  }
};

/**
 * Angel One OAuth Configuration
 */
export const angelOneConfig: BrokerOAuthConfig = {
  brokerName: 'angel',
  displayName: 'Angel One',
  authFlow: 'popup',
  tokenType: 'bearer',
  expiryType: 'fixed',
  requiresDaily: false,
  popupDimensions: {
    width: 500,
    height: 600
  },
  scopes: ['read', 'trade'],
  metadata: {
    tokenExpiryTime: '24 hours',
    refreshable: true,
    multiStep: false
  }
};

/**
 * Finvasia OAuth Configuration
 */
export const finvasiaConfig: BrokerOAuthConfig = {
  brokerName: 'finvasia',
  displayName: 'Finvasia',
  authFlow: 'redirect',
  tokenType: 'bearer',
  expiryType: 'fixed',
  requiresDaily: false,
  scopes: ['trading'],
  metadata: {
    tokenExpiryTime: '8 hours',
    refreshable: false,
    multiStep: false
  }
};

/**
 * Zebu MYNT OAuth Configuration
 * Tokens are refreshable with ~1 hour validity
 */
export const zebuConfig: BrokerOAuthConfig = {
  brokerName: 'zebu',
  displayName: 'Zebu MYNT',
  authFlow: 'popup',
  tokenType: 'bearer',
  expiryType: 'refresh',
  requiresDaily: false,
  popupDimensions: {
    width: 500,
    height: 650
  },
  scopes: [],
  metadata: {
    tokenExpiryTime: '1 hour',
    refreshable: true,
    multiStep: false
  }
};

/**
 * Upstox OAuth Configuration (Future Implementation)
 */
export const upstoxConfig: BrokerOAuthConfig = {
  brokerName: 'upstox',
  displayName: 'Upstox',
  authFlow: 'popup',
  tokenType: 'refresh',
  expiryType: 'refresh',
  requiresDaily: false,
  popupDimensions: {
    width: 500,
    height: 600
  },
  scopes: ['read', 'orders'],
  metadata: {
    tokenExpiryTime: '24 hours',
    refreshable: true,
    multiStep: true
  }
};

/**
 * All broker configurations mapped by broker name
 */
export const brokerConfigs: Record<string, BrokerOAuthConfig> = {
  zerodha: zerodhaConfig,
  angel: angelOneConfig,
  finvasia: finvasiaConfig,
  zebu: zebuConfig,
  upstox: upstoxConfig
};

/**
 * Get broker configuration by name
 */
export function getBrokerConfig(brokerName: string): BrokerOAuthConfig | null {
  return brokerConfigs[brokerName.toLowerCase()] || null;
}

/**
 * Check if broker supports OAuth
 */
export function supportsOAuth(brokerName: string): boolean {
  const config = getBrokerConfig(brokerName);
  return config !== null;
}

/**
 * Get OAuth-enabled brokers list
 */
export function getOAuthEnabledBrokers(): string[] {
  return Object.keys(brokerConfigs);
}

/**
 * Check if broker requires daily authentication
 */
export function requiresDailyAuth(brokerName: string): boolean {
  const config = getBrokerConfig(brokerName);
  return config?.requiresDaily ?? false;
}

/**
 * Get broker display name
 */
export function getBrokerDisplayName(brokerName: string): string {
  const config = getBrokerConfig(brokerName);
  return config?.displayName ?? brokerName;
}

/**
 * Get popup dimensions for broker
 */
export function getPopupDimensions(brokerName: string): { width: number; height: number } {
  const config = getBrokerConfig(brokerName);
  return config?.popupDimensions ?? { width: 500, height: 600 };
}

/**
 * Validate broker configuration
 */
export function validateBrokerConfig(brokerName: string): boolean {
  const config = getBrokerConfig(brokerName);
  if (!config) return false;

  return !!(
    config.brokerName &&
    config.displayName &&
    config.authFlow &&
    config.tokenType &&
    config.expiryType
  );
}