// src/components/task/ExecutableTaskDisplay.jsx
import React from 'react';
import { Activity, Download, Upload, ShieldCheck, ChevronsRight } from 'lucide-react';

export const ExecutableTaskDisplay = ({ task, taskIndex }) => {
  if (!task) return null;

  return (
    <div className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-600" />
          <h5 className="font-semibold text-gray-800">{task.name}</h5>
          <span className="text-xs font-mono bg-gray-100 px-1.5 py-0.5 rounded text-gray-600">
            Seq: {task.sequence_order}
          </span>
        </div>
        <span className="text-xs font-mono text-gray-400">{task.id}</span>
      </div>

      {/* Description */}
      <p className="text-sm text-gray-700 ml-7">{task.description}</p>

      {/* Dependencies */}
      {task.dependencies && task.dependencies.length > 0 && (
        <div className="ml-7 text-xs text-gray-600 flex items-center gap-2">
          <ChevronsRight className="w-4 h-4 text-gray-400" />
          <span className="font-medium">Depends on:</span>
          <div className="flex flex-wrap gap-1">
            {task.dependencies.map(depId => (
              <span key={depId} className="font-mono bg-gray-200 px-1.5 py-0.5 rounded">{depId}</span>
            ))}
          </div>
        </div>
      )}

      {/* Required Inputs */}
      {task.required_inputs && task.required_inputs.length > 0 && (
        <div className="ml-7">
          <h6 className="text-xs font-medium text-gray-500 uppercase tracking-wider flex items-center gap-1 mb-1">
            <Download className="w-3 h-3" /> Required Inputs
          </h6>
          <div className="space-y-1">
            {task.required_inputs.map((artifact, idx) => (
              // Reuse ArtifactDisplay if it's suitable and exported
              // Or use a simpler format here
              <div key={`in-${idx}`} className="text-xs flex items-center gap-1 bg-gray-50 p-1 rounded border border-gray-100">
                <span className="font-medium">{artifact.name}</span>
                <span className="text-gray-500">({artifact.type})</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Generated Artifacts */}
      {task.generated_artifacts && task.generated_artifacts.length > 0 && (
        <div className="ml-7">
          <h6 className="text-xs font-medium text-gray-500 uppercase tracking-wider flex items-center gap-1 mb-1">
            <Upload className="w-3 h-3" /> Generated Artifacts
          </h6>
          <div className="space-y-1">
            {task.generated_artifacts.map((artifact, idx) => (
               <div key={`out-${idx}`} className="text-xs flex items-center gap-1 bg-gray-50 p-1 rounded border border-gray-100">
                <span className="font-medium">{artifact.name}</span>
                <span className="text-gray-500">({artifact.type})</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Validation Criteria */}
      {task.validation_criteria && task.validation_criteria.length > 0 && (
        <div className="ml-7">
          <h6 className="text-xs font-medium text-gray-500 uppercase tracking-wider flex items-center gap-1 mb-1">
            <ShieldCheck className="w-3 h-3 text-green-600" /> Validation Criteria
          </h6>
          <ul className="space-y-1 pl-4 list-disc text-sm text-gray-600">
            {task.validation_criteria.map((criterion, index) => (
              <li key={`val-${index}`}>{criterion}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};