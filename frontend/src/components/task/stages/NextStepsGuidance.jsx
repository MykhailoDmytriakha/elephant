import React from 'react';
import { RefreshCw, Layers, Workflow } from 'lucide-react';

/**
 * Component that provides guidance for next steps in task progression
 * Shows appropriate actions based on current state
 */
const NextStepsGuidance = ({
  anyWorkPackagesExist,
  anyTasksExist,
  isGeneratingAllWork,
  isGeneratingAllTasks,
  loading,
  onGenerateWorkPackages,
  onGenerateTasks,
  className = ""
}) => {
  // Show work packages guidance when they don't exist
  if (!anyWorkPackagesExist) {
    return (
      <div className={`bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4 ${className}`}>
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
            <Layers className="w-4 h-4 text-blue-600" />
          </div>
          <div>
            <h3 className="font-medium text-blue-900 mb-1">Ready to generate work packages!</h3>
            <p className="text-blue-700 text-sm mb-3">
              Your stages are complete with detailed descriptions and expected results. 
              The next step is to break each stage down into specific work packages.
            </p>
            <button
              onClick={onGenerateWorkPackages}
              disabled={loading || isGeneratingAllWork || isGeneratingAllTasks}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isGeneratingAllWork ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Layers className="w-4 h-4" />
              )}
              {isGeneratingAllWork ? 'Generating Work Packages...' : 'Generate Work Packages'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Show tasks guidance when work packages exist but tasks don't
  if (anyWorkPackagesExist && !anyTasksExist) {
    return (
      <div className={`bg-purple-50 border border-purple-200 rounded-lg p-4 mb-4 ${className}`}>
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
            <Workflow className="w-4 h-4 text-purple-600" />
          </div>
          <div>
            <h3 className="font-medium text-purple-900 mb-1">Ready to generate executable tasks!</h3>
            <p className="text-purple-700 text-sm mb-3">
              Great! Your work packages are ready. Now let's break them down into specific executable tasks 
              that can be assigned and tracked.
            </p>
            <button
              onClick={onGenerateTasks}
              disabled={loading || isGeneratingAllWork || isGeneratingAllTasks}
              className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isGeneratingAllTasks ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Workflow className="w-4 h-4" />
              )}
              {isGeneratingAllTasks ? 'Generating Tasks...' : 'Generate Executable Tasks'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Return null if no guidance is needed
  return null;
};

export default NextStepsGuidance; 