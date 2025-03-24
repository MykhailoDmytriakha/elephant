import React, { useState } from 'react';
import { CheckCircle2, ChevronRight, FileText, ShieldCheck } from 'lucide-react';

export default function StageDetails({ stage }) {
  const [activeCheckpoints, setActiveCheckpoints] = useState([]);

  if (!stage) return null;

  // Helpers for UI rendering
  const handleCheckpointClick = (checkpointIndex) => {
    setActiveCheckpoints(prev => {
      // If already active, remove it from array
      if (prev.includes(checkpointIndex)) {
        return prev.filter(idx => idx !== checkpointIndex);
      } 
      // Otherwise add it to the array
      return [...prev, checkpointIndex];
    });
  };

  const renderArtifact = (artifact) => {
    const getArtifactIcon = (type) => {
      switch (type.toLowerCase()) {
        case 'document':
          return <FileText className="w-5 h-5 text-amber-600" />;
        case 'software':
          return <div className="w-5 h-5 text-purple-600">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 20V6a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v14"></path>
              <path d="M2 20h20"></path>
              <path d="M14 12v.01"></path>
            </svg>
          </div>;
        default:
          return <FileText className="w-5 h-5 text-gray-600" />;
      }
    };

    return (
      <div className="mt-4 p-4 bg-gray-50 rounded-md border border-gray-200">
        <div className="flex items-start">
          {getArtifactIcon(artifact.type)}
          <div className="ml-3">
            <h4 className="font-medium text-gray-900">{artifact.name}</h4>
            <p className="text-sm text-gray-600 mt-1">{artifact.description}</p>
            {artifact.location && (
              <p className="text-xs text-gray-500 mt-2">
                Location: <span className="font-mono">{artifact.location}</span>
              </p>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderValidationList = (validations) => {
    if (!validations || validations.length === 0) return null;
    
    return (
      <div className="mt-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
          <ShieldCheck className="w-4 h-4 mr-1 text-green-600" />
          Validations
        </h4>
        <ul className="space-y-1 pl-6 list-disc text-sm text-gray-600">
          {validations.map((validation, index) => (
            <li key={`validation-${index}`}>{validation}</li>
          ))}
        </ul>
      </div>
    );
  };

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">{stage.name}</h2>
        <p className="mt-2 text-gray-700">{stage.description}</p>
      </div>

      {stage.result && stage.result.length > 0 && (
        <div className="mt-8">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Results</h3>
          <ul className="space-y-1 pl-6 list-disc text-sm">
            {stage.result.map((result, index) => (
              <li key={`result-${index}`}>{result}</li>
            ))}
          </ul>
        </div>
      )}

      {stage.what_should_be_delivered && stage.what_should_be_delivered.length > 0 && (
        <div className="mt-8">
          <h3 className="text-lg font-medium text-gray-900 mb-4">What should be delivered</h3>
          <ul className="space-y-1 pl-6 list-disc text-sm">
            {stage.what_should_be_delivered.map((item, index) => (
              <li key={`delivered-item-${index}`}>{item}</li> 
            ))}
          </ul>
        </div>
      )}

      {stage.checkpoints && stage.checkpoints.length > 0 && (
        <div className="mt-8">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Checkpoints</h3>
          <div className="space-y-4">
            {stage.checkpoints.map((checkpoint, index) => (
              <div 
                key={`checkpoint-${index}`}
                className="border border-gray-200 rounded-lg overflow-hidden"
              >
                {/* Checkpoint header - clickable */}
                <button
                  onClick={() => handleCheckpointClick(index)}
                  className="w-full px-4 py-3 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition-colors text-left"
                >
                  <div className="flex items-center">
                    <CheckCircle2 className="w-5 h-5 text-green-600 mr-3" />
                    <div>
                      <h4 className="font-medium text-gray-900">{checkpoint.checkpoint}</h4>
                    </div>
                  </div>
                  <ChevronRight 
                    className={`w-5 h-5 text-gray-400 transition-transform ${activeCheckpoints.includes(index) ? 'transform rotate-90' : ''}`} 
                  />
                </button>
                
                {/* Expanded checkpoint details */}
                {activeCheckpoints.includes(index) && (
                  <div className="px-4 py-3 border-t border-gray-200">
                    <p className="text-gray-700 text-sm">{checkpoint.description}</p>
                    
                    {/* Artifact section */}
                    {checkpoint.artifact && renderArtifact(checkpoint.artifact)}
                    
                    {/* Validations list */}
                    {renderValidationList(checkpoint.validations)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
} 