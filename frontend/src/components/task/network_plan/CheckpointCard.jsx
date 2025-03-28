import React, { useState } from 'react';
import { CheckCircle2, ChevronRight, ShieldCheck } from 'lucide-react';
import { ArtifactDisplay } from '../TaskComponents';

export default function CheckpointCard({ checkpoint }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleClick = () => {
    setIsExpanded(!isExpanded);
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
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {/* Checkpoint header - clickable */}
      <button
        onClick={handleClick}
        className="w-full px-4 py-3 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition-colors text-left"
      >
        <div className="flex items-center">
          <CheckCircle2 className="w-5 h-5 text-green-600 mr-3" />
          <div>
            <h4 className="font-medium text-gray-900">{checkpoint.checkpoint}</h4>
          </div>
        </div>
        <ChevronRight 
          className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? 'transform rotate-90' : ''}`} 
        />
      </button>
      
      {/* Expanded checkpoint details */}
      {isExpanded && (
        <div className="px-4 py-3 border-t border-gray-200">
          <p className="text-gray-700 text-sm">{checkpoint.description}</p>
          
          {/* Artifact section */}
          {checkpoint.artifact && (
            <div className="mt-4">
              <ArtifactDisplay artifact={checkpoint.artifact} />
            </div>
          )}
          
          {/* Validations list */}
          {renderValidationList(checkpoint.validations)}
        </div>
      )}
    </div>
  );
} 