// src/hooks/useStageDetails.js
import { useState, useEffect, useCallback } from 'react';
import { useToast } from '../components/common/ToastProvider';
import {
    generateWorkForStage,
    generateAllTasksForWork,
    generateAllSubtasksForWork,
    generateSubtasksForTask,
    fetchTaskDetails,
    generateAllTasksForStage
} from '../utils/api';

/**
 * Custom hook to manage state and operations for the StageDetailPage.
 * @param {string} taskId - The ID of the parent task.
 * @param {string} stageId - The ID of the current stage.
 * @param {object | null} initialStageData - Initial stage data passed via location state.
 * @param {object | null} initialTaskInfo - Initial task info passed via location state.
 * @returns {object} State variables and handler functions.
 */
export function useStageDetails(taskId, stageId, initialStageData, initialTaskInfo) {
    const toast = useToast();

    // --- State Management ---
    const [currentStageData, setCurrentStageData] = useState(initialStageData);
    const [taskInfo, setTaskInfo] = useState(initialTaskInfo || { id: taskId, shortDescription: '' });
    const [isLoadingData, setIsLoadingData] = useState(!initialStageData);
    const [isDataInitialized, setIsDataInitialized] = useState(!!initialStageData); // Initialize based on initial data presence
    const [isGeneratingWork, setIsGeneratingWork] = useState(false);
    const [workGenerationError, setWorkGenerationError] = useState(null); // Keep setter internal if only used here
    const [generatingAllTasksForWorkId, setGeneratingAllTasksForWorkId] = useState(null);
    const [allTasksGenerationErrors, setAllTasksGenerationErrors] = useState({});
    const [generatingAllSubtasksForWorkId, setGeneratingAllSubtasksForWorkId] = useState(null);
    const [allSubtasksGenerationErrors, setAllSubtasksGenerationErrors] = useState({});
    const [isGeneratingAllTasksForStage, setIsGeneratingAllTasksForStage] = useState(false);
    const [allTasksForStageError, setAllTasksForStageError] = useState(null); // Keep setter internal
    // --- End State Management ---

    // --- Data Fetching ---
    const fetchStageData = useCallback(async () => {
        if (!taskId) {
            console.error("Cannot fetch stage data: taskId is missing");
            toast.showError("Task ID is missing, cannot load stage data.");
            setIsLoadingData(false);
            return;
        }
        
        console.log(`Fetching stage data for task ${taskId}, stage ${stageId}`);
        setIsLoadingData(true);
        setWorkGenerationError(null); // Clear errors on fetch
        setAllTasksForStageError(null);
        
        // Set a timeout to prevent infinite loading
        const timeout = setTimeout(() => {
            if (setIsLoadingData) {
                console.warn(`Fetch timeout reached for stage ${stageId}, forcing loading state to false`);
                setIsLoadingData(false);
                toast.showError("Loading stage data timed out. Please try again.");
            }
        }, 10000); // 10 seconds timeout
        
        try {
            const taskData = await fetchTaskDetails(taskId);
            clearTimeout(timeout); // Clear the timeout on success
            
            if (!taskData || !taskData.network_plan) {
                throw new Error("Task data or network plan is missing");
            }
            
            console.log(`Task data received, looking for stage ${stageId} among ${taskData.network_plan.stages.length} stages`);
            console.log(`Available stage IDs: ${taskData.network_plan.stages.map(s => s.id).join(', ')}`);
            
            const foundStage = taskData.network_plan.stages.find(s => String(s.id) === String(stageId));
            if (!foundStage) {
                throw new Error(`Stage ${stageId} not found in task data`);
            }
            
            console.log(`Found stage ${stageId}, updating state`);
            setCurrentStageData(foundStage);
            setTaskInfo(prev => ({
                ...prev,
                shortDescription: taskData.short_description || taskData.task,
                id: taskData.id // Ensure task ID is updated if needed
            }));
            setIsDataInitialized(true); // Mark as initialized on successful fetch
        } catch (error) {
            clearTimeout(timeout); // Clear the timeout on error
            console.error("Error fetching task/stage data:", error);
            toast.showError(`Error loading stage data: ${error.message}`);
            // Keep potential old data, but stop loading
        } finally {
            clearTimeout(timeout); // Ensure timeout is cleared
            setIsLoadingData(false);
            console.log(`Finished loading stage ${stageId}`);
        }
    }, [taskId, stageId, toast]); // Removed fetchStageData from its own dependencies

    // Effect to fetch data if initial state is missing or when stageId/taskId changes
    useEffect(() => {
        // Reset errors
        setWorkGenerationError(null);
        setAllTasksForStageError(null);
        setGeneratingAllTasksForWorkId(null);
        setAllTasksGenerationErrors({});
        setGeneratingAllSubtasksForWorkId(null);
        setAllSubtasksGenerationErrors({});
        setIsGeneratingAllTasksForStage(false);
        setIsGeneratingWork(false);
        // Reset initialization flag ONLY if taskId or stageId changes
        //setIsDataInitialized(false); // Let's manage this more carefully below
        
        // Update stage data if we have initialStageData that matches the current stageId
        if (!isDataInitialized && initialStageData && String(initialStageData.id) === String(stageId)) {
            console.log(`Using initial stage data for stage ${stageId}`);
            setCurrentStageData(initialStageData);
            setIsLoadingData(false);
            setIsDataInitialized(true); // Mark as initialized
            return;
        }
        
        // If we don't have data or the stageId/taskId changed, we need to fetch
        const needsFetch = !isDataInitialized || 
                           (currentStageData && String(currentStageData.id) !== String(stageId)) ||
                           (taskInfo && taskId && String(taskInfo.id) !== String(taskId));

        if (needsFetch && taskId && stageId) {
            console.log(`Fetching data for stage ${stageId}, current stage data: ${currentStageData?.id || 'none'}`);
            
            // Important: Keep old data visible during loading to reduce flickering
            if (currentStageData) {
                // Don't set loading to true immediately to prevent flashing
                // Instead fetch in background first
                (async () => {
                    try {
                        const taskData = await fetchTaskDetails(taskId);
                        if (!taskData || !taskData.network_plan) {
                            throw new Error("Task data or network plan is missing");
                        }
                        
                        const foundStage = taskData.network_plan.stages.find(s => String(s.id) === String(stageId));
                        if (!foundStage) {
                            throw new Error(`Stage ${stageId} not found in task data`);
                        }
                        
                        setCurrentStageData(foundStage);
                        setTaskInfo(prev => ({
                            ...prev,
                            shortDescription: taskData.short_description || taskData.task,
                            id: taskData.id
                        }));
                        setIsLoadingData(false);
                        setIsDataInitialized(true); // Mark as initialized
                    } catch (error) {
                        console.error("Error background-fetching stage data:", error);
                        // Now show loading state since we couldn't fetch in background
                        setIsLoadingData(true);
                        fetchStageData();
                    }
                })();
            } else {
                // No current data, show loading state immediately
                setIsLoadingData(true);
                fetchStageData();
            }
        } else {
            // If we have data (either initial or fetched), ensure loading is false
            if (currentStageData && String(currentStageData.id) === String(stageId)) {
                setIsLoadingData(false);
                // Ensure initialized flag is set if we landed here with valid data
                if (!isDataInitialized) setIsDataInitialized(true);
            }
        }
    }, [taskId, stageId, initialStageData, fetchStageData, isDataInitialized]); // Removed currentStageData, added isDataInitialized

    // --- Handler Functions ---
    const handleGenerateWork = useCallback(async () => {
        setIsGeneratingWork(true);
        setWorkGenerationError(null);
        setAllTasksForStageError(null); // Clear stage-level errors too
        try {
            const currentTaskId = taskInfo.id || taskId;
            if (!currentTaskId || !stageId) throw new Error("Task ID or Stage ID missing.");

            const generatedWorkPackages = await generateWorkForStage(currentTaskId, stageId);

            if (!generatedWorkPackages || !Array.isArray(generatedWorkPackages)) {
                await fetchStageData(); // Fetch full data if API response is weird
                toast.showSuccess("Work packages generated. Refreshed stage data.");
            } else {
                // Simplified state update without JSON stringify/parse
                setCurrentStageData(prev => {
                    console.log("Updating state with NEW work packages:", generatedWorkPackages);
                    return {
                        ...prev,
                        work_packages: generatedWorkPackages
                    };
                });
                toast.showSuccess(`Successfully generated ${generatedWorkPackages.length} work packages.`);
            }
        } catch (error) {
            const errorMsg = error.message || "Unknown error generating work.";
            setWorkGenerationError(errorMsg); // Use the state setter
            toast.showError(`Error generating work: ${errorMsg}`);
            setTimeout(fetchStageData, 1000); // Attempt recovery fetch
        } finally {
            setIsGeneratingWork(false);
        }
    }, [taskId, stageId, taskInfo.id, fetchStageData, toast]);

    const handleGenerateAllTasksForStage = useCallback(async () => {
        setIsGeneratingAllTasksForStage(true);
        setAllTasksForStageError(null);
        setAllTasksGenerationErrors({}); // Clear individual work errors
        try {
            const currentTaskId = taskInfo.id || taskId;
            if (!currentTaskId || !stageId) throw new Error("Task ID or Stage ID missing.");

            const updatedWorkPackages = await generateAllTasksForStage(currentTaskId, stageId);
            setCurrentStageData(prev => ({ ...prev, work_packages: updatedWorkPackages || [] }));
            toast.showSuccess(`Generated tasks for all work packages in Stage ${stageId}.`);
            setTimeout(fetchStageData, 500); // Refresh data after completion

        } catch (error) {
            const errorMsg = error.message || `Unknown error generating tasks for stage ${stageId}.`;
            setAllTasksForStageError(errorMsg); // Use the state setter
            toast.showError(`Error generating tasks for stage: ${errorMsg}`);
            setTimeout(fetchStageData, 500); // Attempt recovery fetch
        } finally {
            setIsGeneratingAllTasksForStage(false);
        }
    }, [taskId, stageId, taskInfo.id, fetchStageData, toast]);

    // handleGenerateAllTasksForWork, handleGenerateAllSubtasksForWork, handleGenerateSubtasksForTask remain the same
    // ... (keep the existing useCallback definitions for these handlers) ...
    const handleGenerateAllTasksForWork = useCallback(async (workId) => {
        setGeneratingAllTasksForWorkId(workId);
        setAllTasksGenerationErrors(prev => ({ ...prev, [workId]: null }));
        try {
            const currentTaskId = taskInfo.id || taskId;
            if (!currentTaskId || !stageId || !workId) throw new Error("Task, Stage, or Work ID missing.");

            const generatedTasks = await generateAllTasksForWork(currentTaskId, stageId, workId);
            setCurrentStageData(prev => {
                if (!prev?.work_packages) return prev;
                const workIndex = prev.work_packages.findIndex(wp => wp.id === workId);
                if (workIndex === -1) return prev;
                const newWorkPackages = [...prev.work_packages];
                newWorkPackages[workIndex] = { ...newWorkPackages[workIndex], tasks: generatedTasks || [] };
                return { ...prev, work_packages: newWorkPackages };
            });
            toast.showSuccess(`Generated ${generatedTasks?.length || 0} tasks for Work ID ${workId}.`);
        } catch (error) {
            const errorMsg = error.message || `Unknown error generating tasks for ${workId}.`;
            setAllTasksGenerationErrors(prev => ({ ...prev, [workId]: errorMsg }));
            toast.showError(`Error generating tasks: ${errorMsg}`);
        } finally {
            setGeneratingAllTasksForWorkId(null);
        }
    }, [taskId, stageId, taskInfo.id, toast]);

    const handleGenerateAllSubtasksForWork = useCallback(async (workId) => {
        setGeneratingAllSubtasksForWorkId(workId);
        setAllSubtasksGenerationErrors(prev => ({ ...prev, [workId]: null }));
        try {
            const currentTaskId = taskInfo.id || taskId;
            if (!currentTaskId || !stageId || !workId) throw new Error("Task, Stage, or Work ID missing.");

            const updatedTasksWithSubtasks = await generateAllSubtasksForWork(currentTaskId, stageId, workId);
            setCurrentStageData(prev => {
                if (!prev?.work_packages) return prev;
                const workIndex = prev.work_packages.findIndex(wp => wp.id === workId);
                if (workIndex === -1) return prev;
                const newWorkPackages = [...prev.work_packages];
                newWorkPackages[workIndex] = { ...newWorkPackages[workIndex], tasks: updatedTasksWithSubtasks || [] };
                return { ...prev, work_packages: newWorkPackages };
            });
            const totalSubtasks = updatedTasksWithSubtasks.reduce((sum, task) => sum + (task.subtasks?.length || 0), 0);
            toast.showSuccess(`Generated ${totalSubtasks} subtasks across ${updatedTasksWithSubtasks?.length || 0} tasks for Work ID ${workId}.`);
        } catch (error) {
            const errorMsg = error.message || `Unknown error generating subtasks for ${workId}.`;
            setAllSubtasksGenerationErrors(prev => ({ ...prev, [workId]: errorMsg }));
            toast.showError(`Error generating subtasks: ${errorMsg}`);
        } finally {
            setGeneratingAllSubtasksForWorkId(null);
        }
    }, [taskId, stageId, taskInfo.id, toast]);

    const handleGenerateSubtasksForTask = useCallback(async (executableTaskId) => {
        // Find the workId associated with the executableTaskId
        let workId = null;
        if (currentStageData?.work_packages) {
            for (const wp of currentStageData.work_packages) {
                if (wp.tasks?.some(et => et.id === executableTaskId)) {
                    workId = wp.id;
                    break;
                }
            }
        }
        if (!workId) {
            toast.showError(`Could not find parent Work package for Executable Task ${executableTaskId}`);
            throw new Error("Parent Work ID not found");
        }

        const currentTaskId = taskInfo.id || taskId;
        if (!currentTaskId || !stageId) throw new Error("Task or Stage ID missing.");

        try {
            const generatedSubtasks = await generateSubtasksForTask(currentTaskId, stageId, workId, executableTaskId);
            setCurrentStageData(prev => {
                if (!prev?.work_packages) return prev;
                const newWorkPackages = prev.work_packages.map(wp => {
                    if (wp.id !== workId || !wp.tasks) return wp;
                    const newTasks = wp.tasks.map(et => {
                        if (et.id !== executableTaskId) return et;
                        return { ...et, subtasks: generatedSubtasks || [] };
                    });
                    return { ...wp, tasks: newTasks };
                });
                return { ...prev, work_packages: newWorkPackages };
            });
            toast.showSuccess(`Generated ${generatedSubtasks?.length || 0} subtasks for Executable Task ${executableTaskId}.`);
        } catch (error) {
            const errorMsg = error.message || `Unknown error generating subtasks for ${executableTaskId}.`;
            toast.showError(`Error generating subtasks: ${errorMsg}`);
            throw error; // Re-throw for local handling in ExecutableTaskDisplay
        }
    }, [taskId, stageId, taskInfo.id, currentStageData, toast]);
    // --- End Handler Functions ---

    // Function to reset stage data for reloading
    const resetStageData = useCallback(() => {
        setCurrentStageData(null);
        setIsLoadingData(true);
        setWorkGenerationError(null);
        setAllTasksForStageError(null);
        setGeneratingAllTasksForWorkId(null);
        setAllTasksGenerationErrors({});
        setGeneratingAllSubtasksForWorkId(null);
        setAllSubtasksGenerationErrors({});
        setIsGeneratingAllTasksForStage(false);
    }, []);

    return {
        currentStageData,
        taskInfo,
        isLoadingData,
        isGeneratingWork,
        workGenerationError,
        generatingAllTasksForWorkId,
        allTasksGenerationErrors,
        generatingAllSubtasksForWorkId,
        allSubtasksGenerationErrors,
        isGeneratingAllTasksForStage,
        allTasksForStageError,
        handleGenerateWork,
        handleGenerateAllTasksForStage,
        handleGenerateAllTasksForWork,
        handleGenerateAllSubtasksForWork,
        handleGenerateSubtasksForTask,
        fetchStageData, // Expose fetch function for manual retry
        // Expose error setters for direct use in the component if needed (though internal handling is preferred)
        setWorkGenerationError,
        setAllTasksForStageError,
        resetStageData, // Add the reset function
        isDataInitialized // Add isDataInitialized to the return object
    };
}