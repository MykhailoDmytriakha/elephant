// src/pages/StageDetailPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useLocation, Link, useNavigate } from 'react-router-dom';
import {
    ArrowLeft, CheckCircle2, ChevronRight, FileText, ShieldCheck, Layers, Cpu, AlertCircle, RefreshCw, TerminalSquare, ChevronsRight, Download, Upload,
    ListPlus, Workflow // <-- Import Workflow icon
} from 'lucide-react';
import { InfoCard, CollapsibleSection } from '../components/task/TaskComponents';
import { useToast } from '../components/common/ToastProvider';
import {
    generateWorkForStage,
    generateTasksForWork, // Keep this for individual task generation if needed later, or remove if fully replaced
    generateAllTasksForWork, // NEW
    generateAllSubtasksForWork, // NEW
    generateSubtasksForTask,
    fetchTaskDetails, // Import for fetching task details directly
    generateAllTasksForStage // <-- Import the new API function
} from '../utils/api';
import { ExecutableTaskDisplay } from '../components/task/ExecutableTaskDisplay';
import StageOverviewPanel from '../components/task/StageOverviewPanel';

// Helper component for Artifacts (assuming it's defined or imported correctly)
// Make sure ArtifactDisplay is exported if it's in a separate file
export const ArtifactDisplay = ({ artifact, title = "Artifact" }) => (
    <div className="mt-3 p-3 bg-gray-50 rounded-md border border-gray-200 w-full">
        <h4 className="text-sm font-medium text-gray-700 mb-2">{title}</h4>
        <div className="flex items-start gap-2">
            <FileText className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
            <div className="w-full">
                <p className="font-medium text-gray-900 text-sm">{artifact.name} ({artifact.type})</p>
                <p className="text-xs text-gray-600 mt-1">{artifact.description}</p>
                {artifact.location && (
                    <p className="text-xs text-gray-500 mt-2">
                        Location: <span className="font-mono bg-gray-100 px-1 rounded">{artifact.location}</span>
                    </p>
                )}
            </div>
        </div>
    </div>
);

