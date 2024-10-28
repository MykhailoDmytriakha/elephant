import React from "react";
import { RefreshCcw, Lightbulb } from "lucide-react";
import { CollapsibleSection } from "./TaskComponents";
import { TaskStates } from "../../constants/taskStates";
import { getStateNumber } from "../../constants/taskStates";

export default function ApproachFormation({
  approaches,
  onRegenerateApproaches,
  isRegenerating,
  taskState,
}) {
  const isApproachFormationStageOrLater =
    getStateNumber(taskState) >=
    getStateNumber(TaskStates.CLARIFICATION_COMPLETE);

  // Show component only during/after APPROACH_FORMATION stage or if approaches exist
  if (!isApproachFormationStageOrLater && !approaches?.approach_list?.length) {
    return null;
  }

  if (!approaches || Object.keys(approaches).length === 0) {
    return (
      <CollapsibleSection title="Approach Formation">
        <div className="text-center py-8">
          <button
            onClick={onRegenerateApproaches}
            disabled={isRegenerating}
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-300"
          >
            {isRegenerating ? (
              <>
                <RefreshCcw className="w-5 h-5 animate-spin" />
                Generating Approaches...
              </>
            ) : (
              <>
                <Lightbulb className="w-5 h-5" />
                Generate Approaches
              </>
            )}
          </button>
        </div>
      </CollapsibleSection>
    );
  }

  return (
    <CollapsibleSection title="Approach Formation">
      <div className="relative">
        <button
          onClick={onRegenerateApproaches}
          disabled={isRegenerating}
          className="absolute right-0 -top-1 inline-flex items-center justify-center gap-1.5 px-6 py-1.5 text-sm bg-gray-50 text-blue-600 rounded-md hover:bg-blue-50 hover:text-blue-700 transition-all shadow-sm disabled:bg-gray-50 disabled:text-gray-400 w-[160px]"
        >
          <RefreshCcw
            className={`w-3.5 h-3.5 ${isRegenerating ? "animate-spin" : ""}`}
            style={{ minWidth: "0.875rem" }}
          />
          {isRegenerating ? "Reapproaching..." : "Reapproach"}
        </button>

        {/* Approaches */}
        <div className="space-y-6 mt-8">
          <h3 className="text-lg font-medium">Proposed Approaches</h3>
          {approaches.approach_list.map((approach) => (
            <div key={approach.approach_id} className="border rounded-lg p-4">
              <div className="flex justify-between items-start mb-2">
                <h4 className="text-md font-semibold">
                  {approach.approach_name}
                </h4>
                <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded">
                  {approach.approach_id}
                </span>
              </div>
              <p className="text-gray-600 mb-3">{approach.description}</p>

              {/* Applied Principles */}
              {/* <div className="mt-4">
                            <h5 className="text-sm font-medium text-gray-500 mb-2">Applied Principles</h5>
                            <ul className="list-disc list-inside space-y-1">
                                {approach.applied_principles.map((principle, index) => (
                                    <li key={index} className="text-gray-600">
                                        <span className="font-medium">{principle.principle_name}:</span>{' '}
                                        {principle.application_description}
                                    </li>
                                ))}
                            </ul>
                        </div> */}

              {/* Resources */}
              <div className="mt-4">
                <h5 className="text-sm font-medium text-gray-500 mb-2">
                  Required Resources
                </h5>
                <ul className="list-disc list-inside space-y-1">
                  {approach.resources.map((resource, index) => (
                    <li key={index} className="text-gray-600">
                      {resource}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Evaluation Scores */}
              {approaches.evaluation_criteria &&
                approaches.evaluation_criteria.map((evaluation) => {
                  if (evaluation.approach_id === approach.approach_id) {
                    return (
                      <div
                        key={evaluation.approach_id}
                        className="mt-4 border-t pt-4"
                      >
                        <h5 className="text-sm font-medium text-gray-500 mb-3">
                          Evaluation Scores
                        </h5>
                        <div className="grid grid-cols-3 gap-4">
                          <div className="text-sm">
                            <div className="font-medium">Ideality</div>
                            <div className="text-gray-600">
                              {evaluation.ideality_score.score}/10
                            </div>
                            <div className="text-xs text-gray-500 mt-1">
                              {evaluation.ideality_score.reasoning}
                            </div>
                          </div>
                          <div className="text-sm">
                            <div className="font-medium">Feasibility</div>
                            <div className="text-gray-600">
                              {(evaluation.feasibility.score * 100).toFixed(0)}%
                            </div>
                            <div className="text-xs text-gray-500 mt-1">
                              {evaluation.feasibility.reasoning}
                            </div>
                          </div>
                          <div className="text-sm">
                            <div className="font-medium">
                              Resource Efficiency
                            </div>
                            <div className="text-gray-600">
                              {(
                                evaluation.resource_efficiency.score * 100
                              ).toFixed(0)}
                              %
                            </div>
                            <div className="text-xs text-gray-500 mt-1">
                              {evaluation.resource_efficiency.reasoning}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  }
                  return null;
                })}
            </div>
          ))}
        </div>
      </div>
    </CollapsibleSection>
  );
}
