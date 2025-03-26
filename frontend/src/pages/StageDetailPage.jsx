import React, { useState, useEffect } from 'react';
import { useParams, useLocation, Link, useNavigate } from 'react-router-dom';
import {
    ArrowLeft, CheckCircle2, ChevronRight, FileText, ShieldCheck, Layers, Cpu, Activity, Clock, Check, AlertCircle, Info, RefreshCw
} from 'lucide-react';
import { InfoCard, CollapsibleSection } from '../components/task/TaskComponents'; // Reuse existing components
import { useToast } from '../components/common/ToastProvider'; // Import useToast
import { generateWorkForStage } from '../utils/api'; // Import the API function

// Helper component for Artifacts (can be moved to a shared file later)
const ArtifactDisplay = ({ artifact, title = "Artifact" }) => (
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

// Helper component for Work Packages
const WorkPackageCard = ({ work }) => {
    const [isExpanded, setIsExpanded] = useState(false);

    const getStatusColor = (status) => {
        switch (status) {
            case 'PENDING': return 'bg-gray-100 text-gray-700';
            case 'READY': return 'bg-yellow-100 text-yellow-700';
            case 'IN_PROGRESS': return 'bg-blue-100 text-blue-700';
            case 'COMPLETED': return 'bg-green-100 text-green-700';
            case 'FAILED': return 'bg-red-100 text-red-700';
            case 'BLOCKED': return 'bg-orange-100 text-orange-700';
            default: return 'bg-gray-100 text-gray-700';
        }
    };

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
                    <p className="text-sm text-gray-800">{work.description}</p>

                    <div className="grid grid-cols-2 gap-4 text-xs">
                         {work.dependencies?.length > 0 && (
                            <div className="col-span-2">
                                <span className="font-medium text-gray-600 block">Depends On (Work IDs):</span>
                                <div className="flex flex-wrap gap-1">
                                    {work.dependencies.map(depId => (
                                        <span key={depId} className="font-mono text-xs bg-gray-200 px-1.5 py-0.5 rounded">{depId}</span>
                                    ))}
                                </div>
                            </div>
                         )}
                    </div>

                    {work.required_inputs?.length > 0 && (
                         <div>
                            <h5 className="text-sm font-medium text-gray-700 mb-1">Required Inputs:</h5>
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
                            <h5 className="text-sm font-medium text-gray-700 mb-1">Generated Artifacts:</h5>
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
                </div>
            )}
        </div>
    );
};


