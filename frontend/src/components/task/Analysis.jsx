import React from "react";
import { BarChart2, RefreshCcw } from "lucide-react";
import { CollapsibleSection } from "./TaskComponents";

export default function Analysis({
  analysis,
  isContextSufficient,
  isAnalyzing,
  onAnalyze,
}) {
  if (!isContextSufficient) {
    return null;
  }

  // Check if analysis is empty object or null/undefined
  if (!analysis || Object.keys(analysis).length === 0) {
    return (
      <CollapsibleSection title="Analysis">
        <div className="text-center py-8">
          <button
            onClick={() => onAnalyze(false)}
            disabled={isAnalyzing}
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-300"
          >
            {isAnalyzing ? (
              <>
                <RefreshCcw className="w-5 h-5 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <BarChart2 className="w-5 h-5" />
                Start Analysis
              </>
            )}
          </button>
        </div>
      </CollapsibleSection>
    );
  }

  return (
    <CollapsibleSection title="Analysis Results">
      <div className="relative">
        <button
          onClick={() => onAnalyze(true)}
          disabled={isAnalyzing}
          className="absolute right-0 -top-1 inline-flex items-center justify-center gap-1.5 px-6 py-1.5 text-sm bg-gray-50 text-blue-600 rounded-md hover:bg-blue-50 hover:text-blue-700 transition-all shadow-sm disabled:bg-gray-50 disabled:text-gray-400 w-[160px]"
        >
          <RefreshCcw
            className={`w-3.5 h-3.5 ${isAnalyzing ? "animate-spin" : ""}`}
            style={{ minWidth: "0.875rem" }}
          />
          {isAnalyzing ? "Analyzing..." : "Reanalyze"}
        </button>
      </div>
      <div className="space-y-6">
        {/* Ideal Final Result */}
        {analysis.ideal_final_result && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2">
              Ideal Final Result
            </h3>
            <p className="text-gray-700">{analysis.ideal_final_result}</p>
          </div>
        )}

        {/* Parameters */}
        {analysis.parameters?.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2">
              Parameters
            </h3>
            <ul className="list-disc list-inside space-y-1">
              {analysis.parameters.map((parameter, index) => (
                <li key={index} className="text-gray-700">
                  {parameter}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Constraints */}
        {analysis.constraints?.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2">
              Constraints
            </h3>
            <ul className="list-disc list-inside space-y-1">
              {analysis.constraints.map((constraint, index) => (
                <li key={index} className="text-gray-700">
                  {constraint}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Current Limitations */}
        {analysis.current_limitations?.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2">
              Current Limitations
            </h3>
            <ul className="list-disc list-inside space-y-1">
              {analysis.current_limitations.map((limitation, index) => (
                <li key={index} className="text-gray-700">
                  {limitation}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Contradictions */}
        {analysis.contradictions?.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2">
              Contradictions
            </h3>
            <ul className="list-inside space-y-1">
              {analysis.contradictions.map((contradiction, index) => (
                <li key={index} className="text-gray-700">
                  <span className="block ml-4">
                    Improving: {contradiction.improving_parameter}
                  </span>
                  <span className="block ml-4">
                    Worsening: {contradiction.worsening_parameter}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Available Resources */}
        {analysis.available_resources?.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2">
              Available Resources
            </h3>
            <ul className="list-disc list-inside space-y-1">
              {analysis.available_resources.map((resource, index) => (
                <li key={index} className="text-gray-700">
                  {resource}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Required Resources */}
        {analysis.required_resources?.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2">
              Required Resources
            </h3>
            <ul className="list-disc list-inside space-y-1">
              {analysis.required_resources.map((resource, index) => (
                <li key={index} className="text-gray-700">
                  {resource}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Missing Information */}
        {analysis.missing_information?.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2">
              Missing Information
            </h3>
            <ul className="list-disc list-inside space-y-1">
              {analysis.missing_information.map((info, index) => (
                <li key={index} className="text-gray-700">
                  {info}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* ETA */}
        {analysis.eta && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2">
              Estimated Time of Arrival (ETA)
            </h3>
            <p className="text-gray-700">Time: {analysis.eta.time}</p>
            <p className="text-gray-700">Reasoning: {analysis.eta.reasoning}</p>
          </div>
        )}

        {/* Complexity */}
        {analysis.complexity && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2">
              Complexity Level
            </h3>
            <p className="text-gray-700">{analysis.complexity}</p>
          </div>
        )}
      </div>
    </CollapsibleSection>
  );
}
