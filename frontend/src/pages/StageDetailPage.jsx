// src/pages/StageDetailPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useLocation, Link, useNavigate } from 'react-router-dom';
import {
    ArrowLeft, CheckCircle2, ChevronRight, FileText, ShieldCheck, Layers, Cpu, Activity, Clock, Check, AlertCircle, Info, RefreshCw, TerminalSquare, ChevronsRight, Download, Upload
} from 'lucide-react';
import { InfoCard, CollapsibleSection } from '../components/task/TaskComponents';
import { useToast } from '../components/common/ToastProvider';
// Import the new API function and the display component
import { generateWorkForStage, generateTasksForWork } from '../utils/api';
import { ExecutableTaskDisplay } from '../components/task/ExecutableTaskDisplay'; // Import the new component

// Helper component for Artifacts (assuming it's defined or imported correctly)
// Make sure ArtifactDisplay is exported if it's in a separate file
export const ArtifactDisplay = ({ artifact, title = "Artifact" }) => (
    <div className="mt-3 p-3 bg-gray-50 rounded-md border border-gray-200">
        <h4 className="text-sm font-medium text-gray-700 mb-2">{title}</h4>
        <div className="flex items-start gap-2">
            <FileText className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
            <div>
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

// Modified WorkPackageCard - Now includes Executable Tasks section
const WorkPackageCard = ({ work, onGenerateTasks, isGeneratingTasks, taskGenerationError }) => {
    const [isExpanded, setIsExpanded] = useState(false);

    // Determine button state and text
    const hasTasks = work.tasks && work.tasks.length > 0;
    let generateButtonText = 'Generate Tasks';
    if (isGeneratingTasks) {
        generateButtonText = 'Generating...';
    } else if (hasTasks) {
        generateButtonText = 'Regenerate Tasks';
    }

    return (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
            <button
                className="w-full text-left p-4 flex justify-between items-center hover:bg-gray-50"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div>
                    <h4 className="font-semibold text-gray-900">{work.name} <span className="text-sm font-normal text-gray-500">(Seq: {work.sequence_order})</span></h4>
                    <p className="text-sm text-gray-600 line-clamp-1">{work.description}</p>
                </div>
                <ChevronRight className={`w-5 h-5 text-gray-400 transform transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
            </button>

            {isExpanded && (
                <div className="p-4 border-t border-gray-200 bg-gray-50 space-y-4">
                    {/* Existing Work Details */}
                    <p className="text-sm text-gray-800">{work.description}</p>
                    {/* ... other work details like dependencies, inputs, outcomes ... */}
                    {work.dependencies?.length > 0 && (
                        <div className="text-xs text-gray-600 flex items-center gap-2">
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
                         <div>
                            <h5 className="text-sm font-medium text-gray-700 mb-1 flex items-center gap-1"><Download className="w-3 h-3"/> Required Inputs:</h5>
                            <div className="space-y-2">
                                {work.required_inputs.map((artifact, idx) => (
                                    <ArtifactDisplay key={`in-${idx}`} artifact={artifact} title="" />
                                ))}
                            </div>
                        </div>
                    )}

                     <div>
                        <h5 className="text-sm font-medium text-gray-700 mb-1">Expected Outcome:</h5>
                        <p className="text-sm text-gray-700 italic">{work.expected_outcome}</p>
                    </div>

                    {work.generated_artifacts?.length > 0 && (
                         <div>
                            <h5 className="text-sm font-medium text-gray-700 mb-1 flex items-center gap-1"><Upload className="w-3 h-3"/> Generated Artifacts:</h5>
                            <div className="space-y-2">
                                {work.generated_artifacts.map((artifact, idx) => (
                                    <ArtifactDisplay key={`out-${idx}`} artifact={artifact} title="" />
                                ))}
                            </div>
                        </div>
                    )}

                    {work.validation_criteria?.length > 0 && (
                        <div>
                            <h5 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                                <ShieldCheck className="w-4 h-4 text-green-600" /> Validation Criteria:
                            </h5>
                            <ul className="space-y-1 pl-5 list-disc text-sm text-gray-600">
                                {work.validation_criteria.map((criterion, index) => (
                                    <li key={`val-${index}`}>{criterion}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* --- NEW: Executable Tasks Section --- */}
                    <div className="pt-4 mt-4 border-t border-gray-200">
                        <h5 className="text-base font-semibold text-gray-800 mb-3 flex items-center gap-2">
                            <TerminalSquare className="w-5 h-5 text-purple-600" />
                            Executable Tasks
                        </h5>

                        {/* Task Generation Loading State */}
                        {isGeneratingTasks && (
                            <div className="text-center py-6">
                                <RefreshCw className="w-6 h-6 text-blue-600 mx-auto animate-spin mb-2" />
                                <p className="text-sm text-gray-600">Generating executable tasks...</p>
                            </div>
                        )}

                        {/* Task Generation Error State */}
                        {!isGeneratingTasks && taskGenerationError && (
                            <div className="bg-red-100 border border-red-300 text-red-700 px-3 py-2 rounded text-sm mb-3 flex items-center gap-2">
                                <AlertCircle className="w-4 h-4" />
                                Error: {taskGenerationError}
                                {/* Optional: Add a retry button here */}
                            </div>
                        )}

                        {/* Task List or Generate Button */}
                        {!isGeneratingTasks && !taskGenerationError && (
                            <>
                                {hasTasks ? (
                                    <div className="space-y-3">
                                        {work.tasks.map((task, index) => (
                                            <ExecutableTaskDisplay key={task.id || index} task={task} taskIndex={index} />
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-sm text-gray-500 italic">No executable tasks generated yet.</p>
                                )}

                                {/* Generate/Regenerate Button */}
                                <div className="mt-4 text-right">
                                    <button
                                        onClick={() => onGenerateTasks(work.id)}
                                        disabled={isGeneratingTasks}
                                        className="px-3 py-1.5 text-xs bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-1"
                                    >
                                        {isGeneratingTasks ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Cpu className="w-3 h-3" />}
                                        {generateButtonText}
                                    </button>
                                </div>
                            </>
                        )}
                    </div>
                    {/* --- END: Executable Tasks Section --- */}
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
    const [taskInfo] = useState({
        shortDescription: location.state?.taskShortDescription,
        id: location.state?.taskId
    });
    const [isGeneratingWork, setIsGeneratingWork] = useState(false);
    const [workGenerationError, setWorkGenerationError] = useState(null);
    // NEW State for Task Generation
    const [generatingTasksForWorkId, setGeneratingTasksForWorkId] = useState(null); // Track which work ID is generating tasks
    const [taskGenerationErrors, setTaskGenerationErrors] = useState({}); // Map workId to error message
    // --- End State Management ---

    // Effect to handle missing initial state
    useEffect(() => {
        if (!currentStageData && taskId) {
            console.warn("Stage data missing from location state. Consider fetching task data.");
        }
         setIsGeneratingWork(false);
         setWorkGenerationError(null);
         setGeneratingTasksForWorkId(null);
         setTaskGenerationErrors({});
    }, [currentStageData, taskId, stageId]);

    // Error handling if data is missing
    if (!currentStageData) {
        const backTaskId = taskInfo.id || taskId;
        return (
             <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
                <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full text-center">
                    <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                    <h2 className="text-xl font-semibold text-red-700 mb-2">Error</h2>
                    <p className="text-gray-600 mb-6">Stage details not found. Please navigate from the main task page.</p>
                    <button
                        onClick={() => navigate(`/tasks/${backTaskId}`)}
                        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                        Go Back to Task
                    </button>
                </div>
            </div>
        );
    }

    // --- Handler Functions ---
    const handleGenerateWork = async () => {
        setIsGeneratingWork(true);
        setWorkGenerationError(null);
        try {
            const currentTaskId = taskInfo.id || taskId;
            const currentStageId = stageId || currentStageData.id;
            if (!currentTaskId || !currentStageId) throw new Error("Task ID or Stage ID missing.");

            const generatedWorkPackages = await generateWorkForStage(currentTaskId, currentStageId);
            setCurrentStageData(prev => ({ ...prev, work_packages: generatedWorkPackages || [] }));
            toast.showSuccess(`Successfully generated ${generatedWorkPackages?.length || 0} work packages.`);
        } catch (error) {
            const errorMsg = error.message || "Unknown error generating work.";
            setWorkGenerationError(errorMsg);
            toast.showError(`Error generating work: ${errorMsg}`);
        } finally {
            setIsGeneratingWork(false);
        }
    };

    // NEW Handler for Generating Tasks for a specific Work package
    const handleGenerateTasksForWork = async (workId) => {
        setGeneratingTasksForWorkId(workId); // Set loading state for this specific workId
        setTaskGenerationErrors(prev => ({ ...prev, [workId]: null })); // Clear previous error for this workId
        try {
            const currentTaskId = taskInfo.id || taskId;
            const currentStageId = stageId || currentStageData.id;
            if (!currentTaskId || !currentStageId || !workId) throw new Error("Task, Stage, or Work ID missing.");

            const generatedTasks = await generateTasksForWork(currentTaskId, currentStageId, workId);

            // Update the currentStageData state IMMUTABLY
            setCurrentStageData(prevStageData => {
                if (!prevStageData || !prevStageData.work_packages) return prevStageData;

                // Find the index of the work package to update
                const workIndex = prevStageData.work_packages.findIndex(wp => wp.id === workId);
                if (workIndex === -1) return prevStageData; // Work package not found

                // Create a new work_packages array
                const newWorkPackages = [...prevStageData.work_packages];

                // Create a new work package object with the updated tasks
                newWorkPackages[workIndex] = {
                    ...newWorkPackages[workIndex],
                    tasks: generatedTasks || [] // Ensure tasks is always an array
                };

                // Return the new stage data object
                return {
                    ...prevStageData,
                    work_packages: newWorkPackages
                };
            });

            toast.showSuccess(`Generated ${generatedTasks?.length || 0} tasks for Work ID ${workId}.`);

        } catch (error) {
            const errorMsg = error.message || `Unknown error generating tasks for ${workId}.`;
            setTaskGenerationErrors(prev => ({ ...prev, [workId]: errorMsg })); // Store error by workId
            toast.showError(`Error generating tasks: ${errorMsg}`);
        } finally {
            setGeneratingTasksForWorkId(null); // Clear loading state
        }
    };
    // --- End Handler Functions ---

    const stage = currentStageData;
    const backTaskId = taskInfo.id || taskId;

    return (
        <div className="min-h-screen bg-gray-50 pb-12">
            {/* Header */}
            <header className="sticky top-0 z-10 bg-white border-b border-gray-200">
                 <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="h-16 flex items-center">
                        <button onClick={() => navigate(`/tasks/${backTaskId}`)} className="mr-4 text-gray-600 hover:text-gray-900" title="Back to Task">
                            <ArrowLeft className="w-5 h-5" />
                        </button>
                        <div className="flex-1 min-w-0">
                            <nav className="flex items-center space-x-1 text-sm text-gray-500 truncate">
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

             {/* Content */}
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">

                <InfoCard title="Stage Overview">
                    <p className="text-gray-700">{stage.description}</p>
                </InfoCard>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* ... Results & Deliverables ... */}
                     {stage.result?.length > 0 && (
                        <InfoCard title="Expected Results">
                             <ul className="space-y-1 pl-5 list-disc text-sm text-gray-700">
                                {stage.result.map((res, index) => ( <li key={`res-${index}`}>{res}</li> ))}
                            </ul>
                        </InfoCard>
                    )}
                     {stage.what_should_be_delivered?.length > 0 && (
                        <InfoCard title="Tangible Deliverables">
                             <ul className="space-y-1 pl-5 list-disc text-sm text-gray-700">
                                {stage.what_should_be_delivered.map((del, index) => ( <li key={`del-${index}`}>{del}</li> ))}
                            </ul>
                        </InfoCard>
                    )}
                </div>

                 {stage.checkpoints?.length > 0 && (
                     <CollapsibleSection title="Checkpoints" defaultOpen={false}>
                         <div className="space-y-4">
                            {stage.checkpoints.map((checkpoint, index) => (
                                <div key={`cp-${index}`} className="border border-gray-200 rounded-lg p-4 bg-white">
                                    <div className="flex items-start gap-3">
                                         <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                                        <div>
                                            <h4 className="font-medium text-gray-900">{checkpoint.checkpoint}</h4>
                                            <p className="text-sm text-gray-600 mt-1">{checkpoint.description}</p>
                                            {checkpoint.artifact && <ArtifactDisplay artifact={checkpoint.artifact} />}
                                            {/* ... validations ... */}
                                             {checkpoint.validations?.length > 0 && (
                                                <div className="mt-3">
                                                    <h5 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Validations</h5>
                                                     <ul className="space-y-1 pl-5 list-disc text-sm text-gray-600">
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

                 {/* Modified Work Packages Section with Task Generation */}
                <CollapsibleSection title="Work Packages" defaultOpen={true}>
                    {/* Work Generation Loading State */}
                    {isGeneratingWork && (
                        <div className="text-center py-10 px-4">
                            <RefreshCw className="w-8 h-8 text-blue-600 mx-auto animate-spin mb-3" />
                            <p className="text-gray-600">Generating work packages...</p>
                        </div>
                    )}

                    {/* Work Generation Error State */}
                    {!isGeneratingWork && workGenerationError && (
                        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
                            <strong className="font-bold">Error!</strong> <span className="block sm:inline ml-2">{workGenerationError}</span>
                            <button onClick={() => setWorkGenerationError(null)} className="absolute top-0 bottom-0 right-0 px-4 py-3"><span className="text-xl leading-none">×</span></button>
                        </div>
                    )}

                    {/* Content: Button or Work Packages List */}
                    {!isGeneratingWork && !workGenerationError && (
                        (!stage.work_packages || stage.work_packages.length === 0) ? (
                            <div className="text-center py-6 px-4">
                                <Layers className="w-10 h-10 text-gray-400 mx-auto mb-3" />
                                <p className="text-gray-600">No work packages generated yet.</p>
                                <button onClick={handleGenerateWork} disabled={isGeneratingWork} className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 inline-flex items-center gap-2">
                                    <Cpu className="w-4 h-4" /> Generate Work Packages
                                </button>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {/* Regenerate Work Button */}
                                <div className="flex justify-end mb-2">
                                     <button onClick={handleGenerateWork} disabled={isGeneratingWork} className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50 inline-flex items-center gap-1" title="Regenerate Work Packages">
                                        <RefreshCw className="w-3 h-3" /> Regenerate Work
                                    </button>
                                </div>
                                {/* Render Work Packages */}
                                {stage.work_packages.map((work) => (
                                    <WorkPackageCard
                                        key={work.id}
                                        work={work}
                                        // Pass task generation props
                                        onGenerateTasks={handleGenerateTasksForWork}
                                        isGeneratingTasks={generatingTasksForWorkId === work.id}
                                        taskGenerationError={taskGenerationErrors[work.id]}
                                    />
                                ))}
                            </div>
                        )
                    )}
                </CollapsibleSection>
                {/* End Modified Work Packages Section */}
            </div>
        </div>
    );
}