import React from 'react';

export interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  emoji?: string;
}

const PageHeader: React.FC<PageHeaderProps> = ({ 
  title, 
  description, 
  actions, 
  emoji 
}) => {
  return (
    <div className="mb-6">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            {emoji && <span className="mr-2">{emoji}</span>}
            {title}
          </h1>
          {description && (
            <p className="text-gray-600 dark:text-gray-300 max-w-3xl">
              {description}
            </p>
          )}
        </div>
        {actions && (
          <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:shrink-0">
            {actions}
          </div>
        )}
      </div>
    </div>
  );
};

export default PageHeader;