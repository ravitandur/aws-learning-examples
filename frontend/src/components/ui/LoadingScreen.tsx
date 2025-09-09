import React from 'react';
import { TrendingUp } from 'lucide-react';

const LoadingScreen: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col justify-center items-center bg-gray-50 dark:bg-gray-900">
      <div className="flex flex-col items-center">
        <TrendingUp className="h-16 w-16 text-blue-600 mb-4" />
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-8">AlgoTrade</h1>
        <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
      </div>
    </div>
  );
};

export default LoadingScreen;