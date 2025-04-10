// src/components/TaskComponents.jsx
import React, { useState, useEffect } from 'react';
import { Clock, CheckCircle2, AlertCircle, ChevronDown, ChevronUp, RefreshCw, FileText } from 'lucide-react';
import { getStateColor, getReadableState } from '../../constants/taskStates';

// --- NEW: Status Enum Colors ---
const getExecutionStatusColorClasses = (status) => {
  switch (status) {
    case 'Completed':
      return 'bg-green-100 text-green-800 border border-green-300';
    case 'Failed':
      return 'bg-red-100 text-red-800 border border-red-300';
    case 'In Progress':
      return 'bg-yellow-100 text-yellow-800 border border-yellow-300';
    case 'Waiting':
      return 'bg-blue-100 text-blue-800 border border-blue-300';
    case 'Cancelled':
      return 'bg-purple-100 text-purple-800 border border-purple-300';
    case 'Pending': // Fallback for Pending or undefined
    default:
      return 'bg-gray-100 text-gray-700 border border-gray-300';
  }
};
// --- END: Status Enum Colors ---

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

// --- NEW: StatusDetailsDisplay Component ---
/**
 * Displays status badge, timestamps, result, and error for execution items.
 * @param {object} item - The item (work, task, subtask) containing status fields.
 */
export const StatusDetailsDisplay = ({ item }) => {
    if (!item || !item.status) {
        return null; // Don't render if no status info
    }

    const formatTimestamp = (isoString) => {
        if (!isoString) return 'N/A';
        try {
            return new Date(isoString).toLocaleString();
        } catch (e) {
            return 'Invalid Date';
        }
    };

    return (
        <div className="mt-2 mb-3 bg-white p-2 rounded border border-gray-200 text-xs space-y-1">
            <div className="flex items-center gap-2">
                <span className="font-medium">Status:</span>
                <span className={`px-1.5 py-0.5 rounded font-medium ${getExecutionStatusColorClasses(item.status)}`}>
                    {item.status || 'Pending'}
                </span>
            </div>
            {item.started_at && (
                <div>
                    <span className="font-medium">Started:</span> {formatTimestamp(item.started_at)}
                </div>
            )}
            {item.completed_at && (
                <div>
                    <span className="font-medium">Completed:</span> {formatTimestamp(item.completed_at)}
                </div>
            )}
            {/* Result Display */}
            {item.result && (
                <div className="mt-1 pt-1 border-t border-gray-100">
                    <span className="font-medium">Result:</span>
                    <div className="mt-0.5 p-1 bg-gray-50 rounded border border-gray-300 max-h-24 overflow-y-auto text-xs">
                        <pre className="whitespace-pre-wrap">{item.result}</pre>
                    </div>
                </div>
            )}
            {/* Error Display */}
            {item.error_message && (
                <div className="mt-1 pt-1 border-t border-red-100">
                    <span className="font-medium text-red-600">Error:</span>
                    <div className="mt-0.5 p-1 bg-red-50 rounded border border-red-200 max-h-24 overflow-y-auto text-red-800 text-xs">
                        <pre className="whitespace-pre-wrap">{item.error_message}</pre>
                    </div>
                </div>
            )}
        </div>
    );
};
// --- END: StatusDetailsDisplay Component ---