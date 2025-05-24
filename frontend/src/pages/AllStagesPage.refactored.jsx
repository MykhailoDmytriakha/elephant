import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCcw, MessageCircle, Minimize2 } from 'lucide-react';

// UI Components
import { LoadingSpinner, ErrorDisplay } from '../components/ui';

// Business Components
import StageProgressIndicator from '../components/task/stages/StageProgressIndicator';
import NextStepsGuidance from '../components/task/stages/NextStepsGuidance';
import StagesList from '../components/task/stages/StagesList';
import TaskStreamingChat from '../components/task/TaskStreamingChat';

// Hooks
import { useTaskDetails } from '../hooks/useTaskDetails';
import { useExpansionState } from '../hooks/useExpansionState';
import { useChatState } from '../hooks/useChatState';

// Services
import { useTaskOperations } from '../services/taskOperations';

// Utils
import { checkWorkPackagesExist, checkTasksExist } from '../utils/statusUtils';

// Context
import { useToast } from '../components/common/ToastProvider';

/**
 * Refactored AllStagesPage - Demonstrates modular approach
 * 
 * Key improvements:
 * - Extracted UI components for reusability
 * - Separated business logic into services
 * - Used custom hooks for state management
 * - Reduced component size from 1000+ lines to ~150 lines
 */
