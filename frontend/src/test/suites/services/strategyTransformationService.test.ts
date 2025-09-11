/**
 * Strategy Transformation Service Test Suite
 * 
 * Tests the bidirectional transformation service between frontend and backend data formats
 * Critical for ensuring data integrity in the options trading platform
 */

import strategyTransformationService from "../../../services/strategyTransformationService";
import { mockStrategyData } from "../../utils/test-utils";

// Mock the validation service
jest.mock('../../../services/strategyValidationService', () => ({
  validateStrategy: jest.fn().mockResolvedValue({
    isValid: true,
    errors: [],
    warnings: []
  })
}));

describe("Strategy Transformation Service", () => {
  describe("Frontend to Backend Transformation", () => {
    test("transforms complete strategy data correctly", () => {
      const backendData = strategyTransformationService.transformToBackend(mockStrategyData);
      
      expect(backendData).toMatchObject({
        name: "Test Strategy",
        underlying: "NIFTY",
        product: "MIS",
        entry_time: "09:15",
        exit_time: "15:30",
      });
      
      expect(backendData.legs).toHaveLength(1);
      expect(backendData.legs[0]).toMatchObject({
        option_type: "CALL",
        action: "BUY",
        strike: 0, // ATM should be transformed to 0
        lots: 1,
        selection_method: "ATM_POINTS",
      });
    });

    test("transforms ATM_PERCENT strikes correctly", () => {
      const testData = {
        ...mockStrategyData,
        legs: [{
          ...mockStrategyData.legs[0],
          strikePrice: "ATM+5.00%",
          selectionMethod: "ATM_PERCENT" as const,
        }]
      };
      
      const backendData = strategyTransformationService.transformToBackend(testData);
      
      expect(backendData.legs[0].strike).toBe(5);
      expect(backendData.legs[0].selection_method).toBe("ATM_PERCENT");
    });

    test("transforms ATM_POINTS strikes correctly", () => {
      const testData = {
        ...mockStrategyData,
        legs: [{
          ...mockStrategyData.legs[0],
          strikePrice: "OTM3",
          selectionMethod: "ATM_POINTS" as const,
        }]
      };
      
      const backendData = strategyTransformationService.transformToBackend(testData);
      
      expect(backendData.legs[0].strike).toBe(3);
      expect(backendData.legs[0].selection_method).toBe("ATM_POINTS");
    });

    test("handles CLOSEST_PREMIUM method", () => {
      const testData = {
        ...mockStrategyData,
        legs: [{
          ...mockStrategyData.legs[0],
          selectionMethod: "CLOSEST_PREMIUM" as const,
          premiumOperator: "CP_GREATER_EQUAL" as const,
          premiumValue: 100,
        }]
      };
      
      const backendData = strategyTransformationService.transformToBackend(testData);
      
      expect(backendData.legs[0].strike).toBe("DYNAMIC");
      expect(backendData.legs[0].premium_criteria).toEqual({
        operator: "CP_GREATER_EQUAL",
        value: 100,
      });
    });

    test("includes risk management configuration", () => {
      const testData = {
        ...mockStrategyData,
        legs: [{
          ...mockStrategyData.legs[0],
          stopLoss: { enabled: true, type: "POINTS" as const, value: 50 },
          targetProfit: { enabled: true, type: "PERCENTAGE" as const, value: 20 },
        }]
      };
      
      const backendData = strategyTransformationService.transformToBackend(testData);
      
      expect(backendData.legs[0].risk_management).toMatchObject({
        stop_loss: {
          enabled: true,
          type: "POINTS",
          value: 50,
        },
        target_profit: {
          enabled: true,
          type: "PERCENTAGE", 
          value: 20,
        },
      });
    });
  });

  describe("Backend to Frontend Transformation", () => {
    test("transforms backend strategy to frontend format", () => {
      const backendStrategy = {
        name: "Iron Condor Strategy",
        underlying: "BANKNIFTY",
        entry_time: "09:30",
        exit_time: "15:15",
        legs: [
          {
            option_type: "CALL",
            action: "SELL",
            strike: 5,
            lots: 2,
            selection_method: "ATM_PERCENT",
          },
          {
            option_type: "PUT",
            action: "BUY",
            strike: -3,
            lots: 1,
            selection_method: "ATM_POINTS",
          },
        ],
        strategy_config: {
          range_breakout: true,
          range_breakout_time: "09:45",
          move_sl_to_cost: true,
          target_profit: {
            type: "TOTAL_MTM",
            value: 1000,
          },
        },
      };
      
      const frontendData = strategyTransformationService.transformToFrontend(
        backendStrategy,
        "test-basket-id"
      );
      
      expect(frontendData).toMatchObject({
        basketId: "test-basket-id",
        strategyName: "Iron Condor Strategy",
        index: "BANKNIFTY",
      });
      
      expect(frontendData.config).toMatchObject({
        entryTimeHour: "09",
        entryTimeMinute: "30",
        exitTimeHour: "15",
        exitTimeMinute: "15",
        rangeBreakout: true,
        rangeBreakoutTimeHour: "09",
        rangeBreakoutTimeMinute: "45",
      });
      
      expect(frontendData.legs).toHaveLength(2);
      
      // Test strike transformations
      expect(frontendData.legs![0].strikePrice).toBe("ATM+5.00%");
      expect(frontendData.legs![0].optionType).toBe("CE");
      expect(frontendData.legs![0].actionType).toBe("SELL");
      
      expect(frontendData.legs![1].strikePrice).toBe("ITM3");
      expect(frontendData.legs![1].optionType).toBe("PE");
      expect(frontendData.legs![1].actionType).toBe("BUY");
    });

    test("handles DYNAMIC strikes for premium methods", () => {
      const backendStrategy = {
        name: "Premium Strategy",
        underlying: "NIFTY",
        legs: [
          {
            option_type: "CALL",
            action: "BUY", 
            strike: "DYNAMIC",
            selection_method: "CLOSEST_PREMIUM",
            premium_criteria: {
              operator: "CP_EQUAL",
              value: 75,
            },
          },
        ],
      };
      
      const frontendData = strategyTransformationService.transformToFrontend(
        backendStrategy,
        "basket-id"
      );
      
      expect(frontendData.legs![0].strikePrice).toBe("DYNAMIC");
      expect(frontendData.legs![0].premiumOperator).toBe("CP_EQUAL");
      expect(frontendData.legs![0].premiumValue).toBe(75);
    });
  });

  describe("Validation", () => {
    test("validates required fields", () => {
      const invalidData = {
        ...mockStrategyData,
        strategyName: "",
        basketId: "",
      };
      
      const validation = strategyTransformationService.validateFrontendData(invalidData);
      
      expect(validation.isValid).toBe(false);
      expect(validation.errors).toContain("Strategy name is required");
      expect(validation.errors).toContain("Basket ID is required");
    });

    test("validates leg configurations", () => {
      const invalidData = {
        ...mockStrategyData,
        legs: [{
          ...mockStrategyData.legs[0],
          totalLots: 0,
          selectionMethod: "CLOSEST_PREMIUM" as const,
          premiumOperator: undefined,
        }]
      };
      
      const validation = strategyTransformationService.validateFrontendData(invalidData);
      
      expect(validation.isValid).toBe(false);
      expect(validation.errors).toContain("Position 1: Total lots must be greater than 0");
      expect(validation.errors).toContain("Position 1: Premium criteria required for Closest Premium selection");
    });

    test("validates time configuration", () => {
      const invalidData = {
        ...mockStrategyData,
        config: {
          ...mockStrategyData.config,
          entryTimeHour: "16", // After market hours
          exitTimeHour: "08",  // Before entry time
        }
      };
      
      const validation = strategyTransformationService.validateFrontendData(invalidData);
      
      expect(validation.isValid).toBe(false);
      expect(validation.errors.some(e => e.includes("Entry time must be between"))).toBe(true);
    });

    test("validates strike formats", () => {
      const invalidData = {
        ...mockStrategyData,
        legs: [{
          ...mockStrategyData.legs[0],
          strikePrice: "INVALID_FORMAT",
          selectionMethod: "ATM_PERCENT" as const,
        }]
      };
      
      const validation = strategyTransformationService.validateFrontendData(invalidData);
      
      expect(validation.isValid).toBe(false);
      expect(validation.errors.some(e => e.includes("Invalid strike price format"))).toBe(true);
    });
  });

  describe("API Payload Creation", () => {
    test("creates valid API payload", () => {
      const payload = strategyTransformationService.createApiPayload(
        "basket-id",
        mockStrategyData
      );
      
      expect(payload).toBeDefined();
      expect(payload.name).toBe("Test Strategy");
      expect(payload.underlying).toBe("NIFTY");
    });

    test("throws on invalid data", () => {
      const invalidData = {
        ...mockStrategyData,
        strategyName: "",
      };
      
      expect(() => {
        strategyTransformationService.createApiPayload("basket-id", invalidData);
      }).toThrow("Validation failed");
    });
  });

  describe("Edge Cases", () => {
    test("handles empty legs array", () => {
      const backendStrategy = {
        name: "Empty Strategy",
        underlying: "NIFTY",
        legs: [],
      };
      
      const frontendData = strategyTransformationService.transformToFrontend(
        backendStrategy,
        "basket-id"
      );
      
      expect(frontendData.legs).toEqual([]);
    });

    test("handles missing optional fields", () => {
      const minimalBackend = {
        name: "Minimal Strategy",
      };
      
      const frontendData = strategyTransformationService.transformToFrontend(
        minimalBackend,
        "basket-id"
      );
      
      expect(frontendData.strategyName).toBe("Minimal Strategy");
      expect(frontendData.index).toBe("NIFTY"); // Default value
    });

    test("handles malformed time strings", () => {
      const backendStrategy = {
        name: "Test Strategy",
        entry_time: "invalid",
        exit_time: "also-invalid",
      };
      
      const frontendData = strategyTransformationService.transformToFrontend(
        backendStrategy,
        "basket-id"
      );
      
      // Should use defaults
      expect(frontendData.config!.entryTimeHour).toBe("09");
      expect(frontendData.config!.entryTimeMinute).toBe("15");
    });
  });

  describe('Time Parsing Edge Cases', () => {
    test('handles various invalid time formats gracefully', () => {
      const testCases = [
        {
          name: 'invalid string',
          entry_time: 'invalid',
          exit_time: 'also-invalid',
          expected: { entryHour: '09', entryMinute: '15', exitHour: '15', exitMinute: '30' }
        },
        {
          name: 'empty strings',
          entry_time: '',
          exit_time: '',
          expected: { entryHour: '09', entryMinute: '15', exitHour: '15', exitMinute: '30' }
        },
        {
          name: 'undefined values',
          entry_time: undefined,
          exit_time: undefined,
          expected: { entryHour: '09', entryMinute: '15', exitHour: '15', exitMinute: '30' }
        },
        {
          name: 'invalid hour ranges',
          entry_time: '25:30',
          exit_time: '24:15',
          expected: { entryHour: '09', entryMinute: '15', exitHour: '15', exitMinute: '30' }
        },
        {
          name: 'invalid minute ranges',
          entry_time: '10:70',
          exit_time: '12:60',
          expected: { entryHour: '09', entryMinute: '15', exitHour: '15', exitMinute: '30' }
        },
        {
          name: 'missing colon',
          entry_time: '1030',
          exit_time: '1245',
          expected: { entryHour: '09', entryMinute: '15', exitHour: '15', exitMinute: '30' }
        },
        {
          name: 'multiple colons',
          entry_time: '10:30:45',
          exit_time: '12:45:00',
          expected: { entryHour: '09', entryMinute: '15', exitHour: '15', exitMinute: '30' }
        }
      ];

      testCases.forEach(({ name, entry_time, exit_time, expected }) => {
        const backendStrategy = {
          name: 'Test Strategy',
          entry_time,
          exit_time,
        };
        
        const frontendData = strategyTransformationService.transformToFrontend(
          backendStrategy,
          'basket-id'
        );
        
        expect(frontendData.config!.entryTimeHour).toBe(expected.entryHour);
        expect(frontendData.config!.entryTimeMinute).toBe(expected.entryMinute);
        expect(frontendData.config!.exitTimeHour).toBe(expected.exitHour);
        expect(frontendData.config!.exitTimeMinute).toBe(expected.exitMinute);
      });
    });

    test('handles valid time formats correctly', () => {
      const validTestCases = [
        {
          name: 'standard format',
          entry_time: '09:15',
          exit_time: '15:30',
          expected: { entryHour: '09', entryMinute: '15', exitHour: '15', exitMinute: '30' }
        },
        {
          name: 'single digit hour',
          entry_time: '9:15',
          exit_time: '5:30',
          expected: { entryHour: '09', entryMinute: '15', exitHour: '05', exitMinute: '30' }
        },
        {
          name: 'midnight and noon',
          entry_time: '00:00',
          exit_time: '12:00',
          expected: { entryHour: '00', entryMinute: '00', exitHour: '12', exitMinute: '00' }
        },
        {
          name: 'late hours',
          entry_time: '23:59',
          exit_time: '22:45',
          expected: { entryHour: '23', entryMinute: '59', exitHour: '22', exitMinute: '45' }
        }
      ];

      validTestCases.forEach(({ name, entry_time, exit_time, expected }) => {
        const backendStrategy = {
          name: 'Test Strategy',
          entry_time,
          exit_time,
        };
        
        const frontendData = strategyTransformationService.transformToFrontend(
          backendStrategy,
          'basket-id'
        );
        
        expect(frontendData.config!.entryTimeHour).toBe(expected.entryHour);
        expect(frontendData.config!.entryTimeMinute).toBe(expected.entryMinute);
        expect(frontendData.config!.exitTimeHour).toBe(expected.exitHour);
        expect(frontendData.config!.exitTimeMinute).toBe(expected.exitMinute);
      });
    });

    test('handles range breakout time parsing', () => {
      const backendStrategy = {
        name: 'Test Strategy',
        strategy_config: {
          range_breakout_time: 'invalid-time',
        },
      };
      
      const frontendData = strategyTransformationService.transformToFrontend(
        backendStrategy,
        'basket-id'
      );
      
      // Should use defaults for invalid range breakout time
      expect(frontendData.config!.rangeBreakoutTimeHour).toBe('09');
      expect(frontendData.config!.rangeBreakoutTimeMinute).toBe('30');
    });
  });
});