/**
 * Product Type Validation Utilities
 * 
 * Business rules:
 * - MIS (Margin Intraday Square-off) is only allowed when:
 *   - tradingType is "INTRADAY" 
 *   - intradayExitMode is "SAME_DAY"
 * - When tradingType is "INTRADAY" and intradayExitMode is "SAME_DAY": 
 *   - User can select either MIS or NRML (both allowed)
 * - In all other cases, it must be NRML (Normal/Carry Forward)
 */

import { TradingType, IntradayExitMode, ProductType } from '../../types/strategy';

/**
 * Validates if MIS product type is allowed based on trading configuration
 */
export const isMISAllowed = (
  tradingType: TradingType,
  intradayExitMode: IntradayExitMode
): boolean => {
  return tradingType === 'INTRADAY' && intradayExitMode === 'SAME_DAY';
};

/**
 * Gets the default product type based on trading configuration
 * Always returns 'NRML' as the default (user can choose MIS when allowed)
 */
export const getDefaultProductType = (
  tradingType: TradingType,
  intradayExitMode: IntradayExitMode
): ProductType => {
  return 'NRML';
};

/**
 * Validates if a product type is valid for the given trading configuration
 */
export const isValidProductType = (
  productType: ProductType,
  tradingType: TradingType,
  intradayExitMode: IntradayExitMode
): boolean => {
  if (productType === 'MIS') {
    return isMISAllowed(tradingType, intradayExitMode);
  }
  // NRML is always allowed
  return true;
};

/**
 * Gets validation error message if product type is invalid
 */
export const getProductTypeValidationError = (
  productType: ProductType,
  tradingType: TradingType,
  intradayExitMode: IntradayExitMode
): string | null => {
  if (!isValidProductType(productType, tradingType, intradayExitMode)) {
    if (productType === 'MIS') {
      return 'MIS product type is only allowed for INTRADAY trading with SAME_DAY exit mode.';
    }
  }
  return null;
};

/**
 * Auto-corrects product type based on trading configuration
 * Only forces change when MIS is selected but not allowed
 * Returns the corrected product type and whether it was changed
 */
export const autoCorrectProductType = (
  currentProductType: ProductType,
  tradingType: TradingType,
  intradayExitMode: IntradayExitMode
): { productType: ProductType; wasChanged: boolean } => {
  // Only auto-correct if MIS is selected but not allowed
  if (currentProductType === 'MIS' && !isMISAllowed(tradingType, intradayExitMode)) {
    return {
      productType: 'NRML',
      wasChanged: true
    };
  }
  
  // For all other cases, keep the current selection
  return {
    productType: currentProductType,
    wasChanged: false
  };
};