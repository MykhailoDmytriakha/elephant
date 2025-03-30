import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, ChevronDown, ChevronRight, Layers } from 'lucide-react';
import { LoadingSpinner, ErrorDisplay } from '../components/task/TaskComponents';
import { useTaskDetails } from '../hooks/useTaskDetails';
import { generateAllWorkPackages } from '../utils/api';
import { useToast } from '../components/common/ToastProvider';

/**
 * A dedicated page that displays all stages with their sublevels (work packages, tasks, subtasks)
 * in an expandable hierarchical view
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

  // Use the task details hook for fetching data
  const {
    task,
    loading,
    error,
    loadTask,
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
      await loadTask();
    } catch (error) {
      console.error("Error generating all work packages:", error);
      toast.showError(`Failed to generate work packages: ${error.message || 'Unknown error'}`);
    } finally {
      setIsGeneratingAllWork(false);
    }
  };

  // Check if any stage already has work packages
  const anyWorkPackagesExist = task?.network_plan?.stages?.some(
    stage => stage.work_packages && stage.work_packages.length > 0
  ) ?? false;

  if (loading && !isGeneratingAllWork) return <LoadingSpinner message="Loading task data..." />;

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
    <div className="min-h-screen bg-gray-50">
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
              <h1 className="text-2xl font-bold text-gray-900">Task Breakdown</h1>
            </div>
            <div className="flex items-center gap-2">
              {/* Generate All Work Packages Button */}
              <button
                onClick={handleGenerateAllWorkPackages}
                disabled={loading || isGeneratingAllWork}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md transition-colors ${
                  isGeneratingAllWork
                    ? 'bg-blue-400 text-white cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
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
                  : (anyWorkPackagesExist ? 'Regenerate All Work Packages' : 'Generate All Work Packages')
                }
              </button>
              {/* Refresh Button */}
              <button
                onClick={loadTask}
                disabled={loading || isGeneratingAllWork}
                className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              {task.shortDescription || 'Task Stages'}
            </h2>
            
            {/* Stage List */}
            <div className="space-y-2">
              {task.network_plan.stages.map((stage, stageIndex) => (
                <div key={stage.id} className="border border-gray-200 rounded-lg overflow-hidden">
                  {/* Stage Header */}
                  <div 
                    className="flex items-center justify-between bg-gray-50 p-3 cursor-pointer hover:bg-gray-100"
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
                      
                      {/* If no work packages */}
                      {(!stage.work_packages || stage.work_packages.length === 0) && (
                        <div className="text-sm text-gray-500 italic p-2">
                          No work packages generated yet.
                        </div>
                      )}
                      
                      {/* Work packages list */}
                      <div className="space-y-2">
                        {stage.work_packages?.map((work, workIndex) => (
                          <div key={work.id} className="border border-gray-200 rounded-lg overflow-hidden">
                            {/* Work Package Header */}
                            <div 
                              className="flex items-center justify-between bg-gray-50 p-2 cursor-pointer hover:bg-gray-100"
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
                                
                                {/* If no tasks */}
                                {(!work.tasks || work.tasks.length === 0) && (
                                  <div className="text-sm text-gray-500 italic p-2">
                                    No tasks generated yet.
                                  </div>
                                )}
                                
                                {/* Tasks list */}
                                <div className="space-y-2">
                                  {work.tasks?.map((task, taskIndex) => (
                                    <div key={task.id} className="border border-gray-200 rounded-lg overflow-hidden">
                                      {/* Task Header */}
                                      <div 
                                        className="flex items-center justify-between bg-gray-50 p-2 cursor-pointer hover:bg-gray-100"
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
                                          
                                          {/* If no subtasks */}
                                          {(!task.subtasks || task.subtasks.length === 0) && (
                                            <div className="text-sm text-gray-500 italic">
                                              No subtasks generated yet.
                                            </div>
                                          )}
                                          
                                          {/* Subtasks list */}
                                          <div className="space-y-1">
                                            {task.subtasks?.map((subtask, subtaskIndex) => (
                                              <div key={subtask.id} className="border border-gray-200 rounded p-2 bg-gray-50">
                                                <div className="flex items-center justify-between">
                                                  <span className="text-sm">
                                                    {stageIndex + 1}.{workIndex + 1}.{taskIndex + 1}.{subtaskIndex + 1} {subtask.name || subtask.subtask_name || subtask.description?.slice(0, 30) + "..." || `Subtask ${subtask.id}`}
                                                    <span className="ml-2 text-xs text-gray-500">ID: {subtask.id}</span>
                                                  </span>
                                                  <span className="text-xs bg-gray-200 text-gray-700 py-0.5 px-2 rounded-full">
                                                    {subtask.executor_type || 'Unknown'}
                                                  </span>
                                                </div>
                                                {subtask.description && (
                                                  <p className="text-xs text-gray-600 mt-1">
                                                    {subtask.description}
                                                  </p>
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
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 