import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, RefreshCcw, ChevronDown, ChevronRight, Layers, Workflow, Minimize2, Maximize2, MessageCircle, RotateCcw } from 'lucide-react';
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
    
    // Add the user message to chat history to immediately show it in UI
    const userMessage = { role: 'user', content: message };
    setChatHistory(prev => [...prev, userMessage]);
    setStreamingMessage(''); // Clear any previous streaming message
    
    try {
      const customCallbacks = {
        onChunk: (chunk) => {
          // Check if the chunk contains an error message and clean it
          if (chunk.includes('⚠️ Error:')) {
            const cleanError = chunk.replace('⚠️ Error:', '').trim();
            setChatError(cleanError);
            setIsStreaming(false);
            
            // Don't add session errors to chat history since they're shown in banner
            if (!cleanError.includes('Session not found') && !cleanError.includes('session')) {
              setChatHistory(prev => [...prev, { 
                role: 'system', 
                content: cleanError
              }]);
            }
            return; // Don't add error chunks to streaming message
          }
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
          
          // Handle session errors with auto-recovery suggestion
          if (errorMessage.includes('Session not found') || errorMessage.includes('session')) {
            setChatError('Your chat session has expired. Please reset to continue.');
          } else {
            setChatError(errorMessage);
            // Only add non-session errors to chat history to avoid duplication
            setChatHistory(prev => [...prev, { 
              role: 'system', 
              content: errorMessage
            }]);
          }
          
          setIsStreaming(false);
          if (callbacks?.onError) callbacks.onError(error);
        }
      };
      
      // Pass an empty array for messageHistory since we're using server-side sessions
      await chatWithTaskAssistant(taskId, message, customCallbacks, []);
    } catch (error) {
      console.error("Error in chat handling:", error);
      const errorMessage = error.message || 'Unknown error';
      setChatError(errorMessage);
      setIsStreaming(false);
      toast.showError(`Chat error: ${errorMessage}`);
      // Ensure the system error message is added to chat history
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
    }
  };
  
  // Reset chat handler
  const handleResetChat = () => {
    setChatHistory([]);
    setStreamingMessage('');
    setChatError(null);
    setIsStreaming(false);
    setIsChatLoading(false);
    // Note: The next message will automatically use a fresh session
    console.log('Chat reset - next message will use a fresh session');
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
              {/* Toggle Chat Button - More prominent position */}
              <button
                onClick={toggleChatExpanded}
                className={`flex items-center gap-2 px-4 py-2 rounded-md transition-colors ${
                  isChatExpanded 
                    ? 'bg-indigo-600 text-white hover:bg-indigo-700' 
                    : 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200 ring-2 ring-indigo-300 ring-opacity-50'
                }`}
                title={isChatExpanded ? "Hide the assistant panel" : "Show the assistant panel to ask questions"}
              >
                {isChatExpanded ? (
                  <Minimize2 className="w-4 h-4" />
                ) : (
                  <MessageCircle className="w-4 h-4" />
                )}
                {isChatExpanded ? 'Hide Assistant' : 'Ask Assistant'}
              </button>
              
              {/* Refresh Button */}
              <button
                onClick={loadTask}
                disabled={loading || isGeneratingAllWork || isGeneratingAllTasks}
                className="flex items-center gap-2 px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="Sync task data from server"
              >
                <RefreshCcw className="w-4 h-4" />
                Sync Data
              </button>
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
            <div className="flex-shrink-0 border-b border-gray-200">
              {/* Progress Indicator - Only show when work packages and tasks don't exist */}
              {!anyWorkPackagesExist && !anyTasksExist && (
                <div className="px-4 py-3 bg-gray-50 border-b border-gray-100">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium text-gray-700">Progress:</span>
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                        <span className="text-green-700">Stages Complete</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${anyWorkPackagesExist ? 'bg-green-500' : 'bg-amber-400'}`}></div>
                        <span className={anyWorkPackagesExist ? 'text-green-700' : 'text-amber-700'}>
                          {anyWorkPackagesExist ? 'Work Packages Ready' : 'Work Packages Needed'}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${anyTasksExist ? 'bg-green-500' : anyWorkPackagesExist ? 'bg-amber-400' : 'bg-gray-300'}`}></div>
                        <span className={anyTasksExist ? 'text-green-700' : anyWorkPackagesExist ? 'text-amber-700' : 'text-gray-500'}>
                          {anyTasksExist ? 'Tasks Ready' : anyWorkPackagesExist ? 'Tasks Pending' : 'Tasks Not Ready'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              <div className="flex items-center justify-between px-4 py-3">
                <div className="flex items-center gap-2">
                  <Layers className="w-5 h-5 text-blue-600" />
                  <h2 className="font-medium text-gray-800">Task Stages</h2>
                </div>
              </div>
            </div>
            
            {/* Stage List - Scrollable */}
            <div className="flex-grow overflow-y-auto p-4 space-y-4">
              {/* Next Steps Guidance - Show when work packages are missing */}
              {!anyWorkPackagesExist && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
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
                        onClick={handleGenerateAllWorkPackages}
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
              )}
              
              {/* Next Steps Guidance - Show when work packages exist but tasks don't */}
              {anyWorkPackagesExist && !anyTasksExist && (
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-4">
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
                        onClick={handleGenerateTasksForAllStages}
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
              )}
              
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
                              <div className="mt-1 p-1 bg-gray-50 rounded border border-gray-300">
                                {Array.isArray(stage.result) ? (
                                  <ul className="list-disc list-inside space-y-1">
                                    {stage.result.map((item, index) => (
                                      <li key={index} className="text-sm">{item}</li>
                                    ))}
                                  </ul>
                                ) : (
                                  <div className="whitespace-pre-wrap">{stage.result}</div>
                                )}
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
                          <div className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3 text-center">
                            <div className="flex items-center justify-center gap-2">
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              No work packages generated yet.
                            </div>
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
                                        <div className="mt-1 p-1 bg-gray-50 rounded border border-gray-300">
                                          {Array.isArray(work.result) ? (
                                            <ul className="list-disc list-inside space-y-1">
                                              {work.result.map((item, index) => (
                                                <li key={index} className="text-sm">{item}</li>
                                              ))}
                                            </ul>
                                          ) : (
                                            <div className="whitespace-pre-wrap">{work.result}</div>
                                          )}
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
                                    <div className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3 text-center">
                                      <div className="flex items-center justify-center gap-2">
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        No tasks generated yet.
                                      </div>
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
                                                  <div className="mt-1 p-1 bg-gray-50 rounded border border-gray-300">
                                                    {Array.isArray(task.result) ? (
                                                      <ul className="list-disc list-inside space-y-1">
                                                        {task.result.map((item, index) => (
                                                          <li key={index} className="text-sm">{item}</li>
                                                        ))}
                                                      </ul>
                                                    ) : (
                                                      <div className="whitespace-pre-wrap">{task.result}</div>
                                                    )}
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
                                              <div className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3 text-center">
                                                <div className="flex items-center justify-center gap-2">
                                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                  </svg>
                                                  No subtasks generated yet.
                                                </div>
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
                                                        <div className="mt-1 p-1 bg-white rounded border border-gray-300">
                                                          {Array.isArray(subtask.result) ? (
                                                            <ul className="list-disc list-inside space-y-1">
                                                              {subtask.result.map((item, index) => (
                                                                <li key={index} className="text-sm">{item}</li>
                                                              ))}
                                                            </ul>
                                                          ) : (
                                                            <div className="whitespace-pre-wrap">{subtask.result}</div>
                                                          )}
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