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
  contextAnswers = {},
  onAnswerChange,
  onSubmitAnswers,
  isSubmittingAnswers = false,
  error = null,
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

        <div className="mt-6">
          <CollapsibleSection 
            title={
              <div className="flex items-center">
                <span>Context Gathering</span>
                {task.is_context_sufficient && (
                  <span className="ml-2 text-xs bg-green-100 text-green-800 py-0.5 px-2 rounded-full">
                    Complete
                  </span>
                )}
              </div>
            } 
            defaultOpen={!task.is_context_sufficient}
          >
            {/* Initial state - show explanation and start button */}
            {currentStep === 'start' && (
              <div className="space-y-4">
                <div className="bg-blue-50 border border-blue-100 rounded-lg p-4">
                  <h3 className="font-medium text-blue-800 text-base mb-2 flex items-center">
                    Context Gathering 
                    <HelpTooltip text="Context gathering helps us understand your task better so we can provide the most relevant assistance." />
                  </h3>
                  
                  <p className="text-blue-700 text-sm mb-3">
                    {task.context_answers && task.context_answers.length > 0 
                      ? "We need some additional information to complete the context gathering process."
                      : "Before we can analyze and break down your task, we need to gather more context about what you're trying to accomplish."}
                  </p>
                  
                  <p className="text-blue-700 text-sm mb-4">
                    {task.context_answers && task.context_answers.length > 0 
                      ? `You've already provided ${task.context_answers.length} answers. Let's continue to ensure we fully understand your requirements.`
                      : "This process will ask you a series of questions to help us understand your task better."}
                  </p>
                  
                  <button
                    onClick={handleStartGathering}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    {task.context_answers && task.context_answers.length > 0 ? "Continue Context Gathering" : "Start Context Gathering"}
                  </button>
                </div>
                
                {/* Display existing context answers when available but context is not sufficient */}
                {currentStep === 'start' && task.context_answers && task.context_answers.length > 0 && !task.is_context_sufficient && (
                  <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm mt-4">
                    <CollapsibleSection 
                      title={<span className="text-sm font-medium text-gray-700">Previously Provided Information ({task.context_answers.length})</span>}
                      defaultOpen={false}
                    >
                      <ul className="list-disc pl-5 space-y-3 mt-2">
                        {task.context_answers.map((item, index) => (
                          <li key={index} className="pb-2">
                            <div className="font-medium text-gray-800 mb-1">{item.question}</div>
                            <div className="text-gray-700 ml-2 border-l-2 border-gray-200 pl-3">
                              {item.answer}
                            </div>
                          </li>
                        ))}
                      </ul>
                    </CollapsibleSection>
                  </div>
                )}
                
                {task.state === TaskStates.CONTEXT_GATHERING && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mt-4">
                    <div className="flex items-start">
                      <AlertCircle className="w-5 h-5 text-yellow-500 mt-0.5 mr-3 flex-shrink-0" />
                      <div className="flex-1">
                        <h4 className="text-sm font-medium text-yellow-800 mb-1">Context Gathering Required</h4>
                        <p className="text-sm text-yellow-700">
                          {task.context_answers && task.context_answers.length > 0 
                            ? "You've made progress, but additional context is still needed before we can proceed with analysis and solution development."
                            : "This task requires additional context before we can proceed with analysis and solution development."}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
            
            {/* Loading state */}
            {currentStep === 'loading' && (
              <div className="flex flex-col items-center justify-center py-12">
                <Loader2 className="w-12 h-12 text-blue-600 animate-spin mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-1">Analyzing Your Task</h3>
                <p className="text-gray-500 text-center max-w-md">
                  We're analyzing your task to determine what additional context is needed. This should only take a moment...
                </p>
              </div>
            )}
            
            {/* Questions state - progressive form */}
            {currentStep === 'questions' && contextQuestions && contextQuestions.length > 0 && (
              <ProgressiveQuestionsForm
                questions={contextQuestions}
                answers={contextAnswers}
                onAnswerChange={onAnswerChange}
                onSubmit={onSubmitAnswers}
                isSubmitting={isSubmittingAnswers}
                error={error}
                onRetry={handleRetryContextGathering}
                isForceRefresh={isForceRefreshMode}
              />
            )}
            
            {/* Completed state */}
            {currentStep === 'complete' && task.is_context_sufficient && (
              <div className="space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-start">
                    <Check className="w-5 h-5 text-green-500 mt-0.5 mr-3 flex-shrink-0" />
                    <div className="flex-1">
                      <h4 className="text-sm font-medium text-green-800 mb-1">Context Gathering Complete</h4>
                      <p className="text-sm text-green-700 mb-3">
                        We have gathered sufficient context for your task. You can now proceed with analysis and planning.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Refresh Button */}
                <div className="mt-4">
                  <button
                    onClick={handleForceRefreshContext}
                    disabled={isContextGatheringLoading}
                    className={`px-4 py-2 flex items-center text-sm text-blue-700 bg-blue-50 rounded-md hover:bg-blue-100 border border-blue-200 ${
                      isContextGatheringLoading ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                  >
                    {isContextGatheringLoading && isForceRefreshMode ? (
                      <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Refreshing...</>
                    ) : (
                      <><RefreshCw className="w-4 h-4 mr-2" />Refresh Context</>
                    )}
                  </button>
                  <p className="text-xs text-gray-500 mt-1">
                    Click to re-summarize the context and update task details.
                  </p>
                </div>
                
                {/* Display list of questions and answers */}
                <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Questions and Answers</h4>
                  {task.context_answers && task.context_answers.length > 0 ? (
                    <ul className="list-disc pl-5 space-y-3">
                      {task.context_answers.map((item, index) => (
                        <li key={index} className="pb-2">
                          <div className="font-medium text-gray-800 mb-1">{item.question}</div>
                          <div className="text-gray-700 ml-2 border-l-2 border-gray-200 pl-3">
                            {item.answer}
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-gray-500 italic">No answers stored for this task.</p>
                  )}
                </div>
              </div>
            )}
            
            {/* Error state */}
            {error && !contextQuestions.length && currentStep !== 'questions' && (
              <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-lg">
                <div className="flex items-start">
                  <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 mr-3 flex-shrink-0" />
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-red-800 mb-1">Error Gathering Context</h4>
                    <p className="text-sm text-red-700 mb-3">{error}</p>
                    <button 
                      onClick={handleRetryContextGathering}
                      className="px-3 py-1.5 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-sm flex items-center gap-1 w-fit"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      Try Again
                    </button>
                  </div>
                </div>
              </div>
            )}
          
          </CollapsibleSection>
        </div>
      </div>
    </div>
  );
};

export default TaskOverview;
