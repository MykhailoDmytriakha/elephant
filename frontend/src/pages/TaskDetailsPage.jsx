// src/pages/TaskDetailsPage.jsx
import React from 'react';
import { useParams } from 'react-router-dom';
import { ArrowLeft, Trash2, RefreshCw } from 'lucide-react';
import { LoadingSpinner } from '../components/task/TaskComponents';
import { TaskStates } from '../constants/taskStates';
import { getStateColor } from '../constants/taskStates';
import TaskOverview from '../components/task/TaskOverview';
import Analysis from '../components/task/Analysis';
import Metadata from '../components/task/Metadata';
import ApproachFormation from '../components/task/ApproachFormation';
import Typification from '../components/task/Typification';
import ClarificationSection from '../components/task/ClarificationSection';
import Decomposition from '../components/task/Decomposition';
import TaskScopeFormulation from '../components/task/TaskFormulation';
import IFRView from '../components/task/IFRView';
import Breadcrumbs from '../components/task/Breadcrumbs';
import { useTaskDetails } from '../hooks/useTaskDetails';

export default function TaskDetailsPage() {
  const { taskId } = useParams();
  
  // Use our custom hook for all task state and operations
  const {
    // State
    task,
    loading,
    error,
    selectedApproachItems,
    isDecompositionStarted,
    isForceRefreshMode,
    
    // Operations
    loadTask,
    handleBack,
    handleDelete,
    handleFormulate,
    isFormulating,
    handleGenerateIFR,
    isGeneratingIFR,
    handleAnalyze,
    isAnalyzing,
    handleTypify,
    isTypifying,
    handleRegenerateApproaches,
    isRegeneratingApproaches,
    handleClarification,
    isStartingClarificationLoading,
    handleDecompose,
    isDecomposing,
    handleApproachSelectionChange,
    
    // Context gathering
    contextQuestions,
    contextAnswers,
    isLoading: isContextGatheringLoading,
    isSubmitting: isSubmittingAnswers,
    startContextGathering: handleStartContextGathering,
    handleAnswerChange,
    submitAnswers: handleSubmitAnswers
  } = useTaskDetails(taskId);

  if (loading) return <LoadingSpinner />;
  
  // If we have an error but also have task data, don't show the error UI
  // The error has already been shown as a toast notification
  if (!task) {
    if (error) {
      // If task loading failed completely, show a more subtle error UI
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Error Loading Task</h2>
            <p className="text-gray-600 mb-4">{error}</p>
            <div className="flex justify-between">
              <button
                onClick={handleBack}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Go Back to Tasks
              </button>
              <button
                onClick={() => loadTask()}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 flex items-center"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Retry
              </button>
            </div>
          </div>
        </div>
      );
    }
    return <LoadingSpinner />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="sticky top-0 z-50 bg-white border-b border-gray-200">
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="h-16 flex items-center">
              <button
                onClick={handleBack}
                className="mr-4 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div className="flex-1">
                <Breadcrumbs task={task} />
                <h1 className="text-2xl font-bold text-gray-900 mt-1">Task Details</h1>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-gray-600 mr-2">Task State:</span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStateColor(task.state)}`}>{task.state}</span>
                <button
                  onClick={handleDelete}
                  className="text-red-600 hover:text-red-700 flex items-center gap-2"
                >
                  <Trash2 className="w-5 h-5" />
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="col-span-2 space-y-6">
            <TaskOverview
              task={task}
              onStartContextGathering={handleStartContextGathering}
              isContextGatheringLoading={isContextGatheringLoading}
              contextQuestions={contextQuestions}
              contextAnswers={contextAnswers}
              onAnswerChange={handleAnswerChange}
              onSubmitAnswers={handleSubmitAnswers}
              isSubmittingAnswers={isSubmittingAnswers}
              error={error}
              isForceRefreshMode={isForceRefreshMode}
            />

            {task.sub_level === 0 && (
              // defin scope of the task
              <TaskScopeFormulation
                task={task}
                isContextGathered={task.state === TaskStates.CONTEXT_GATHERED || task.state === TaskStates.TASK_FORMATION}
                onFormulate={handleFormulate}
                isFormulating={isFormulating}
                defaultOpen={!(task.scope && task.scope.status === "approved")}
              />
            )}

            {task.scope && task.scope.status === "approved" && (
              <IFRView
                ifr={task.ifr}
                isGeneratingIFR={isGeneratingIFR}
                onGenerateIFR={handleGenerateIFR}
                taskState={task.state}
              />
            )}

            <Analysis
              analysis={task.analysis}
              isContextSufficient={task.is_context_sufficient && task.state === TaskStates.ANALYSIS}
              isAnalyzing={isAnalyzing}
              onAnalyze={handleAnalyze}
            />

            {(task.complexity == null || task.complexity > 1) && (
              <Typification
                typification={task.typification}
                isContextSufficient={task.is_context_sufficient}
                isTypifying={isTypifying}
                onTypify={handleTypify}
                taskState={task.state}
              />
            )}

            {task.complexity > 1 && (
              <ClarificationSection
                taskState={task.state}
                clarification_data={task.clarification_data}
                onStartClarification={() => handleClarification()}
                isStartingClarificationLoading={isStartingClarificationLoading}
                isLoading={loading}
              />
            )}

            <ApproachFormation
              approaches={task.approaches}
              onRegenerateApproaches={handleRegenerateApproaches}
              isRegenerating={isRegeneratingApproaches}
              taskState={task.state}
              onSelectionChange={handleApproachSelectionChange}
              selectedItems={selectedApproachItems}
              isDecompositionStarted={isDecompositionStarted}
            />

            {task.complexity > 1 && (
              <Decomposition
                task={task}
                taskState={task.state}
                isDecomposing={isDecomposing}
                onDecompose={handleDecompose}
                selectedItems={selectedApproachItems}
              />
            )}

            {/* {task.complexity === 1 && (
              <SolutionDevelopment
                task={task}
                taskState={task.state}
                isDecomposing={isDecomposing}
                onDecompose={handleDecompose}
                selectedItems={selectedApproachItems}
              />
            )} */}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <div className="sticky top-24">
              <Metadata task={task} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
