import { useState, useCallback, useMemo } from 'react';
import { useToast } from '../components/common/ToastProvider';

/**
 * Base configuration for async operations
 */
const DEFAULT_OPTIONS = {
  successMessage: 'Operation completed successfully',
  errorMessage: 'Operation failed',
  showSuccessToast: true,
  showErrorToast: true,
  logErrors: true
};

/**
 * Custom hook for handling async operations with consistent loading, error handling, and toast notifications
 * @param {Object} options - Configuration options
 * @returns {Object} - Operation helpers and state
 */
export function useAsyncOperation(options = {}) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const toast = useToast();
  
  const config = useMemo(() => ({ ...DEFAULT_OPTIONS, ...options }), [options]);

  /**
   * Execute an async operation with full error handling and notifications
   * @param {Function} operationFn - The async function to execute
   * @param {Function} onComplete - Callback executed on success
   * @param {Object} operationOptions - Per-operation options that override defaults
   * @returns {Function} - Async function that can be called with operation arguments
   */
  const executeOperation = useCallback((operationFn, onComplete, operationOptions = {}) => {
    const finalOptions = { ...config, ...operationOptions };
    
    return async (...args) => {
      setIsLoading(true);
      setError(null);
      
      try {
        const result = await operationFn(...args);

        // Handle success message
        if (finalOptions.showSuccessToast) {
          let message = finalOptions.successMessage;
          if (typeof message === 'function') {
            message = message(result, ...args);
          }
          if (message) {
            toast.showSuccess(message);
          }
        }

        // Execute completion callback
        if (onComplete) {
          await Promise.resolve(onComplete(result, ...args));
        }
        
        return result;

      } catch (err) {
        const errorObj = err instanceof Error ? err : new Error(String(err));
        
        // Handle error message
        if (finalOptions.showErrorToast) {
          let message = finalOptions.errorMessage;
          if (typeof message === 'function') {
            message = message(errorObj, ...args);
          } else {
            message = `${message}: ${errorObj.message}`;
          }
          if (message) {
            toast.showError(message);
          }
        }

        // Log error if configured
        if (finalOptions.logErrors) {
          console.error('Async operation failed:', errorObj);
        }

        setError(errorObj);
        throw errorObj;

      } finally {
        setIsLoading(false);
      }
    };
  }, [config, toast]);

  /**
   * Create multiple operation handlers at once
   * @param {Object} operations - Object with operation definitions
   * @returns {Object} - Object with same keys but bound operation handlers
   */
  const createOperations = useCallback((operations) => {
    const handlers = {};
    
    Object.entries(operations).forEach(([key, { operation, onComplete, options }]) => {
      handlers[key] = executeOperation(operation, onComplete, options);
    });
    
    return handlers;
  }, [executeOperation]);

  /**
   * Simple execute function for one-off operations
   * @param {Function} operationFn - The operation to execute
   * @param {Object} operationOptions - Options for this specific operation
   * @returns {Promise} - The operation result
   */
  const execute = useCallback(async (operationFn, operationOptions = {}) => {
    const operation = executeOperation(operationFn, null, operationOptions);
    return operation();
  }, [executeOperation]);

  return {
    isLoading,
    error,
    executeOperation,
    createOperations,
    execute,
    // Utility functions
    clearError: useCallback(() => setError(null), []),
    reset: useCallback(() => {
      setIsLoading(false);
      setError(null);
    }, [])
  };
} 