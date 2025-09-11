/**
 * Strike Value Parser Test
 *
 * Tests complete bidirectional transformation between frontend and backend strike values
 */

import {
  parseStrikeValue,
  formatStrikeForDisplay,
  parseATMPointStrike,
  parseATMPercentStrike,
  validateStrikeFormat,
} from "../../../utils/strategy/strikeValueParser";

describe("Strike Value Parser - Bidirectional Transformation", () => {
  // ATM Points Bidirectional Tests
  describe("ATM Points Method", () => {
    const testCases = [
      { display: "ATM", numeric: 0, method: "ATM_POINTS" },
      { display: "ATM", numeric: 0, method: "ATM_POINTS" },
      { display: "OTM3", numeric: 3, method: "ATM_POINTS" },
      { display: "OTM3", numeric: 3, method: "ATM_POINTS" },
      { display: "ITM5", numeric: -5, method: "ATM_POINTS" },
      { display: "ITM5", numeric: -5, method: "ATM_POINTS" },
      { display: "OTM20", numeric: 20, method: "ATM_POINTS" },
      { display: "ITM20", numeric: -20, method: "ATM_POINTS" },
    ];

    testCases.forEach(({ display, numeric, method }) => {
      test(`${method}: "${display}" ⟷ ${numeric} (bidirectional)`, () => {
        // Frontend → Backend transformation
        const parsedValue = parseStrikeValue(display, method as any);
        expect(parsedValue).toBe(numeric);

        // Backend → Frontend transformation
        const displayValue = formatStrikeForDisplay(numeric, method as any);
        expect(displayValue).toBe(display);

        // Validate format
        expect(validateStrikeFormat(display, method as any)).toBe(true);
      });
    });
  });

  // ATM Percent Bidirectional Tests
  describe("ATM Percent Method", () => {
    const testCases = [
      { display: "ATM", numeric: 0 },
      { display: "ATM+5.00%", numeric: 5.0 },
      { display: "ATM+10.25%", numeric: 10.25 },
      { display: "ATM-2.50%", numeric: -2.5 },
      { display: "ATM-7.75%", numeric: -7.75 },
    ];

    testCases.forEach(({ display, numeric }) => {
      test(`ATM_PERCENT: "${display}" ⟷ ${numeric} (bidirectional)`, () => {
        // Frontend → Backend transformation
        const parsedValue = parseStrikeValue(display, "ATM_PERCENT");
        expect(parsedValue).toBe(numeric);

        // Backend → Frontend transformation
        const displayValue = formatStrikeForDisplay(numeric, "ATM_PERCENT");
        expect(displayValue).toBe(display);

        // Validate format
        expect(validateStrikeFormat(display, "ATM_PERCENT")).toBe(true);
      });
    });
  });

  // Edge Cases and Dynamic Methods
  describe("Special Methods", () => {
    test("CLOSEST_PREMIUM: Dynamic value", () => {
      const result = parseStrikeValue("100", "CLOSEST_PREMIUM");
      expect(result).toBe("DYNAMIC");

      const display = formatStrikeForDisplay("DYNAMIC", "CLOSEST_PREMIUM");
      expect(display).toBe("DYNAMIC");
    });

    test("CLOSEST_STRADDLE_PREMIUM: Dynamic value", () => {
      const result = parseStrikeValue("25", "CLOSEST_STRADDLE_PREMIUM");
      expect(result).toBe("DYNAMIC");

      const display = formatStrikeForDisplay(
        "DYNAMIC",
        "CLOSEST_STRADDLE_PREMIUM"
      );
      expect(display).toBe("DYNAMIC");
    });
  });

  // Real-world scenario: User creates strategy with ATM+5%, backend stores 5, UI loads and displays ATM+5%
  describe("Complete User Scenario", () => {
    test("User workflow: ATM+5% → 5 → ATM+5.00%", () => {
      const userInput = "ATM+5%";
      const selectionMethod = "ATM_PERCENT";

      // Step 1: User enters "ATM+5%" in UI
      console.log("Step 1: User input:", userInput);

      // Step 2: Frontend transforms for backend API
      const backendValue = parseStrikeValue(userInput, selectionMethod);
      console.log("Step 2: Backend receives:", backendValue);
      expect(backendValue).toBe(5);

      // Step 3: Strategy is saved with numeric value 5
      // Step 4: User loads existing strategy, backend returns 5
      console.log("Step 3: Backend returns:", backendValue);

      // Step 5: Frontend displays "ATM+5.00%" in UI
      const displayValue = formatStrikeForDisplay(
        backendValue,
        selectionMethod
      );
      console.log("Step 4: UI displays:", displayValue);
      expect(displayValue).toBe("ATM+5.00%");

      console.log("✅ Complete workflow: User sees consistent UI display");
    });

    test("User workflow: OTM3 → 3 → OTM3", () => {
      const userInput = "OTM3";
      const selectionMethod = "ATM_POINTS";

      // User enters "OTM3" in UI
      const backendValue = parseStrikeValue(userInput, selectionMethod);
      expect(backendValue).toBe(3);

      // Backend returns 3, UI displays "OTM3"
      const displayValue = formatStrikeForDisplay(
        backendValue,
        selectionMethod
      );
      expect(displayValue).toBe("OTM3");

      console.log(
        `✅ ATM Points workflow: ${userInput} → ${backendValue} → ${displayValue}`
      );
    });
  });

  // Individual Parser Function Tests
  describe("Individual Parser Functions", () => {
    test("parseATMPointStrike", () => {
      expect(parseATMPointStrike("ATM")).toBe(0);
      expect(parseATMPointStrike("OTM5")).toBe(5);
      expect(parseATMPointStrike("ITM3")).toBe(-3);
      expect(parseATMPointStrike("invalid")).toBe(0); // fallback
    });

    test("parseATMPercentStrike", () => {
      expect(parseATMPercentStrike("ATM")).toBe(0);
      expect(parseATMPercentStrike("ATM+2.50%")).toBe(2.5);
      expect(parseATMPercentStrike("ATM-1.25%")).toBe(-1.25);
      expect(parseATMPercentStrike("invalid")).toBe(0); // fallback
    });
  });

  // Validation Tests
  describe("Format Validation", () => {
    test("ATM_POINTS validation", () => {
      expect(validateStrikeFormat("ATM", "ATM_POINTS")).toBe(true);
      expect(validateStrikeFormat("OTM5", "ATM_POINTS")).toBe(true);
      expect(validateStrikeFormat("ITM10", "ATM_POINTS")).toBe(true);
      expect(validateStrikeFormat("ATM+5%", "ATM_POINTS")).toBe(false);
      expect(validateStrikeFormat("invalid", "ATM_POINTS")).toBe(false);
    });

    test("ATM_PERCENT validation", () => {
      expect(validateStrikeFormat("ATM", "ATM_PERCENT")).toBe(true);
      expect(validateStrikeFormat("ATM+5.00%", "ATM_PERCENT")).toBe(true);
      expect(validateStrikeFormat("ATM-2.50%", "ATM_PERCENT")).toBe(true);
      expect(validateStrikeFormat("OTM3", "ATM_PERCENT")).toBe(false);
      expect(validateStrikeFormat("invalid", "ATM_PERCENT")).toBe(false);
    });
  });
});
