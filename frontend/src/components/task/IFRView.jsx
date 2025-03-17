import React, { useEffect, useState } from 'react';
import { CollapsibleSection, InfoCard } from './TaskComponents';
import { ChevronRight, CheckCircle2, RefreshCw, AlertCircle } from 'lucide-react';
import { TaskStates } from '../../constants/taskStates';

export default function IFRView({ 
  ifr,
  isGeneratingIFR,
  onGenerateIFR,
  taskState
}) {
  const [localIfr, setLocalIfr] = useState(ifr);
  
  // Update local state when prop changes
  useEffect(() => {
    if (ifr) {
      setLocalIfr(ifr);
    }
  }, [ifr]);
  
  // Check if we should display IFR content
  const shouldShowIFR = localIfr && Object.keys(localIfr).length > 0;
  
  // The state from the backend is a string like "3.5. Task Formation" so compare with full string
  const canGenerateIFR = taskState === TaskStates.TASK_FORMATION;

  console.log('IFRView rendering with:', { 
    ifr: localIfr, 
    shouldShowIFR, 
    taskState, 
    canGenerateIFR, 
    expectedState: TaskStates.TASK_FORMATION 
  });

  const renderIFRContent = () => {
    if (isGeneratingIFR) {
      return (
        <div className="flex items-center justify-center p-8">
          <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
            <div className="text-gray-500">Generating Ideal Final Result...</div>
          </div>
        </div>
      );
    }

    if (!shouldShowIFR) {
      return (
        <div className="text-center p-6">
          {canGenerateIFR ? (
            <>
              <p className="text-gray-600 mb-4">
                Generate an Ideal Final Result (IFR) based on the task scope to define success criteria and expected outcomes.
              </p>
              <button
                onClick={onGenerateIFR}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                disabled={!canGenerateIFR}
              >
                Generate Ideal Final Result
              </button>
            </>
          ) : (
            <div className="flex flex-col items-center gap-2 p-4 text-amber-700 bg-amber-50 rounded-md">
              <AlertCircle className="w-5 h-5" />
              <p>Please complete the task formulation before generating an Ideal Final Result.</p>
            </div>
          )}
        </div>
      );
    }

    return (
      <div className="space-y-6">
        <div className="bg-blue-50 p-4 rounded-md border border-blue-100">
          <h3 className="text-lg font-medium text-blue-800 mb-2">Ideal Final Result</h3>
          <p className="text-gray-700">{localIfr.ideal_final_result}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <InfoCard title="Success Criteria" className="h-full">
            <ul className="space-y-2">
              {localIfr.success_criteria.map((criterion, index) => (
                <li key={`criterion-${index}`} className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                  <span>{criterion}</span>
                </li>
              ))}
            </ul>
          </InfoCard>

          <InfoCard title="Expected Outcomes" className="h-full">
            <ul className="space-y-2">
              {localIfr.expected_outcomes.map((outcome, index) => (
                <li key={`outcome-${index}`} className="flex items-start gap-2">
                  <ChevronRight className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
                  <span>{outcome}</span>
                </li>
              ))}
            </ul>
          </InfoCard>
        </div>

        <InfoCard title="Quality Metrics">
          <div>
            <table className="w-full divide-y divide-gray-200 table-fixed">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/3">Metric</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-2/3">Target Value</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {localIfr.quality_metrics.map((metric, index) => (
                  <tr key={`metric-${index}`}>
                    <td className="px-6 py-4 text-sm text-gray-500 break-words">{metric.metric_name}</td>
                    <td className="px-6 py-4 text-sm text-blue-600 font-medium break-words hyphens-auto">{metric.metric_value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </InfoCard>

        <InfoCard title="Validation Checklist">
          <ul className="space-y-4">
            {localIfr.validation_checklist.map((checkItem, index) => (
              <li key={`check-${index}`} className="bg-gray-50 p-3 rounded-md">
                <div className="font-medium text-gray-800 mb-1">{checkItem.item}</div>
                <div className="text-gray-600 text-sm">{checkItem.criteria}</div>
              </li>
            ))}
          </ul>
        </InfoCard>

        <div className="flex justify-end">
          <button
            onClick={onGenerateIFR}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Regenerate
          </button>
        </div>
      </div>
    );
  };

  return (
    <CollapsibleSection title="Ideal Final Result (IFR)" defaultOpen={true}>
      {renderIFRContent()}
    </CollapsibleSection>
  );
}
