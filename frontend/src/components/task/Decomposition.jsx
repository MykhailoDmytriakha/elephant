import React, { useEffect, useState } from "react";
import { Split, RefreshCcw } from "lucide-react";
import { CollapsibleSection } from './TaskComponents';
import { TaskStates, getStateNumber } from '../../constants/taskStates';
import { fetchTaskDetails } from '../../utils/api';

export default function Decomposition({
  task,
  taskState,
  isDecomposing,
  onDecompose,
  selectedItems,
}) {
  const [subtaskDetails, setSubtaskDetails] = useState([]);
  const [isLoadingSubtasks, setIsLoadingSubtasks] = useState(false);

  useEffect(() => {
    const loadSubtaskDetails = async () => {
      if (!task.sub_tasks?.length) return;
      
      setIsLoadingSubtasks(true);
      try {
        const details = await Promise.all(
          task.sub_tasks.map(taskId => fetchTaskDetails(taskId))
        );
        setSubtaskDetails(details);
      } catch (error) {
        console.error('Failed to fetch subtask details:', error);
      } finally {
        setIsLoadingSubtasks(false);
      }
    };

    loadSubtaskDetails();
  }, [task.sub_tasks]);

  const isApproachFormationStageOrLater = getStateNumber(taskState) >= getStateNumber(TaskStates.APPROACH_FORMATION);

  if (task.approaches?.selected_approaches) {
    selectedItems = task.approaches.selected_approaches;
  }

  // Check if user has selected at least one of each category
  const hasRequiredSelections = selectedItems && 
    selectedItems.analytical_tools?.length > 0 && 
    selectedItems.practical_methods?.length > 0 && 
    selectedItems.frameworks?.length > 0;

  // Only show decomposition if we're in/past approach formation stage OR if subtasks already exist
  if (!isApproachFormationStageOrLater && !task.sub_tasks) {
    return null;
  }

  // Only show if approaches have been selected or hasRequiredSelections is true
  if (!task.approaches?.selected_approaches && !hasRequiredSelections) {
    return null;
  }

  // Only show if all required selections (TMF) are made
  if (!hasRequiredSelections) {
    return null;
  }

  // Check if decomposition is empty object or null/undefined
  if (!task.sub_tasks || Object.keys(task.sub_tasks).length === 0) {
    return (
      <CollapsibleSection title="Decomposition">
        <div className="text-center py-8">
          <button
            onClick={() => onDecompose(selectedItems, false)}
            disabled={isDecomposing || !hasRequiredSelections}
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-300 relative group"
          >
            {isDecomposing ? (
              <>
                <RefreshCcw className="w-5 h-5 animate-spin" />
                Decomposing...
              </>
            ) : (
              <>
                <Split className="w-5 h-5" />
                Start Decomposition
              </>
            )}
            {/* Tooltip for disabled state */}
            {!hasRequiredSelections && !isDecomposing && (
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-1 text-xs text-white bg-gray-800 rounded-md opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                Select at least one tool, method, and framework
              </div>
            )}
          </button>
        </div>
      </CollapsibleSection>
    );
  }

  return (
    <CollapsibleSection title="Decomposition Results">
      <div className="relative">
        <button
          onClick={() => onDecompose(selectedItems, true)}
          disabled={isDecomposing}
          className="absolute right-0 -top-1 inline-flex items-center justify-center gap-1.5 px-6 py-1.5 text-sm bg-gray-50 text-blue-600 rounded-md hover:bg-blue-50 hover:text-blue-700 transition-all shadow-sm disabled:bg-gray-50 disabled:text-gray-400 w-[160px]"
        >
          <RefreshCcw
            className={`w-3.5 h-3.5 ${isDecomposing ? "animate-spin" : ""}`}
            style={{ minWidth: "0.875rem" }}
          />
          {isDecomposing ? "Decomposing..." : "Redecompose"}
        </button>

        <div className="space-y-6 mt-8">
          {/* Subtasks */}
          {task.sub_tasks?.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">
                Subtasks
              </h3>
              <div className="space-y-4">
                {isLoadingSubtasks ? (
                  <div className="text-center py-4">
                    <RefreshCcw className="w-5 h-5 animate-spin mx-auto" />
                    <p className="text-sm text-gray-500 mt-2">Loading subtasks...</p>
                  </div>
                ) : (
                  [...subtaskDetails]
                    .sort((a, b) => (a.order || 0) - (b.order || 0))
                    .map((subtask, index) => (
                    <div key={subtask.id || index} className="border rounded-lg p-4 bg-white relative">
                      <div className="absolute -left-2 -top-2 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                        {subtask.order || index + 1}
                      </div>
                      <h4 className="font-medium mb-2">{subtask.short_description}</h4>
                      <p className="text-sm text-gray-600 mb-2">{subtask.task}</p>
                      {subtask.level && (
                        <p className="text-sm text-gray-600 mb-2">Complexity: {subtask.level}</p>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Execution Order */}
          {/* TODO: Add execution order */}
        </div>
      </div>
    </CollapsibleSection>
  );
} 