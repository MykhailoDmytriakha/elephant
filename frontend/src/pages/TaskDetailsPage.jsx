// src/pages/TaskDetailsPage.jsx
import React from 'react';
import { useParams } from 'react-router-dom';
import { ArrowLeft, Trash2, RefreshCw } from 'lucide-react';
import { LoadingSpinner } from '../components/task/TaskComponents';
import { TaskStates } from '../constants/taskStates';
import { getStateColor } from '../constants/taskStates';
import TaskOverview from '../components/task/TaskOverview';
import Metadata from '../components/task/Metadata';
import TaskScope from '../components/task/scope/TaskScope';
import IFRView from '../components/task/IFRView';
import TaskRequirements from '../components/task/requirements/TaskRequirements';
import TaskContext from '../components/task/context/TaskContext';
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
    isForceRefreshMode,
    
    // Operations
    loadTask,
    handleBack,
    handleDelete,
    handleGenerateIFR,
    isGeneratingIFR,
    handleGenerateRequirements,
    isGeneratingRequirements,
    
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
      <header className="sticky top-0 z-50 bg-white border-b border-gray-200">
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
      </header>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="col-span-2 space-y-6">
            <TaskOverview
              task={task}
            />

            <TaskContext
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

            {task.sub_level === 0 && task.is_context_sufficient &&(
              // defin scope of the task
              <TaskScope
                task={task}
                isContextGathered={task.is_context_sufficient}
                defaultOpen={!(task.scope && task.scope.status === "approved")}
              />
            )}

            {task.scope && task.scope.status === "approved" && (
              <IFRView
                ifr={task.ifr}
                isGeneratingIFR={isGeneratingIFR}
                onGenerateIFR={handleGenerateIFR}
                taskState={task.state}
                defaultOpen={!(task.requirements && Object.keys(task.requirements).length > 0)}
                isCompleted={task.requirements && Object.keys(task.requirements).length > 0}
              />
            )}

            {task.ifr && (
              <TaskRequirements
                requirements={task.requirements}
                isGeneratingRequirements={isGeneratingRequirements}
                onGenerateRequirements={handleGenerateRequirements}
                taskState={task.state}
              />
            )}
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
