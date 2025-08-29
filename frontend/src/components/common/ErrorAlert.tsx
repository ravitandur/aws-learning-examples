import React from 'react';
import { X } from 'lucide-react';

interface ErrorAlertProps {
  message: string;
  title?: string;
  onClose?: () => void;
  severity?: 'error' | 'warning' | 'info' | 'success';
}

const ErrorAlert: React.FC<ErrorAlertProps> = ({ 
  message, 
  title,
  onClose,
  severity = 'error'
}) => {
  if (!message) return null;

  const getSeverityStyles = () => {
    switch (severity) {
      case 'error':
        return 'bg-red-50 border border-red-200 text-red-800';
      case 'warning':
        return 'bg-yellow-50 border border-yellow-200 text-yellow-800';
      case 'info':
        return 'bg-blue-50 border border-blue-200 text-blue-800';
      case 'success':
        return 'bg-green-50 border border-green-200 text-green-800';
      default:
        return 'bg-red-50 border border-red-200 text-red-800';
    }
  };

  return (
    <div className={`rounded-lg p-4 ${getSeverityStyles()}`}>
      <div className="flex">
        <div className="flex-1">
          {title && (
            <h3 className="text-sm font-medium mb-1">{title}</h3>
          )}
          <p className="text-sm">{message}</p>
        </div>
        {onClose && (
          <button
            className="ml-3 flex-shrink-0 hover:opacity-70"
            onClick={onClose}
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
};

export default ErrorAlert;