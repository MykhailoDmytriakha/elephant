// src/components/task/WorkPackageCard.jsx
import React, { useState } from 'react';
import {
    ChevronRight, Download, Upload, ShieldCheck, TerminalSquare, ChevronsRight, RefreshCw, AlertCircle, ListPlus // Removed Layers, Workflow
} from 'lucide-react';
import { ExecutableTaskDisplay } from './ExecutableTaskDisplay';
import { ArtifactDisplay } from './TaskComponents'; // Import from shared components

/**
 * Card component to display details of a Work Package and its Executable Tasks.
 * Includes buttons for generating all tasks/subtasks within the work package.
 */
const WorkPackageCard = ({
    work,
    taskId,
    stageId,
    onGenerateAllTasks, // Handler for generating all tasks in this work
    isGeneratingAllTasks, // Loading state for generating all tasks
    allTasksError, // Error state for generating all tasks
    onGenerateAllSubtasks, // Handler for generating all subtasks in this work
    isGeneratingAllSubtasks, // Loading state for generating all subtasks
    allSubtasksError, // Error state for generating all subtasks
    onGenerateSubtasks // Handler for generating subtasks for a single ExecutableTask (passed down)
 }) => {
    const [isExpanded, setIsExpanded] = useState(false);

    const hasTasks = work.tasks && work.tasks.length > 0;
    const hasSubtasks = hasTasks && work.tasks.some(t => t.subtasks && t.subtasks.length > 0);

    // Button text logic remains the same
    let generateAllTasksButtonText = 'Generate All Tasks';
    if (isGeneratingAllTasks) {
        generateAllTasksButtonText = 'Generating All Tasks...';
    } else if (hasTasks) {
        generateAllTasksButtonText = 'Regenerate All Tasks';
    }

    let generateAllSubtasksButtonText = 'Generate All Subtasks';
    if (isGeneratingAllSubtasks) {
        generateAllSubtasksButtonText = 'Generating All Subtasks...';
    } else if (hasSubtasks) {
        generateAllSubtasksButtonText = 'Regenerate All Subtasks';
    }

    return (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden w-full">
            {/* Header Button */}
            <button
                className="w-full text-left p-4 flex justify-between items-center hover:bg-gray-50 transition-colors"
                onClick={() => setIsExpanded(!isExpanded)}
                aria-expanded={isExpanded}
                aria-controls={`work-details-${work.id}`}
            >
                 <div className="w-5/6">
                    <h4 className="font-semibold text-gray-900 truncate">{work.name} <span className="text-sm font-normal text-gray-500">(ID: {work.id}, Seq: {work.sequence_order})</span></h4>
                    <p className="text-sm text-gray-600 line-clamp-1">{work.description}</p>
                </div>
                <ChevronRight className={`w-5 h-5 text-gray-400 transform transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''}`} />
            </button>

            {/* Collapsible Details */}
            {isExpanded && (
                <div id={`work-details-${work.id}`} className="p-4 border-t border-gray-200 bg-gray-50 space-y-4 w-full">
                    {/* Work Description */}
                    <p className="text-sm text-gray-800 w-full">{work.description}</p>

                    {/* Dependencies */}
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

                    {/* Required Inputs */}
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

                    {/* Expected Outcome */}
                     <div className="w-full">
                        <h5 className="text-sm font-medium text-gray-700 mb-1">Expected Outcome:</h5>
                        <p className="text-sm text-gray-700 italic">{work.expected_outcome}</p>
                    </div>

                    {/* Generated Artifacts */}
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

                    {/* Validation Criteria */}
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
                            {/* Generate All Buttons */}
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => onGenerateAllTasks(work.id)}
                                    disabled={isGeneratingAllTasks || isGeneratingAllSubtasks}
                                    className="px-3 py-1.5 text-xs bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-1"
                                    title={generateAllTasksButtonText}
                                >
                                    {isGeneratingAllTasks ? <RefreshCw className="w-3 h-3 animate-spin" /> : <ListPlus className="w-3 h-3" />}
                                    {hasTasks ? 'Regen All Tasks' : 'Gen All Tasks'}
                                </button>
                                <button
                                    onClick={() => onGenerateAllSubtasks(work.id)}
                                    disabled={!hasTasks || isGeneratingAllTasks || isGeneratingAllSubtasks}
                                    className="px-3 py-1.5 text-xs bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-1"
                                    title={generateAllSubtasksButtonText}
                                >
                                    {isGeneratingAllSubtasks ? <RefreshCw className="w-3 h-3 animate-spin" /> : <ListPlus className="w-3 h-3" />}
                                    {hasSubtasks ? 'Regen Work Subs' : 'Gen Work Subs'}
                                </button>
                            </div>
                         </div>

                        {/* Loading/Error States for "Generate All" */}
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
                                                onGenerateSubtasks={onGenerateSubtasks} // Pass down the handler
                                            />
                                        ))}
                                    </div>
                                ) : (
                                     !isGeneratingAllTasks && // Only show if not loading tasks
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

export default WorkPackageCard;