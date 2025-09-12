/**
 * Product Type Validation Tests
 * 
 * Comprehensive test coverage for MIS/NRML product type validation business rules:
 * - MIS is only allowed when tradingType = 'INTRADAY' AND intradayExitMode = 'SAME_DAY'
 * - In all other cases, it must be NRML
 */

import {
  isMISAllowed,
  getDefaultProductType,
  isValidProductType,
  getProductTypeValidationError,
  autoCorrectProductType
} from '../../../utils/strategy/productTypeValidation';
import { TradingType, IntradayExitMode, ProductType } from '../../../types/strategy';

describe('productTypeValidation', () => {
  describe('isMISAllowed', () => {
    it('should return true for INTRADAY + SAME_DAY', () => {
      const result = isMISAllowed('INTRADAY', 'SAME_DAY');
      expect(result).toBe(true);
    });

    it('should return false for INTRADAY + NEXT_DAY_BTST', () => {
      const result = isMISAllowed('INTRADAY', 'NEXT_DAY_BTST');
      expect(result).toBe(false);
    });

    it('should return false for POSITIONAL + SAME_DAY', () => {
      const result = isMISAllowed('POSITIONAL', 'SAME_DAY');
      expect(result).toBe(false);
    });

    it('should return false for POSITIONAL + NEXT_DAY_BTST', () => {
      const result = isMISAllowed('POSITIONAL', 'NEXT_DAY_BTST');
      expect(result).toBe(false);
    });
  });

  describe('getDefaultProductType', () => {
    it('should always return NRML as default for INTRADAY + SAME_DAY', () => {
      const result = getDefaultProductType('INTRADAY', 'SAME_DAY');
      expect(result).toBe('NRML');
    });

    it('should return NRML as default for INTRADAY + NEXT_DAY_BTST', () => {
      const result = getDefaultProductType('INTRADAY', 'NEXT_DAY_BTST');
      expect(result).toBe('NRML');
    });

    it('should return NRML as default for POSITIONAL + SAME_DAY', () => {
      const result = getDefaultProductType('POSITIONAL', 'SAME_DAY');
      expect(result).toBe('NRML');
    });

    it('should return NRML as default for POSITIONAL + NEXT_DAY_BTST', () => {
      const result = getDefaultProductType('POSITIONAL', 'NEXT_DAY_BTST');
      expect(result).toBe('NRML');
    });
  });

  describe('isValidProductType', () => {
    describe('MIS validation', () => {
      it('should be valid for MIS with INTRADAY + SAME_DAY', () => {
        const result = isValidProductType('MIS', 'INTRADAY', 'SAME_DAY');
        expect(result).toBe(true);
      });

      it('should be invalid for MIS with INTRADAY + NEXT_DAY_BTST', () => {
        const result = isValidProductType('MIS', 'INTRADAY', 'NEXT_DAY_BTST');
        expect(result).toBe(false);
      });

      it('should be invalid for MIS with POSITIONAL + SAME_DAY', () => {
        const result = isValidProductType('MIS', 'POSITIONAL', 'SAME_DAY');
        expect(result).toBe(false);
      });

      it('should be invalid for MIS with POSITIONAL + NEXT_DAY_BTST', () => {
        const result = isValidProductType('MIS', 'POSITIONAL', 'NEXT_DAY_BTST');
        expect(result).toBe(false);
      });
    });

    describe('NRML validation', () => {
      it('should be valid for NRML with INTRADAY + SAME_DAY', () => {
        const result = isValidProductType('NRML', 'INTRADAY', 'SAME_DAY');
        expect(result).toBe(true);
      });

      it('should be valid for NRML with INTRADAY + NEXT_DAY_BTST', () => {
        const result = isValidProductType('NRML', 'INTRADAY', 'NEXT_DAY_BTST');
        expect(result).toBe(true);
      });

      it('should be valid for NRML with POSITIONAL + SAME_DAY', () => {
        const result = isValidProductType('NRML', 'POSITIONAL', 'SAME_DAY');
        expect(result).toBe(true);
      });

      it('should be valid for NRML with POSITIONAL + NEXT_DAY_BTST', () => {
        const result = isValidProductType('NRML', 'POSITIONAL', 'NEXT_DAY_BTST');
        expect(result).toBe(true);
      });
    });
  });

  describe('getProductTypeValidationError', () => {
    it('should return null for valid MIS with INTRADAY + SAME_DAY', () => {
      const error = getProductTypeValidationError('MIS', 'INTRADAY', 'SAME_DAY');
      expect(error).toBeNull();
    });

    it('should return error message for invalid MIS with INTRADAY + NEXT_DAY_BTST', () => {
      const error = getProductTypeValidationError('MIS', 'INTRADAY', 'NEXT_DAY_BTST');
      expect(error).toBe('MIS product type is only allowed for INTRADAY trading with SAME_DAY exit mode.');
    });

    it('should return error message for invalid MIS with POSITIONAL + SAME_DAY', () => {
      const error = getProductTypeValidationError('MIS', 'POSITIONAL', 'SAME_DAY');
      expect(error).toBe('MIS product type is only allowed for INTRADAY trading with SAME_DAY exit mode.');
    });

    it('should return error message for invalid MIS with POSITIONAL + NEXT_DAY_BTST', () => {
      const error = getProductTypeValidationError('MIS', 'POSITIONAL', 'NEXT_DAY_BTST');
      expect(error).toBe('MIS product type is only allowed for INTRADAY trading with SAME_DAY exit mode.');
    });

    it('should return null for valid NRML with any trading configuration', () => {
      expect(getProductTypeValidationError('NRML', 'INTRADAY', 'SAME_DAY')).toBeNull();
      expect(getProductTypeValidationError('NRML', 'INTRADAY', 'NEXT_DAY_BTST')).toBeNull();
      expect(getProductTypeValidationError('NRML', 'POSITIONAL', 'SAME_DAY')).toBeNull();
      expect(getProductTypeValidationError('NRML', 'POSITIONAL', 'NEXT_DAY_BTST')).toBeNull();
    });
  });

  describe('autoCorrectProductType', () => {
    describe('when product type is already correct', () => {
      it('should not change MIS for INTRADAY + SAME_DAY', () => {
        const result = autoCorrectProductType('MIS', 'INTRADAY', 'SAME_DAY');
        expect(result).toEqual({
          productType: 'MIS',
          wasChanged: false
        });
      });

      it('should not change NRML for INTRADAY + NEXT_DAY_BTST', () => {
        const result = autoCorrectProductType('NRML', 'INTRADAY', 'NEXT_DAY_BTST');
        expect(result).toEqual({
          productType: 'NRML',
          wasChanged: false
        });
      });

      it('should not change NRML for POSITIONAL + SAME_DAY', () => {
        const result = autoCorrectProductType('NRML', 'POSITIONAL', 'SAME_DAY');
        expect(result).toEqual({
          productType: 'NRML',
          wasChanged: false
        });
      });

      it('should not change NRML for POSITIONAL + NEXT_DAY_BTST', () => {
        const result = autoCorrectProductType('NRML', 'POSITIONAL', 'NEXT_DAY_BTST');
        expect(result).toEqual({
          productType: 'NRML',
          wasChanged: false
        });
      });
    });

    describe('when product type needs correction', () => {
      it('should NOT change NRML to MIS for INTRADAY + SAME_DAY (user choice preserved)', () => {
        const result = autoCorrectProductType('NRML', 'INTRADAY', 'SAME_DAY');
        expect(result).toEqual({
          productType: 'NRML',
          wasChanged: false
        });
      });

      it('should change MIS to NRML for INTRADAY + NEXT_DAY_BTST', () => {
        const result = autoCorrectProductType('MIS', 'INTRADAY', 'NEXT_DAY_BTST');
        expect(result).toEqual({
          productType: 'NRML',
          wasChanged: true
        });
      });

      it('should change MIS to NRML for POSITIONAL + SAME_DAY', () => {
        const result = autoCorrectProductType('MIS', 'POSITIONAL', 'SAME_DAY');
        expect(result).toEqual({
          productType: 'NRML',
          wasChanged: true
        });
      });

      it('should change MIS to NRML for POSITIONAL + NEXT_DAY_BTST', () => {
        const result = autoCorrectProductType('MIS', 'POSITIONAL', 'NEXT_DAY_BTST');
        expect(result).toEqual({
          productType: 'NRML',
          wasChanged: true
        });
      });
    });
  });

  describe('integration scenarios', () => {
    it('should handle typical user workflow: starts with INTRADAY+SAME_DAY, changes to POSITIONAL', () => {
      // User starts with INTRADAY + SAME_DAY (MIS allowed, both MIS and NRML valid)
      expect(isMISAllowed('INTRADAY', 'SAME_DAY')).toBe(true);
      expect(isValidProductType('MIS', 'INTRADAY', 'SAME_DAY')).toBe(true);
      expect(isValidProductType('NRML', 'INTRADAY', 'SAME_DAY')).toBe(true);
      
      // User changes to POSITIONAL (MIS no longer allowed)
      expect(isMISAllowed('POSITIONAL', 'SAME_DAY')).toBe(false);
      expect(isValidProductType('MIS', 'POSITIONAL', 'SAME_DAY')).toBe(false);
      
      // Auto-correction should fix it only if MIS was selected
      const corrected = autoCorrectProductType('MIS', 'POSITIONAL', 'SAME_DAY');
      expect(corrected.productType).toBe('NRML');
      expect(corrected.wasChanged).toBe(true);
    });

    it('should handle edge case: INTRADAY with NEXT_DAY_BTST (MIS not allowed)', () => {
      expect(isMISAllowed('INTRADAY', 'NEXT_DAY_BTST')).toBe(false);
      expect(getDefaultProductType('INTRADAY', 'NEXT_DAY_BTST')).toBe('NRML');
      
      const error = getProductTypeValidationError('MIS', 'INTRADAY', 'NEXT_DAY_BTST');
      expect(error).toContain('MIS product type is only allowed for INTRADAY trading with SAME_DAY exit mode');
      
      const corrected = autoCorrectProductType('MIS', 'INTRADAY', 'NEXT_DAY_BTST');
      expect(corrected.productType).toBe('NRML');
      expect(corrected.wasChanged).toBe(true);
    });
  });
});