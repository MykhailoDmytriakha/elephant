// src/components/task/SubtaskDisplay.jsx
import React from 'react';
import { Cpu, Cog, User, ListTree } from 'lucide-react'; // Added ListTree

// --- NEW: Import StatusDetailsDisplay ---
import { StatusDetailsDisplay } from './TaskComponents'; 
// --- END: Import StatusDetailsDisplay ---

// Helper to get executor icon
const getExecutorIcon = (executorType) => {
  switch (executorType) {
    case 'AI_AGENT':
      return <Cpu className="w-4 h-4 text-blue-600" />;
    case 'ROBOT':
      return <Cog className="w-4 h-4 text-purple-600" />;
    case 'HUMAN':
      return <User className="w-4 h-4 text-orange-600" />;
    default:
      return <ListTree className="w-4 h-4 text-gray-500" />;
  }
};

export const SubtaskDisplay = ({ subtask }) => {
  if (!subtask) return null;

  return (
    <div className="p-3 bg-gray-100 rounded-md border border-gray-200 space-y-1.5 hover:bg-gray-200 transition-colors duration-150">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {getExecutorIcon(subtask.executor_type)}
          <h6 className="font-medium text-gray-800 text-sm">{subtask.name}</h6>
           <span className="text-xs font-mono bg-gray-200 px-1 py-0.5 rounded text-gray-600">
            Seq: {subtask.sequence_order}
          </span>
        </div>
        <span className="text-xs font-mono text-gray-400">{subtask.id}</span>
      </div>

      {/* Description */}
      <p className="text-xs text-gray-600 ml-6">{subtask.description}</p>

      {/* --- NEW: Subtask Status Details --- */}
      <div className="ml-6">
        <StatusDetailsDisplay item={subtask} />
      </div>
      {/* --- END: Subtask Status Details --- */}

      {/* Executor Type */}
      <div className="ml-6 text-xs text-gray-500 flex items-center gap-1">
         <span className="font-medium">Executor:</span>
         <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
             subtask.executor_type === 'AI_AGENT' ? 'bg-blue-100 text-blue-700' :
             subtask.executor_type === 'ROBOT' ? 'bg-purple-100 text-purple-700' :
             subtask.executor_type === 'HUMAN' ? 'bg-orange-100 text-orange-700' : 'bg-gray-200 text-gray-600'
         }`}>{subtask.executor_type.replace('_', ' ')}</span>
      </div>

      {/* Optionally show parent IDs for debugging */}
      
      <div className="ml-6 text-xs text-gray-400 mt-1 flex flex-wrap gap-x-2">
        <span>Task: {subtask.parent_task_id}</span>
        <span>Stage: {subtask.parent_stage_id}</span>
        <span>Work: {subtask.parent_work_id}</span>
        <span>Exec: {subtask.parent_executable_task_id}</span>
      </div>
     
    </div>
  );
};