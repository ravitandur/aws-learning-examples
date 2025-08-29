import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  message?: string;
  size?: number;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  message = 'Loading...', 
  size = 24 
}) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[200px] gap-2">
      <Loader2 className="animate-spin text-blue-600" size={size} />
      {message && (
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {message}
        </p>
      )}
    </div>
  );
};

export default LoadingSpinner;