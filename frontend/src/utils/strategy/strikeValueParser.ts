/**
 * Strike Value Parser
 *
 * Utilities for parsing display strike values into backend-compatible numeric values.
 * Extracts numeric values from UI display strings while preserving display formatting.
 */

import { SelectionMethod } from "../../types/strategy";

/**
 * Parse ATM Points strike values
 * Examples: "OTM3" → 3, "ITM5" → -5, "ATM" → 0
 */
export const parseATMPointStrike = (value: string): number => {
  // Handle ATM case
  if (value === "ATM") {
    return 0;
  }

  // Parse OTM values (positive)
  const otmMatch = value.match(/^OTM(\d+)$/);
  if (otmMatch) {
    return parseInt(otmMatch[1], 10);
  }

  // Parse ITM values (negative)
  const itmMatch = value.match(/^ITM(\d+)$/);
  if (itmMatch) {
    return -parseInt(itmMatch[1], 10);
  }

  // Fallback: try to parse as number
  const numericValue = parseFloat(value);
  return isNaN(numericValue) ? 0 : numericValue;
};

/**
 * Parse ATM Percent strike values
 * Examples: "ATM+5.00%" → 5.00, "ATM-2.50%" → -2.50, "ATM" → 0
 */
export const parseATMPercentStrike = (value: string): number => {
  // Handle ATM case
  if (value === "ATM") {
    return 0;
  }

  // Parse positive percentage: "ATM+5.00%"
  const positiveMatch = value.match(/^ATM\+([0-9]+\.?[0-9]*)%$/);
  if (positiveMatch) {
    return parseFloat(positiveMatch[1]);
  }

  // Parse negative percentage: "ATM-2.50%"
  const negativeMatch = value.match(/^ATM(-[0-9]+\.?[0-9]*)%$/);
  if (negativeMatch) {
    return parseFloat(negativeMatch[1]);
  }

  // Fallback: try to parse as number
  const numericValue = parseFloat(value);
  return isNaN(numericValue) ? 0 : numericValue;
};

/**
 * Main strike value parser
 * Routes to appropriate parser based on selection method
 */
export const parseStrikeValue = (
  value: string,
  method: SelectionMethod
): number | string => {
  try {
    switch (method) {
      case "ATM_POINTS":
        return parseATMPointStrike(value);

      case "ATM_PERCENT":
        return parseATMPercentStrike(value);

      case "CLOSEST_PREMIUM":
      case "CLOSEST_STRADDLE_PREMIUM":
        // These methods use dynamic strike resolution in backend
        return "DYNAMIC";

      default:
        // For any other methods, try to parse as number or return as string
        const numericValue = parseFloat(value);
        return isNaN(numericValue) ? value : numericValue;
    }
  } catch (error) {
    // Error handling: return original value if parsing fails
    console.warn(
      `Strike value parsing failed for "${value}" with method "${method}":`,
      error
    );
    return value;
  }
};

/**
 * Validate strike value format for given selection method
 * Returns true if value is in expected format
 */
export const validateStrikeFormat = (
  value: string,
  method: SelectionMethod
): boolean => {
  try {
    switch (method) {
      case "ATM_POINTS":
        return value === "ATM" || /^(OTM|ITM)\d+$/.test(value);

      case "ATM_PERCENT":
        return (
          value === "ATM" ||
          /^ATM\+[0-9]+\.?[0-9]*%$/.test(value) ||
          /^ATM-[0-9]+\.?[0-9]*%$/.test(value)
        );

      case "CLOSEST_PREMIUM":
      case "CLOSEST_STRADDLE_PREMIUM":
        // These methods don't use strike value directly
        return true;

      default:
        // For other methods, allow any string
        return true;
    }
  } catch (error) {
    return false;
  }
};

/**
 * REVERSE TRANSFORMATION: Convert backend numeric value to frontend display string
 * Used when loading existing strategies from backend
 */
export const formatStrikeForDisplay = (
  numericValue: number | string,
  method: SelectionMethod
): string => {
  // If it's already a string (like "DYNAMIC"), return as-is
  if (typeof numericValue === "string") {
    return numericValue;
  }

  try {
    switch (method) {
      case "ATM_POINTS":
        if (numericValue === 0) return "ATM";
        if (numericValue > 0) return `OTM${numericValue}`;
        return `ITM${Math.abs(numericValue)}`;

      case "ATM_PERCENT":
        if (numericValue === 0) return "ATM";
        if (numericValue > 0) return `ATM+${numericValue.toFixed(2)}%`;
        return `ATM${numericValue.toFixed(2)}%`; // Negative already has minus sign

      default:
        return numericValue.toString();
    }
  } catch (error) {
    console.warn(
      `Strike display formatting failed for ${numericValue} with method ${method}:`,
      error
    );
    return numericValue.toString();
  }
};

/**
 * Get display label for strike value (for UI consistency)
 * This ensures consistent display formatting
 */
export const getStrikeDisplayLabel = (
  value: string,
  _method: SelectionMethod
): string => {
  // For most cases, return the value as-is since it's already formatted for display
  return value;
};

export default {
  parseStrikeValue,
  parseATMPointStrike,
  parseATMPercentStrike,
  validateStrikeFormat,
  getStrikeDisplayLabel,
};
