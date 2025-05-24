// frontend/src/hooks/useTaskOperation.js
import { useAsyncOperation } from './useAsyncOperation';

/**
 * Custom hook to handle common task operations with loading state and error handling
 * This is a specialized wrapper around useAsyncOperation for task-specific operations
 * 
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
  const { executeOperation, isLoading, error } = useAsyncOperation(options);
  
  // Create the execute function using the base async operation handler
  const execute = executeOperation(operationFn, onComplete, options);
  
  return [execute, isLoading, error];
}