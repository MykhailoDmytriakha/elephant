import React from 'react';
import { RefreshCcw, Lightbulb } from "lucide-react";
import { CollapsibleSection } from './TaskComponents';
import { TaskStates } from "../../constants/taskStates";

export default function ApproachFormation({ approaches, onRegenerateApproaches, isRegenerating, taskState }) {
    if (!approaches || Object.keys(approaches).length === 0) {
        console.log("No approaches found, checking if can generate");
        const canGenerateApproaches = taskState === TaskStates.TYPIFY;
    
        if (!canGenerateApproaches) {
          console.log("Cannot generate approaches in current state");
          return null;
        }
    
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
      </div>
      
      {/* TRIZ Principles */}
      {/* <div className="mb-6">
        <h3 className="text-lg font-medium mb-2">Applied TRIZ Principles</h3>
        <ul className="list-disc pl-5 space-y-1">
          {approaches.principles.map((principle, index) => (
            <li key={index} className="text-gray-700">{principle}</li>
          ))}
        </ul>
      </div> */}

      {/* Approaches */}
      <div className="space-y-6">
        <h3 className="text-lg font-medium">Proposed Approaches</h3>
        {approaches.approach_list.map((approach) => (
          <div key={approach.approach_id} className="border rounded-lg p-4">
            <div className="flex justify-between items-start mb-2">
              <h4 className="text-md font-semibold">{approach.approach_name}</h4>
              <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded">
                {approach.approach_id}
              </span>
            </div>
            <p className="text-gray-600 mb-3">{approach.description}</p>
            
            {/* Evaluation Scores */}
            {approaches.evaluation_criteria && approaches.evaluation_criteria.map((evaluation) => {
              if (evaluation.approach_id === approach.approach_id) {
                return (
                  <div key={evaluation.approach_id} className="grid grid-cols-3 gap-4 mt-3">
                    <div className="text-sm">
                      <div className="font-medium">Ideality</div>
                      <div className="text-gray-600">{evaluation.ideality_score.score}/10</div>
                    </div>
                    <div className="text-sm">
                      <div className="font-medium">Feasibility</div>
                      <div className="text-gray-600">{(evaluation.feasibility.score * 100).toFixed(0)}%</div>
                    </div>
                    <div className="text-sm">
                      <div className="font-medium">Resource Efficiency</div>
                      <div className="text-gray-600">{(evaluation.resource_efficiency.score * 100).toFixed(0)}%</div>
                    </div>
                  </div>
                );
              }
              return null;
            })}
          </div>
        ))}
      </div>
    </CollapsibleSection>
  );
}
