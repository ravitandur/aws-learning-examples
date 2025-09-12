import React, { useEffect } from 'react';
import Select from '../../ui/Select';
import { INDEX_OPTIONS, EXPIRY_TYPE_OPTIONS } from '../../../utils/strategy/strategyConstants';
import { ExpiryType, ProductType, TradingType, IntradayExitMode } from '../../../types/strategy';
import { isMISAllowed, autoCorrectProductType } from '../../../utils/strategy/productTypeValidation';

interface GlobalIndexSelectorProps {
  value: string;
  onChange: (value: string) => void;
  expiryType: ExpiryType;
  onExpiryTypeChange: (expiryType: ExpiryType) => void;
  productType: ProductType;
  onProductTypeChange: (productType: ProductType) => void;
  tradingType: TradingType;
  intradayExitMode: IntradayExitMode;
}

const GlobalIndexSelector: React.FC<GlobalIndexSelectorProps> = ({ 
  value, 
  onChange, 
  expiryType, 
  onExpiryTypeChange,
  productType,
  onProductTypeChange,
  tradingType,
  intradayExitMode
}) => {
  const handleIndexChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    onChange(event.target.value);
  };

  const handleExpiryTypeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    onExpiryTypeChange(event.target.value as ExpiryType);
  };

  // Check if MIS is allowed based on current trading configuration
  const misAllowed = isMISAllowed(tradingType, intradayExitMode);
  
  // Auto-correct product type when trading configuration changes
  // Only auto-corrects when MIS is selected but not allowed
  useEffect(() => {
    const { productType: correctedProductType, wasChanged } = autoCorrectProductType(
      productType,
      tradingType,
      intradayExitMode
    );
    
    if (wasChanged) {
      onProductTypeChange(correctedProductType);
    }
  }, [tradingType, intradayExitMode, productType, onProductTypeChange]);

  const handleProductTypeChange = (newProductType: ProductType) => {
    // Only allow the change if it's valid
    if (newProductType === 'MIS' && !misAllowed) {
      // Don't allow MIS if conditions aren't met
      return;
    }
    onProductTypeChange(newProductType);
  };

  return (
    <div className="mx-4 mb-4">
      <div className="bg-blue-50 dark:bg-blue-900/10 border-l-4 border-blue-500 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Strategy Configuration
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
              Select index, expiry type and product type that will apply to all positions in this strategy
            </p>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
              Index
            </label>
            <Select 
              value={value} 
              onChange={handleIndexChange}
              options={INDEX_OPTIONS}
              className="bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
              Expiry Type
            </label>
            <Select 
              value={expiryType} 
              onChange={handleExpiryTypeChange}
              options={EXPIRY_TYPE_OPTIONS}
              className="bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
              Product Type
            </label>
            <div className="flex rounded-lg overflow-hidden border border-gray-300 dark:border-gray-600">
              <button
                type="button"
                onClick={() => handleProductTypeChange('MIS')}
                disabled={!misAllowed}
                className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                  productType === 'MIS'
                    ? 'bg-blue-600 text-white'
                    : misAllowed
                    ? 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-500 cursor-not-allowed'
                }`}
                title={!misAllowed ? 'MIS is only available for INTRADAY trading with SAME_DAY exit mode' : ''}
              >
                MIS
              </button>
              <button
                type="button"
                onClick={() => handleProductTypeChange('NRML')}
                className={`flex-1 px-4 py-2 text-sm font-medium border-l border-gray-300 dark:border-gray-600 transition-colors ${
                  productType === 'NRML'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600'
                }`}
              >
                NRML
              </button>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {misAllowed 
                ? 'MIS: Intraday (available), NRML: Carry Forward (available)'
                : 'MIS: Intraday (requires INTRADAY + SAME_DAY), NRML: Carry Forward'
              }
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GlobalIndexSelector;