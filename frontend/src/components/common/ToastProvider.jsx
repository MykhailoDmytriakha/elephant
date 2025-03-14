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

  const contextValue = {
    addToast,
    removeToast,
    showError,
    showSuccess,
    showInfo
  };

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      <div className="toast-container">
        {toasts.map(toast => (
          <ToastNotification
            key={toast.id}
            message={toast.message}
            type={toast.type}
            autoClose={toast.autoClose}
            duration={toast.duration}
            onClose={() => removeToast(toast.id)}
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