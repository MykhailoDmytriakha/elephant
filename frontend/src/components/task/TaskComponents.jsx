// src/components/TaskComponents.jsx
import React, { useState, useEffect } from 'react';
import { Clock, CheckCircle2, AlertCircle, ChevronDown, ChevronUp, RefreshCw, FileText } from 'lucide-react'; // Added FileText
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

export const LoadingSpinner = ({ message = "Loading..." }) => ( // Added optional message
  <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
    <div className="flex flex-col items-center gap-2 text-center">
      <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
      <div className="text-gray-500">{message}</div>
    </div>
  </div>
);

export const ErrorDisplay = ({ message, onRetry }) => ( // Added onRetry prop
  <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
    <div className="bg-red-50 text-red-700 p-6 rounded-lg max-w-md text-center shadow-md">
      <AlertCircle className="w-8 h-8 mx-auto mb-3" />
      <h2 className="text-xl font-semibold mb-2">Error</h2>
      <p className="mb-4">{message}</p>
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

  // Allow controlled state via isOpen prop
  useEffect(() => {
    if (isOpen !== undefined) {
      setIsExpanded(isOpen);
    }
  }, [isOpen]);

  // Allow uncontrolled state toggle
  const toggleExpand = () => {
    if (isOpen === undefined) { // Only toggle if not controlled
        setIsExpanded(!isExpanded);
    }
    // If controlled, the parent component handles the state change
  };


  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      <button // Changed to button for accessibility
        type="button"
        className="flex justify-between items-center w-full cursor-pointer p-4 border-b border-gray-200 text-left"
        onClick={toggleExpand}
        aria-expanded={isExpanded}
      >
        <div className="text-lg font-semibold text-gray-900">{title}</div>
        {isExpanded ? <ChevronUp className="w-5 h-5 text-gray-500" /> : <ChevronDown className="w-5 h-5 text-gray-500" />}
      </button>
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

// --- NEW: ArtifactDisplay Component ---
/**
 * Displays details of a single artifact.
 * @param {object} artifact - The artifact object { name, type, description, location }.
 * @param {string} title - Optional title for the artifact section.
 */
export const ArtifactDisplay = ({ artifact, title = "Artifact" }) => {
    if (!artifact) return null;

    const getArtifactIcon = (type) => {
      switch (type?.toLowerCase()) {
        case 'document':
          return <FileText className="w-5 h-5 text-amber-600" />;
        case 'software':
        case 'code':
        case 'repository':
          return <svg className="w-5 h-5 text-purple-600" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 20V6a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v14"></path>
              <path d="M2 20h20"></path>
              <path d="M14 12v.01"></path>
            </svg>;
        default:
          return <FileText className="w-5 h-5 text-gray-600" />;
      }
    };

    return (
        <div className="mt-3 p-3 bg-gray-50 rounded-md border border-gray-200 w-full">
            {title && <h4 className="text-sm font-medium text-gray-700 mb-2">{title}</h4>}
            <div className="flex items-start gap-2">
                {getArtifactIcon(artifact.type)}
                <div className="w-full">
                    <p className="font-medium text-gray-900 text-sm">{artifact.name} ({artifact.type || 'Unknown Type'})</p>
                    {artifact.description && <p className="text-xs text-gray-600 mt-1">{artifact.description}</p>}
                    {artifact.location && (
                        <p className="text-xs text-gray-500 mt-2">
                            Location: <span className="font-mono bg-gray-100 px-1 rounded">{artifact.location}</span>
                        </p>
                    )}
                </div>
            </div>
        </div>
    );
};
// --- END: ArtifactDisplay Component ---