import React from 'react';
import {cn} from "../../shared/utils/cn";

interface LoadingSpinnerProps {
    className?: string;
    size?: 'sm' | 'md' | 'lg';
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({className, size = 'md'}) => {
    const sizeClasses = {
        sm: 'h-4 w-4',
        md: 'h-8 w-8',
        lg: 'h-12 w-12'
    };

    return (
        <div className={cn('flex items-center justify-center', className)}>
            <div className={cn(
                'border-4 border-gray-200 border-t-blue-600 rounded-full animate-spin',
                sizeClasses[size]
            )}/>
        </div>
    );
};

export default LoadingSpinner;