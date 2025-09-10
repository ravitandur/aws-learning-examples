/**
 * Unified Error Handling Service
 * 
 * Provides consistent error handling and user-friendly error messages across all basket/strategy operations.
 * Includes retry logic, error categorization, and logging for debugging.
 */

interface ErrorResponse {
  message: string;
  code?: string;
  details?: any;
  timestamp?: string;
}

interface UserFriendlyError {
  title: string;
  message: string;
  type: 'error' | 'warning' | 'info';
  actionable: boolean;
  retryable: boolean;
  suggestions?: string[];
}

interface ErrorHandlingOptions {
  enableRetry?: boolean;
  maxRetries?: number;
  retryDelay?: number;
  logError?: boolean;
  showToUser?: boolean;
  context?: string;
}

class ErrorHandlingService {
  private readonly defaultOptions: Required<ErrorHandlingOptions> = {
    enableRetry: false,
    maxRetries: 3,
    retryDelay: 1000,
    logError: true,
    showToUser: true,
    context: 'Unknown'
  };

  /**
   * Main error handling method - processes and transforms errors
   */
  handleError(
    error: any, 
    options: ErrorHandlingOptions = {}
  ): UserFriendlyError {
    const opts = { ...this.defaultOptions, ...options };
    
    // Log error for debugging if enabled
    if (opts.logError) {
      this.logError(error, opts.context);
    }

    // Transform error to user-friendly format
    const userError = this.transformError(error, opts.context);
    
    return userError;
  }

