/**
 * Strike Options Generator
 *
 * Utilities for generating strike price options based on different selection methods.
 * Extracted from StrategyWizardDialog.tsx for better maintainability.
 */

import { SelectOption, SelectionMethod } from "../../types/strategy";

/**
 * Generate default strike price options using ATM Points method
 * Creates ITM20 to OTM20 options with ATM in the center
 */
export const generateStrikeOptions = (): SelectOption[] => {
  const options: SelectOption[] = [];

  // ITM options (20 below ATM)
  for (let i = 20; i >= 1; i--) {
    options.push({ value: `ITM${i}`, label: `ITM${i}` });
  }

  // ATM option
  options.push({ value: "ATM", label: "ATM" });

  // OTM options (20 above ATM)
  for (let i = 1; i <= 20; i++) {
    options.push({ value: `OTM${i}`, label: `OTM${i}` });
  }

  return options;
};

/**
 * Generate ATM percentage-based options
 * Creates percentage-based options with positive percentages above ATM and negative percentages below ATM
 */
export const generatePercentageOptions = (): SelectOption[] => {
  const options: SelectOption[] = [];

  // Positive percentages (above ATM) - shown first
  for (let i = 10; i >= 0.25; i -= 0.25) {
    const percentage = i.toFixed(2);
    options.push({ value: `ATM+${percentage}%`, label: `ATM+${percentage}%` });
  }

  // ATM (0%) - in the middle
  options.push({ value: "ATM", label: "ATM" });

  // Negative percentages (below ATM) - shown last
  for (let i = -0.25; i >= -10; i -= 0.25) {
    const percentage = i.toFixed(2);
    options.push({ value: `ATM${percentage}%`, label: `ATM${percentage}%` });
  }

  return options;
};

/**
 * Generate straddle premium percentage options
 * Creates percentage options from 5% to 60% in 5% increments
 */
export const generateStraddlePremiumPercentageOptions = (): SelectOption[] => {
  const options: SelectOption[] = [];

  for (let i = 5; i <= 60; i += 5) {
    options.push({ value: i.toString(), label: `${i}%` });
  }

  return options;
};

/**
 * Generate strike options based on selection method for a specific position
 * Main function that routes to appropriate generator based on method
 */
export const generatePositionStrikeOptions = (
  selectionMethod: SelectionMethod
): SelectOption[] => {
  switch (selectionMethod) {
    case "ATM_PERCENT":
      return generatePercentageOptions();
    case "ATM_POINTS":
    default:
      return generateStrikeOptions();
  }
};

/**
 * Check if selection method requires premium criteria
 */
export const requiresPremiumCriteria = (
  selectionMethod: SelectionMethod
): boolean => {
  return selectionMethod === "CLOSEST_PREMIUM";
};

/**
 * Check if selection method requires straddle premium criteria
 */
export const requiresStraddlePremiumCriteria = (
  selectionMethod: SelectionMethod
): boolean => {
  return selectionMethod === "CLOSEST_STRADDLE_PREMIUM";
};

/**
 * Check if selection method uses regular strike price selection
 */
export const usesRegularStrikeSelection = (
  selectionMethod: SelectionMethod
): boolean => {
  return selectionMethod === "ATM_POINTS" || selectionMethod === "ATM_PERCENT";
};
