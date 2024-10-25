import React from "react";
import { CollapsibleSection } from "./TaskComponents";
import { RefreshCcw, Lightbulb } from "lucide-react";
import { TaskStates } from "../../constants/taskStates";

const ConceptDefinition = ({
  concepts,
  isLoading,
  onGenerateConcepts,
  taskState,
  isContextSufficient,
}) => {
  const shouldShowConcepts = () => {
    return (
      taskState === TaskStates.ANALYSIS ||
      taskState === TaskStates.CONCEPT_DEFINITION
    );
  };

  if (!shouldShowConcepts()) {
    return null;
  }

  console.log("ConceptDefinition props:", {
    concepts,
    taskState,
    isContextSufficient,
    isLoading,
  });

  if (!isContextSufficient) {
    console.log("Context not sufficient, returning null");
    return null;
  }

  // Show generate button in Analysis state if no concepts or concepts is empty
  if (!concepts || Object.keys(concepts).length === 0) {
    console.log("No concepts found, checking if can generate");
    const canGenerateConcepts = taskState === TaskStates.ANALYSIS;

    if (!canGenerateConcepts) {
      console.log("Cannot generate concepts in current state");
      return null;
    }

    return (
      <CollapsibleSection title="Concept Formation">
        <div className="text-center py-8">
          <button
            onClick={onGenerateConcepts}
            disabled={isLoading}
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-300"
          >
            {isLoading ? (
              <>
                <RefreshCcw className="w-5 h-5 animate-spin" />
                Generating Concepts...
              </>
            ) : (
              <>
                <Lightbulb className="w-5 h-5" />
                Generate Concepts
              </>
            )}
          </button>
        </div>
      </CollapsibleSection>
    );
  }

  // Show detailed concept information in Concept Definition state
  if (taskState === TaskStates.CONCEPT_DEFINITION) {
    console.log("Showing concept definition state data:", concepts);
    return (
      <CollapsibleSection title="Concept Formation">
        <div className="relative">
          <button
            onClick={onGenerateConcepts}
            disabled={isLoading}
            className="absolute right-0 -top-1 inline-flex items-center justify-center gap-1.5 px-6 py-1.5 text-sm bg-gray-50 text-blue-600 rounded-md hover:bg-blue-50 hover:text-blue-700 transition-all shadow-sm disabled:bg-gray-50 disabled:text-gray-400 w-[160px]"
          >
            <RefreshCcw
              className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`}
              style={{ minWidth: "0.875rem" }} // 0.875rem = 3.5 (w-3.5)
            />
            {isLoading ? "Regenerating..." : "Regenerate"}
          </button>

          <div className="space-y-6">
            {/* Contribution to Parent Task */}
            {concepts.contribution_to_parent_task && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">
                  Contribution to Parent Task
                </h3>
                <p className="text-gray-700">
                  {concepts.contribution_to_parent_task}
                </p>
              </div>
            )}

            {/* Ideas */}
            {concepts.ideas?.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">
                  Ideas
                </h3>
                <ul className="list-disc list-inside space-y-1">
                  {concepts.ideas.map((idea, index) => (
                    <li key={index} className="text-gray-700">
                      {idea}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* TOP TRIZ Principles */}
            {/* {concepts.TOP_TRIZ_principles?.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">TOP TRIZ Principles</h3>
                <ul className="list-disc list-inside space-y-1">
                  {concepts.TOP_TRIZ_principles.map((principle, index) => (
                    <li key={index} className="text-gray-700">{principle}</li>
                  ))}
                </ul>
              </div>
            )} */}

            {/* Solution Approaches */}
            {concepts.solution_approaches?.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">
                  Solution Approaches
                </h3>
                <ul className="list-disc list-inside space-y-1">
                  {concepts.solution_approaches.map((approach, index) => (
                    <li key={index} className="text-gray-700">
                      {approach}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Resources per Concept */}
            {concepts.resources_per_concept?.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">
                  Resources per Concept
                </h3>
                <div className="space-y-4">
                  {concepts.resources_per_concept.map((item, index) => (
                    <div key={index} className="bg-gray-50 p-4 rounded-lg">
                      <h4 className="font-medium text-gray-700 mb-2">
                        {item.concept}
                      </h4>
                      <p className="text-gray-600">{item.resources}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </CollapsibleSection>
    );
  }
};

export default ConceptDefinition;
