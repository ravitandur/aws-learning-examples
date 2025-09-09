import React from 'react';
import { CheckCircle, AlertCircle, X } from 'lucide-react';
import { Card, CardContent } from '../ui/Card';
import Button from '../ui/Button';

export interface AlertMessageProps {
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  dismissible?: boolean;
  onDismiss?: () => void;
  className?: string;
}

const AlertMessage: React.FC<AlertMessageProps> = ({
  type,
  message,
  dismissible = true,
  onDismiss,
  className = ""
}) => {
  const getAlertStyles = () => {
    switch (type) {
      case 'success':
        return {
          cardClass: 'border-green-200 bg-green-50 dark:bg-green-900/20',
          textClass: 'text-green-800 dark:text-green-200',
          iconClass: 'text-green-600',
          Icon: CheckCircle
        };
      case 'error':
        return {
          cardClass: 'border-red-200 bg-red-50 dark:bg-red-900/20',
          textClass: 'text-red-800 dark:text-red-200',
          iconClass: 'text-red-600',
          Icon: AlertCircle
        };
      case 'warning':
        return {
          cardClass: 'border-yellow-200 bg-yellow-50 dark:bg-yellow-900/20',
          textClass: 'text-yellow-800 dark:text-yellow-200',
          iconClass: 'text-yellow-600',
          Icon: AlertCircle
        };
      case 'info':
      default:
        return {
          cardClass: 'border-blue-200 bg-blue-50 dark:bg-blue-900/20',
          textClass: 'text-blue-800 dark:text-blue-200',
          iconClass: 'text-blue-600',
          Icon: AlertCircle
        };
    }
  };

  const { cardClass, textClass, iconClass, Icon } = getAlertStyles();

  return (
    <Card className={`${cardClass} ${className}`}>
      <CardContent className="py-3">
        <div className="flex items-center gap-3">
          <Icon className={`h-5 w-5 ${iconClass} flex-shrink-0`} />
          <span className={`${textClass} flex-1`}>
            {message}
          </span>
          {dismissible && onDismiss && (
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={onDismiss} 
              className="h-8 w-8 p-0 hover:bg-transparent"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default AlertMessage;