// Modified WorkPackageCard - Now includes "Generate All" buttons and props
const WorkPackageCard = ({
    work,
    taskId,
    stageId,
    onGenerateTasks, // Keep individual generation handler (could be used for retry?)
    onGenerateAllTasks, // NEW: Handler for generating all tasks in this work
    isGeneratingAllTasks, // NEW: Loading state for generating all tasks
    allTasksError, // NEW: Error state for generating all tasks
    onGenerateAllSubtasks, // NEW: Handler for generating all subtasks in this work
    isGeneratingAllSubtasks, // NEW: Loading state for generating all subtasks
    allSubtasksError, // NEW: Error state for generating all subtasks
    onGenerateSubtasks // Keep individual subtask generation handler for ExecutableTaskDisplay
 }) => {
    const [isExpanded, setIsExpanded] = useState(false);

    const hasTasks = work.tasks && work.tasks.length > 0;
    const hasSubtasks = hasTasks && work.tasks.some(t => t.subtasks && t.subtasks.length > 0);

    // Button text for generating all tasks
    let generateAllTasksButtonText = 'Generate All Tasks';
    if (isGeneratingAllTasks) {
        generateAllTasksButtonText = 'Generating All Tasks...';
    } else if (hasTasks) {
        generateAllTasksButtonText = 'Regenerate All Tasks';
    }

    // Button text for generating all subtasks
    let generateAllSubtasksButtonText = 'Generate All Subtasks';
    if (isGeneratingAllSubtasks) {
        generateAllSubtasksButtonText = 'Generating All Subtasks...';
    } else if (hasSubtasks) {
        generateAllSubtasksButtonText = 'Regenerate All Subtasks';
    }

    return (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden w-full">
            <button
                className="w-full text-left p-4 flex justify-between items-center hover:bg-gray-50"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                 <div className="w-5/6">
                    <h4 className="font-semibold text-gray-900 truncate">{work.name} <span className="text-sm font-normal text-gray-500">(ID: {work.id}, Seq: {work.sequence_order})</span></h4>
                    <p className="text-sm text-gray-600 line-clamp-1">{work.description}</p>
                </div>
                <ChevronRight className={`w-5 h-5 text-gray-400 transform transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
            </button>

            {isExpanded && (
                <div className="p-4 border-t border-gray-200 bg-gray-50 space-y-4 w-full">
                    <p className="text-sm text-gray-800 w-full">{work.description}</p>
                    {work.dependencies?.length > 0 && (
                        <div className="text-xs text-gray-600 flex items-center gap-2 w-full">
                          <ChevronsRight className="w-4 h-4 text-gray-400" />
                          <span className="font-medium">Depends on Work IDs:</span>
                          <div className="flex flex-wrap gap-1">
                            {work.dependencies.map(depId => (
                              <span key={depId} className="font-mono bg-gray-200 px-1.5 py-0.5 rounded">{depId}</span>
                            ))}
                          </div>
                        </div>
                      )}

                     {work.required_inputs?.length > 0 && (
                         <div className="w-full">
                            <h5 className="text-sm font-medium text-gray-700 mb-1 flex items-center gap-1"><Download className="w-3 h-3"/> Required Inputs:</h5>
                            <div className="space-y-2 w-full">
                                {work.required_inputs.map((artifact, idx) => (
                                    <ArtifactDisplay key={`in-${idx}`} artifact={artifact} title="" />
                                ))}
                            </div>
                        </div>
                    )}

                     <div className="w-full">
                        <h5 className="text-sm font-medium text-gray-700 mb-1">Expected Outcome:</h5>
                        <p className="text-sm text-gray-700 italic">{work.expected_outcome}</p>
                    </div>

                    {work.generated_artifacts?.length > 0 && (
                         <div className="w-full">
                            <h5 className="text-sm font-medium text-gray-700 mb-1 flex items-center gap-1"><Upload className="w-3 h-3"/> Generated Artifacts:</h5>
                            <div className="space-y-2 w-full">
                                {work.generated_artifacts.map((artifact, idx) => (
                                    <ArtifactDisplay key={`out-${idx}`} artifact={artifact} title="" />
                                ))}
                            </div>
                        </div>
                    )}

                    {work.validation_criteria?.length > 0 && (
                        <div className="w-full">
                            <h5 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                                <ShieldCheck className="w-4 h-4 text-green-600" /> Validation Criteria:
                            </h5>
                            <ul className="space-y-1 pl-5 list-disc text-sm text-gray-600 w-full">
                                {work.validation_criteria.map((criterion, index) => (
                                    <li key={`val-${index}`}>{criterion}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* Executable Tasks Section */}
                    <div className="pt-4 mt-4 border-t border-gray-200 w-full">
                         <div className="flex justify-between items-center mb-3">
                             <h5 className="text-base font-semibold text-gray-800 flex items-center gap-2">
                                <TerminalSquare className="w-5 h-5 text-purple-600" />
                                Executable Tasks ({work.tasks?.length || 0})
                            </h5>
                             {/* --- NEW: Generate All Buttons --- */}
                            <div className="flex items-center gap-2">
                                {/* Generate/Regenerate All Tasks Button */}
                                <button
                                    onClick={() => onGenerateAllTasks(work.id)}
                                    disabled={isGeneratingAllTasks || isGeneratingAllSubtasks} // Disable if any "all" action is running for this work
                                    className="px-3 py-1.5 text-xs bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-1"
                                    title={generateAllTasksButtonText}
                                >
                                    {isGeneratingAllTasks ? <RefreshCw className="w-3 h-3 animate-spin" /> : <ListPlus className="w-3 h-3" />}
                                    {hasTasks ? 'Regen All Tasks' : 'Gen All Tasks'} {/* Shorter text */}
                                </button>

                                {/* Generate/Regenerate All Subtasks Button */}
                                <button
                                    onClick={() => onGenerateAllSubtasks(work.id)}
                                    disabled={!hasTasks || isGeneratingAllTasks || isGeneratingAllSubtasks} // Disable if no tasks or if generating tasks/subtasks
                                    className="px-3 py-1.5 text-xs bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-1"
                                    title={generateAllSubtasksButtonText}
                                >
                                    {isGeneratingAllSubtasks ? <RefreshCw className="w-3 h-3 animate-spin" /> : <ListPlus className="w-3 h-3" />}
                                    {hasSubtasks ? 'Regen Work Subs' : 'Gen Work Subs'} {/* Shorter text */}
                                </button>
                            </div>
                             {/* --- END: Generate All Buttons --- */}
                         </div>


                        {/* Task Generation Loading/Error State (for "Generate All Tasks") */}
                        {isGeneratingAllTasks && (
                            <div className="text-center py-6 w-full">
                                <RefreshCw className="w-6 h-6 text-blue-600 mx-auto animate-spin mb-2" />
                                <p className="text-sm text-gray-600">Generating all executable tasks...</p>
                            </div>
                        )}
                        {!isGeneratingAllTasks && allTasksError && (
                            <div className="bg-red-100 border border-red-300 text-red-700 px-3 py-2 rounded text-sm mb-3 flex items-center gap-2 w-full">
                                <AlertCircle className="w-4 h-4" /> Error: {allTasksError}
                            </div>
                        )}

                        {/* Subtask Generation Loading/Error State (for "Generate All Subtasks") */}
                        {isGeneratingAllSubtasks && (
                            <div className="text-center py-6 w-full">
                                <RefreshCw className="w-6 h-6 text-indigo-600 mx-auto animate-spin mb-2" />
                                <p className="text-sm text-gray-600">Generating all subtasks...</p>
                            </div>
                        )}
                        {!isGeneratingAllSubtasks && allSubtasksError && (
                            <div className="bg-red-100 border border-red-300 text-red-700 px-3 py-2 rounded text-sm mb-3 flex items-center gap-2 w-full">
                                <AlertCircle className="w-4 h-4" /> Error: {allSubtasksError}
                            </div>
                        )}

                        {/* Task List */}
                        {!isGeneratingAllTasks && !allTasksError && (
                            <>
                                {hasTasks ? (
                                    <div className="space-y-3 w-full">
                                        {work.tasks.map((task, index) => (
                                            <ExecutableTaskDisplay
                                                key={task.id || index}
                                                task={task}
                                                taskIndex={index}
                                                taskId={taskId}
                                                stageId={stageId}
                                                workId={work.id}
                                                onGenerateSubtasks={onGenerateSubtasks} // Pass individual handler
                                            />
                                        ))}
                                    </div>
                                ) : (
                                     !isGeneratingAllTasks && // Only show if not loading
                                    <p className="text-sm text-gray-500 italic text-center py-4 w-full">
                                        No executable tasks generated yet. Click "Gen All Tasks" above.
                                    </p>
                                )}
                            </>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

// Main Stage Detail Page Component
export default function StageDetailPage() {
    const { taskId, stageId } = useParams();
    const location = useLocation();
    const navigate = useNavigate();
    const toast = useToast();

    // --- State Management ---
    const [currentStageData, setCurrentStageData] = useState(location.state?.stage || null);
    const [taskInfo, setTaskInfo] = useState({
        shortDescription: location.state?.taskShortDescription,
        id: location.state?.taskId
    });
    const [isGeneratingWork, setIsGeneratingWork] = useState(false);
    const [workGenerationError, setWorkGenerationError] = useState(null);
    const [isLoadingData, setIsLoadingData] = useState(false); // New loading state for direct data fetching
    // States for "Generate All Tasks"
    const [generatingAllTasksForWorkId, setGeneratingAllTasksForWorkId] = useState(null);
    const [allTasksGenerationErrors, setAllTasksGenerationErrors] = useState({});
    // States for "Generate All Subtasks"
    const [generatingAllSubtasksForWorkId, setGeneratingAllSubtasksForWorkId] = useState(null);
    const [allSubtasksGenerationErrors, setAllSubtasksGenerationErrors] = useState({});
    
    // --- NEW State for generating all tasks for the STAGE ---
    const [isGeneratingAllTasksForStage, setIsGeneratingAllTasksForStage] = useState(false);
    const [allTasksForStageError, setAllTasksForStageError] = useState(null);
    // --- End State Management ---

    // New function to fetch task and stage data directly if needed
    const fetchStageData = async () => {
        if (!taskId) {
            console.error("Cannot fetch stage data: taskId is missing");
            return;
        }
        
        try {
            setIsLoadingData(true);
            console.log("Fetching task data directly from API for taskId:", taskId);
            const taskData = await fetchTaskDetails(taskId);
            
            if (!taskData || !taskData.network_plan) {
                console.error("Task data or network plan is missing", taskData);
                return;
            }
            
            const foundStage = taskData.network_plan.stages.find(s => s.id === stageId);
            if (!foundStage) {
                console.error(`Stage ${stageId} not found in task data`);
                return;
            }
            
            console.log("Directly fetched stage data:", foundStage);
            setCurrentStageData(foundStage);
            setTaskInfo(prev => ({
                ...prev,
                shortDescription: taskData.short_description || taskData.task,
                id: taskData.id
            }));
        } catch (error) {
            console.error("Error fetching task/stage data:", error);
            toast.showError(`Error loading stage data: ${error.message}`);
        } finally {
            setIsLoadingData(false);
        }
    };

    // Effect to handle missing initial state
    useEffect(() => {
        // Add logging to check data received and missing
        console.log("StageDetailPage - Initial state:", {
            currentStageData,
            taskId, 
            stageId,
            locationState: location.state,
            hasWorkPackages: currentStageData?.work_packages ? true : false,
            workPackagesCount: currentStageData?.work_packages?.length || 0
        });

        // If stage data is missing, try to fetch it directly
        if (!currentStageData && taskId && stageId) {
            console.warn("Stage data missing from location state. Fetching data directly.");
            fetchStageData();
        }
        // If work_packages exists but is empty, also fetch data directly
        else if (currentStageData && currentStageData.work_packages && currentStageData.work_packages.length === 0) {
            console.warn("Work packages array exists but is empty. Fetching complete stage data.");
            fetchStageData();
        }
        
        // Reset loading states on mount/change
        setIsGeneratingWork(false);
        setWorkGenerationError(null);
        setGeneratingAllTasksForWorkId(null);
        setAllTasksGenerationErrors({});
        setGeneratingAllSubtasksForWorkId(null);
        setAllSubtasksGenerationErrors({});
    }, [taskId, stageId]); // Don't include currentStageData here to avoid loops


    // Error handling if data is missing
    if (!currentStageData && isLoadingData) {
        // Loading state while fetching data
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
                <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full text-center">
                    <RefreshCw className="w-12 h-12 text-blue-500 mx-auto mb-4 animate-spin" />
                    <h2 className="text-xl font-semibold text-gray-700 mb-2">Loading Stage Data</h2>
                    <p className="text-gray-600 mb-6">Please wait while we fetch stage details...</p>
                </div>
            </div>
        );
    }
    
    if (!currentStageData && !isLoadingData) {
        const backTaskId = taskInfo.id || taskId;
        return (
             <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
                <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full text-center">
                    <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                    <h2 className="text-xl font-semibold text-red-700 mb-2">Error</h2>
                    <p className="text-gray-600 mb-6">Stage details not found. Please navigate from the main task page.</p>
                    <div className="space-y-3">
                        <button
                            onClick={() => navigate(`/tasks/${backTaskId}`)}
                            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 w-full"
                        >
                            Go Back to Task
                        </button>
                        <button
                            onClick={fetchStageData}
                            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 w-full"
                        >
                            Try Again
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // --- Handler Functions ---
    const handleGenerateWork = async () => {
        console.log("Generating work packages - Starting process");
        setIsGeneratingWork(true);
        setWorkGenerationError(null);
        // Clear stage-level errors too
        setAllTasksForStageError(null);
        try {
            const currentTaskId = taskInfo.id || taskId;
            const currentStageId = stageId || currentStageData.id;
            if (!currentTaskId || !currentStageId) throw new Error("Task ID or Stage ID missing.");

            console.log("Generating work packages - Calling API with:", { currentTaskId, currentStageId });
            const generatedWorkPackages = await generateWorkForStage(currentTaskId, currentStageId);
            console.log("Generating work packages - API response:", generatedWorkPackages);

            if (!generatedWorkPackages || !Array.isArray(generatedWorkPackages)) {
                console.warn("API didn't return a valid work packages array, fetching full stage data");
                await fetchStageData(); // This will update the state with full data
                toast.showSuccess("Work packages generated. Refreshed stage data from server.");
            } else if (generatedWorkPackages.length === 0) {
                console.warn("API returned an empty work packages array, this might be an issue");
                toast.showWarning("Generated work packages array is empty. This may be unexpected.");
                // Update state with empty array
                setCurrentStageData(prev => ({
                    ...prev,
                    work_packages: []
                }));
                // Try fetching full data just in case
                setTimeout(() => fetchStageData(), 1000); 
            } else {
                // Normal success case - we got work packages
                setCurrentStageData(prev => {
                    const updated = { ...prev, work_packages: generatedWorkPackages };
                    console.log("Generating work packages - Updated stage data:", updated);
                    return updated;
                });
                toast.showSuccess(`Successfully generated ${generatedWorkPackages.length} work packages.`);
            }
        } catch (error) {
            const errorMsg = error.message || "Unknown error generating work.";
            console.error("Generating work packages - Error:", errorMsg);
            setWorkGenerationError(errorMsg);
            toast.showError(`Error generating work: ${errorMsg}`);
            
            // If there was an error, try fetching complete stage data
            setTimeout(() => fetchStageData(), 1000);
        } finally {
            setIsGeneratingWork(false);
            console.log("Generating work packages - Process completed");
        }
    };

    // NEW Handler for Generating ALL Tasks for the entire Stage
    const handleGenerateAllTasksForStage = async () => {
        console.log("Generating all tasks for STAGE - Starting process for stageId:", stageId);
        setIsGeneratingAllTasksForStage(true);
        setAllTasksForStageError(null);
        // Clear individual work errors as well
        setAllTasksGenerationErrors({});
        try {
            const currentTaskId = taskInfo.id || taskId;
            const currentStageId = stageId || currentStageData.id;
            if (!currentTaskId || !currentStageId) throw new Error("Task ID or Stage ID missing.");

            console.log("Generating all stage tasks - Calling API with:", { currentTaskId, currentStageId });
            // Call the NEW API function
            const updatedWorkPackages = await generateAllTasksForStage(currentTaskId, currentStageId);
            console.log("Generating all stage tasks - API response (updated work packages):", updatedWorkPackages);

            // Update the current stage data with the new work packages list
            setCurrentStageData(prevStageData => {
                const updated = { ...prevStageData, work_packages: updatedWorkPackages || [] };
                console.log("Generating all stage tasks - Updated stage data:", updated);
                return updated;
            });

            toast.showSuccess(`Generated tasks for all work packages in Stage ${currentStageId}.`);
            
            // Fetch full stage data after completion to ensure all components have updated data
            setTimeout(() => fetchStageData(), 500);

        } catch (error) {
            const errorMsg = error.message || `Unknown error generating tasks for stage ${stageId}.`;
            console.error("Generating all stage tasks - Error:", errorMsg);
            setAllTasksForStageError(errorMsg);
            toast.showError(`Error generating tasks for stage: ${errorMsg}`);
            
            // Try to fetch full data even if there was an error
            setTimeout(() => fetchStageData(), 500);
        } finally {
            setIsGeneratingAllTasksForStage(false);
            console.log("Generating all stage tasks - Process completed for stageId:", stageId);
        }
    };

    // NEW Handler for Generating ALL Tasks for a specific Work package
    const handleGenerateAllTasksForWork = async (workId) => {
        console.log("Generating all tasks for work - Starting process for workId:", workId);
        setGeneratingAllTasksForWorkId(workId);
        setAllTasksGenerationErrors(prev => ({ ...prev, [workId]: null }));
        try {
            const currentTaskId = taskInfo.id || taskId;
            const currentStageId = stageId || currentStageData.id;
            if (!currentTaskId || !currentStageId || !workId) throw new Error("Task, Stage, or Work ID missing.");

            console.log("Generating all tasks - Calling API with:", { currentTaskId, currentStageId, workId });
            // Call the NEW API function
            const generatedTasks = await generateAllTasksForWork(currentTaskId, currentStageId, workId);
            console.log("Generating all tasks - API response:", generatedTasks);

            setCurrentStageData(prevStageData => {
                if (!prevStageData?.work_packages) return prevStageData;
                const workIndex = prevStageData.work_packages.findIndex(wp => wp.id === workId);
                if (workIndex === -1) return prevStageData;
                const newWorkPackages = [...prevStageData.work_packages];
                newWorkPackages[workIndex] = {
                    ...newWorkPackages[workIndex],
                    tasks: generatedTasks || []
                };
                const updated = { ...prevStageData, work_packages: newWorkPackages };
                console.log("Generating all tasks - Updated stage data:", updated);
                return updated;
            });

            toast.showSuccess(`Generated ${generatedTasks?.length || 0} tasks for Work ID ${workId}.`);

        } catch (error) {
            const errorMsg = error.message || `Unknown error generating tasks for ${workId}.`;
            console.error("Generating all tasks - Error:", errorMsg);
            setAllTasksGenerationErrors(prev => ({ ...prev, [workId]: errorMsg }));
            toast.showError(`Error generating tasks: ${errorMsg}`);
        } finally {
            setGeneratingAllTasksForWorkId(null);
            console.log("Generating all tasks - Process completed for workId:", workId);
        }
    };

    // NEW Handler for Generating ALL Subtasks for a specific Work package
    const handleGenerateAllSubtasksForWork = async (workId) => {
        console.log("Generating all subtasks for work - Starting process for workId:", workId);
        setGeneratingAllSubtasksForWorkId(workId);
        setAllSubtasksGenerationErrors(prev => ({ ...prev, [workId]: null }));
        try {
            const currentTaskId = taskInfo.id || taskId;
            const currentStageId = stageId || currentStageData.id;
            if (!currentTaskId || !currentStageId || !workId) throw new Error("Task, Stage, or Work ID missing.");

            console.log("Generating all subtasks - Calling API with:", { currentTaskId, currentStageId, workId });
            // Call the NEW API function
            const updatedTasksWithSubtasks = await generateAllSubtasksForWork(currentTaskId, currentStageId, workId);
            console.log("Generating all subtasks - API response:", updatedTasksWithSubtasks);

            setCurrentStageData(prevStageData => {
                if (!prevStageData?.work_packages) return prevStageData;
                const workIndex = prevStageData.work_packages.findIndex(wp => wp.id === workId);
                if (workIndex === -1) return prevStageData;
                const newWorkPackages = [...prevStageData.work_packages];
                // Replace the tasks array with the updated one from the API response
                newWorkPackages[workIndex] = {
                    ...newWorkPackages[workIndex],
                    // Important: the API returns the list of ExecutableTasks for the work, updated with subtasks
                    tasks: updatedTasksWithSubtasks || []
                };
                const updated = { ...prevStageData, work_packages: newWorkPackages };
                console.log("Generating all subtasks - Updated stage data:", updated);
                return updated;
            });

            // Count total subtasks generated
            const totalSubtasks = updatedTasksWithSubtasks.reduce((sum, task) => sum + (task.subtasks?.length || 0), 0);
            toast.showSuccess(`Generated ${totalSubtasks} subtasks across ${updatedTasksWithSubtasks?.length || 0} tasks for Work ID ${workId}.`);

        } catch (error) {
            const errorMsg = error.message || `Unknown error generating subtasks for ${workId}.`;
            console.error("Generating all subtasks - Error:", errorMsg);
            setAllSubtasksGenerationErrors(prev => ({ ...prev, [workId]: errorMsg }));
            toast.showError(`Error generating subtasks: ${errorMsg}`);
        } finally {
            setGeneratingAllSubtasksForWorkId(null);
            console.log("Generating all subtasks - Process completed for workId:", workId);
        }
    };


    // Keep the individual subtask generator for the ExecutableTaskDisplay component
    const handleGenerateSubtasksForTask = async (executableTaskId) => {
        console.log("Generating subtasks for task - Starting process for executableTaskId:", executableTaskId);
        try {
            const currentTaskId = taskInfo.id || taskId;
            const currentStageId = stageId || currentStageData.id;
            let workId = null;
            if (currentStageData?.work_packages) {
                for (const wp of currentStageData.work_packages) {
                    if (wp.tasks?.some(et => et.id === executableTaskId)) {
                        workId = wp.id;
                        break;
                    }
                }
            }
            if (!currentTaskId || !currentStageId || !workId || !executableTaskId) {
                throw new Error("Task, Stage, Work, or Executable Task ID missing.");
            }

            console.log("Generating subtasks for task - Calling API with:", { currentTaskId, currentStageId, workId, executableTaskId });
            const generatedSubtasks = await generateSubtasksForTask(currentTaskId, currentStageId, workId, executableTaskId);
            console.log("Generating subtasks for task - API response:", generatedSubtasks);

            setCurrentStageData(prevStageData => {
                 if (!prevStageData?.work_packages) return prevStageData;
                 const newWorkPackages = prevStageData.work_packages.map(wp => {
                     if (wp.id !== workId || !wp.tasks) return wp;
                     const newTasks = wp.tasks.map(et => {
                         if (et.id !== executableTaskId) return et;
                         return { ...et, subtasks: generatedSubtasks || [] };
                     });
                     return { ...wp, tasks: newTasks };
                 });
                 const updated = { ...prevStageData, work_packages: newWorkPackages };
                 console.log("Generating subtasks for task - Updated stage data:", updated);
                 return updated;
            });

            toast.showSuccess(`Generated ${generatedSubtasks?.length || 0} subtasks for Executable Task ${executableTaskId}.`);
        } catch (error) {
            const errorMsg = error.message || `Unknown error generating subtasks for ${executableTaskId}.`;
            console.error("Generating subtasks for task - Error:", errorMsg);
            toast.showError(`Error generating subtasks: ${errorMsg}`);
            throw error; // Re-throw for local handling in ExecutableTaskDisplay
        } finally {
            console.log("Generating subtasks for task - Process completed for executableTaskId:", executableTaskId);
        }
    };
    // --- End Handler Functions ---

    const stage = currentStageData;
    const backTaskId = taskInfo.id || taskId;

    // Helper to check if any work package has executable tasks
    const checkIfAnyTaskExists = () => {
        return stage?.work_packages?.some(wp => wp.tasks && wp.tasks.length > 0);
    };
    const anyTaskExists = checkIfAnyTaskExists();

    // Log stage data before rendering to check what's causing the UI to show "generate work packages"
    console.log("StageDetailPage - Render data:", {
        stageId: stage.id,
        hasWorkPackages: stage.work_packages ? true : false, 
        workPackagesLength: stage.work_packages?.length || 0,
        workPackages: stage.work_packages,
        isGeneratingWork,
        workGenerationError
    });

    return (
        <div className="min-h-screen bg-gray-50 pb-12 w-full">
            {/* Header */}
             <header className="sticky top-0 z-10 bg-white border-b border-gray-200 w-full">
                 <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
                    <div className="h-16 flex items-center w-full">
                        <button onClick={() => navigate(`/tasks/${backTaskId}`)} className="mr-4 text-gray-600 hover:text-gray-900" title="Back to Task">
                            <ArrowLeft className="w-5 h-5" />
                        </button>
                        <div className="flex-1 min-w-0 w-full">
                            <nav className="flex items-center space-x-1 text-sm text-gray-500 truncate w-full">
                                <Link to={`/tasks/${backTaskId}`} className="hover:text-gray-700 flex-shrink-0" title={taskInfo.shortDescription}>Task:</Link>
                                <span className="truncate flex-1 mx-1" title={taskInfo.shortDescription}>{taskInfo.shortDescription || backTaskId}</span>
                                <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
                                <span className="font-medium text-gray-700 flex-shrink-0">Stage {stage.id}</span>
                            </nav>
                             <h1 className="text-xl font-bold text-gray-900 truncate" title={stage.name}>Stage {stage.id}: {stage.name}</h1>
                        </div>
                    </div>
                </div>
            </header>

            {/* Content Grid */}
            <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
                 <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 w-full">

                    {/* Main Content Area */}
                    <div className="lg:col-span-3 space-y-6 w-full">
                        <InfoCard title="Stage Overview">
                            <p className="text-gray-700 w-full">{stage.description}</p>
                        </InfoCard>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full">
                             {stage.result?.length > 0 && (
                                <InfoCard title="Expected Results">
                                     <ul className="space-y-1 pl-5 list-disc text-sm text-gray-700 w-full">
                                        {stage.result.map((res, index) => ( <li key={`res-${index}`}>{res}</li> ))}
                                    </ul>
                                </InfoCard>
                            )}
                             {stage.what_should_be_delivered?.length > 0 && (
                                <InfoCard title="Tangible Deliverables">
                                     <ul className="space-y-1 pl-5 list-disc text-sm text-gray-700 w-full">
                                        {stage.what_should_be_delivered.map((del, index) => ( <li key={`del-${index}`}>{del}</li> ))}
                                    </ul>
                                </InfoCard>
                            )}
                        </div>

                         {stage.checkpoints?.length > 0 && (
                             <CollapsibleSection title="Checkpoints" defaultOpen={false}>
                                 <div className="space-y-4 w-full">
                                    {stage.checkpoints.map((checkpoint, index) => (
                                        <div key={`cp-${index}`} className="border border-gray-200 rounded-lg p-4 bg-white w-full">
                                            <div className="flex items-start gap-3 w-full">
                                                 <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                                                <div className="w-full">
                                                    <h4 className="font-medium text-gray-900">{checkpoint.checkpoint}</h4>
                                                    <p className="text-sm text-gray-600 mt-1">{checkpoint.description}</p>
                                                    {checkpoint.artifact && <ArtifactDisplay artifact={checkpoint.artifact} />}
                                                     {checkpoint.validations?.length > 0 && (
                                                        <div className="mt-3 w-full">
                                                            <h5 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Validations</h5>
                                                             <ul className="space-y-1 pl-5 list-disc text-sm text-gray-600 w-full">
                                                                {checkpoint.validations.map((val, valIdx) => ( <li key={`val-${index}-${valIdx}`}>{val}</li> ))}
                                                            </ul>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </CollapsibleSection>
                        )}


                        {/* Modified Work Packages Section */}
                        <CollapsibleSection
                            title="Work Packages"
                            defaultOpen={true}
                        >
                            {isGeneratingWork && (
                                <div className="text-center py-10 px-4 w-full">
                                    <RefreshCw className="w-8 h-8 text-blue-600 mx-auto animate-spin mb-3" />
                                    <p className="text-gray-600">Generating work packages...</p>
                                </div>
                            )}
                            {!isGeneratingWork && workGenerationError && (
                                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative mb-4 w-full" role="alert">
                                    <strong className="font-bold">Error!</strong> <span className="block sm:inline ml-2">{workGenerationError}</span>
                                    <button onClick={() => setWorkGenerationError(null)} className="absolute top-0 bottom-0 right-0 px-4 py-3"><span className="text-xl leading-none">×</span></button>
                                </div>
                            )}

                            {/* --- NEW: Loading/Error Display for Stage-Level Task Generation --- */}
                             {isGeneratingAllTasksForStage && (
                                <div className="text-center py-6 px-4 w-full border-t border-gray-200 mt-4">
                                    <RefreshCw className="w-8 h-8 text-blue-600 mx-auto animate-spin mb-3" />
                                    <p className="text-gray-600">Generating tasks for the entire stage...</p>
                                </div>
                            )}
                            {!isGeneratingAllTasksForStage && allTasksForStageError && (
                                <div className="bg-red-100 border border-red-300 text-red-700 px-4 py-3 rounded relative mb-4 mt-4 w-full" role="alert">
                                    <strong className="font-bold">Stage Task Error!</strong>
                                    <span className="block sm:inline ml-2">{allTasksForStageError}</span>
                                    <button onClick={() => setAllTasksForStageError(null)} className="absolute top-0 bottom-0 right-0 px-4 py-3"><span className="text-xl leading-none">×</span></button>
                                </div>
                            )}
                             {/* --- END: Stage-Level Loading/Error --- */}

                             {!isGeneratingWork && !workGenerationError && !isGeneratingAllTasksForStage && ( // Only show content if work generation isn't running/failed
                                (!stage.work_packages || stage.work_packages.length === 0) ? (
                                    <div className="text-center py-6 px-4 w-full">
                                        <Layers className="w-10 h-10 text-gray-400 mx-auto mb-3" />
                                        <p className="text-gray-600">No work packages generated yet.</p>
                                        <button onClick={handleGenerateWork} disabled={isGeneratingWork || isGeneratingAllTasksForStage} className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 inline-flex items-center gap-2">
                                            <Cpu className="w-4 h-4" /> Generate Work Packages
                                        </button>
                                    </div>
                                ) : (
                                     <div className="space-y-4 w-full pt-4 border-t border-gray-200 mt-4"> {/* Add top border/padding */}
                                         <div className="flex justify-end items-center gap-2 mb-2 w-full">                                            
                                             <button onClick={handleGenerateWork} disabled={isGeneratingWork || isGeneratingAllTasksForStage} className="px-3 py-1.5 text-xs bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50 inline-flex items-center gap-1" title="Regenerate Work Packages">
                                                <RefreshCw className="w-3 h-3" /> Regenerate Work
                                            </button>
                                            {/* --- MOVED: Generate All Tasks for Stage Button --- */}
                                            {stage.work_packages && stage.work_packages.length > 0 && (
                                                <button
                                                    onClick={handleGenerateAllTasksForStage}
                                                    disabled={isGeneratingWork || isGeneratingAllTasksForStage}
                                                    className="px-3 py-1.5 text-xs bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-1"
                                                    title={anyTaskExists ? "Regenerate All Tasks for Stage" : "Generate All Tasks for Stage"}
                                                >
                                                    {isGeneratingAllTasksForStage ? (
                                                        <RefreshCw className="w-3 h-3 animate-spin" />
                                                    ) : (
                                                        <Workflow className="w-3 h-3" />
                                                    )}
                                                    {anyTaskExists ? 'Regen Stage Tasks' : 'Gen Stage Tasks'}
                                                </button>
                                            )}
                                        </div>
                                        {stage.work_packages.map((work) => (
                                            <WorkPackageCard
                                                key={work.id}
                                                work={work}
                                                taskId={taskInfo.id || taskId}
                                                stageId={stage.id}
                                                // Pass down handlers and states for INDIVIDUAL work/subtask generation
                                                onGenerateTasks={handleGenerateAllTasksForWork}
                                                onGenerateAllTasks={handleGenerateAllTasksForWork}
                                                isGeneratingAllTasks={generatingAllTasksForWorkId === work.id}
                                                allTasksError={allTasksGenerationErrors[work.id]}
                                                onGenerateAllSubtasks={handleGenerateAllSubtasksForWork}
                                                isGeneratingAllSubtasks={generatingAllSubtasksForWorkId === work.id}
                                                allSubtasksError={allSubtasksGenerationErrors[work.id]}
                                                onGenerateSubtasks={handleGenerateSubtasksForTask}
                                            />
                                        ))}
                                    </div>
                                )
                            )}
                        </CollapsibleSection>
                        {/* End Modified Work Packages Section */}

                    </div> {/* End Main Content Area */}

                    {/* Sidebar Area */}
                    <div className="lg:col-span-2 w-full">
                        <div className="sticky top-24 space-y-6 w-full">
                            <StageOverviewPanel stage={stage} />
                        </div>
                    </div> {/* End Sidebar Area */}

                 </div> {/* End Content Grid */}
            </div>
        </div>
    );
}