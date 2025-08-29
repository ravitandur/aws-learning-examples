import React from 'react';
import { Alert, AlertTitle, IconButton } from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';

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

  return (
    <Alert 
      severity={severity}
      action={
        onClose && (
          <IconButton
            aria-label="close"
            color="inherit"
            size="small"
            onClick={onClose}
          >
            <CloseIcon fontSize="inherit" />
          </IconButton>
        )
      }
    >
      {title && <AlertTitle>{title}</AlertTitle>}
      {message}
    </Alert>
  );
};

export default ErrorAlert;