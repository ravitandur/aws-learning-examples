"""
Shared logging configuration for AWS Lambda functions
Provides structured logging with CloudWatch integration for all modules
"""
import logging
import json
import os
from typing import Dict, Any

def setup_logger(name: str, level: str = None) -> logging.Logger:
    """
    Set up a structured logger for Lambda functions
    
    Args:
        name: Logger name (usually __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured logger instance
    """
    
    # Get log level from environment or default to INFO
    log_level = level or os.environ.get('LOG_LEVEL', 'INFO')
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create console handler (CloudWatch captures stdout/stderr)
    handler = logging.StreamHandler()
    handler.setLevel(getattr(logging, log_level.upper()))
    
    # Create structured formatter
    formatter = StructuredFormatter()
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs
    Perfect for CloudWatch Logs and AWS X-Ray integration
    """
    
    def format(self, record):
        # Base log structure
        log_obj = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add AWS Lambda context if available
        if hasattr(record, 'aws_request_id'):
            log_obj['aws_request_id'] = record.aws_request_id
            
        if hasattr(record, 'user_id'):
            log_obj['user_id'] = record.user_id
            
        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
            
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                          'pathname', 'filename', 'module', 'lineno', 
                          'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process',
                          'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                log_obj[key] = value
                
        return json.dumps(log_obj, default=str)

def log_lambda_event(logger: logging.Logger, event: Dict[str, Any], context=None):
    """
    Log Lambda event details (sanitized)
    
    Args:
        logger: Logger instance
        event: Lambda event
        context: Lambda context (optional)
    """
    
    # Sanitize event (remove sensitive data)
    sanitized_event = sanitize_event(event)
    
    extra_fields = {
        'event_type': 'lambda_invocation',
        'http_method': event.get('httpMethod'),
        'resource_path': event.get('resource')
    }
    
    if context:
        extra_fields.update({
            'aws_request_id': context.aws_request_id,
            'function_name': context.function_name,
            'remaining_time_ms': context.get_remaining_time_in_millis()
        })
    
    logger.info("Lambda invocation started", extra=extra_fields)

def sanitize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove sensitive information from event for logging
    
    Args:
        event: Original Lambda event
        
    Returns:
        Sanitized event dictionary
    """
    
    sensitive_keys = {'password', 'api_secret', 'api_key', 'secret', 'token', 'authorization'}
    
    def sanitize_dict(obj):
        if isinstance(obj, dict):
            return {
                k: '***REDACTED***' if k.lower() in sensitive_keys else sanitize_dict(v)
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [sanitize_dict(item) for item in obj]
        else:
            return obj
    
    return sanitize_dict(event)

def log_user_action(logger: logging.Logger, user_id: str, action: str, details: Dict[str, Any] = None):
    """
    Log user actions for audit trail
    
    Args:
        logger: Logger instance  
        user_id: User identifier
        action: Action performed
        details: Additional details
    """
    
    extra_fields = {
        'event_type': 'user_action',
        'user_id': user_id,
        'action': action
    }
    
    if details:
        extra_fields.update(details)
    
    logger.info(f"User action: {action}", extra=extra_fields)

def log_api_response(logger: logging.Logger, status_code: int, user_id: str = None, response_size: int = None):
    """
    Log API response details
    
    Args:
        logger: Logger instance
        status_code: HTTP status code
        user_id: User identifier (optional)
        response_size: Response body size in bytes (optional)
    """
    
    extra_fields = {
        'event_type': 'api_response',
        'status_code': status_code
    }
    
    if user_id:
        extra_fields['user_id'] = user_id
        
    if response_size:
        extra_fields['response_size_bytes'] = response_size
    
    level = 'info' if status_code < 400 else 'warning' if status_code < 500 else 'error'
    getattr(logger, level)(f"API response: {status_code}", extra=extra_fields)