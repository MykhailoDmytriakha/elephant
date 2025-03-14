// src/components/TaskComponents.jsx
import React, { useState, useEffect } from 'react';
import { Clock, CheckCircle2, AlertCircle, ChevronDown, ChevronUp, RefreshCw } from 'lucide-react';
import { getStateColor, getReadableState } from '../../constants/taskStates';

export const StatusBadge = ({ state }) => {
  const getStatusIcon = () => {
    const stateNumber = parseInt(state?.split('.')[0]);
    if (state?.includes('12.')) return <CheckCircle2 className="w-4 h-4" />;
    if (state?.includes('1.')) return <Clock className="w-4 h-4" />;
    if (stateNumber >= 9) return <CheckCircle2 className="w-4 h-4" />;
    return <Clock className="w-4 h-4" />;
  };

  return (
    <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full border ${getStateColor(state)}`}>
      {getStatusIcon()}
      <span className="text-sm font-medium">{getReadableState(state)}</span>
    </div>
  );
};

export const InfoCard = ({ title, children, className = '' }) => (
  <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
    <h2 className="text-lg font-semibold text-gray-900 mb-4">{title}</h2>
    {children}
  </div>
);

export const LoadingSpinner = () => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="flex flex-col items-center gap-2">
      <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
      <div className="text-gray-500">Loading...</div>
    </div>
  </div>
);

export const ErrorDisplay = ({ message }) => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="bg-red-50 text-red-700 p-4 rounded-lg max-w-md text-center">
      <AlertCircle className="w-6 h-6 mx-auto mb-2" />
      <p>{message}</p>
    </div>
  </div>
);

export const ProgressBar = ({ progress }) => (
  <div className="mt-2">
    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
      <div
        className="h-full bg-blue-500 rounded-full transition-all duration-500"
        style={{ width: `${progress}%` }}
      />
    </div>
    <span className="mt-1 text-sm text-gray-600">{progress}% Complete</span>
  </div>
);

export const CollapsibleSection = ({ title, children, defaultOpen = true, isOpen, className = '' }) => {
  const [isExpanded, setIsExpanded] = useState(defaultOpen);
  
  // If isOpen prop is provided, use it to control the component - but only once initially
  useEffect(() => {
    if (isOpen !== undefined) {
      setIsExpanded(isOpen);
    }
  }, []); // Empty dependency array means this only runs once on mount

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      <div 
        className="flex justify-between items-center cursor-pointer p-4 border-b border-gray-200"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
        {isExpanded ? <ChevronUp className="w-5 h-5 text-gray-500" /> : <ChevronDown className="w-5 h-5 text-gray-500" />}
      </div>
      {isExpanded && (
        <div className="p-4 transition-all duration-200">
          {children}
        </div>
      )}
    </div>
  );
};

export const InlineErrorWithRetry = ({ message, onRetry }) => (
  <div className="bg-red-50 border border-red-200 rounded-lg p-4 mt-4">
    <div className="flex flex-col items-center text-center">
      <AlertCircle className="w-6 h-6 text-red-500 mb-2" />
      <h3 className="text-red-800 font-medium mb-2">Error</h3>
      <p className="text-red-700 mb-4">{message}</p>
      {onRetry && (
        <button 
          onClick={onRetry}
          className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Try Again
        </button>
      )}
    </div>
  </div>
);