export default function AllStagesPageRefactored() {
  const { taskId } = useParams();
  const navigate = useNavigate();
  const toast = useToast();

  // Hooks for state management
  const { task, loading, error, loadTask, setTask } = useTaskDetails(taskId);
  const stageExpansion = useExpansionState({}, true);
  const workExpansion = useExpansionState();
  const taskExpansion = useExpansionState();
  const chatState = useChatState();

  // Services for business logic
  const taskOps = useTaskOperations(toast);

  // UI state
  const [isGeneratingAllWork, setIsGeneratingAllWork] = React.useState(false);
  const [isGeneratingAllTasks, setIsGeneratingAllTasks] = React.useState(false);
  const [isChatExpanded, setIsChatExpanded] = React.useState(true);

  // Derived state
  const anyWorkPackagesExist = checkWorkPackagesExist(task?.network_plan?.stages);
  const anyTasksExist = checkTasksExist(task?.network_plan?.stages);

  // Initialize stage expansion when task loads
  useEffect(() => {
    if (task?.network_plan?.stages) {
      const stageIds = task.network_plan.stages.map(stage => stage.id);
      stageExpansion.initializeExpansion(stageIds, true);
    }
  }, [task]);

  // Event handlers
  const handleBack = () => navigate(`/tasks/${taskId}`);
  
  const handleGenerateWorkPackages = async () => {
    setIsGeneratingAllWork(true);
    try {
      await taskOps.generateWorkPackages(taskId, async () => {
        const updatedTask = await taskOps.loadTaskData(taskId);
        if (updatedTask?.network_plan) {
          setTask(prevTask => ({
            ...prevTask,
            network_plan: updatedTask.network_plan
          }));
        }
      });
    } finally {
      setIsGeneratingAllWork(false);
    }
  };

  const handleGenerateTasks = async () => {
    setIsGeneratingAllTasks(true);
    try {
      await taskOps.generateTasks(taskId, async () => {
        const updatedTask = await taskOps.loadTaskData(taskId);
        if (updatedTask?.network_plan) {
          setTask(prevTask => ({
            ...prevTask,
            network_plan: updatedTask.network_plan
          }));
        }
      });
    } finally {
      setIsGeneratingAllTasks(false);
    }
  };

  const handleSendChatMessage = async (message, callbacks, messageHistory) => {
    chatState.startStreaming();
    chatState.addMessage({ role: 'user', content: message });

    try {
      const customCallbacks = {
        onChunk: (chunk) => {
          if (chunk.includes('⚠️ Error:')) {
            const cleanError = chunk.replace('⚠️ Error:', '').trim();
            chatState.setErrorState(cleanError);
            return;
          }
          chatState.updateStreamingMessage(chunk);
          callbacks?.onChunk?.(chunk);
        },
        onComplete: (fullResponse) => {
          chatState.addMessage({ role: 'assistant', content: fullResponse });
          chatState.clearStreamingMessage();
          chatState.stopStreaming();
          callbacks?.onComplete?.(fullResponse);
        },
        onError: (error) => {
          chatState.setErrorState(error.message || 'Unknown error');
          callbacks?.onError?.(error);
        }
      };

      await taskOps.sendChatMessage(taskId, message, customCallbacks, messageHistory);
    } catch (error) {
      chatState.setErrorState(error.message);
    }
  };

  // Loading and error states
  if (loading && !isGeneratingAllWork && !isGeneratingAllTasks) {
    return <LoadingSpinner message="Loading task data..." />;
  }

  if (error) {
    return (
      <ErrorDisplay
        message={`Task data could not be loaded: ${error}`}
        onRetry={loadTask}
      />
    );
  }

  if (!task?.network_plan?.stages) {
    return (
      <ErrorDisplay
        message="No network plan or stages available for this task."
        onRetry={loadTask}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="h-16 flex items-center justify-between">
            <div className="flex items-center">
              <button onClick={handleBack} className="mr-4 text-gray-600 hover:text-gray-900 transition-colors">
                <ArrowLeft className="w-5 h-5" />
              </button>
              <h1 className="text-2xl font-bold text-gray-900">
                {task.shortDescription ? (
                  <span className="truncate max-w-md inline-block" title={task.shortDescription}>
                    {task.shortDescription}
                  </span>
                ) : (
                  'Task Breakdown'
                )}
              </h1>
            </div>
            
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsChatExpanded(!isChatExpanded)}
                className={`flex items-center gap-2 px-4 py-2 rounded-md transition-colors ${
                  isChatExpanded 
                    ? 'bg-indigo-600 text-white hover:bg-indigo-700' 
                    : 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200 ring-2 ring-indigo-300 ring-opacity-50'
                }`}
              >
                {isChatExpanded ? <Minimize2 className="w-4 h-4" /> : <MessageCircle className="w-4 h-4" />}
                {isChatExpanded ? 'Hide Assistant' : 'Ask Assistant'}
              </button>
              
              <button
                onClick={loadTask}
                disabled={loading || isGeneratingAllWork || isGeneratingAllTasks}
                className="flex items-center gap-2 px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors disabled:opacity-50"
              >
                <RefreshCcw className="w-4 h-4" />
                Sync Data
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Content with Split Panel Layout */}
      <div className="flex flex-grow h-[calc(100vh-4rem)] overflow-hidden">
        {/* Left Panel - Task Breakdown */}
        <div className={`${isChatExpanded ? 'w-1/2' : 'w-full'} h-full overflow-hidden flex flex-col`}>
          <div className="flex-grow bg-white shadow overflow-hidden flex flex-col">
            {/* Progress Indicator */}
            <StageProgressIndicator 
              anyWorkPackagesExist={anyWorkPackagesExist}
              anyTasksExist={anyTasksExist}
            />
            
            {/* Stages Content */}
            <div className="flex-grow overflow-y-auto p-4 space-y-4">
              {/* Next Steps Guidance */}
              <NextStepsGuidance
                anyWorkPackagesExist={anyWorkPackagesExist}
                anyTasksExist={anyTasksExist}
                isGeneratingAllWork={isGeneratingAllWork}
                isGeneratingAllTasks={isGeneratingAllTasks}
                loading={loading}
                onGenerateWorkPackages={handleGenerateWorkPackages}
                onGenerateTasks={handleGenerateTasks}
              />
              
              {/* Stages List */}
              <StagesList
                stages={task.network_plan.stages}
                stageExpansion={stageExpansion}
                workExpansion={workExpansion}
                taskExpansion={taskExpansion}
                onNavigateToStage={(stageId) => {
                  navigate(`/tasks/${taskId}/stages/${stageId}`, {
                    state: {
                      stage: task.network_plan.stages.find(s => s.id === stageId),
                      taskShortDescription: task.shortDescription,
                      taskId: taskId,
                      task: { network_plan: { stages: task.network_plan.stages } }
                    }
                  });
                }}
              />
            </div>
          </div>
        </div>
        
        {/* Right Panel - Chat Assistant */}
        {isChatExpanded && (
          <div className="w-1/2 h-full border-l border-gray-200 flex flex-col overflow-hidden">
            <TaskStreamingChat 
              taskId={taskId}
              onSendMessage={handleSendChatMessage}
              isLoading={chatState.isStreaming}
              onResetChat={chatState.resetChat}
              chatHistory={chatState.chatHistory}
              streamingMessage={chatState.streamingMessage}
              error={chatState.error}
              isStreaming={chatState.isStreaming}
              isExternallyManaged={true}
            />
          </div>
        )}
      </div>
    </div>
  );
} 