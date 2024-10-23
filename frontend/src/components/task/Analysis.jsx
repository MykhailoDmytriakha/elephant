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
            onClick={onAnalyze}
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

        {/* Parameters and Constraints */}
        {analysis.parameters_constraints && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2">
              Parameters & Constraints
            </h3>
            <p className="text-gray-700">{analysis.parameters_constraints}</p>
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
