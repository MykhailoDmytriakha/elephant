import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, ChevronDown, ChevronRight, Layers, Workflow, Minimize2, Maximize2, MessageCircle } from 'lucide-react';
import { LoadingSpinner, ErrorDisplay } from '../components/task/TaskComponents';
import { useTaskDetails } from '../hooks/useTaskDetails';
import { generateAllWorkPackages, generateTasksForAllStages, chatWithTaskAssistant, loadTaskDataOnly } from '../utils/api';
import { useToast } from '../components/common/ToastProvider';
import TaskStreamingChat from '../components/task/TaskStreamingChat';

/**
 * A dedicated page that displays all stages with their sublevels (work packages, tasks, subtasks)
 * in an expandable hierarchical view with a chat assistant panel
 */
export default function AllStagesPage() {
  const { taskId } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  
  // Track expanded states
  const [expandedStages, setExpandedStages] = useState({});
  const [expandedWorks, setExpandedWorks] = useState({});
  const [expandedTasks, setExpandedTasks] = useState({});
  const [isGeneratingAllWork, setIsGeneratingAllWork] = useState(false);
  const [isGeneratingAllTasks, setIsGeneratingAllTasks] = useState(false);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [isChatExpanded, setIsChatExpanded] = useState(true);
  
  // Store chat history at this level to prevent it from resetting during task updates
  const [chatHistory, setChatHistory] = useState([]);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [chatError, setChatError] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);

  // Use the task details hook for fetching data
  const {
    task,
    loading,
    error,
    loadTask,
    setTask,
  } = useTaskDetails(taskId);

  // Initialize all stages as expanded by default
  useEffect(() => {
    if (task?.network_plan?.stages) {
      const stageMap = {};
      task.network_plan.stages.forEach(stage => {
        stageMap[stage.id] = true;
      });
      setExpandedStages(stageMap);
    }
  }, [task]);

  const handleBack = () => {
    navigate(`/tasks/${taskId}`);
  };

  // Toggle expansion of a stage
  const toggleStage = (stageId) => {
    setExpandedStages(prev => ({
      ...prev,
      [stageId]: !prev[stageId]
    }));
  };

  // Toggle expansion of a work package
  const toggleWork = (workId) => {
    setExpandedWorks(prev => ({
      ...prev,
      [workId]: !prev[workId]
    }));
  };

  // Toggle expansion of a task
  const toggleTask = (taskId) => {
    setExpandedTasks(prev => ({
      ...prev,
      [taskId]: !prev[taskId]
    }));
  };

  // Navigate to stage details page
  const navigateToStage = (stageId) => {
    navigate(`/tasks/${taskId}/stages/${stageId}`, {
      state: {
        stage: task.network_plan.stages.find(s => s.id === stageId),
        taskShortDescription: task.shortDescription,
        taskId: taskId,
        task: { network_plan: { stages: task.network_plan.stages } }
      }
    });
  };

  // Handler for generating work packages for all stages
  const handleGenerateAllWorkPackages = async () => {
    if (!taskId) return;
    setIsGeneratingAllWork(true);
    try {
      await generateAllWorkPackages(taskId);
      toast.showSuccess('Successfully generated work packages for all stages.');
      // Update only task stages data, not the entire UI
      await loadTaskStagesOnly();
    } catch (error) {
      console.error("Error generating all work packages:", error);
      toast.showError(`Failed to generate work packages: ${error.message || 'Unknown error'}`);
    } finally {
      setIsGeneratingAllWork(false);
    }
  };

  // Handler for generating tasks for all stages
  const handleGenerateTasksForAllStages = async () => {
    if (!taskId || !anyWorkPackagesExist) return;
    setIsGeneratingAllTasks(true);
    try {
      await generateTasksForAllStages(taskId);
      toast.showSuccess('Successfully generated tasks for all stages.');
      // Update only task stages data, not the entire UI
      await loadTaskStagesOnly();
    } catch (error) {
      console.error("Error generating tasks for all stages:", error);
      toast.showError(`Failed to generate tasks: ${error.message || 'Unknown error'}`);
    } finally {
      setIsGeneratingAllTasks(false);
    }
  };

  // New function to load only the task stages without affecting the chat panel
  const loadTaskStagesOnly = async () => {
    if (!taskId) return;
    try {
      const updatedTask = await loadTaskDataOnly(taskId);
      if (updatedTask && updatedTask.network_plan) {
        // Update only the relevant parts of the task state, keeping chat state intact
        setTask(prevTask => ({
          ...prevTask,
          network_plan: updatedTask.network_plan
        }));
      }
    } catch (error) {
      console.error("Error loading task stages:", error);
      toast.showError(`Failed to load task stages: ${error.message || 'Unknown error'}`);
    }
  };

  // Handler for chat messages
  const handleSendChatMessage = async (message, callbacks, messageHistory) => {
    if (!taskId) return;
    setIsChatLoading(true);
    setChatError(null);
    setIsStreaming(true);
    
    const isEdit = messageHistory.length < chatHistory.length && 
                   chatHistory[messageHistory.length]?.role === 'user' &&
                   chatHistory[messageHistory.length + 1]?.role === 'assistant';
                   
    let currentChatHistory = chatHistory;
    let editIndex = -1;
    
    if (isEdit) {
        // This is an edit, update the history
        editIndex = messageHistory.length; // The index of the message being edited
        console.log(`Detected edit at index: ${editIndex}`);
        // Truncate the history and replace the edited message
        currentChatHistory = [
            ...chatHistory.slice(0, editIndex),
            { role: 'user', content: message } // Replace with the new message content
        ];
        // Update the state immediately to reflect the truncated history + edited message
        setChatHistory(currentChatHistory);
        // We will add the assistant's response later
        setStreamingMessage(''); // Clear any previous streaming message
    } else {
        // This is a new message, add user message to chat history
        const userMessage = { role: 'user', content: message };
        setChatHistory(prev => [...prev, userMessage]);
        currentChatHistory = [...chatHistory, userMessage]; // Use updated history for API call
    }
    
    try {
      const customCallbacks = {
        onChunk: (chunk) => {
          setStreamingMessage(prev => prev + chunk);
          if (callbacks?.onChunk) callbacks.onChunk(chunk);
        },
        onComplete: (fullResponse) => {
          setChatHistory(prev => [...prev, { role: 'assistant', content: fullResponse }]);
          setStreamingMessage('');
          setIsStreaming(false);
          if (callbacks?.onComplete) callbacks.onComplete(fullResponse);
        },
        onError: (error) => {
          console.error("Error in chat:", error);
          const errorMessage = error.message || 'Unknown error';
          setChatError(errorMessage);
          setIsStreaming(false);
          setChatHistory(prev => [...prev, { 
            role: 'system', 
            content: `Error: ${errorMessage}`
          }]);
          if (callbacks?.onError) callbacks.onError(error);
        }
      };
      
      // Use the potentially truncated history for the API call
      const historyForApi = currentChatHistory.map(msg => ({
          role: msg.role,
          content: msg.content
      }));
      
      await chatWithTaskAssistant(taskId, message, customCallbacks, historyForApi);
    } catch (error) {
      console.error("Error in chat handling:", error);
      const errorMessage = error.message || 'Unknown error';
      setChatError(errorMessage);
      setIsStreaming(false);
      toast.showError(`Chat error: ${errorMessage}`);
      // Ensure the system error message is added to the potentially updated history
      setChatHistory(prev => [...prev, { 
        role: 'system', 
        content: `Error: ${errorMessage}`
      }]);
    } finally {
      // Don't set isLoading to false here if streaming is still happening
      // It will be set in onComplete/onError
      // Set loading to false only if not streaming anymore (e.g., initial error)
      if (!isStreaming) {
           setIsChatLoading(false); 
      }
       // Ensure streaming message is cleared if an error occurred before completion
       // setStreamingMessage(''); // This is handled in onComplete/onError now
    }
  };
  
  // Handler to reset chat
  const handleResetChat = () => {
    setChatHistory([]);
    setStreamingMessage('');
    setChatError(null);
    setIsStreaming(false);
  };

  // Check if any stage already has work packages
  const anyWorkPackagesExist = task?.network_plan?.stages?.some(
    stage => stage.work_packages && stage.work_packages.length > 0
  ) ?? false;

  // Check if any work package already has tasks
  const anyTasksExist = task?.network_plan?.stages?.some(
    stage => stage.work_packages?.some(
      work => work.tasks && work.tasks.length > 0
    )
  ) ?? false;

  // Toggle chat panel expanded state
  const toggleChatExpanded = () => {
    setIsChatExpanded(!isChatExpanded);
  };

  if (loading && !isGeneratingAllWork && !isGeneratingAllTasks) return <LoadingSpinner message="Loading task data..." />;

  if (error) {
    return (
      <ErrorDisplay
        message={`Task data could not be loaded: ${error}`}
        onRetry={loadTask}
      />
    );
  }

  if (!task || !task.network_plan || !task.network_plan.stages) {
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
              <button
                onClick={handleBack}
                className="mr-4 text-gray-600 hover:text-gray-900 transition-colors"
              >
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
              {/* Generate All Work Packages Button */}
              <button
                onClick={handleGenerateAllWorkPackages}
                disabled={loading || isGeneratingAllWork || isGeneratingAllTasks}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md transition-colors ${
                  isGeneratingAllWork
                    ? 'bg-blue-400 text-white cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                } disabled:opacity-60 disabled:cursor-not-allowed`}
                title={anyWorkPackagesExist ? "Regenerate Work Packages for all stages in this task" : "Generate Work Packages for all stages in this task"}
              >
                {isGeneratingAllWork ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : anyWorkPackagesExist ? (
                  <RefreshCw className="w-4 h-4" />
                ) : (
                  <Layers className="w-4 h-4" />
                )}
                {isGeneratingAllWork 
                  ? 'Generating...' 
                  : (anyWorkPackagesExist ? 'Regen All Work Pkgs' : 'Gen All Work Pkgs')
                }
              </button>
              {/* Generate Tasks for All Stages Button */}
              <button
                onClick={handleGenerateTasksForAllStages}
                disabled={loading || isGeneratingAllWork || isGeneratingAllTasks || !anyWorkPackagesExist}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md transition-colors ${
                   isGeneratingAllTasks
                    ? 'bg-purple-400 text-white cursor-not-allowed'
                    : !anyWorkPackagesExist
                      ? 'bg-purple-300 text-white cursor-not-allowed'
                      : 'bg-purple-600 text-white hover:bg-purple-700'
                } disabled:opacity-60 disabled:cursor-not-allowed`}
                title={
                    !anyWorkPackagesExist 
                        ? "Generate Work Packages first" 
                        : anyTasksExist
                            ? "Regenerate Executable Tasks for all work packages in all stages"
                            : "Generate Executable Tasks for all work packages in all stages"
                }
              >
                {isGeneratingAllTasks ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                ) : anyTasksExist ? (
                    <RefreshCw className="w-4 h-4" />
                ) : (
                    <Workflow className="w-4 h-4" />
                )}
                {isGeneratingAllTasks
                    ? 'Generating...' 
                    : anyTasksExist 
                        ? 'Regen All Tasks'
                        : 'Gen All Tasks'
                }
              </button>
              {/* Toggle Chat Button */}
              <button
                onClick={toggleChatExpanded}
                className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
                title={isChatExpanded ? "Hide the assistant panel" : "Show the assistant panel to ask questions"}
              >
                {isChatExpanded ? (
                  <Minimize2 className="w-4 h-4" />
                ) : (
                  <MessageCircle className="w-4 h-4" />
                )}
                {isChatExpanded ? 'Hide Assistant' : 'Ask Questions'}
              </button>
              {/* Refresh Button - Only shown in the header when chat is collapsed */}
              {!isChatExpanded && (
                <button
                  onClick={loadTask}
                  disabled={loading || isGeneratingAllWork || isGeneratingAllTasks}
                  className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <RefreshCw className="w-4 h-4" />
                  Refresh
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Content with Split Panel Layout - Fixed height for the area below header */}
      <div className="flex flex-grow h-[calc(100vh-4rem)] overflow-hidden">
        {/* Left Panel - Task Breakdown */}
        <div className={`${isChatExpanded ? 'w-1/2' : 'w-full'} h-full overflow-hidden flex flex-col`}>
          {/* Single container with proper scrolling - removed margins */}
          <div className="flex-grow bg-white shadow overflow-hidden flex flex-col">
            {/* Task Stages Header - Fixed */}
            <div className="flex-shrink-0 flex items-center justify-between border-b border-gray-200 px-4 py-3">
              <div className="flex items-center gap-2">
                <Layers className="w-5 h-5 text-blue-600" />
                <h2 className="font-medium text-gray-800">Task Stages</h2>
              </div>
              {/* Only show refresh button in the panel when chat is expanded 
                  (since the main refresh button is hidden in this case) */}
              {isChatExpanded && (
                <button
                  onClick={loadTask}
                  disabled={loading || isGeneratingAllWork || isGeneratingAllTasks}
                  className="text-gray-500 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Refresh stages"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              )}
            </div>
            
            {/* Stage List - Scrollable */}
            <div className="flex-grow overflow-y-auto p-4 space-y-4">
              <div className="space-y-2">
                {task.network_plan.stages.map((stage, stageIndex) => (
                  <div key={stage.id} className="border-2 border-indigo-300 rounded-lg overflow-hidden">
                    {/* Stage Header */}
                    <div 
                      className="flex items-center justify-between bg-indigo-50 p-3 cursor-pointer hover:bg-indigo-100"
                      onClick={() => toggleStage(stage.id)}
                    >
                      <div className="flex items-center gap-2">
                        {expandedStages[stage.id] ? (
                          <ChevronDown className="w-5 h-5 text-gray-600" />
                        ) : (
                          <ChevronRight className="w-5 h-5 text-gray-600" />
                        )}
                        <span className="font-medium">
                          {stageIndex + 1}. {stage.name || stage.title || stage.description?.slice(0, 40) + "..." || `Stage ${stage.id}`}
                          <span className="ml-2 text-xs text-gray-500">ID: {stage.id}</span>
                        </span>
                      </div>
                      <div className="flex gap-2">
                        <span className="text-xs bg-blue-100 text-blue-800 py-0.5 px-2 rounded-full">
                          {stage.work_packages?.length || 0} Work Packages
                        </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigateToStage(stage.id);
                          }}
                          className="text-xs bg-gray-200 text-gray-700 py-0.5 px-2 rounded hover:bg-gray-300"
                        >
                          View Details
                        </button>
                      </div>
                    </div>
                    
                    {/* Stage Content (Work Packages) */}
                    {expandedStages[stage.id] && (
                      <div className="pl-6 pr-3 py-3 border-t border-gray-200">
                        {/* Stage Description */}
                        {stage.description && (
                          <div className="mb-3 text-sm text-gray-700 p-2 bg-gray-50 rounded">
                            <span className="font-medium">Description:</span> {stage.description}
                          </div>
                        )}
                        
                        {/* Stage Additional Details */}
                        <div className="mb-3 bg-white p-2 rounded border border-gray-200 text-xs">
                          <div className="grid grid-cols-2 gap-2">
                            {stage.sequence_order !== undefined && (
                              <div>
                                <span className="font-medium">Sequence:</span> {stage.sequence_order}
                              </div>
                            )}
                            {stage.status && (
                              <div>
                                <span className="font-medium">Status:</span> 
                                <span className={`ml-1 px-1.5 py-0.5 rounded ${
                                  stage.status === 'Completed' ? 'bg-green-200 text-green-800 border border-green-300' : 
                                  stage.status === 'Failed' ? 'bg-red-200 text-red-800 border border-red-300' : 
                                  stage.status === 'In Progress' ? 'bg-yellow-200 text-yellow-800 border border-yellow-300' : 
                                  stage.status === 'Waiting' ? 'bg-blue-200 text-blue-800 border border-blue-300' :
                                  stage.status === 'Cancelled' ? 'bg-purple-200 text-purple-800 border border-purple-300' :
                                  'bg-gray-200 text-gray-700 border border-gray-300'
                                }`}>
                                  {stage.status}
                                </span>
                              </div>
                            )}
                            {stage.started_at && (
                              <div>
                                <span className="font-medium">Started:</span> {new Date(stage.started_at).toLocaleString()}
                              </div>
                            )}
                            {stage.completed_at && (
                              <div>
                                <span className="font-medium">Completed:</span> {new Date(stage.completed_at).toLocaleString()}
                              </div>
                            )}
                          </div>
                          
                          {/* Dependencies section for stages if applicable */}
                          {stage.dependencies && stage.dependencies.length > 0 && (
                            <div className="mt-2">
                              <span className="font-medium">Dependencies:</span>
                              <div className="flex flex-wrap gap-1 mt-1">
                                {stage.dependencies.map(dep => (
                                  <span key={dep} className="bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded text-xs">
                                    {dep}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {/* Additional stage information if available */}
                          {stage.metadata && Object.keys(stage.metadata).length > 0 && (
                            <div className="mt-2">
                              <span className="font-medium">Additional Info:</span>
                              <div className="mt-1 grid grid-cols-2 gap-x-4 gap-y-1">
                                {Object.entries(stage.metadata).map(([key, value]) => (
                                  <div key={key} className="text-xs">
                                    <span className="font-medium">{key}:</span> {typeof value === 'object' ? JSON.stringify(value) : value}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {/* Result/Error display for stages if applicable */}
                          {stage.result && (
                            <div className="mt-2">
                              <span className="font-medium">Result:</span>
                              <div className="mt-1 p-1 bg-gray-50 rounded border border-gray-300 max-h-24 overflow-y-auto">
                                {stage.result}
                              </div>
                            </div>
                          )}
                          
                          {stage.error_message && (
                            <div className="mt-2">
                              <span className="font-medium text-red-600">Error:</span>
                              <div className="mt-1 p-1 bg-red-50 rounded border border-red-200 max-h-24 overflow-y-auto text-red-800">
                                {stage.error_message}
                              </div>
                            </div>
                          )}
                        </div>
                        
                        {/* If no work packages */}
                        {(!stage.work_packages || stage.work_packages.length === 0) && (
                          <div className="text-sm text-gray-500 italic p-2">
                            No work packages generated yet.
                          </div>
                        )}
                        
                        {/* Work packages list */}
                        <div className="space-y-2">
                          {stage.work_packages?.map((work, workIndex) => (
                            <div key={work.id} className="border-2 border-blue-300 rounded-lg overflow-hidden">
                              {/* Work content */}
                              {/* Work Package Header */}
                              <div 
                                className="flex items-center justify-between bg-blue-50 p-2 cursor-pointer hover:bg-blue-100"
                                onClick={() => toggleWork(work.id)}
                              >
                                <div className="flex items-center gap-2">
                                  {expandedWorks[work.id] ? (
                                    <ChevronDown className="w-4 h-4 text-gray-600" />
                                  ) : (
                                    <ChevronRight className="w-4 h-4 text-gray-600" />
                                  )}
                                  <span className="font-medium text-sm">
                                    {stageIndex + 1}.{workIndex + 1} {work.name || work.title || work.description?.slice(0, 30) + "..." || `Work ${work.id}`}
                                    <span className="ml-2 text-xs text-gray-500">ID: {work.id}</span>
                                  </span>
                                </div>
                                <span className="text-xs bg-green-100 text-green-800 py-0.5 px-2 rounded-full">
                                  {work.tasks?.length || 0} Tasks
                                </span>
                              </div>
                              
                              {/* Work Package Content (Tasks) */}
                              {expandedWorks[work.id] && (
                                <div className="pl-6 pr-3 py-2 border-t border-gray-200">
                                  {/* Work Package Description */}
                                  {work.description && (
                                    <div className="mb-3 text-sm text-gray-700 p-2 bg-gray-50 rounded">
                                      <span className="font-medium">Description:</span> {work.description}
                                    </div>
                                  )}
                                  
                                  {/* Work Package Additional Details */}
                                  <div className="mb-3 bg-white p-2 rounded border border-gray-200 text-xs">
                                    <div className="grid grid-cols-2 gap-2">
                                      {work.sequence_order !== undefined && (
                                        <div>
                                          <span className="font-medium">Sequence:</span> {work.sequence_order}
                                        </div>
                                      )}
                                      {work.status && (
                                        <div>
                                          <span className="font-medium">Status:</span> 
                                          <span className={`ml-1 px-1.5 py-0.5 rounded ${
                                            work.status === 'Completed' ? 'bg-green-200 text-green-800 border border-green-300' : 
                                            work.status === 'Failed' ? 'bg-red-200 text-red-800 border border-red-300' : 
                                            work.status === 'In Progress' ? 'bg-yellow-200 text-yellow-800 border border-yellow-300' :
                                            work.status === 'Waiting' ? 'bg-blue-200 text-blue-800 border border-blue-300' :
                                            work.status === 'Cancelled' ? 'bg-purple-200 text-purple-800 border border-purple-300' :
                                            'bg-gray-200 text-gray-700 border border-gray-300'
                                          }`}>
                                            {work.status}
                                          </span>
                                        </div>
                                      )}
                                      {work.started_at && (
                                        <div>
                                          <span className="font-medium">Started:</span> {new Date(work.started_at).toLocaleString()}
                                        </div>
                                      )}
                                      {work.completed_at && (
                                        <div>
                                          <span className="font-medium">Completed:</span> {new Date(work.completed_at).toLocaleString()}
                                        </div>
                                      )}
                                    </div>
                                    
                                    {/* Dependencies section for work packages if applicable */}
                                    {work.dependencies && work.dependencies.length > 0 && (
                                      <div className="mt-2">
                                        <span className="font-medium">Dependencies:</span>
                                        <div className="flex flex-wrap gap-1 mt-1">
                                          {work.dependencies.map(dep => (
                                            <span key={dep} className="bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded text-xs">
                                              {dep}
                                            </span>
                                          ))}
                                        </div>
                                      </div>
                                    )}
                                    
                                    {/* Result/Error display for work packages if applicable */}
                                    {work.result && (
                                      <div className="mt-2">
                                        <span className="font-medium">Result:</span>
                                        <div className="mt-1 p-1 bg-gray-50 rounded border border-gray-300 max-h-24 overflow-y-auto">
                                          {work.result}
                                        </div>
                                      </div>
                                    )}
                                    
                                    {work.error_message && (
                                      <div className="mt-2">
                                        <span className="font-medium text-red-600">Error:</span>
                                        <div className="mt-1 p-1 bg-red-50 rounded border border-red-200 max-h-24 overflow-y-auto text-red-800">
                                          {work.error_message}
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                  
                                  {/* If no tasks */}
                                  {(!work.tasks || work.tasks.length === 0) && (
                                    <div className="text-sm text-gray-500 italic p-2">
                                      No tasks generated yet.
                                    </div>
                                  )}
                                  
                                  {/* Tasks list */}
                                  <div className="space-y-2">
                                    {work.tasks?.map((task, taskIndex) => (
                                      <div key={task.id} className="border-2 border-purple-300 rounded-lg overflow-hidden">
                                        {/* Task Header */}
                                        <div 
                                          className="flex items-center justify-between bg-purple-50 p-2 cursor-pointer hover:bg-purple-100"
                                          onClick={() => toggleTask(task.id)}
                                        >
                                          <div className="flex items-center gap-2">
                                            {expandedTasks[task.id] ? (
                                              <ChevronDown className="w-4 h-4 text-gray-600" />
                                            ) : (
                                              <ChevronRight className="w-4 h-4 text-gray-600" />
                                            )}
                                            <span className="font-medium text-sm">
                                              {stageIndex + 1}.{workIndex + 1}.{taskIndex + 1} {task.name || task.task_name || task.description?.slice(0, 30) + "..." || `Task ${task.id}`}
                                              <span className="ml-2 text-xs text-gray-500">ID: {task.id}</span>
                                            </span>
                                          </div>
                                          <span className="text-xs bg-purple-100 text-purple-800 py-0.5 px-2 rounded-full">
                                            {task.subtasks?.length || 0} Subtasks
                                          </span>
                                        </div>
                                        
                                        {/* Task Content (Subtasks) */}
                                        {expandedTasks[task.id] && (
                                          <div className="pl-6 pr-3 py-2 border-t border-gray-200">
                                            {/* Task Description */}
                                            <div className="mb-2 text-sm text-gray-700">
                                              <span className="font-medium">Description:</span> {task.description}
                                            </div>
                                            
                                            {/* Task Additional Details */}
                                            <div className="mb-3 bg-white p-2 rounded border border-gray-200 text-xs">
                                              <div className="grid grid-cols-2 gap-2">
                                                <div>
                                                  <span className="font-medium">Status:</span> 
                                                  <span className={`ml-1 px-1.5 py-0.5 rounded ${
                                                    task.status === 'Completed' ? 'bg-green-200 text-green-800 border border-green-300' : 
                                                    task.status === 'Failed' ? 'bg-red-200 text-red-800 border border-red-300' : 
                                                    task.status === 'In Progress' ? 'bg-yellow-200 text-yellow-800 border border-yellow-300' :
                                                    task.status === 'Waiting' ? 'bg-blue-200 text-blue-800 border border-blue-300' :
                                                    task.status === 'Cancelled' ? 'bg-purple-200 text-purple-800 border border-purple-300' :
                                                    'bg-gray-200 text-gray-700 border border-gray-300'
                                                  }`}>
                                                    {task.status || 'Pending'}
                                                  </span>
                                                </div>
                                                <div>
                                                  <span className="font-medium">Sequence:</span> {task.sequence_order}
                                                </div>
                                                {task.started_at && (
                                                  <div>
                                                    <span className="font-medium">Started:</span> {new Date(task.started_at).toLocaleString()}
                                                  </div>
                                                )}
                                                {task.completed_at && (
                                                  <div>
                                                    <span className="font-medium">Completed:</span> {new Date(task.completed_at).toLocaleString()}
                                                  </div>
                                                )}
                                              </div>
                                              
                                              {/* Dependencies section */}
                                              {task.dependencies && task.dependencies.length > 0 && (
                                                <div className="mt-2">
                                                  <span className="font-medium">Dependencies:</span>
                                                  <div className="flex flex-wrap gap-1 mt-1">
                                                    {task.dependencies.map(dep => (
                                                      <span key={dep} className="bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded text-xs">
                                                        {dep}
                                                      </span>
                                                    ))}
                                                  </div>
                                                </div>
                                              )}
                                              
                                              {/* Required Inputs */}
                                              {task.required_inputs && task.required_inputs.length > 0 && (
                                                <div className="mt-2">
                                                  <span className="font-medium">Required Inputs:</span>
                                                  <div className="mt-1">
                                                    {task.required_inputs.map((input, idx) => (
                                                      <div key={idx} className="text-xs py-0.5">
                                                        • {input.name} ({input.type})
                                                        {input.description && <span className="text-gray-500 ml-1">- {input.description}</span>}
                                                      </div>
                                                    ))}
                                                  </div>
                                                </div>
                                              )}
                                              
                                              {/* Generated Artifacts */}
                                              {task.generated_artifacts && task.generated_artifacts.length > 0 && (
                                                <div className="mt-2">
                                                  <span className="font-medium">Generated Artifacts:</span>
                                                  <div className="mt-1">
                                                    {task.generated_artifacts.map((artifact, idx) => (
                                                      <div key={idx} className="text-xs py-0.5">
                                                        • {artifact.name} ({artifact.type})
                                                        {artifact.description && <span className="text-gray-500 ml-1">- {artifact.description}</span>}
                                                      </div>
                                                    ))}
                                                  </div>
                                                </div>
                                              )}
                                              
                                              {/* Validation Criteria */}
                                              {task.validation_criteria && task.validation_criteria.length > 0 && (
                                                <div className="mt-2">
                                                  <span className="font-medium">Validation Criteria:</span>
                                                  <div className="mt-1">
                                                    {task.validation_criteria.map((criteria, idx) => (
                                                      <div key={idx} className="text-xs py-0.5">
                                                        • {criteria}
                                                      </div>
                                                    ))}
                                                  </div>
                                                </div>
                                              )}
                                              
                                              {/* Result/Error display */}
                                              {task.result && (
                                                <div className="mt-2">
                                                  <span className="font-medium">Result:</span>
                                                  <div className="mt-1 p-1 bg-gray-50 rounded border border-gray-300 max-h-24 overflow-y-auto">
                                                    {task.result}
                                                  </div>
                                                </div>
                                              )}
                                              
                                              {task.error_message && (
                                                <div className="mt-2">
                                                  <span className="font-medium text-red-600">Error:</span>
                                                  <div className="mt-1 p-1 bg-red-50 rounded border border-red-200 max-h-24 overflow-y-auto text-red-800">
                                                    {task.error_message}
                                                  </div>
                                                </div>
                                              )}
                                            </div>
                                            
                                            {/* If no subtasks */}
                                            {(!task.subtasks || task.subtasks.length === 0) && (
                                              <div className="text-sm text-gray-500 italic p-2">
                                                No subtasks generated yet.
                                              </div>
                                            )}
                                            
                                            {/* Subtasks list */}
                                            <div className="space-y-1">
                                              {task.subtasks?.map((subtask, subtaskIndex) => (
                                                <div key={subtask.id} className={`border-2 rounded p-2 ${
                                                  subtask.status === 'Completed' ? 'border-green-400 bg-green-50' :
                                                  subtask.status === 'Failed' ? 'border-red-400 bg-red-50' :
                                                  subtask.status === 'In Progress' ? 'border-yellow-400 bg-yellow-50' :
                                                  subtask.status === 'Waiting' ? 'border-blue-400 bg-blue-50' :
                                                  subtask.status === 'Cancelled' ? 'border-purple-400 bg-purple-50' :
                                                  'border-gray-300 bg-gray-50'
                                                }`}>
                                                  <div className="flex items-center justify-between">
                                                    <span className="text-sm">
                                                      {stageIndex + 1}.{workIndex + 1}.{taskIndex + 1}.{subtaskIndex + 1} {subtask.name || subtask.subtask_name || subtask.description?.slice(0, 30) + "..." || `Subtask ${subtask.id}`}
                                                      <span className="ml-2 text-xs text-gray-500">ID: {subtask.id}</span>
                                                    </span>
                                                    <span className={`text-xs py-0.5 px-2 rounded-full ${
                                                      subtask.status === 'Completed' ? 'bg-green-200 text-green-800 border border-green-300' :
                                                      subtask.status === 'Failed' ? 'bg-red-200 text-red-800 border border-red-300' :
                                                      subtask.status === 'In Progress' ? 'bg-yellow-200 text-yellow-800 border border-yellow-300' :
                                                      subtask.status === 'Waiting' ? 'bg-blue-200 text-blue-800 border border-blue-300' :
                                                      subtask.status === 'Cancelled' ? 'bg-purple-200 text-purple-800 border border-purple-300' :
                                                      'bg-gray-200 text-gray-700 border border-gray-300'
                                                    }`}>
                                                      {subtask.status || 'Pending'} | {subtask.executor_type || 'Unknown'}
                                                    </span>
                                                  </div>
                                                  {subtask.description && (
                                                    <p className="text-xs text-gray-600 mt-1">
                                                      {subtask.description}
                                                    </p>
                                                  )}
                                                  
                                                  {/* Expanded Subtask Details */}
                                                  <div className="mt-2 text-xs border-t border-gray-200 pt-2">
                                                    <div className="grid grid-cols-2 gap-2">
                                                      <div>
                                                        <span className="font-medium">Sequence:</span> {subtask.sequence_order}
                                                      </div>
                                                      <div>
                                                        <span className="font-medium">Parent Task:</span> {subtask.parent_executable_task_id}
                                                      </div>
                                                      {subtask.started_at && (
                                                        <div>
                                                          <span className="font-medium">Started:</span> {new Date(subtask.started_at).toLocaleString()}
                                                        </div>
                                                      )}
                                                      {subtask.completed_at && (
                                                        <div>
                                                          <span className="font-medium">Completed:</span> {new Date(subtask.completed_at).toLocaleString()}
                                                        </div>
                                                      )}
                                                    </div>
                                                    
                                                    {subtask.result && (
                                                      <div className="mt-2">
                                                        <span className="font-medium">Result:</span>
                                                        <div className="mt-1 p-1 bg-white rounded border border-gray-300 max-h-24 overflow-y-auto">
                                                          {subtask.result}
                                                        </div>
                                                      </div>
                                                    )}
                                                    
                                                    {subtask.error_message && (
                                                      <div className="mt-2">
                                                        <span className="font-medium text-red-600">Error:</span>
                                                        <div className="mt-1 p-1 bg-red-50 rounded border border-red-200 max-h-24 overflow-y-auto text-red-800">
                                                          {subtask.error_message}
                                                        </div>
                                                      </div>
                                                    )}
                                                  </div>
                                                </div>
                                              ))}
                                            </div>
                                          </div>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
        
        {/* Right Panel - Chat Assistant */}
        {isChatExpanded && (
          <div className="w-1/2 h-full border-l border-gray-200 flex flex-col overflow-hidden">
            <TaskStreamingChat 
              taskId={taskId}
              onSendMessage={handleSendChatMessage}
              isLoading={isChatLoading}
              onResetChat={handleResetChat}
              // Pass the preserved chat state
              chatHistory={chatHistory}
              streamingMessage={streamingMessage}
              error={chatError}
              isStreaming={isStreaming}
              isExternallyManaged={true}
            />
          </div>
        )}
      </div>
    </div>
  );
} 