// src/components/task/StageOverviewPanel.jsx
import React from 'react';
import { Layers, TerminalSquare, ListTree, Circle } from 'lucide-react'; // Added Circle for default
import { InfoCard } from './TaskComponents'; // Assuming InfoCard is in TaskComponents

// Helper to get executor icon - simplified for overview
const getExecutorIconSimple = (executorType) => {
  switch (executorType) {
    case 'AI_AGENT':
      return <Circle className="w-2 h-2 text-blue-500 fill-current" />;
    case 'ROBOT':
      return <Circle className="w-2 h-2 text-purple-500 fill-current" />;
    case 'HUMAN':
      return <Circle className="w-2 h-2 text-orange-500 fill-current" />;
    default:
      return <Circle className="w-2 h-2 text-gray-400 fill-current" />;
  }
};

export default function StageOverviewPanel({ stage }) {
    if (!stage) {
        return (
            <InfoCard title="Stage Overview">
                <p className="text-sm text-gray-500">No stage data available.</p>
            </InfoCard>
        );
    }

    return (
        <InfoCard title={`Stage ${stage.id}: ${stage.name}`}>
            <div className="space-y-3 max-h-[70vh] overflow-y-auto pr-2">
                {!stage.work_packages || stage.work_packages.length === 0 ? (
                    <p className="text-sm text-gray-500 italic px-2 py-1">No work packages defined for this stage.</p>
                ) : (
                    stage.work_packages.map((work) => (
                        <div key={work.id} className="pl-1 border-l-2 border-gray-200">
                            <div className="flex items-center gap-2 px-2 py-1 bg-gray-50 rounded-r-md">
                                <Layers className="w-3.5 h-3.5 text-gray-500 flex-shrink-0" />
                                <span className="text-sm font-medium text-gray-800 truncate" title={work.name}>
                                    {work.name}
                                    <span className="text-xs font-mono text-gray-400 ml-1">({work.id})</span>
                                </span>
                            </div>
                            {!work.tasks || work.tasks.length === 0 ? (
                                <p className="text-xs text-gray-400 italic px-2 py-1 ml-4">No executable tasks.</p>
                            ) : (
                                <div className="ml-4 space-y-1 mt-1">
                                    {work.tasks.map((execTask) => (
                                        <div key={execTask.id} className="pl-1 border-l-2 border-purple-200">
                                            <div className="flex items-center gap-2 px-2 py-0.5 bg-purple-50 rounded-r-md">
                                                <TerminalSquare className="w-3 h-3 text-purple-600 flex-shrink-0" />
                                                <span className="text-xs font-medium text-purple-800 truncate" title={execTask.name}>
                                                    {execTask.name}
                                                    <span className="text-xs font-mono text-purple-400 ml-1">({execTask.id})</span>
                                                </span>
                                            </div>
                                            {!execTask.subtasks || execTask.subtasks.length === 0 ? (
                                                <p className="text-xs text-gray-400 italic px-2 py-0.5 ml-4">No subtasks.</p>
                                            ) : (
                                                <div className="ml-4 space-y-0.5 mt-0.5">
                                                    {execTask.subtasks.map((subtask) => (
                                                        <div key={subtask.id} className="flex items-center gap-1.5 px-2 py-0 rounded-r-md">
                                                             {getExecutorIconSimple(subtask.executor_type)}
                                                            <span className="text-xs text-gray-600 truncate" title={subtask.name}>
                                                                {subtask.name}
                                                                <span className="text-xs font-mono text-gray-400 ml-1">({subtask.id})</span>
                                                            </span>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))
                )}
            </div>
        </InfoCard>
    );
}