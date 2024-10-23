import React from 'react';
import { InfoCard } from './TaskComponents';
import { RefreshCcw, Lightbulb } from 'lucide-react';
import { TaskStates } from '../constants/taskStates';

const ConceptDefinition = ({ 
  concepts, 
  isLoading, 
  onGenerateConcepts, 
  taskState, 
  isContextSufficient 
}) => {
  console.log("ConceptDefinition props:", {
    concepts,
    taskState,
    isContextSufficient,
    isLoading
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
    );
  }

  // Show detailed concept information in Concept Definition state
  if (taskState === TaskStates.CONCEPT_DEFINITION) {
    console.log("Showing concept definition state data:", concepts);
    return (
      <div className="space-y-6">
        {/* Contribution to Parent Task */}
        {concepts.contribution_to_parent_task && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2">Contribution to Parent Task</h3>
            <p className="text-gray-700">{concepts.contribution_to_parent_task}</p>
          </div>
        )}

        {/* Ideas */}
        {concepts.ideas?.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2">Ideas</h3>
            <ul className="list-disc list-inside space-y-1">
              {concepts.ideas.map((idea, index) => (
                <li key={index} className="text-gray-700">{idea}</li>
              ))}
            </ul>
          </div>
        )}

        {/* TOP TRIZ Principles */}
        {concepts.TOP_TRIZ_principles?.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2">TOP TRIZ Principles</h3>
            <ul className="list-disc list-inside space-y-1">
              {concepts.TOP_TRIZ_principles.map((principle, index) => (
                <li key={index} className="text-gray-700">{principle}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Solution Approaches */}
        {concepts.solution_approaches?.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2">Solution Approaches</h3>
            <ul className="list-disc list-inside space-y-1">
              {concepts.solution_approaches.map((approach, index) => (
                <li key={index} className="text-gray-700">{approach}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Resources per Concept */}
        {concepts.resources_per_concept?.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2">Resources per Concept</h3>
            <div className="space-y-4">
              {concepts.resources_per_concept.map((item, index) => (
                <div key={index} className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-700 mb-2">{item.concept}</h4>
                  <p className="text-gray-600">{item.resources}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // Default return for Analysis state with existing concepts
  return (
    <div className="space-y-6">
      {/* Core Concepts */}
      {concepts.core_concepts?.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-2">Core Concepts</h3>
          <div className="flex flex-wrap gap-2">
            {concepts.core_concepts.map((concept, index) => (
              <span 
                key={index}
                className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
              >
                {concept}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Solution Principles */}
      {concepts.solution_principles && (
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-2">Solution Principles</h3>
          <p className="text-gray-700">{concepts.solution_principles}</p>
        </div>
      )}

      {/* Key Insights */}
      {concepts.key_insights?.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-2">Key Insights</h3>
          <ul className="list-disc list-inside space-y-1">
            {concepts.key_insights.map((insight, index) => (
              <li key={index} className="text-gray-700">{insight}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Design Considerations */}
      {concepts.design_considerations?.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-2">Design Considerations</h3>
          <ul className="list-disc list-inside space-y-1">
            {concepts.design_considerations.map((consideration, index) => (
              <li key={index} className="text-gray-700">{consideration}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Implementation Approaches */}
      {concepts.implementation_approaches?.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-2">Implementation Approaches</h3>
          <ul className="list-disc list-inside space-y-1">
            {concepts.implementation_approaches.map((approach, index) => (
              <li key={index} className="text-gray-700">{approach}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default ConceptDefinition;
