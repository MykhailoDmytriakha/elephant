import React, { useState } from 'react';
import { Activity, Download, Upload, ShieldCheck, ChevronsRight, RefreshCw, AlertCircle, ListTree } from 'lucide-react';
import { CollapsibleSection } from './TaskComponents';
import { SubtaskDisplay } from './SubtaskDisplay';

export const ExecutableTaskDisplay = ({ task, taskIndex, taskId, stageId, workId, onGenerateSubtasks }) => {
  const [isGeneratingSubtasks, setIsGeneratingSubtasks] = useState(false);
  const [subtaskGenerationError, setSubtaskGenerationError] = useState(null);
  const subtasks = task?.subtasks || [];
  const hasSubtasks = subtasks.length > 0;

  const handleGenerateClick = async () => {
    setIsGeneratingSubtasks(true);
    setSubtaskGenerationError(null);
    try {
      await onGenerateSubtasks(task.id);
    } catch (error) {
      setSubtaskGenerationError(error.message || "Failed to generate subtasks.");
    } finally {
      setIsGeneratingSubtasks(false);
    }
  };

  let generateButtonText = 'Generate Subtasks';
  if (isGeneratingSubtasks) {
      generateButtonText = 'Generating...';
  } else if (hasSubtasks) {
      generateButtonText = 'Regenerate Subtasks';
  }

  return (
    <div className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-600" />
          <h5 className="font-semibold text-gray-800">{task.name}</h5>
          <span className="text-xs font-mono bg-gray-100 px-1.5 py-0.5 rounded text-gray-600">
            Seq: {task.sequence_order}
          </span>
        </div>
        <span className="text-xs font-mono text-gray-400">{task.id}</span>
      </div>

      {/* Description */}
      <p className="text-sm text-gray-700 ml-7">{task.description}</p>

      {/* Dependencies */}
      {task.dependencies && task.dependencies.length > 0 && (
        <div className="ml-7 text-xs text-gray-600 flex items-center gap-2">
          <ChevronsRight className="w-4 h-4 text-gray-400" />
          <span className="font-medium">Depends on:</span>
          <div className="flex flex-wrap gap-1">
            {task.dependencies.map(depId => (
              <span key={depId} className="font-mono bg-gray-200 px-1.5 py-0.5 rounded">{depId}</span>
            ))}
          </div>
        </div>
      )}

      {/* Required Inputs */}
      {task.required_inputs && task.required_inputs.length > 0 && (
        <div className="ml-7">
          <h6 className="text-xs font-medium text-gray-500 uppercase tracking-wider flex items-center gap-1 mb-1">
            <Download className="w-3 h-3" /> Required Inputs
          </h6>
          <div className="space-y-1">
            {task.required_inputs.map((artifact, idx) => (
              <div key={`in-${idx}`} className="text-xs flex items-center gap-1 bg-gray-50 p-1 rounded border border-gray-100">
                <span className="font-medium">{artifact.name}</span>
                <span className="text-gray-500">({artifact.type})</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Generated Artifacts */}
      {task.generated_artifacts && task.generated_artifacts.length > 0 && (
        <div className="ml-7">
          <h6 className="text-xs font-medium text-gray-500 uppercase tracking-wider flex items-center gap-1 mb-1">
            <Upload className="w-3 h-3" /> Generated Artifacts
          </h6>
          <div className="space-y-1">
            {task.generated_artifacts.map((artifact, idx) => (
               <div key={`out-${idx}`} className="text-xs flex items-center gap-1 bg-gray-50 p-1 rounded border border-gray-100">
                <span className="font-medium">{artifact.name}</span>
                <span className="text-gray-500">({artifact.type})</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Validation Criteria */}
      {task.validation_criteria && task.validation_criteria.length > 0 && (
        <div className="ml-7">
          <h6 className="text-xs font-medium text-gray-500 uppercase tracking-wider flex items-center gap-1 mb-1">
            <ShieldCheck className="w-3 h-3 text-green-600" /> Validation Criteria
          </h6>
          <ul className="space-y-1 pl-4 list-disc text-sm text-gray-600">
            {task.validation_criteria.map((criterion, index) => (
              <li key={`val-${index}`}>{criterion}</li>
            ))}
          </ul>
        </div>
      )}

      {/* --- NEW: Subtasks Section --- */}
      <div className="pt-3 mt-3 border-t border-dashed border-gray-200 ml-7">
        <CollapsibleSection
            title={
                <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                    <ListTree className="w-4 h-4 text-gray-500" />
                    Subtasks ({subtasks.length})
                </div>
            }
            className="bg-transparent shadow-none border-none p-0"
        >
           <div className="mt-3 space-y-3">
                {isGeneratingSubtasks && (
                    <div className="text-center py-4">
                        <RefreshCw className="w-5 h-5 text-blue-600 mx-auto animate-spin mb-1" />
                        <p className="text-xs text-gray-500">Generating subtasks...</p>
                    </div>
                )}

                {!isGeneratingSubtasks && subtaskGenerationError && (
                    <div className="bg-red-100 border border-red-300 text-red-700 px-3 py-2 rounded text-xs mb-2 flex items-center gap-1">
                        <AlertCircle className="w-4 h-4" />
                        Error: {subtaskGenerationError}
                    </div>
                )}

                {!isGeneratingSubtasks && !subtaskGenerationError && (
                    <>
                        {hasSubtasks ? (
                            <div className="space-y-2">
                                {subtasks.map((subtaskItem) => (
                                    <SubtaskDisplay key={subtaskItem.id} subtask={subtaskItem} />
                                ))}
                            </div>
                        ) : (
                            <p className="text-xs text-gray-500 italic text-center py-2">No subtasks generated yet.</p>
                        )}

                        <div className="mt-3 text-right">
                            <button
                                onClick={handleGenerateClick}
                                disabled={isGeneratingSubtasks}
                                className="px-2.5 py-1 text-xs bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-1"
                            >
                                {isGeneratingSubtasks ? <RefreshCw className="w-3 h-3 animate-spin" /> : <ListTree className="w-3 h-3" />}
                                {generateButtonText}
                            </button>
                        </div>
                    </>
                )}
           </div>
        </CollapsibleSection>
      </div>
      {/* --- END: Subtasks Section --- */}

    </div>
  );
};