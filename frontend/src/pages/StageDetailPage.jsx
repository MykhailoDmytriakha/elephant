// src/pages/StageDetailPage.jsx
import React from 'react';
// Import useLocation
import { useParams, Link, useNavigate, useLocation } from 'react-router-dom';
import {
    ArrowLeft, CheckCircle2, Layers, Cpu, RefreshCw, Workflow, ChevronRight // Added ChevronRight back
} from 'lucide-react'; // Removed AlertCircle
import { InfoCard, CollapsibleSection, LoadingSpinner, ErrorDisplay, ArtifactDisplay } from '../components/task/TaskComponents';
import StageOverviewPanel from '../components/task/StageOverviewPanel';
import WorkPackageCard from '../components/task/WorkPackageCard';
import { useStageDetails } from '../hooks/useStageDetails';

/**
 * Page component to display detailed information about a specific stage within a task.
 * Handles fetching stage data, displaying details, and managing work package generation.
 */
export default function StageDetailPage() {
    const { taskId, stageId } = useParams();
    const navigate = useNavigate();
    const location = useLocation(); // Use useLocation hook

    // Use the custom hook to manage state and logic
    // Pass initial state from location.state
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
        setWorkGenerationError, // Get the setter from the hook
        setAllTasksForStageError // Get the setter from the hook
    } = useStageDetails(
        taskId,
        stageId,
        location.state?.stage, // Pass initial stage data
        location.state // Pass full location state which might contain taskInfo
                      // Adjust based on how you pass data in Metadata.jsx Link state prop
                      // Assuming state = { stage: stage, taskShortDescription: task.short_description, taskId: task.id }
                      ? { id: location.state.taskId, shortDescription: location.state.taskShortDescription }
                      : null
    );

    // Loading state
    if (isLoadingData) {
        return <LoadingSpinner message="Loading Stage Data..." />;
    }

    // Error state if stage data couldn't be loaded
    if (!stage) {
        return (
            <ErrorDisplay
                message="Stage details could not be loaded. Please ensure you navigated from the task page or try again."
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

    return (
        <div className="min-h-screen bg-gray-50 pb-12 w-full">
            {/* Header */}
             <header className="sticky top-0 z-10 bg-white border-b border-gray-200 w-full shadow-sm">
                 <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
                    <div className="h-16 flex items-center w-full">
                        {/* Back Button */}
                        <button
                            onClick={() => navigate(`/tasks/${backTaskId}`)}
                            className="mr-4 text-gray-600 hover:text-gray-900 p-1 rounded-md hover:bg-gray-100 transition-colors"
                            title="Back to Task"
                            aria-label="Back to Task Details"
                        >
                            <ArrowLeft className="w-5 h-5" />
                        </button>
                        {/* Breadcrumbs and Title */}
                        <div className="flex-1 min-w-0 w-full">
                            <nav className="flex items-center space-x-1 text-sm text-gray-500 truncate w-full" aria-label="Breadcrumb">
                                <Link to={`/tasks/${backTaskId}`} className="hover:text-gray-700 flex-shrink-0" title={taskInfo?.shortDescription}>Task:</Link>
                                <span className="truncate flex-1 mx-1" title={taskInfo?.shortDescription}>{taskInfo?.shortDescription || backTaskId}</span>
                                <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0" aria-hidden="true" /> {/* Added ChevronRight back */}
                                <span className="font-medium text-gray-700 flex-shrink-0" aria-current="page">Stage {stage.id}</span>
                            </nav>
                             <h1 className="text-xl font-bold text-gray-900 truncate" title={stage.name}>Stage {stage.id}: {stage.name}</h1>
                        </div>
                    </div>
                </div>
            </header>

            {/* Content Grid */}
            <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
                 <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 w-full">

                    {/* Main Content Area (lg:col-span-3) */}
                    <div className="lg:col-span-3 space-y-6 w-full">
                        {/* Stage Overview Card */}
                        <InfoCard title="Stage Overview">
                            <p className="text-gray-700 w-full">{stage.description}</p>
                        </InfoCard>

                        {/* Results & Deliverables Grid */}
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

                        {/* Checkpoints Section */}
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
                                                    {/* Use the imported ArtifactDisplay */}
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

                        {/* Work Packages Section */}
                        <CollapsibleSection title="Work Packages" defaultOpen={true}>
                            {/* Work Generation Loading State */}
                            {isGeneratingWork && (
                                <div className="text-center py-10 px-4 w-full">
                                    <RefreshCw className="w-8 h-8 text-blue-600 mx-auto animate-spin mb-3" />
                                    <p className="text-gray-600">Generating work packages...</p>
                                </div>
                            )}
                            {/* Work Generation Error State */}
                            {!isGeneratingWork && workGenerationError && (
                                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative mb-4 w-full" role="alert">
                                    <strong className="font-bold">Error!</strong> <span className="block sm:inline ml-2">{workGenerationError}</span>
                                    {/* Use the setter from the hook */}
                                    <button onClick={() => setWorkGenerationError(null)} className="absolute top-0 bottom-0 right-0 px-4 py-3"><span className="text-xl leading-none">×</span></button>
                                </div>
                            )}
                            {/* Stage-Level Task Generation Loading/Error */}
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
                                    {/* Use the setter from the hook */}
                                    <button onClick={() => setAllTasksForStageError(null)} className="absolute top-0 bottom-0 right-0 px-4 py-3"><span className="text-xl leading-none">×</span></button>
                                </div>
                            )}

                             {/* Content: Either "Generate Work" button or the list of WorkPackageCards */}
                             {!isGeneratingWork && !workGenerationError && !isGeneratingAllTasksForStage && (
                                (!stage.work_packages || stage.work_packages.length === 0) ? (
                                    // State when no work packages exist
                                    <div className="text-center py-6 px-4 w-full">
                                        <Layers className="w-10 h-10 text-gray-400 mx-auto mb-3" />
                                        <p className="text-gray-600">No work packages generated yet.</p>
                                        <button
                                            onClick={handleGenerateWork}
                                            disabled={isGeneratingWork || isGeneratingAllTasksForStage}
                                            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 inline-flex items-center gap-2"
                                        >
                                            <Cpu className="w-4 h-4" /> Generate Work Packages
                                        </button>
                                    </div>
                                ) : (
                                    // State when work packages exist
                                     <div className="space-y-4 w-full pt-4 border-t border-gray-200 mt-4">
                                         {/* Action Buttons for existing work packages */}
                                         <div className="flex justify-end items-center gap-2 mb-2 w-full">
                                             <button
                                                onClick={handleGenerateWork} // Regenerate Work
                                                disabled={isGeneratingWork || isGeneratingAllTasksForStage}
                                                className="px-3 py-1.5 text-xs bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50 inline-flex items-center gap-1"
                                                title="Regenerate Work Packages"
                                            >
                                                <RefreshCw className="w-3 h-3" /> Regenerate Work
                                            </button>
                                            {/* Generate All Tasks for Stage Button */}
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
                                        </div>
                                        {/* List of Work Packages */}
                                        {stage.work_packages.map((work) => (
                                            <WorkPackageCard
                                                key={work.id}
                                                work={work}
                                                taskId={taskInfo.id || taskId}
                                                stageId={stage.id}
                                                // Pass down handlers and states from the hook
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

                    </div> {/* End Main Content Area */}

                    {/* Sidebar Area (lg:col-span-2) */}
                    <div className="lg:col-span-2 w-full">
                        <div className="sticky top-24 space-y-6 w-full">
                            {/* Overview Panel */}
                            <StageOverviewPanel stage={stage} />
                            {/* Add other sidebar components if needed */}
                        </div>
                    </div> {/* End Sidebar Area */}

                 </div> {/* End Content Grid */}
            </div>
        </div>
    );
}