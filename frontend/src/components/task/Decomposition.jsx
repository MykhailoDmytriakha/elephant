import React, { useEffect, useState } from "react";
import { Split, RefreshCcw } from "lucide-react";
import { CollapsibleSection } from './TaskComponents';
import { TaskStates, getStateNumber } from '../../constants/taskStates';

export default function Decomposition({
  task,
  taskState,
  isDecomposing,
  onDecompose,
  selectedItems,
}) {
  const isApproachFormationStageOrLater = getStateNumber(taskState) >= getStateNumber(TaskStates.APPROACH_FORMATION);

  const decomposition = task.decomposition;
  if (task.approaches?.selected_approaches) {
    selectedItems = task.approaches.selected_approaches;
  }

  // Check if user has selected at least one of each category
  const hasRequiredSelections = selectedItems && 
    selectedItems.analytical_tools?.length > 0 && 
    selectedItems.practical_methods?.length > 0 && 
    selectedItems.frameworks?.length > 0;

  if (!isApproachFormationStageOrLater && !decomposition) {
    return null;
  }

  // Check if decomposition is empty object or null/undefined
  if (!decomposition || Object.keys(decomposition).length === 0) {
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
          onClick={() => onDecompose(true)}
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
          {decomposition.subtasks?.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">
                Subtasks
              </h3>
              <div className="space-y-4">
                {decomposition.subtasks.map((subtask, index) => (
                  <div key={index} className="border rounded-lg p-4 bg-white">
                    <h4 className="font-medium mb-2">{subtask.title}</h4>
                    <p className="text-sm text-gray-600 mb-2">{subtask.description}</p>
                    {subtask.dependencies?.length > 0 && (
                      <div className="mt-2">
                        <strong className="text-sm text-gray-500">Dependencies:</strong>
                        <div className="flex flex-wrap gap-2 mt-1">
                          {subtask.dependencies.map((dep, idx) => (
                            <span key={idx} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                              {dep}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Dependencies Graph */}
          {decomposition.dependencies_graph && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">
                Dependencies Graph
              </h3>
              <pre className="bg-gray-50 p-4 rounded-lg text-sm overflow-x-auto">
                {decomposition.dependencies_graph}
              </pre>
            </div>
          )}

          {/* Execution Order */}
          {decomposition.execution_order?.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">
                Suggested Execution Order
              </h3>
              <ol className="list-decimal list-inside space-y-1">
                {decomposition.execution_order.map((step, index) => (
                  <li key={index} className="text-gray-700">
                    {step}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      </div>
    </CollapsibleSection>
  );
} 