export default function StageDetailPage() {
    const { taskId, stageId } = useParams();
    const location = useLocation();
    const navigate = useNavigate();
    const toast = useToast(); // Get toast functions

    // --- State Management ---
    const [currentStageData, setCurrentStageData] = useState(location.state?.stage || null);
    const [taskInfo] = useState({ // Store task info separately
        shortDescription: location.state?.taskShortDescription,
        id: location.state?.taskId
    });
    const [isGeneratingWork, setIsGeneratingWork] = useState(false);
    const [generationError, setGenerationError] = useState(null);
    // --- End State Management ---

    // Effect to handle missing initial state (optional but good practice)
    useEffect(() => {
        if (!currentStageData && taskId) {
            console.warn("Stage data missing from location state. Consider fetching task data.");
            // You could potentially fetch the full task here and find the stage,
            // but for now, we rely on the error message below.
        }
         // Reset generation state if stage changes (e.g., if component is reused without full unmount)
         setIsGeneratingWork(false);
         setGenerationError(null);
    }, [currentStageData, taskId, stageId]); // Add stageId to dependencies

    // Handle case where state is missing
    if (!currentStageData) {
        // Use taskInfo.id if available, otherwise taskId from params
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

    // --- Handler Function ---
    const handleGenerateWork = async () => {
        setIsGeneratingWork(true);
        setGenerationError(null);
        try {
            // Ensure we use the correct taskId and stageId
            const currentTaskId = taskInfo.id || taskId;
            const currentStageId = stageId || currentStageData.id;

            if (!currentTaskId || !currentStageId) {
                throw new Error("Task ID or Stage ID is missing.");
            }

            const generatedWorkPackages = await generateWorkForStage(currentTaskId, currentStageId);

            // Update the local stage data state
            setCurrentStageData(prevStageData => ({
                ...prevStageData,
                work_packages: generatedWorkPackages || [] // Ensure it's an array
            }));

            toast.showSuccess(`Successfully generated ${generatedWorkPackages?.length || 0} work packages for Stage ${currentStageId}.`);

        } catch (error) {
            console.error("Failed to generate work packages:", error);
            const errorMsg = error.message || "An unknown error occurred.";
            setGenerationError(errorMsg);
            toast.showError(`Error generating work packages: ${errorMsg}`);
        } finally {
            setIsGeneratingWork(false);
        }
    };
    // --- End Handler Function ---

    // Use currentStageData for rendering
    const stage = currentStageData;
    const backTaskId = taskInfo.id || taskId; // Ensure we have a task ID for the back button

    return (
        <div className="min-h-screen bg-gray-50 pb-12">
            {/* Header */}
            <header className="sticky top-0 z-10 bg-white border-b border-gray-200">
                 <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="h-16 flex items-center">
                        <button
                            onClick={() => navigate(`/tasks/${backTaskId}`)} // Navigate back to the main task page
                            className="mr-4 text-gray-600 hover:text-gray-900 transition-colors"
                            title="Back to Task"
                        >
                            <ArrowLeft className="w-5 h-5" />
                        </button>
                        <div className="flex-1 min-w-0"> {/* Added min-w-0 for flex truncation */}
                            {/* Optional Breadcrumbs */}
                            <nav className="flex items-center space-x-1 text-sm text-gray-500 truncate">
                                <Link to={`/tasks/${backTaskId}`} className="hover:text-gray-700 flex-shrink-0" title={taskInfo.shortDescription}>
                                    Task:
                                </Link>
                                <span className="truncate flex-1 mx-1" title={taskInfo.shortDescription}>
                                     {taskInfo.shortDescription || backTaskId}
                                </span>
                                <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
                                <span className="font-medium text-gray-700 flex-shrink-0">Stage {stage.id}</span>
                            </nav>
                             <h1 className="text-xl font-bold text-gray-900 truncate" title={stage.name}>
                                Stage {stage.id}: {stage.name}
                            </h1>
                        </div>
                    </div>
                </div>
            </header>

             {/* Content */}
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">

                {/* Stage Overview */}
                <InfoCard title="Stage Overview">
                    <p className="text-gray-700">{stage.description}</p>
                </InfoCard>

                {/* Results & Deliverables */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {stage.result?.length > 0 && (
                        <InfoCard title="Expected Results">
                             <ul className="space-y-1 pl-5 list-disc text-sm text-gray-700">
                                {stage.result.map((res, index) => (
                                <li key={`res-${index}`}>{res}</li>
                                ))}
                            </ul>
                        </InfoCard>
                    )}
                     {stage.what_should_be_delivered?.length > 0 && (
                        <InfoCard title="Tangible Deliverables">
                             <ul className="space-y-1 pl-5 list-disc text-sm text-gray-700">
                                {stage.what_should_be_delivered.map((del, index) => (
                                <li key={`del-${index}`}>{del}</li>
                                ))}
                            </ul>
                        </InfoCard>
                    )}
                </div>

                {/* Checkpoints */}
                {stage.checkpoints?.length > 0 && (
                     <CollapsibleSection title="Checkpoints" defaultOpen={false}> {/* Default closed */}
                         <div className="space-y-4">
                            {stage.checkpoints.map((checkpoint, index) => (
                                <div key={`cp-${index}`} className="border border-gray-200 rounded-lg p-4 bg-white">
                                    <div className="flex items-start gap-3">
                                         <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                                        <div>
                                            <h4 className="font-medium text-gray-900">{checkpoint.checkpoint}</h4>
                                            <p className="text-sm text-gray-600 mt-1">{checkpoint.description}</p>

                                            {checkpoint.artifact && (
                                                <ArtifactDisplay artifact={checkpoint.artifact} />
                                            )}

                                            {checkpoint.validations?.length > 0 && (
                                                <div className="mt-3">
                                                    <h5 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Validations</h5>
                                                     <ul className="space-y-1 pl-5 list-disc text-sm text-gray-600">
                                                        {checkpoint.validations.map((val, valIdx) => (
                                                            <li key={`val-${index}-${valIdx}`}>{val}</li>
                                                        ))}
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


                 {/* Work Packages - Modified Section */}
                <CollapsibleSection title="Work Packages" defaultOpen={true}>
                    {/* Loading State */}
                    {isGeneratingWork && (
                        <div className="text-center py-10 px-4">
                            <RefreshCw className="w-8 h-8 text-blue-600 mx-auto animate-spin mb-3" />
                            <p className="text-gray-600">Generating work packages...</p>
                        </div>
                    )}

                    {/* Error State */}
                    {!isGeneratingWork && generationError && (
                        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
                            <strong className="font-bold">Error!</strong>
                            <span className="block sm:inline ml-2">{generationError}</span>
                            <button
                                onClick={() => setGenerationError(null)} // Allow dismissing error
                                className="absolute top-0 bottom-0 right-0 px-4 py-3"
                            >
                                <span className="text-xl leading-none">×</span>
                            </button>
                        </div>
                    )}

                    {/* Content: Button or Work Packages List */}
                    {!isGeneratingWork && !generationError && (
                        (!stage.work_packages || stage.work_packages.length === 0) ? (
                            // Show Generate button if no work packages exist
                            <div className="text-center py-6 px-4">
                                <Layers className="w-10 h-10 text-gray-400 mx-auto mb-3" />
                                <p className="text-gray-600">No work packages have been generated for this stage yet.</p>
                                <button
                                    onClick={handleGenerateWork}
                                    disabled={isGeneratingWork} // Disable while generating
                                    className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-2"
                                >
                                    <Cpu className="w-4 h-4" />
                                    Generate Work Packages
                                </button>
                            </div>
                        ) : (
                            // Show Work Packages list if they exist
                            <div className="space-y-4">
                                <div className="flex justify-end mb-2">
                                     <button
                                        onClick={handleGenerateWork}
                                        disabled={isGeneratingWork} // Disable while generating
                                        className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-1"
                                        title="Regenerate Work Packages"
                                    >
                                        <RefreshCw className="w-3 h-3" />
                                        Regenerate
                                    </button>
                                </div>
                                {stage.work_packages.map((work) => (
                                    <WorkPackageCard key={work.id} work={work} />
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