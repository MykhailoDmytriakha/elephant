import React from 'react';

/**
 * Progress indicator component for task stages
 * Shows completion status of stages, work packages, and tasks
 */
const StageProgressIndicator = ({ 
  anyWorkPackagesExist, 
  anyTasksExist,
  className = ""
}) => {
  const getIndicatorColor = (condition) => {
    return condition ? 'bg-green-500' : 'bg-amber-400';
  };

  const getTextColor = (condition) => {
    return condition ? 'text-green-700' : 'text-amber-700';
  };

  return (
    <div className={`px-4 py-3 bg-gray-50 border-b border-gray-100 ${className}`}>
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-gray-700">Progress:</span>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-green-700">Stages Complete</span>
          </div>
          
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${getIndicatorColor(anyWorkPackagesExist)}`}></div>
            <span className={getTextColor(anyWorkPackagesExist)}>
              {anyWorkPackagesExist ? 'Work Packages Ready' : 'Work Packages Needed'}
            </span>
          </div>
          
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${
              anyTasksExist ? 'bg-green-500' : 
              anyWorkPackagesExist ? 'bg-amber-400' : 'bg-gray-300'
            }`}></div>
            <span className={
              anyTasksExist ? 'text-green-700' : 
              anyWorkPackagesExist ? 'text-amber-700' : 'text-gray-500'
            }>
              {anyTasksExist ? 'Tasks Ready' : 
               anyWorkPackagesExist ? 'Tasks Pending' : 'Tasks Not Ready'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StageProgressIndicator; 