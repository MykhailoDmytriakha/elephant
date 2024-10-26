import React from "react";
import { RefreshCcw, FileType } from "lucide-react";
import { CollapsibleSection } from "./TaskComponents";
import { TaskStates, getStateNumber } from "../../constants/taskStates";
export default function Typification({
  typification,
  isContextSufficient,
  isTypifying,
  onTypify,
  taskState
}) {
  if (!isContextSufficient) {
    return null;
  }

  const canTypify = getStateNumber(taskState) >= 4;

  if (!canTypify) {
    return null;
  }

  // Check if typification is empty object or null/undefined
  if (!typification || Object.keys(typification).length === 0) {
    return (
      <CollapsibleSection title="Typification">
        <div className="text-center py-8">
          <button
            onClick={() => onTypify(false)}
            disabled={isTypifying}
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-300"
          >
            {isTypifying ? (
              <>
                <RefreshCcw className="w-5 h-5 animate-spin" />
                Typifying...
              </>
            ) : (
              <>
                <FileType className="w-5 h-5" />
                Start Typification
              </>
            )}
          </button>
        </div>
      </CollapsibleSection>
    );
  }

  return (
    <CollapsibleSection title="Typification Results">
      <div className="relative">
        <button
          onClick={() => onTypify(true)}
          disabled={isTypifying}
          className="absolute right-0 -top-1 inline-flex items-center justify-center gap-1.5 px-6 py-1.5 text-sm bg-gray-50 text-blue-600 rounded-md hover:bg-blue-50 hover:text-blue-700 transition-all shadow-sm disabled:bg-gray-50 disabled:text-gray-400 w-[160px]"
        >
          <RefreshCcw
            className={`w-3.5 h-3.5 ${isTypifying ? "animate-spin" : ""}`}
            style={{ minWidth: "0.875rem" }}
          />
          {isTypifying ? "Typifying..." : "Retypify"}
        </button>

        <div className="space-y-6 mt-8">
          {/* Classification Section */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Classification</h3>

            {/* Nature */}
            <div className="bg-white p-4 rounded-lg border">
              <h4 className="text-sm font-medium text-gray-500 mb-2">Nature</h4>
              <div className="space-y-2">
                <div>
                  <span className="font-medium">Primary: </span>
                  <span className="text-gray-700">
                    {typification.classification.nature.primary}
                  </span>
                </div>
                <div>
                  <span className="font-medium">Secondary: </span>
                  <span className="text-gray-700">
                    {typification.classification.nature.secondary.join(", ")}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-2">
                  {typification.classification.nature.reasoning}
                </p>
              </div>
            </div>

            {/* Domain */}
            <div className="bg-white p-4 rounded-lg border">
              <h4 className="text-sm font-medium text-gray-500 mb-2">Domain</h4>
              <div className="space-y-2">
                <div>
                  <span className="font-medium">Primary: </span>
                  <span className="text-gray-700">
                    {typification.classification.domain.primary}
                  </span>
                </div>
                <div>
                  <span className="font-medium">Aspects: </span>
                  <span className="text-gray-700">
                    {typification.classification.domain.aspects.join(", ")}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-2">
                  {typification.classification.domain.reasoning}
                </p>
              </div>
            </div>

            {/* Structure */}
            <div className="bg-white p-4 rounded-lg border">
              <h4 className="text-sm font-medium text-gray-500 mb-2">
                Structure
              </h4>
              <div className="space-y-2">
                <div>
                  <span className="font-medium">Type: </span>
                  <span className="text-gray-700">
                    {typification.classification.structure.type}
                  </span>
                </div>
                <div>
                  <span className="font-medium">Characteristics:</span>
                  <ul className="list-disc list-inside ml-4 text-gray-700">
                    {typification.classification.structure.characteristics.map(
                      (char, index) => (
                        <li key={index}>{char}</li>
                      )
                    )}
                  </ul>
                </div>
                <p className="text-sm text-gray-600 mt-2">
                  {typification.classification.structure.reasoning}
                </p>
              </div>
            </div>

            {/* Complexity Level */}
            <div className="bg-white p-4 rounded-lg border">
              <h4 className="text-sm font-medium text-gray-500 mb-2">
                Complexity Level
              </h4>
              <div className="space-y-2">
                <div>
                  <span className="font-medium">Level: </span>
                  <span className="text-gray-700">
                    {typification.classification.complexity_level.level}
                  </span>
                </div>
                <div>
                  <span className="font-medium">Factors:</span>
                  <ul className="list-disc list-inside ml-4 text-gray-700">
                    {typification.classification.complexity_level.factors.map(
                      (factor, index) => (
                        <li key={index}>{factor}</li>
                      )
                    )}
                  </ul>
                </div>
                <p className="text-sm text-gray-600 mt-2">
                  {typification.classification.complexity_level.reasoning}
                </p>
              </div>
            </div>
          </div>

          {/* Methodology Section */}
          <div className="bg-white p-4 rounded-lg border">
            <h3 className="text-lg font-medium mb-4">Methodology</h3>
            <div className="space-y-4">
              <div>
                <span className="font-medium">Primary Method: </span>
                <span className="text-gray-700">
                  {typification.methodology.primary}
                </span>
              </div>
              <div>
                <span className="font-medium">Supporting Methods: </span>
                <span className="text-gray-700">
                  {typification.methodology.supporting.join(", ")}
                </span>
              </div>
              <div>
                <span className="font-medium">Principles:</span>
                <ul className="list-disc list-inside ml-4 text-gray-700">
                  {typification.methodology.principles.map(
                    (principle, index) => (
                      <li key={index}>{principle}</li>
                    )
                  )}
                </ul>
              </div>
              <div>
                <span className="font-medium">Application Guidelines:</span>
                <ul className="list-disc list-inside ml-4 text-gray-700">
                  {typification.methodology.application_guidelines.map(
                    (guideline, index) => (
                      <li key={index}>{guideline}</li>
                    )
                  )}
                </ul>
              </div>
            </div>
          </div>

          {/* System Analysis Section */}
          <div className="bg-white p-4 rounded-lg border">
            <h3 className="text-lg font-medium mb-4">System Analysis</h3>
            <div className="space-y-4">
              <div>
                <span className="font-medium">System Level: </span>
                <span className="text-gray-700">
                  {typification.system_analysis.system_level}
                </span>
              </div>

              {/* Super System */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-500">
                  Super System
                </h4>
                <div>
                  <span className="font-medium">Components:</span>
                  <ul className="list-disc list-inside ml-4 text-gray-700">
                    {typification.system_analysis.super_system.components.map(
                      (component, index) => (
                        <li key={index}>{component}</li>
                      )
                    )}
                  </ul>
                </div>
                <div>
                  <span className="font-medium">Interactions:</span>
                  <ul className="list-disc list-inside ml-4 text-gray-700">
                    {typification.system_analysis.super_system.interactions.map(
                      (interaction, index) => (
                        <li key={index}>{interaction}</li>
                      )
                    )}
                  </ul>
                </div>
              </div>

              {/* System */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-500">System</h4>
                <div>
                  <span className="font-medium">Components:</span>
                  <ul className="list-disc list-inside ml-4 text-gray-700">
                    {typification.system_analysis.system.components.map(
                      (component, index) => (
                        <li key={index}>{component}</li>
                      )
                    )}
                  </ul>
                </div>
                <div>
                  <span className="font-medium">Interactions:</span>
                  <ul className="list-disc list-inside ml-4 text-gray-700">
                    {typification.system_analysis.system.interactions.map(
                      (interaction, index) => (
                        <li key={index}>{interaction}</li>
                      )
                    )}
                  </ul>
                </div>
              </div>

              {/* Sub Systems */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-500">
                  Sub Systems
                </h4>
                <div>
                  <span className="font-medium">Components:</span>
                  <ul className="list-disc list-inside ml-4 text-gray-700">
                    {typification.system_analysis.sub_systems.components.map(
                      (component, index) => (
                        <li key={index}>{component}</li>
                      )
                    )}
                  </ul>
                </div>
                <div>
                  <span className="font-medium">Interactions:</span>
                  <ul className="list-disc list-inside ml-4 text-gray-700">
                    {typification.system_analysis.sub_systems.interactions.map(
                      (interaction, index) => (
                        <li key={index}>{interaction}</li>
                      )
                    )}
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Solution Characteristics Section */}
          <div className="bg-white p-4 rounded-lg border">
            <h3 className="text-lg font-medium mb-4">
              Solution Characteristics
            </h3>
            <div className="space-y-4">
              <div>
                <span className="font-medium">Required Resources:</span>
                <ul className="list-disc list-inside ml-4 text-gray-700">
                  {typification.solution_characteristics.required_resources.map(
                    (resource, index) => (
                      <li key={index}>{resource}</li>
                    )
                  )}
                </ul>
              </div>
              <div>
                <span className="font-medium">Key Constraints:</span>
                <ul className="list-disc list-inside ml-4 text-gray-700">
                  {typification.solution_characteristics.key_constraints.map(
                    (constraint, index) => (
                      <li key={index}>{constraint}</li>
                    )
                  )}
                </ul>
              </div>
              <div>
                <span className="font-medium">Success Criteria:</span>
                <ul className="list-disc list-inside ml-4 text-gray-700">
                  {typification.solution_characteristics.success_criteria.map(
                    (criteria, index) => (
                      <li key={index}>{criteria}</li>
                    )
                  )}
                </ul>
              </div>
            </div>
          </div>

          {/* ETA Section */}
          {typification.eta && (
            <div className="bg-white p-4 rounded-lg border">
              <h3 className="text-lg font-medium mb-4">
                Estimated Time of Arrival
              </h3>
              <div className="space-y-2">
                <div>
                  <span className="font-medium">Time: </span>
                  <span className="text-gray-700">{typification.eta.time}</span>
                </div>
                <p className="text-sm text-gray-600">
                  {typification.eta.reasoning}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </CollapsibleSection>
  );
}
