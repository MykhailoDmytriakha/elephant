import React from 'react';
import CheckpointCard from './CheckpointCard';
import StageSection from './StageSection';

export default function StageDetails({ stage }) {
  if (!stage) return null;

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">{stage.name}</h2>
        <p className="mt-2 text-gray-700">{stage.description}</p>
      </div>

      <StageSection title="Results" items={stage.result} />
      <StageSection title="What should be delivered" items={stage.what_should_be_delivered} />

      {stage.checkpoints && stage.checkpoints.length > 0 && (
        <div className="mt-8">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Checkpoints</h3>
          <div className="space-y-4">
            {stage.checkpoints.map((checkpoint, index) => (
              <CheckpointCard key={`checkpoint-${index}`} checkpoint={checkpoint} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
} 