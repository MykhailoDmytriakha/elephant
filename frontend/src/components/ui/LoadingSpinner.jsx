import React from 'react';

/**
 * A reusable loading spinner component with customizable size and message
 */
const LoadingSpinner = ({ 
  message = "Loading...", 
  size = "default", 
  fullScreen = true,
  className = "",
  spinnerClassName = ""
}) => {
  const sizeClasses = {
    small: "w-4 h-4",
    default: "w-8 h-8", 
    large: "w-12 h-12"
  };

  const spinnerClass = `${sizeClasses[size]} border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin ${spinnerClassName}`;

  if (fullScreen) {
    return (
      <div className={`min-h-screen bg-gray-50 flex items-center justify-center p-4 ${className}`}>
        <div className="flex flex-col items-center gap-2 text-center">
          <div className={spinnerClass} />
          <div className="text-gray-500">{message}</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex items-center justify-center p-4 ${className}`}>
      <div className="flex flex-col items-center gap-2 text-center">
        <div className={spinnerClass} />
        <div className="text-gray-500 text-sm">{message}</div>
      </div>
    </div>
  );
};

export default LoadingSpinner; 