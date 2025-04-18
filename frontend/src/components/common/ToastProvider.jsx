import React, { createContext, useContext, useState, useCallback } from 'react';
import ToastNotification from './ToastNotification';

// Create context for toast notifications
const ToastContext = createContext();

// Generate unique IDs for toasts
let toastIdCounter = 0;
const generateId = () => `toast-${toastIdCounter++}`;

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  // Add a new toast notification
  const addToast = useCallback((message, type = 'error', options = {}) => {
    const id = generateId();
    const newToast = {
      id,
      message,
      type,
      ...options
    };
    
    setToasts(prevToasts => [...prevToasts, newToast]);
    return id;
  }, []);

  // Remove a toast by ID
  const removeToast = useCallback((id) => {
    setToasts(prevToasts => prevToasts.filter(toast => toast.id !== id));
  }, []);

  // Helper methods for common toast types
  const showError = useCallback((message, options = {}) => 
    addToast(message, 'error', options), [addToast]);
    
  const showSuccess = useCallback((message, options = {}) => 
    addToast(message, 'success', options), [addToast]);
    
  const showInfo = useCallback((message, options = {}) => 
    addToast(message, 'info', options), [addToast]);
    
  const showWarning = useCallback((message, options = {}) => 
    addToast(message, 'warning', options), [addToast]);

  const contextValue = {
    addToast,
    removeToast,
    showError,
    showSuccess,
    showInfo,
    showWarning
  };

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col-reverse gap-3 max-h-[80vh] overflow-y-auto pr-1 toast-container" style={{ pointerEvents: 'none' }}>
        {toasts.map((toast, index) => (
          <ToastNotification
            key={toast.id}
            message={toast.message}
            type={toast.type}
            autoClose={toast.autoClose}
            duration={toast.duration}
            onClose={() => removeToast(toast.id)}
            style={{ 
              position: 'relative', 
              bottom: 'auto', 
              right: 'auto',
              pointerEvents: 'auto'
            }}
          />
        ))}
      </div>
    </ToastContext.Provider>
  );
};

// Custom hook to use toast functionality
export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

export default ToastProvider; 