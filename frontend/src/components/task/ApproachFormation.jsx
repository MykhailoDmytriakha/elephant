import React, { useState } from "react";
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
  const [activeTab, setActiveTab] = useState('tools');
  
  const isApproachFormationStageOrLater =
    getStateNumber(taskState) >= getStateNumber(TaskStates.CLARIFICATION_COMPLETE);

  if (!isApproachFormationStageOrLater && !approaches?.tool_categories) {
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

  const renderToolsAndResources = () => (
    <div className="space-y-8">
      {/* Analytical Tools */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Analytical Tools</h3>
        <div className="grid grid-cols-1 gap-4">
          {approaches.tool_categories.analytical_tools.map((tool) => (
            <div key={tool.tool_id} className="border rounded-lg p-4 bg-white relative">
              <div className="flex justify-between items-start mb-2">
                <h4 className="font-medium">{tool.name}</h4>
                <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                  {tool.tool_id}
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-2">{tool.purpose}</p>
              <div className="text-sm mb-3">
                <strong>When to use:</strong> {tool.when_to_use}
              </div>
              <div className="text-sm mb-8">
                <strong>Contribution:</strong> {tool.contribution_to_task}
              </div>
              <div className="mt-2 mb-6">
                <strong className="text-sm block mb-2">Examples:</strong>
                <ul className="space-y-1">
                  {tool.examples.map((example, idx) => (
                    <li key={idx} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded w-fit">
                      {example}
                    </li>
                  ))}
                </ul>
              </div>
              <span className="absolute bottom-4 right-4 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                {tool.ease_of_use}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Practical Methods */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Practical Methods</h3>
        <div className="grid grid-cols-1 gap-4">
          {approaches.tool_categories.practical_methods.map((method) => (
            <div key={method.method_id} className="border rounded-lg p-4 bg-white relative">
              <div className="flex justify-between items-start mb-2">
                <h4 className="font-medium">{method.name}</h4>
                <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                  {method.method_id}
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-2">{method.description}</p>
              <div className="text-sm mb-8">
                <strong>Best for:</strong>
                <ul className="list-disc list-inside mt-1">
                  {method.best_for.map((use, idx) => (
                    <li key={idx} className="text-gray-600">{use}</li>
                  ))}
                </ul>
              </div>
              <span className="absolute bottom-4 right-4 text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                {method.difficulty_level}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Frameworks */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Frameworks</h3>
        <div className="grid grid-cols-1 gap-4">
          {approaches.tool_categories.frameworks.map((framework) => (
            <div key={framework.framework_id} className="border rounded-lg p-4 bg-white">
              <div className="flex justify-between items-start mb-2">
                <h4 className="font-medium">{framework.name}</h4>
                <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                  {framework.framework_id}
                </span>
              </div>
              <div className="text-sm text-gray-600 mb-3">
                <strong>Structure:</strong> {framework.structure}
              </div>
              <div className="text-sm text-gray-600 mb-4">
                <strong>How to use:</strong> {framework.how_to_use}
              </div>
              
              <div className="space-y-3">
                <div>
                  <strong className="text-sm">Benefits:</strong>
                  <ul className="list-disc list-inside text-sm text-gray-600">
                    {framework.benefits.map((benefit, idx) => (
                      <li key={idx}>{benefit}</li>
                    ))}
                  </ul>
                </div>
                
                <div>
                  <strong className="text-sm">Adaptation Tips:</strong>
                  <ul className="list-disc list-inside text-sm text-gray-600">
                    {framework.adaptation_tips.map((tip, idx) => (
                      <li key={idx}>{tip}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tool Combinations */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Recommended Combinations</h3>
        {approaches.tool_combinations.map((combo, idx) => (
          <div key={idx} className="border rounded-lg p-4 bg-white">
            <h4 className="font-medium mb-2">{combo.combination_name}</h4>
            <p className="text-sm text-gray-600 mb-2">{combo.synergy_description}</p>
            <div className="text-sm">
              <strong>Use case:</strong> {combo.use_case}
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              {combo.tools.map((tool, idx) => (
                <span key={idx} className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded">
                  {tool}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

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

        <div className="mt-8">
          {renderToolsAndResources()}
        </div>
      </div>
    </CollapsibleSection>
  );
}
