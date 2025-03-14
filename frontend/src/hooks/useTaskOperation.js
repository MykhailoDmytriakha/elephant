import { useState } from 'react';
import { useToast } from '../components/common/ToastProvider';

/**
 * Custom hook to handle common task operations with loading state and error handling
 * @param {Function} operationFn - The API function to call
 * @param {Function} onComplete - Callback after successful operation
 * @param {Object} options - Additional options
 * @returns {Array} [execute, isLoading, error]
 */
export function useTaskOperation(operationFn, onComplete, options = {}) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const toast = useToast();
  
  const { 
    successMessage = 'Operation completed successfully',
    errorMessage = 'Operation failed',
    showToasts = true
  } = options;

  /**
   * Execute the operation
   * @param {...any} args - Arguments to pass to the operation function
   */
  const execute = async (...args) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const result = await operationFn(...args);

      if (showToasts) {
        // Handle different types of success messages
        let finalSuccessMessage = successMessage;
        
        if (typeof showToasts === 'function') {
          // If showToasts is a function, use it to determine whether to show toasts
          if (!showToasts(args)) {
            // Skip toast if the function returns false
            finalSuccessMessage = null;
          }
        }
        
        if (finalSuccessMessage) {
          if (typeof successMessage === 'function') {
            // If successMessage is a function, call it with args to get the message
            finalSuccessMessage = successMessage(args);
          }
          
          if (finalSuccessMessage) {
            toast.showSuccess(finalSuccessMessage);
          }
        }
      }
      
      if (onComplete) {
        await onComplete(result);
      }
      
      return result;
    } catch (err) {
      const errorMsg = `${errorMessage}: ${err.message}`;
      setError(errorMsg);
      
      if (showToasts && typeof showToasts !== 'function' || (typeof showToasts === 'function' && showToasts(args))) {
        toast.showError(errorMsg);
      }
      
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return [execute, isLoading, error];
} 