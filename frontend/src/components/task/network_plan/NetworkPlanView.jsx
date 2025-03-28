import React, { useState } from 'react';
import { RefreshCw, AlertCircle, List } from 'lucide-react';
import { CollapsibleSection } from '../TaskComponents';
import NetworkGraph from './NetworkGraph';
import StageDetails from './StageDetails';
import { TaskStates } from '../../../constants/taskStates';
import { ReactFlowProvider } from '@xyflow/react';
import { useNavigate, useParams } from 'react-router-dom';

export default function NetworkPlanView({
  networkPlan,
  isGeneratingNetworkPlan,
  onGenerateNetworkPlan,
  taskState,
  isCompleted = false
}) {
  const [selectedStageId, setSelectedStageId] = useState(null);
  const navigate = useNavigate();
  const { taskId } = useParams();
  
  const hasNetworkPlan = networkPlan && 
    networkPlan.stages && 
    networkPlan.stages.length > 0 && 
    networkPlan.connections && 
    networkPlan.connections.length > 0;
    
  const canGenerateNetworkPlan = taskState === TaskStates.REQUIREMENTS_GENERATED;

  const handleStageSelect = (stageId) => {
    setSelectedStageId(stageId);
  };

  const getSelectedStage = () => {
    if (!selectedStageId || !hasNetworkPlan) return null;
    return networkPlan.stages.find(stage => stage.id === selectedStageId);
  };

  const handleViewAllStages = () => {
    navigate(`/tasks/${taskId}/all-stages`);
  };

  const renderNetworkPlanContent = () => {
    if (isGeneratingNetworkPlan) {
      return (
        <div className="flex items-center justify-center p-8">
          <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
            <div className="text-gray-500">Generating Network Plan...</div>
          </div>
        </div>
      );
    }

    if (!hasNetworkPlan) {
      return (
        <div className="text-center p-6">
          {canGenerateNetworkPlan ? (
            <>
              <p className="text-gray-600 mb-4">
                Generate a Network Plan based on the task requirements to define the stages and checkpoints needed to complete this task.
              </p>
              <button
                onClick={onGenerateNetworkPlan}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                disabled={!canGenerateNetworkPlan}
              >
                Generate Network Plan
              </button>
            </>
          ) : (
            <div className="flex flex-col items-center gap-2 p-4 text-amber-700 bg-amber-50 rounded-md">
              <AlertCircle className="w-5 h-5" />
              <p>Please complete the requirements before generating a Network Plan.</p>
            </div>
          )}
        </div>
      );
    }

    const selectedStage = getSelectedStage();

    return (
      <div className="space-y-8">
        <div className="bg-gray-50 border border-gray-200 rounded-lg shadow-sm overflow-hidden">
          <div className="h-[450px]">
            <ReactFlowProvider>
              <NetworkGraph 
                stages={networkPlan.stages}
                connections={networkPlan.connections}
                selectedStageId={selectedStageId}
                onStageSelect={handleStageSelect}
              />
            </ReactFlowProvider>
          </div>
        </div>

        {selectedStage ? (
          <StageDetails stage={selectedStage} />
        ) : (
          <div className="bg-blue-50 p-4 rounded-md border border-blue-100">
            <h3 className="text-lg font-medium text-blue-800 mb-2">Network Plan Overview</h3>
            <p className="text-gray-700 mb-4">This network plan outlines the stages and checkpoints required to complete this task. Click on any stage in the graph above to view its details.</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white p-4 rounded-md border border-gray-200">
                <h4 className="font-medium text-gray-800 mb-2">Total Stages</h4>
                <p className="text-2xl font-bold text-blue-600">{networkPlan.stages.length}</p>
              </div>
              <div className="bg-white p-4 rounded-md border border-gray-200">
                <h4 className="font-medium text-gray-800 mb-2">Total Checkpoints</h4>
                <p className="text-2xl font-bold text-green-600">
                  {networkPlan.stages.reduce((total, stage) => total + (stage.checkpoints ? stage.checkpoints.length : 0), 0)}
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="flex justify-between">
          <button
            onClick={handleViewAllStages}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
          >
            <List className="w-4 h-4" />
            Breakdown View
          </button>

          <button
            onClick={() => onGenerateNetworkPlan(true)}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Regenerate Network Plan
          </button>
        </div>
      </div>
    );
  };

  return (
    <CollapsibleSection 
      title={
        <div className="flex items-center justify-between w-full">
          <span>Network Plan</span>
          {isCompleted && (
            <span className="ml-2 text-xs bg-green-100 text-green-800 py-0.5 px-2 rounded-full">
              Complete
            </span>
          )}
        </div>
      }
      defaultOpen={!isCompleted}
      isCompleted={isCompleted}
    >
      {renderNetworkPlanContent()}
    </CollapsibleSection>
  );
} 