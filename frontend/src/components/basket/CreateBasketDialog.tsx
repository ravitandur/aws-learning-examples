import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import { X, ShoppingCart, AlertCircle } from 'lucide-react';
import { CreateBasket } from '../../types';

interface CreateBasketDialogProps {
  onClose: () => void;
  onSubmit: (basketData: CreateBasket) => void;
}

const CreateBasketDialog: React.FC<CreateBasketDialogProps> = ({ onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    basket_name: '',
    description: '',
    initial_capital: 100000
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (!formData.basket_name.trim()) {
      setError('Basket name is required');
      return;
    }

    if (formData.initial_capital < 10000) {
      setError('Initial capital must be at least ₹10,000');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const basketData: CreateBasket = {
        basket_name: formData.basket_name.trim(),
        description: formData.description.trim() || undefined,
        strategies: [], // Start with empty strategies
        initial_capital: formData.initial_capital
      };

      await onSubmit(basketData);
      // Success - dialog will be closed by parent
      
    } catch (error: any) {
      console.error('Failed to create basket:', error);
      // Extract meaningful error message from API response
      let errorMessage = 'Failed to create basket. Please try again.';
      
      if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setError(errorMessage);
      setIsSubmitting(false);
    }
  };

  const handleTryAgain = () => {
    setError(null);
    setIsSubmitting(false);
  };

  const handleClose = () => {
    if (!isSubmitting) {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md mx-4">
        <Card className="border-0 shadow-none">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <ShoppingCart className="h-5 w-5" />
                Create New Basket
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClose}
                disabled={isSubmitting}
                className="h-8 w-8 p-0"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Create a new strategy basket to organize your trading strategies
            </p>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              
              {/* Error Message */}
              {error && (
                <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <span className="text-sm text-red-800 dark:text-red-200">{error}</span>
                      <div className="mt-2 flex gap-2">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={handleTryAgain}
                          className="text-xs h-7 px-2"
                        >
                          Try Again
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={handleClose}
                          className="text-xs h-7 px-2"
                        >
                          Close
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Basket Name */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Basket Name *
                </label>
                <Input
                  value={formData.basket_name}
                  onChange={(e) => setFormData(prev => ({ ...prev, basket_name: e.target.value }))}
                  placeholder="e.g., Conservative Income Strategies"
                  disabled={isSubmitting}
                  className="w-full"
                  autoFocus
                />
                <p className="text-xs text-gray-500 mt-1">
                  Choose a descriptive name for your basket
                </p>
              </div>

              {/* Initial Capital */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Initial Capital *
                </label>
                <Input
                  type="number"
                  value={formData.initial_capital}
                  onChange={(e) => setFormData(prev => ({ ...prev, initial_capital: parseInt(e.target.value) || 0 }))}
                  placeholder="100000"
                  disabled={isSubmitting}
                  min="10000"
                  step="1000"
                  className="w-full"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Starting capital for this basket (minimum ₹10,000)
                </p>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Description (Optional)
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Brief description of your basket's investment approach and goals..."
                  disabled={isSubmitting}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Help others understand the purpose of this basket
                </p>
              </div>

              {/* Info Box */}
              <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                <div className="flex items-start gap-2">
                  <div className="w-4 h-4 bg-blue-600 rounded-full mt-0.5 flex-shrink-0">
                    <div className="w-2 h-2 bg-white rounded-full m-1"></div>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200">
                      Next Steps
                    </h4>
                    <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                      After creating your basket, you'll be able to add strategies and configure 
                      multi-broker allocations for optimal execution.
                    </p>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-3 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleClose}
                  disabled={isSubmitting}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isSubmitting || !formData.basket_name.trim() || formData.initial_capital < 10000}
                  className="flex-1"
                  leftIcon={isSubmitting ? undefined : <ShoppingCart className="h-4 w-4" />}
                >
                  {isSubmitting ? 'Creating...' : 'Create Basket'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CreateBasketDialog;