// src/pages/StageDetailPage.jsx
import React, { useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { LoadingSpinner, ErrorDisplay } from '../components/task/TaskComponents';
import StageOverviewPanel from '../components/task/StageOverviewPanel';
import StageContent from '../components/task/StageContent';
import StageHeader from '../components/task/StageHeader';
import { useStageDetails } from '../hooks/useStageDetails';
import { useStageNavigation } from '../hooks/useStageNavigation';

/**
 * Wrapper component that provides a key to force remounting when stageId changes
 */
export default function StageDetailPageWrapper() {
    const { taskId } = useParams();
    const location = useLocation();
    
    // Using a combination of taskId and data source (whether we have location state) as part of key
    // This prevents unnecessary remounting when navigating between stages
    const hasLocationState = Boolean(location.state?.stage);
    const dataSource = hasLocationState ? 'fromState' : 'fromFetch';
    
    // Create a stable key that doesn't change just because you click next/prev
    return <StageDetailPage key={`task-${taskId}-${dataSource}`} />;
}

/**
 * Page component to display detailed information about a specific stage within a task.
 * Handles fetching stage data, displaying details, and managing work package generation.
 */
function StageDetailPage() {
    const { taskId, stageId } = useParams();
    const navigate = useNavigate();
    const location = useLocation();
    
    // Use the custom hook to manage state and logic
    const {
        currentStageData: stage,
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
        fetchStageData,
        setWorkGenerationError,
        setAllTasksForStageError
    } = useStageDetails(
        taskId,
        stageId,
        location.state?.stage,
        location.state
            ? { id: location.state.taskId, shortDescription: location.state.taskShortDescription }
            : null
    );

    // Use the stage navigation hook
    const { allStages, isLoadingStages, getStageNavigation } = useStageNavigation(taskId, location);

    // Debug logging to track state
    useEffect(() => {
        console.log(`StageDetailPage: stageId=${stageId}, isLoadingData=${isLoadingData}, stage=${stage?.id}`);
    }, [stageId, isLoadingData, stage]);

    // Loading state
    if (isLoadingData) {
        return <LoadingSpinner message={`Loading Stage ${stageId} Data...`} />;
    }

    // Error state if stage data couldn't be loaded
    if (!stage) {
        return (
            <ErrorDisplay
                message={`Stage ${stageId} details could not be loaded. Please ensure you navigated from the task page or try again.`}
                onRetry={fetchStageData}
            />
        );
    }

    const backTaskId = taskInfo?.id || taskId;

    // Helper to check if any work package has executable tasks
    const checkIfAnyTaskExists = () => {
        return stage?.work_packages?.some(wp => wp.tasks && wp.tasks.length > 0);
    };
    const anyTaskExists = checkIfAnyTaskExists();

    // Navigate to a different stage
    const navigateToStage = (targetStageId) => {
        if (targetStageId) {
            // Find the target stage data in allStages
            const targetStage = allStages.find(s => s.id === targetStageId);
            
            // Pass the current state to avoid unnecessary loading
            navigate(`/tasks/${backTaskId}/stages/${targetStageId}`, {
                state: {
                    stage: targetStage, 
                    taskShortDescription: taskInfo.shortDescription,
                    taskId: backTaskId,
                    // Include the entire stages list to avoid refetching
                    task: { network_plan: { stages: allStages } }
                }
            });
        }
    };

    const { currentStageIndex } = getStageNavigation(stage.id);

    return (
        <div className="min-h-screen bg-gray-50 pb-12 w-full">
            <StageHeader 
                taskInfo={taskInfo}
                stage={stage}
                backTaskId={backTaskId}
                navigate={navigate}
                currentStageIndex={currentStageIndex}
                allStages={allStages}
                isLoadingStages={isLoadingStages}
                navigateToStage={navigateToStage}
                getStageNavigation={getStageNavigation}
            />

            {/* Content Grid */}
            <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
                <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 w-full">
                    {/* Main Content Area */}
                    <StageContent
                        stage={stage}
                        isGeneratingWork={isGeneratingWork}
                        workGenerationError={workGenerationError}
                        isGeneratingAllTasksForStage={isGeneratingAllTasksForStage}
                        allTasksForStageError={allTasksForStageError}
                        handleGenerateWork={handleGenerateWork}
                        handleGenerateAllTasksForStage={handleGenerateAllTasksForStage}
                        handleGenerateAllTasksForWork={handleGenerateAllTasksForWork}
                        handleGenerateAllSubtasksForWork={handleGenerateAllSubtasksForWork}
                        handleGenerateSubtasksForTask={handleGenerateSubtasksForTask}
                        setWorkGenerationError={setWorkGenerationError}
                        setAllTasksForStageError={setAllTasksForStageError}
                        taskInfo={taskInfo}
                        taskId={taskId}
                        anyTaskExists={anyTaskExists}
                        generatingAllTasksForWorkId={generatingAllTasksForWorkId}
                        allTasksGenerationErrors={allTasksGenerationErrors}
                        generatingAllSubtasksForWorkId={generatingAllSubtasksForWorkId}
                        allSubtasksGenerationErrors={allSubtasksGenerationErrors}
                    />

                    {/* Sidebar Area */}
                    <div className="lg:col-span-2 w-full">
                        <div className="sticky top-24 space-y-6 w-full">
                            <StageOverviewPanel stage={stage} />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}