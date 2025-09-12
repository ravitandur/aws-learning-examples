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
        product: "NRML",
        entry_time: "09:15",
        exit_time: "15:30",
        trading_type: "INTRADAY",
        intraday_exit_mode: "SAME_DAY",
      });
      
      // Verify INTRADAY mode doesn't include positional fields
      expect(backendData.entry_trading_days_before_expiry).toBeUndefined();
      expect(backendData.exit_trading_days_before_expiry).toBeUndefined();
      
      // Verify flattened strategy configuration fields
      expect(backendData.range_breakout).toBe(false);
      expect(backendData.range_breakout_time).toBeUndefined();
      expect(backendData.move_sl_to_cost).toBe(false);
      expect(backendData.target_profit).toBeUndefined(); // Default value is 0
      expect(backendData.mtm_stop_loss).toBeUndefined(); // Default value is 0
      
      // Verify nested strategy_config object no longer exists
      expect(backendData).not.toHaveProperty('strategy_config');
      
      expect(backendData.legs).toHaveLength(1);
      expect(backendData.legs[0]).toMatchObject({
        option_type: "CE",
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

    test("handles PREMIUM method", () => {
      const testData = {
        ...mockStrategyData,
        legs: [{
          ...mockStrategyData.legs[0],
          selectionMethod: "PREMIUM" as const,
          premiumOperator: "GTE" as const,
          premiumValue: 100,
        }]
      };
      
      const backendData = strategyTransformationService.transformToBackend(testData);
      
      expect(backendData.legs[0].strike).toBe("DYNAMIC");
      expect(backendData.legs[0].premium_criteria).toEqual({
        operator: "GTE",
        value: 100,
      });
    });

    test("includes flattened risk management configuration", () => {
      const testData = {
        ...mockStrategyData,
        legs: [{
          ...mockStrategyData.legs[0],
          stopLoss: { enabled: true, type: "PERCENTAGE" as const, value: 50 },
          targetProfit: { enabled: true, type: "PERCENTAGE" as const, value: 20 },
          trailingStopLoss: { enabled: true, type: "POINTS" as const, instrumentMoveValue: 10, stopLossMoveValue: 5 },
          waitAndTrade: { enabled: true, type: "PERCENTAGE" as const, value: 15 },
        }]
      };
      
      const backendData = strategyTransformationService.transformToBackend(testData);
      
      // Verify flattened risk management fields at leg level
      expect(backendData.legs[0].stop_loss).toEqual({
        enabled: true,
        type: "PERCENTAGE",
        value: 50,
      });
      expect(backendData.legs[0].target_profit).toEqual({
        enabled: true,
        type: "PERCENTAGE", 
        value: 20,
      });
      expect(backendData.legs[0].trailing_stop_loss).toEqual({
        enabled: true,
        type: "POINTS",
        instrument_move_value: 10,
        stop_loss_move_value: 5,
      });
      expect(backendData.legs[0].wait_and_trade).toEqual({
        enabled: true,
        type: "PERCENTAGE",
        value: 15,
      });
      
      // Verify nested risk_management object no longer exists
      expect(backendData.legs[0]).not.toHaveProperty('risk_management');
    });

    test("transforms INTRADAY trading type correctly", () => {
      const testData = {
        ...mockStrategyData,
        config: {
          ...mockStrategyData.config,
          tradingType: "INTRADAY" as const,
          intradayExitMode: "NEXT_DAY_BTST" as const,
        }
      };
      
      const backendData = strategyTransformationService.transformToBackend(testData);
      
      expect(backendData.trading_type).toBe("INTRADAY");
      expect(backendData.intraday_exit_mode).toBe("NEXT_DAY_BTST");
      
      // Verify INTRADAY mode doesn't include positional fields
      expect(backendData.entry_trading_days_before_expiry).toBeUndefined();
      expect(backendData.exit_trading_days_before_expiry).toBeUndefined();
    });

    test("transforms POSITIONAL trading type correctly", () => {
      const testData = {
        ...mockStrategyData,
        config: {
          ...mockStrategyData.config,
          tradingType: "POSITIONAL" as const,
          entryTradingDaysBeforeExpiry: 5,
          exitTradingDaysBeforeExpiry: 1,
        }
      };
      
      const backendData = strategyTransformationService.transformToBackend(testData);
      
      expect(backendData.trading_type).toBe("POSITIONAL");
      expect(backendData.entry_trading_days_before_expiry).toBe(5);
      expect(backendData.exit_trading_days_before_expiry).toBe(1);
      
      // Verify POSITIONAL mode doesn't include intraday fields
      expect(backendData.intraday_exit_mode).toBeUndefined();
    });

    test("transforms flattened strategy configuration correctly", () => {
      const testData = {
        ...mockStrategyData,
        config: {
          ...mockStrategyData.config,
          rangeBreakout: true,
          rangeBreakoutTimeHour: "09",
          rangeBreakoutTimeMinute: "45",
          moveSlToCost: true,
          targetProfit: { type: "TOTAL_MTM" as const, value: 1500 },
          mtmStopLoss: { type: "COMBINED_PREMIUM_PERCENT" as const, value: 500 },
        }
      };
      
      const backendData = strategyTransformationService.transformToBackend(testData);
      
      // Verify flattened strategy configuration fields are at top level
      expect(backendData.range_breakout).toBe(true);
      expect(backendData.range_breakout_time).toBe("09:45");
      expect(backendData.move_sl_to_cost).toBe(true);
      expect(backendData.target_profit).toEqual({
        type: "TOTAL_MTM",
        value: 1500
      });
      expect(backendData.mtm_stop_loss).toEqual({
        type: "COMBINED_PREMIUM_PERCENT",
        value: 500
      });
      
      // Verify no nested strategy_config object exists
      expect(backendData).not.toHaveProperty('strategy_config');
    });

    test("handles product type selection correctly", () => {
      // Test MIS product type (default)
      const misData = {
        ...mockStrategyData,
        config: {
          ...mockStrategyData.config,
          productType: "MIS" as const,
        }
      };
      
      const misBackendData = strategyTransformationService.transformToBackend(misData);
      expect(misBackendData.product).toBe("MIS");

      // Test NRML product type
      const nrmlData = {
        ...mockStrategyData,
        config: {
          ...mockStrategyData.config,
          productType: "NRML" as const,
        }
      };
      
      const nrmlBackendData = strategyTransformationService.transformToBackend(nrmlData);
      expect(nrmlBackendData.product).toBe("NRML");
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
            option_type: "CE",
            action: "SELL",
            strike: 5,
            lots: 2,
            selection_method: "ATM_PERCENT",
          },
          {
            option_type: "PE",
            action: "BUY",
            strike: -3,
            lots: 1,
            selection_method: "ATM_POINTS",
          },
        ],
        // Flattened strategy configuration
        trading_type: "INTRADAY",
        intraday_exit_mode: "SAME_DAY",
        range_breakout: true,
        range_breakout_time: "09:45",
        move_sl_to_cost: true,
        target_profit: {
          type: "TOTAL_MTM",
          value: 1000,
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
      
      // Test product type transformation
      expect(frontendData.config.productType).toBe("MIS");
    });

    test("transforms product type from backend correctly", () => {
      const backendStrategy = {
        name: "NRML Strategy",
        underlying: "BANKNIFTY",
        product: "NRML",
        entry_time: "09:15",
        exit_time: "15:30",
        trading_type: "POSITIONAL",
        entry_trading_days_before_expiry: 5,
        exit_trading_days_before_expiry: 1,
        legs: [
          {
            option_type: "CE",
            action: "BUY",
            strike: "ATM",
            selection_method: "ATM_POINTS",
            lots: 2,
          }
        ]
      };

      const frontendData = strategyTransformationService.transformToFrontend(
        "test-basket-id",
        backendStrategy
      );

      expect(frontendData.config.productType).toBe("NRML");
      expect(frontendData.config.tradingType).toBe("POSITIONAL");
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
            selection_method: "PREMIUM",
            premium_criteria: {
              operator: "CLOSEST",
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
      expect(frontendData.legs![0].premiumOperator).toBe("CLOSEST");
      expect(frontendData.legs![0].premiumValue).toBe(75);
    });

    test("transforms flattened backend strategy with risk management", () => {
      const backendStrategy = {
        name: "Flattened Risk Strategy",
        underlying: "NIFTY",
        entry_time: "09:15",
        exit_time: "15:30",
        legs: [
          {
            option_type: "PE",
            action: "BUY",
            strike: 0,
            lots: 1,
            selection_method: "ATM_POINTS",
            // Flattened risk management
            stop_loss: { enabled: true, type: "PERCENTAGE", value: 10 },
            target_profit: { enabled: true, type: "PERCENTAGE", value: 15 },
            trailing_stop_loss: {
              enabled: true,
              type: "POINTS",
              instrument_move_value: 5,
              stop_loss_move_value: 3
            },
            wait_and_trade: { enabled: true, type: "PERCENTAGE", value: 8 },
            re_entry: { enabled: true, type: "SL_REENTRY", count: 2 },
            re_execute: { enabled: true, type: "TP_REEXEC", count: 1 }
          }
        ],
        // Flattened strategy configuration
        trading_type: "POSITIONAL",
        entry_trading_days_before_expiry: 5,
        exit_trading_days_before_expiry: 1,
        range_breakout: false,
        move_sl_to_cost: false,
        target_profit: { type: "COMBINED_PREMIUM_PERCENT", value: 2000 },
        mtm_stop_loss: { type: "TOTAL_MTM", value: 1500 }
      };
      
      const frontendData = strategyTransformationService.transformToFrontend(
        backendStrategy,
        "test-basket-id"
      );
      
      // Verify strategy-level configuration
      expect(frontendData.config).toMatchObject({
        tradingType: "POSITIONAL",
        entryTradingDaysBeforeExpiry: 5,
        exitTradingDaysBeforeExpiry: 1,
        rangeBreakout: false,
        moveSlToCost: false,
        targetProfit: { type: "COMBINED_PREMIUM_PERCENT", value: 2000 },
        mtmStopLoss: { type: "TOTAL_MTM", value: 1500 }
      });
      
      // Verify risk management transformation
      const leg = frontendData.legs![0];
      expect(leg.stopLoss).toEqual({ enabled: true, type: "PERCENTAGE", value: 10 });
      expect(leg.targetProfit).toEqual({ enabled: true, type: "PERCENTAGE", value: 15 });
      expect(leg.trailingStopLoss).toEqual({
        enabled: true,
        type: "POINTS",
        instrumentMoveValue: 5,
        stopLossMoveValue: 3
      });
      expect(leg.waitAndTrade).toEqual({ enabled: true, type: "PERCENTAGE", value: 8 });
      expect(leg.reEntry).toEqual({ enabled: true, type: "SL_REENTRY", count: 2 });
      expect(leg.reExecute).toEqual({ enabled: true, type: "TP_REEXEC", count: 1 });
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
          selectionMethod: "PREMIUM" as const,
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

  describe("Product Type Validation", () => {
    test("allows MIS for INTRADAY + SAME_DAY configuration", () => {
      const testData = {
        ...mockStrategyData,
        config: {
          ...mockStrategyData.config,
          productType: "MIS" as const,
          tradingType: "INTRADAY" as const,
          intradayExitMode: "SAME_DAY" as const,
        }
      };
      
      const backendData = strategyTransformationService.transformToBackend(testData);
      expect(backendData.product).toBe("MIS");
    });

    test("throws error for MIS with INTRADAY + NEXT_DAY_BTST", () => {
      const testData = {
        ...mockStrategyData,
        config: {
          ...mockStrategyData.config,
          productType: "MIS" as const,
          tradingType: "INTRADAY" as const,
          intradayExitMode: "NEXT_DAY_BTST" as const,
        }
      };
      
      expect(() => {
        strategyTransformationService.transformToBackend(testData);
      }).toThrow("Product type validation failed: MIS product type is only allowed for INTRADAY trading with SAME_DAY exit mode.");
    });

    test("throws error for MIS with POSITIONAL trading", () => {
      const testData = {
        ...mockStrategyData,
        config: {
          ...mockStrategyData.config,
          productType: "MIS" as const,
          tradingType: "POSITIONAL" as const,
          intradayExitMode: "SAME_DAY" as const,
        }
      };
      
      expect(() => {
        strategyTransformationService.transformToBackend(testData);
      }).toThrow("Product type validation failed: MIS product type is only allowed for INTRADAY trading with SAME_DAY exit mode.");
    });

    test("allows NRML for any trading configuration", () => {
      // Test NRML with INTRADAY + NEXT_DAY_BTST
      const testData1 = {
        ...mockStrategyData,
        config: {
          ...mockStrategyData.config,
          productType: "NRML" as const,
          tradingType: "INTRADAY" as const,
          intradayExitMode: "NEXT_DAY_BTST" as const,
        }
      };
      
      expect(() => {
        const result = strategyTransformationService.transformToBackend(testData1);
        expect(result.product).toBe("NRML");
      }).not.toThrow();

      // Test NRML with POSITIONAL
      const testData2 = {
        ...mockStrategyData,
        config: {
          ...mockStrategyData.config,
          productType: "NRML" as const,
          tradingType: "POSITIONAL" as const,
          intradayExitMode: "SAME_DAY" as const,
        }
      };
      
      expect(() => {
        const result = strategyTransformationService.transformToBackend(testData2);
        expect(result.product).toBe("NRML");
      }).not.toThrow();
    });

    test("preserves user choice for INTRADAY + SAME_DAY combinations", () => {
      // Test that NRML is preserved for INTRADAY + SAME_DAY (user choice)
      const testData = {
        ...mockStrategyData,
        config: {
          ...mockStrategyData.config,
          productType: "NRML" as const, // User chooses NRML for INTRADAY + SAME_DAY
          tradingType: "INTRADAY" as const,
          intradayExitMode: "SAME_DAY" as const,
        }
      };
      
      const backendData = strategyTransformationService.transformToBackend(testData);
      
      // Should preserve user choice (NRML)
      expect(backendData.product).toBe("NRML");
    });

    test("throws error for invalid MIS configuration", () => {
      const testData = {
        ...mockStrategyData,
        config: {
          ...mockStrategyData.config,
          productType: "MIS" as const, // Invalid: MIS not allowed for POSITIONAL
          tradingType: "POSITIONAL" as const,
          intradayExitMode: "SAME_DAY" as const,
        }
      };
      
      // Should throw validation error for invalid configuration
      expect(() => {
        strategyTransformationService.transformToBackend(testData);
      }).toThrow("Product type validation failed: MIS product type is only allowed for INTRADAY trading with SAME_DAY exit mode.");
    });
  });
});