import React from 'react';
import { Clock, CheckCircle2, AlertCircle, XCircle, Play, Pause } from 'lucide-react';

/**
 * A unified status badge component that handles both task states and execution statuses
 */
const StatusBadge = ({ 
  status, 
  state, 
  variant = "default",
  size = "default",
  showIcon = true,
  className = ""
}) => {
  // Handle execution status colors (used in tasks, subtasks, etc.)
  const getExecutionStatusStyles = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return {
          className: 'bg-green-100 text-green-800 border-green-300',
          icon: <CheckCircle2 className="w-4 h-4" />
        };
      case 'failed':
        return {
          className: 'bg-red-100 text-red-800 border-red-300',
          icon: <XCircle className="w-4 h-4" />
        };
      case 'in progress':
        return {
          className: 'bg-yellow-100 text-yellow-800 border-yellow-300',
          icon: <Play className="w-4 h-4" />
        };
      case 'waiting':
        return {
          className: 'bg-blue-100 text-blue-800 border-blue-300',
          icon: <Pause className="w-4 h-4" />
        };
      case 'cancelled':
        return {
          className: 'bg-purple-100 text-purple-800 border-purple-300',
          icon: <XCircle className="w-4 h-4" />
        };
      case 'pending':
      default:
        return {
          className: 'bg-gray-100 text-gray-700 border-gray-300',
          icon: <Clock className="w-4 h-4" />
        };
    }
  };

  // Handle task state colors (legacy state system)
  const getTaskStateStyles = (state) => {
    const stateNumber = parseInt(state?.split('.')[0]);
    
    if (state?.includes('12.')) {
      return {
        className: 'bg-green-100 text-green-800 border-green-300',
        icon: <CheckCircle2 className="w-4 h-4" />
      };
    }
    
    if (state?.includes('1.')) {
      return {
        className: 'bg-blue-100 text-blue-800 border-blue-300',
        icon: <Clock className="w-4 h-4" />
      };
    }
    
    if (stateNumber >= 9) {
      return {
        className: 'bg-green-100 text-green-800 border-green-300',
        icon: <CheckCircle2 className="w-4 h-4" />
      };
    }
    
    return {
      className: 'bg-gray-100 text-gray-700 border-gray-300',
      icon: <Clock className="w-4 h-4" />
    };
  };

  // Get readable state text
  const getReadableState = (state) => {
    if (!state) return 'Unknown';
    
    const stateNumber = parseInt(state.split('.')[0]);
    const stateMap = {
      1: 'Created',
      2: 'Context Analysis',
      3: 'Scope Definition',
      4: 'Requirements',
      5: 'Network Planning',
      6: 'Work Packages',
      7: 'Task Generation',
      8: 'Execution Planning',
      9: 'In Progress',
      10: 'Quality Check',
      11: 'Delivery',
      12: 'Completed'
    };
    
    return stateMap[stateNumber] || 'Unknown';
  };

  // Determine which system to use
  const useStatus = status || (state && getReadableState(state));
  const styles = status ? getExecutionStatusStyles(status) : getTaskStateStyles(state);

  // Size variants
  const sizeClasses = {
    small: 'px-2 py-0.5 text-xs',
    default: 'px-3 py-1 text-sm',
    large: 'px-4 py-2 text-base'
  };

  return (
    <div className={`
      flex items-center gap-1.5 rounded-full border font-medium
      ${styles.className}
      ${sizeClasses[size]}
      ${className}
    `}>
      {showIcon && styles.icon}
      <span>{useStatus}</span>
    </div>
  );
};

export default StatusBadge; 