  /**
   * Execute function with automatic error handling and retry logic
   */
  async executeWithHandling<T>(
    operation: () => Promise<T>,
    options: ErrorHandlingOptions = {}
  ): Promise<{ success: true; data: T } | { success: false; error: UserFriendlyError }> {
    const opts = { ...this.defaultOptions, ...options };
    let lastError: any;
    
    const maxAttempts = opts.enableRetry ? opts.maxRetries + 1 : 1;
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        const result = await operation();
        return { success: true, data: result };
      } catch (error) {
        lastError = error;
        
        // Log attempt
        if (opts.logError) {
          console.warn(`Attempt ${attempt}/${maxAttempts} failed for ${opts.context}:`, error);
        }
        
        // Don't retry on non-retryable errors
        if (!this.isRetryableError(error) || attempt === maxAttempts) {
          break;
        }
        
        // Wait before retry
        if (attempt < maxAttempts) {
          await this.delay(opts.retryDelay * attempt); // Exponential backoff
        }
      }
    }
    
    // All attempts failed
    const userError = this.handleError(lastError, { ...opts, enableRetry: false });
    return { success: false, error: userError };
  }

  /**
   * Transform raw error into user-friendly error message
   */
  private transformError(error: any, context: string): UserFriendlyError {
    // Handle axios errors
    if (error.response) {
      return this.handleApiError(error, context);
    }
    
    // Handle network errors
    if (error.code === 'NETWORK_ERROR' || !navigator.onLine) {
      return this.createNetworkError();
    }
    
    // Handle validation errors
    if (error.message?.includes('Validation failed')) {
      return this.handleValidationError(error);
    }
    
    // Handle timeout errors
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      return this.createTimeoutError(context);
    }
    
    // Handle strategy-specific errors
    if (context.includes('strategy')) {
      return this.handleStrategyError(error, context);
    }
    
    // Handle basket-specific errors
    if (context.includes('basket')) {
      return this.handleBasketError(error, context);
    }
    
    // Generic error fallback
    return this.createGenericError(error, context);
  }

  /**
   * Handle API response errors
   */
  private handleApiError(error: any, context: string): UserFriendlyError {
    const status = error.response.status;
    const data = error.response.data;
    
    switch (status) {
      case 400:
        return {
          title: 'Invalid Request',
          message: data.message || 'The request contains invalid data. Please check your input and try again.',
          type: 'error',
          actionable: true,
          retryable: false,
          suggestions: this.getBadRequestSuggestions(context, data)
        };
        
      case 401:
        return {
          title: 'Authentication Required',
          message: 'Your session has expired. Please log in again to continue.',
          type: 'error',
          actionable: true,
          retryable: false,
          suggestions: ['Log out and log back in', 'Clear browser cache and cookies']
        };
        
      case 403:
        return {
          title: 'Access Denied',
          message: 'You don\'t have permission to perform this action.',
          type: 'error',
          actionable: false,
          retryable: false,
          suggestions: ['Contact support if you believe this is an error']
        };
        
      case 404:
        return this.createNotFoundError(context);
        
      case 409:
        return {
          title: 'Conflict',
          message: data.message || 'This action conflicts with the current state. Please refresh and try again.',
          type: 'error',
          actionable: true,
          retryable: true,
          suggestions: ['Refresh the page', 'Check if the item still exists']
        };
        
      case 429:
        return {
          title: 'Rate Limit Exceeded',
          message: 'Too many requests. Please wait a moment before trying again.',
          type: 'warning',
          actionable: true,
          retryable: true,
          suggestions: ['Wait 1-2 minutes before retrying']
        };
        
      case 500:
      case 502:
      case 503:
        return this.createServerError(status);
        
      default:
        return this.createGenericApiError(status, data, context);
    }
  }

  /**
   * Handle strategy-specific errors
   */
  private handleStrategyError(error: any, context: string): UserFriendlyError {
    const message = error.message?.toLowerCase() || '';
    
    if (message.includes('premium criteria')) {
      return {
        title: 'Premium Criteria Error',
        message: 'The premium criteria you specified couldn\'t be satisfied. Please adjust your premium values.',
        type: 'error',
        actionable: true,
        retryable: false,
        suggestions: [
          'Try a wider premium range',
          'Use different strike selection method',
          'Check current market volatility'
        ]
      };
    }
    
    if (message.includes('strike price') || message.includes('expiry')) {
      return {
        title: 'Invalid Strategy Configuration',
        message: 'There\'s an issue with your strike prices or expiry dates. Please review your strategy configuration.',
        type: 'error',
        actionable: true,
        retryable: false,
        suggestions: [
          'Check strike prices are within valid range',
          'Ensure expiry dates are in the future',
          'Verify underlying symbol is correct'
        ]
      };
    }
    
    if (message.includes('risk management') || message.includes('stop loss')) {
      return {
        title: 'Risk Management Error',
        message: 'There\'s an issue with your risk management settings. Please review your stop loss and target profit configurations.',
        type: 'error',
        actionable: true,
        retryable: false,
        suggestions: [
          'Check stop loss values are positive',
          'Ensure target profit is greater than stop loss',
          'Verify risk management types are compatible'
        ]
      };
    }
    
    return this.createGenericError(error, context);
  }

  /**
   * Handle basket-specific errors
   */
  private handleBasketError(error: any, context: string): UserFriendlyError {
    const message = error.message?.toLowerCase() || '';
    
    if (message.includes('allocation') || message.includes('broker')) {
      return {
        title: 'Broker Allocation Error',
        message: 'There\'s an issue with your broker allocations. Please check your broker configurations.',
        type: 'error',
        actionable: true,
        retryable: false,
        suggestions: [
          'Verify broker accounts are active',
          'Check allocation percentages add up to 100%',
          'Ensure minimum lot requirements are met'
        ]
      };
    }
    
    if (message.includes('execution') || message.includes('timing')) {
      return {
        title: 'Execution Error',
        message: 'Unable to execute the basket strategy. Please check your execution settings.',
        type: 'error',
        actionable: true,
        retryable: true,
        suggestions: [
          'Check market hours',
          'Verify broker connection status',
          'Review execution timing settings'
        ]
      };
    }
    
    return this.createGenericError(error, context);
  }

  /**
   * Handle validation errors
   */
  private handleValidationError(error: any): UserFriendlyError {
    const message = error.message || '';
    const errors = message.replace('Validation failed: ', '').split(', ');
    
    return {
      title: 'Validation Error',
      message: 'Please fix the following issues:',
      type: 'error',
      actionable: true,
      retryable: false,
      suggestions: errors
    };
  }

  /**
   * Create specific error types
   */
  private createNetworkError(): UserFriendlyError {
    return {
      title: 'Connection Error',
      message: 'Unable to connect to the server. Please check your internet connection.',
      type: 'error',
      actionable: true,
      retryable: true,
      suggestions: [
        'Check your internet connection',
        'Try refreshing the page',
        'Contact support if the problem persists'
      ]
    };
  }

  private createTimeoutError(context: string): UserFriendlyError {
    return {
      title: 'Request Timeout',
      message: 'The request took too long to complete. Please try again.',
      type: 'warning',
      actionable: true,
      retryable: true,
      suggestions: [
        'Try again in a few moments',
        'Check your internet connection speed',
        'Simplify your request if possible'
      ]
    };
  }

  private createNotFoundError(context: string): UserFriendlyError {
    const itemType = this.getItemTypeFromContext(context);
    
    return {
      title: `${itemType} Not Found`,
      message: `The ${itemType.toLowerCase()} you're looking for doesn't exist or has been deleted.`,
      type: 'error',
      actionable: true,
      retryable: false,
      suggestions: [
        'Check if the item was recently deleted',
        'Refresh the page to see the latest data',
        'Go back to the main list'
      ]
    };
  }

  private createServerError(status: number): UserFriendlyError {
    return {
      title: 'Server Error',
      message: 'The server is experiencing issues. Our team has been notified.',
      type: 'error',
      actionable: true,
      retryable: true,
      suggestions: [
        'Try again in a few minutes',
        'Contact support if the issue persists'
      ]
    };
  }

  private createGenericError(error: any, context: string): UserFriendlyError {
    return {
      title: 'Unexpected Error',
      message: error.message || 'An unexpected error occurred. Please try again.',
      type: 'error',
      actionable: true,
      retryable: true,
      suggestions: [
        'Try refreshing the page',
        'Check your network connection',
        'Contact support with error details'
      ]
    };
  }

  private createGenericApiError(status: number, data: any, context: string): UserFriendlyError {
    return {
      title: `API Error (${status})`,
      message: data?.message || `The server returned an error (${status}). Please try again.`,
      type: 'error',
      actionable: true,
      retryable: status >= 500,
      suggestions: status >= 500 ? 
        ['Try again in a few minutes', 'Contact support if the issue persists'] :
        ['Check your request and try again', 'Contact support if needed']
    };
  }

  /**
   * Helper methods
   */
  private getBadRequestSuggestions(context: string, data: any): string[] {
    const suggestions = [];
    
    if (context.includes('strategy')) {
      suggestions.push('Check all required fields are filled');
      suggestions.push('Verify strike prices and dates');
      suggestions.push('Review risk management settings');
    } else if (context.includes('basket')) {
      suggestions.push('Check basket name and description');
      suggestions.push('Verify broker allocations');
      suggestions.push('Ensure all strategies are valid');
    }
    
    if (data?.validation_errors) {
      suggestions.push(...data.validation_errors);
    }
    
    return suggestions.length > 0 ? suggestions : ['Review your input and try again'];
  }

  private getItemTypeFromContext(context: string): string {
    if (context.includes('strategy')) return 'Strategy';
    if (context.includes('basket')) return 'Basket';
    if (context.includes('allocation')) return 'Allocation';
    return 'Item';
  }

  private isRetryableError(error: any): boolean {
    // Don't retry validation errors or 4xx client errors (except 429)
    if (error.response) {
      const status = error.response.status;
      if (status >= 400 && status < 500 && status !== 429) {
        return false;
      }
    }
    
    // Don't retry validation errors
    if (error.message?.includes('Validation failed')) {
      return false;
    }
    
    return true;
  }

  private logError(error: any, context: string): void {
    const errorInfo = {
      context,
      message: error.message,
      stack: error.stack,
      response: error.response?.data,
      status: error.response?.status,
      timestamp: new Date().toISOString()
    };
    
    console.error(`[ErrorHandling] ${context}:`, errorInfo);
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Create formatted error for toast notifications
   */
  createToastError(error: UserFriendlyError): {
    title: string;
    description: string;
    type: 'error' | 'warning' | 'info';
  } {
    return {
      title: error.title,
      description: error.message + (error.suggestions?.length ? 
        `\n\nSuggestions:\n• ${error.suggestions.join('\n• ')}` : ''),
      type: error.type
    };
  }

  /**
   * Get error summary for logging/debugging
   */
  getErrorSummary(error: UserFriendlyError): string {
    return `${error.title}: ${error.message}${error.retryable ? ' (retryable)' : ''}`;
  }
}

const errorHandlingService = new ErrorHandlingService();
export default errorHandlingService;
export { ErrorHandlingService };
export type { UserFriendlyError, ErrorHandlingOptions };