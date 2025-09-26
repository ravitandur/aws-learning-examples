import React, { useState } from 'react';
import { AlertTriangle, X, Trash2 } from 'lucide-react';
import Button from '../ui/Button';
import Input from '../ui/Input';

interface BulkDeleteConfirmationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  itemCount: number;
  itemType: string; // e.g., "strategies", "baskets"
  isDeleting: boolean;
  deletingMessage?: string;
}

const BulkDeleteConfirmationDialog: React.FC<BulkDeleteConfirmationDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  itemCount,
  itemType,
  isDeleting,
  deletingMessage = 'Deleting...'
}) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [confirmationText, setConfirmationText] = useState('');
  const [isConfirmationValid, setIsConfirmationValid] = useState(false);

  // Reset state when dialog closes
  React.useEffect(() => {
    if (!isOpen) {
      setCurrentStep(1);
      setConfirmationText('');
      setIsConfirmationValid(false);
    }
  }, [isOpen]);

  // Validate confirmation text
  React.useEffect(() => {
    setIsConfirmationValid(confirmationText === 'DELETE ALL');
  }, [confirmationText]);

  const handleNext = () => {
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleConfirm = () => {
    onConfirm();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-full">
              <AlertTriangle className="h-6 w-6 text-red-600 dark:text-red-400" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              {title}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            disabled={isDeleting}
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Step 1: Initial Confirmation */}
          {currentStep === 1 && (
            <div className="space-y-4">
              <div className="text-center">
                <div className="text-4xl font-bold text-red-600 dark:text-red-400 mb-2">
                  {itemCount}
                </div>
                <p className="text-gray-600 dark:text-gray-400">
                  {itemType} will be permanently deleted
                </p>
              </div>

              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-red-800 dark:text-red-200 mb-1">
                      This action cannot be undone
                    </h4>
                    <p className="text-sm text-red-700 dark:text-red-300">
                      All {itemCount} {itemType} will be permanently removed.
                      This includes all related data and cannot be recovered.
                    </p>
                  </div>
                </div>
              </div>

              <div className="text-sm text-gray-600 dark:text-gray-400">
                Are you sure you want to continue?
              </div>
            </div>
          )}

          {/* Step 2: Type Confirmation */}
          {currentStep === 2 && (
            <div className="space-y-4">
              <div className="text-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  Type Confirmation Required
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  To confirm this destructive action, please type:
                </p>
              </div>

              <div className="text-center">
                <div className="inline-block px-4 py-2 bg-red-100 dark:bg-red-900/30 rounded-lg border border-red-200 dark:border-red-800">
                  <span className="font-mono text-red-700 dark:text-red-300 font-semibold">
                    DELETE ALL
                  </span>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-200">
                  Confirmation Text
                </label>
                <Input
                  type="text"
                  value={confirmationText}
                  onChange={(e) => setConfirmationText(e.target.value)}
                  placeholder="Type 'DELETE ALL' to confirm"
                  className={`font-mono ${
                    confirmationText && !isConfirmationValid
                      ? 'border-red-300 dark:border-red-600'
                      : ''
                  }`}
                  autoFocus
                />
                {confirmationText && !isConfirmationValid && (
                  <p className="text-sm text-red-600 dark:text-red-400">
                    Text must match exactly: "DELETE ALL"
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Step 3: Final Warning */}
          {currentStep === 3 && (
            <div className="space-y-4">
              <div className="text-center">
                <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                  <Trash2 className="h-8 w-8 text-red-600 dark:text-red-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  Final Warning
                </h3>
              </div>

              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <div className="text-center space-y-2">
                  <p className="font-semibold text-red-800 dark:text-red-200">
                    This will permanently delete {itemCount} {itemType}
                  </p>
                  <p className="text-sm text-red-700 dark:text-red-300">
                    • All data will be lost forever
                  </p>
                  <p className="text-sm text-red-700 dark:text-red-300">
                    • This action cannot be reversed
                  </p>
                  <p className="text-sm text-red-700 dark:text-red-300">
                    • No recovery options available
                  </p>
                </div>
              </div>

              <div className="text-center">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Click "Delete All {itemCount} {itemType}" to proceed
                </p>
              </div>

              {isDeleting && (
                <div className="text-center">
                  <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                    <span className="text-sm text-blue-700 dark:text-blue-300">
                      {deletingMessage}
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-between px-6 py-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            {/* Step indicators */}
            <div className="flex gap-1">
              {[1, 2, 3].map((step) => (
                <div
                  key={step}
                  className={`w-2 h-2 rounded-full ${
                    step === currentStep
                      ? 'bg-red-600 dark:bg-red-400'
                      : step < currentStep
                      ? 'bg-red-300 dark:bg-red-600'
                      : 'bg-gray-300 dark:bg-gray-600'
                  }`}
                />
              ))}
            </div>
            <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">
              Step {currentStep} of 3
            </span>
          </div>

          <div className="flex gap-3">
            {/* Back Button */}
            {currentStep > 1 && (
              <Button
                variant="ghost"
                onClick={handleBack}
                disabled={isDeleting}
                className="text-gray-600 dark:text-gray-400"
              >
                Back
              </Button>
            )}

            {/* Cancel Button */}
            <Button
              variant="ghost"
              onClick={onClose}
              disabled={isDeleting}
              className="text-gray-600 dark:text-gray-400"
            >
              Cancel
            </Button>

            {/* Next/Confirm Button */}
            {currentStep < 3 ? (
              <Button
                variant="danger"
                onClick={handleNext}
                disabled={currentStep === 2 && !isConfirmationValid}
              >
                {currentStep === 1 ? 'Continue' : 'Next'}
              </Button>
            ) : (
              <Button
                variant="danger"
                onClick={handleConfirm}
                disabled={isDeleting}
                className="bg-red-600 hover:bg-red-700 text-white"
              >
                {isDeleting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete All {itemCount} {itemType}
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BulkDeleteConfirmationDialog;