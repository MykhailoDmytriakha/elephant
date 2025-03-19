// src/components/task/TaskOverview.jsx
import React, { useState, useEffect } from 'react';
import { CollapsibleSection } from './TaskComponents';
import { AlertCircle, Loader2, RefreshCw, Check, HelpCircle } from 'lucide-react';
import { TaskStates } from '../../constants/taskStates';
import ProgressiveQuestionsForm from './ProgressiveQuestionsForm';

// Help tooltip component
const HelpTooltip = ({ text }) => {
  const [showTooltip, setShowTooltip] = useState(false);
  
  return (
    <div className="relative inline-block ml-1">
      <button
        type="button"
        className="text-gray-400 hover:text-gray-600 focus:outline-none"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onClick={() => setShowTooltip(!showTooltip)}
      >
        <HelpCircle className="w-4 h-4" />
      </button>
      {showTooltip && (
        <div className="absolute z-10 w-64 p-2 text-xs text-gray-600 bg-white border border-gray-200 rounded-md shadow-lg top-full mt-1 -left-32">
          {text}
        </div>
      )}
    </div>
  );
};

const TaskOverview = ({ 
  task, 
  onStartContextGathering, 
  isContextGatheringLoading,
  contextQuestions = [],
  isForceRefreshMode
}) => {
  const [currentStep, setCurrentStep] = useState('start');
  
  // Set the current step based on state
  useEffect(() => {
    if (isContextGatheringLoading && !isForceRefreshMode) {
      setCurrentStep('loading');
    } else if (contextQuestions && contextQuestions.length > 0) {
      setCurrentStep('questions');
    } else if (task.is_context_sufficient) {
      setCurrentStep('complete');
    } else {
      setCurrentStep('start');
    }
  }, [isContextGatheringLoading, contextQuestions, task, isForceRefreshMode]);

  const handleStartGathering = () => {
    onStartContextGathering(false);
  };

  const handleForceRefreshContext = () => {
    onStartContextGathering(true);
  };

  const handleRetryContextGathering = () => {
    onStartContextGathering(false);
  };

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      <div className="p-5 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-800">Task Overview</h2>
      </div>
      <div className="p-5">
        <div className="space-y-4">
          {/* Subtask information if applicable */}
          {task.sub_level > 0 && (
            <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 mb-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-200 text-blue-700 text-sm font-medium">{task.sub_level}</span>
                <span className="text-sm text-blue-700 font-medium">Subtask Level</span>
              </div>
              {task.contribution_to_parent_task && (
                <div className="text-sm text-blue-800">
                  <span className="font-medium">Contribution to Parent Task:</span>
                  <p className="mt-1">{task.contribution_to_parent_task}</p>
                </div>
              )}
            </div>
          )}

          {/* Task description */}
          <div>
            <h3 className="text-sm font-medium text-gray-500">Initial user query</h3>
            <p className="mt-1 text-gray-900 whitespace-pre-line">{task.short_description}</p>
          </div>

          {/* Task data */}
          {task.task && (
            <div>
              <h3 className="text-sm font-medium text-gray-500">Task</h3>
              <p className="mt-1 text-gray-900 whitespace-pre-line">{task.task}</p>
            </div>
          )}

          {/* Task context */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-sm font-medium text-gray-500">Context</h3>
              <div className="flex items-center">
                <span className="text-sm text-gray-600 mr-2">Status:</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  task.is_context_sufficient 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {task.is_context_sufficient ? 'Sufficient' : 'Insufficient'}
                </span>
              </div>
            </div>
            
            <p className="mt-1 text-gray-900 whitespace-pre-line">
              {task.context || 'No context provided yet.'}
            </p>
          </div>

          {/* Task metadata */}
          {task.level && (
            <div>
              <h3 className="text-sm font-medium text-gray-500">Level</h3>
              <p className="mt-1 text-gray-900">{task.level}</p>
            </div>
          )}

          {task.eta_to_complete && (
            <div>
              <h3 className="text-sm font-medium text-gray-500">ETA to Complete</h3>
              <p className="mt-1 text-gray-900">{task.eta_to_complete}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TaskOverview;
