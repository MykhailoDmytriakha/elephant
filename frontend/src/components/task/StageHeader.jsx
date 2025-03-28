import React from 'react';
import { Link } from 'react-router-dom';
import {
    ArrowLeft, ChevronRight, ChevronLeft, Loader2
} from 'lucide-react';

export default function StageHeader({
    taskInfo,
    stage,
    backTaskId,
    navigate,
    currentStageIndex,
    allStages,
    isLoadingStages,
    navigateToStage,
    getStageNavigation
}) {
    const { hasPrevStage, hasNextStage, prevStageId, nextStageId } = getStageNavigation(stage.id);

    return (
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
                        </nav>
                        <h1 className="text-xl font-bold text-gray-900 truncate" title={stage.name}>Stage {stage.id}: {stage.name}</h1>
                    </div>
                    
                    {/* Stage Switcher */}
                    <div className="flex items-center ml-4 bg-gray-100 rounded-md p-1 shadow-sm">
                        {isLoadingStages ? (
                            <div className="px-3 py-1 flex items-center">
                                <Loader2 className="w-3 h-3 text-blue-500 animate-spin mr-1" />
                                <span className="text-xs text-gray-500">Loading</span>
                            </div>
                        ) : (
                            <>
                                <button
                                    onClick={() => navigateToStage(prevStageId)}
                                    disabled={!hasPrevStage || isLoadingStages}
                                    className={`p-1.5 rounded-md transition-colors ${
                                        hasPrevStage && !isLoadingStages
                                        ? 'text-gray-700 hover:bg-white hover:text-blue-600 hover:shadow-sm' 
                                        : 'text-gray-300 cursor-not-allowed'
                                    }`}
                                    title={hasPrevStage ? `Previous: Stage ${prevStageId}` : "No previous stage"}
                                    aria-label={hasPrevStage ? "Go to previous stage" : "No previous stage"}
                                >
                                    <ChevronLeft className="w-4 h-4" />
                                </button>
                                
                                <span className="text-xs font-medium text-gray-500 mx-2 select-none">
                                    {currentStageIndex !== -1 ? `${currentStageIndex + 1}/${allStages.length}` : ''}
                                </span>
                                
                                <button
                                    onClick={() => navigateToStage(nextStageId)}
                                    disabled={!hasNextStage || isLoadingStages}
                                    className={`p-1.5 rounded-md transition-colors ${
                                        hasNextStage && !isLoadingStages
                                        ? 'text-gray-700 hover:bg-white hover:text-blue-600 hover:shadow-sm' 
                                        : 'text-gray-300 cursor-not-allowed'
                                    }`}
                                    title={hasNextStage ? `Next: Stage ${nextStageId}` : "No next stage"}
                                    aria-label={hasNextStage ? "Go to next stage" : "No next stage"}
                                >
                                    <ChevronRight className="w-4 h-4" />
                                </button>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
} 