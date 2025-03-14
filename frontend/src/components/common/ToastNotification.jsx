import React, { useState, useEffect } from 'react';
import { X, AlertCircle, CheckCircle, Info } from 'lucide-react';

// Different types of notifications with their respective styling
const TOAST_TYPES = {
  error: {
    icon: AlertCircle,
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    textColor: 'text-red-800',
    iconColor: 'text-red-500',
  },
  success: {
    icon: CheckCircle,
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    textColor: 'text-green-800',
    iconColor: 'text-green-500',
  },
  info: {
    icon: Info,
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    textColor: 'text-blue-800',
    iconColor: 'text-blue-500',
  },
};

const ToastNotification = ({ message, type = 'error', onClose, autoClose = true, duration = 5000 }) => {
  const [visible, setVisible] = useState(true);
  const toastStyle = TOAST_TYPES[type] || TOAST_TYPES.error;
  const Icon = toastStyle.icon;

  useEffect(() => {
    if (autoClose && visible) {
      const timer = setTimeout(() => {
        setVisible(false);
        if (onClose) setTimeout(onClose, 300); // Allow animation to complete
      }, duration);
      
      return () => clearTimeout(timer);
    }
  }, [autoClose, duration, onClose, visible]);

  const handleClose = () => {
    setVisible(false);
    if (onClose) setTimeout(onClose, 300); // Allow animation to complete
  };

  return (
    <div
      className={`fixed top-4 right-4 z-50 flex items-start p-4 mb-4 min-w-[320px] max-w-md 
        ${toastStyle.bgColor} ${toastStyle.borderColor} border rounded-lg shadow-md
        transition-all duration-300 ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-2'}`}
      role="alert"
    >
      <div className="flex items-center">
        <Icon className={`w-5 h-5 mr-3 ${toastStyle.iconColor}`} />
        <div className={`text-sm font-medium ${toastStyle.textColor} flex-1 mr-2`}>
          {message}
        </div>
        <button
          type="button"
          className={`ml-auto -mx-1.5 -my-1.5 ${toastStyle.bgColor} ${toastStyle.textColor} rounded-lg focus:ring-2 focus:ring-gray-300 p-1.5 hover:bg-gray-200 inline-flex h-8 w-8 items-center justify-center`}
          onClick={handleClose}
          aria-label="Close"
        >
          <span className="sr-only">Close</span>
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default ToastNotification; 