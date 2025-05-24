import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

/**
 * A reusable error display component with optional retry functionality
 */
const ErrorDisplay = ({ 
  message, 
  onRetry, 
  fullScreen = true,
  className = "",
  variant = "default" // "default", "inline", "banner"
}) => {
  const getVariantClasses = () => {
    switch (variant) {
      case "inline":
        return "bg-red-50 border border-red-200 rounded-lg p-4";
      case "banner":
        return "bg-red-50 border-l-4 border-red-400 p-4";
      default:
        return "bg-red-50 text-red-700 p-6 rounded-lg shadow-md";
    }
  };

  if (fullScreen && variant === "default") {
    return (
      <div className={`min-h-screen bg-gray-50 flex items-center justify-center p-4 ${className}`}>
        <div className={`max-w-md text-center ${getVariantClasses()}`}>
          <AlertCircle className="w-8 h-8 mx-auto mb-3 text-red-500" />
          <h2 className="text-xl font-semibold mb-2 text-red-800">Error</h2>
          <p className="mb-4 text-red-700">{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="px-5 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center justify-center gap-2 mx-auto"
            >
              <RefreshCw className="w-4 h-4" />
              Try Again
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={`${getVariantClasses()} ${className}`}>
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h3 className="text-red-800 font-medium mb-1">Error</h3>
          <p className="text-red-700 text-sm">{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors flex items-center gap-2 text-sm"
            >
              <RefreshCw className="w-4 h-4" />
              Try Again
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ErrorDisplay; 