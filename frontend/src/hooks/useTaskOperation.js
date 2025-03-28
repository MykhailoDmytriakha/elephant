// frontend/src/hooks/useTaskOperation.js
import { useState, useCallback } from 'react'; // Added useCallback
import { useToast } from '../components/common/ToastProvider';

/**
 * Custom hook to handle common task operations with loading state and error handling
 * @param {Function} operationFn - The API function to call. Should return data on success or throw an error.
 * @param {Function} onComplete - Callback with the result after successful operation.
 * @param {Object} options - Configuration options.
 * @param {string | Function | null} [options.successMessage='Operation completed successfully'] - Message on success. Can be a function receiving the result. Null disables toast.
 * @param {string | Function | null} [options.errorMessage='Operation failed'] - Base message on error. Can be a function receiving the error. Null disables toast.
 * @param {boolean} [options.showSuccessToast=true] - Whether to show a toast on success.
 * @param {boolean} [options.showErrorToast=true] - Whether to show a toast on error.
 * @returns {Array} [execute (async function), isLoading (boolean), error (Error | null)]
 */
export function useTaskOperation(operationFn, onComplete, options = {}) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const toast = useToast();

  const {
    successMessage = 'Operation completed successfully',
    errorMessage = 'Operation failed',
    showSuccessToast = true,
    showErrorToast = true,
  } = options;

  const execute = useCallback(async (...args) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await operationFn(...args);

      if (showSuccessToast) {
        let finalSuccessMessage = successMessage;
        if (typeof successMessage === 'function') {
          finalSuccessMessage = successMessage(result, ...args); // Pass result and args to function
        }
        // Show toast only if message is not null or empty
        if (finalSuccessMessage) {
            toast.showSuccess(finalSuccessMessage);
        }
      }

      if (onComplete) {
        // Allow onComplete to be async
        await Promise.resolve(onComplete(result));
      }
      return result; // Return the result for potential chaining or further processing

    } catch (err) {
      // Ensure err is an Error object
      const errorObj = err instanceof Error ? err : new Error(String(err));
      let finalErrorMessage = errorMessage;

      if (typeof errorMessage === 'function') {
        finalErrorMessage = errorMessage(errorObj, ...args); // Pass error and args to function
      } else {
        // Append the actual error message if errorMessage is a string
        finalErrorMessage = `${errorMessage}: ${errorObj.message}`;
      }

      setError(errorObj); // Store the actual Error object

      if (showErrorToast && finalErrorMessage) {
        toast.showError(finalErrorMessage);
      }

      // Re-throw the original error object to allow calling code to handle it further if needed
      // This preserves the stack trace and original error type
      throw errorObj;

    } finally {
      setIsLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [operationFn, onComplete, successMessage, errorMessage, showSuccessToast, showErrorToast, toast]); // Add dependencies

  return [execute, isLoading, error];
}