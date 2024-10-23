import React from 'react';
import { useNavigate } from 'react-router-dom';
import { InfoCard, StatusBadge, ProgressBar } from './TaskComponents';

export default function Metadata({ task }) {
  const navigate = useNavigate();

  return (
    <InfoCard title="Metadata">
      <div className="space-y-3">
        <div>
          <h3 className="text-sm font-medium text-gray-500">Task ID</h3>
          <p className="mt-1 text-gray-900 font-mono">{task.id}</p>
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-500">Created</h3>
          <p className="mt-1 text-gray-900">
            {new Date(task.created_at).toLocaleString()}
          </p>
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-500">Last Updated</h3>
          <p className="mt-1 text-gray-900">
            {new Date(task.updated_at).toLocaleString()}
          </p>
        </div>
        {task.progress !== undefined && (
          <div>
            <h3 className="text-sm font-medium text-gray-500">Progress</h3>
            <ProgressBar progress={task.progress} />
          </div>
        )}
        {task.sub_tasks?.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-500">Sub Tasks</h3>
            <div className="mt-2 space-y-2">
              {task.sub_tasks.map(subTask => (
                <div 
                  key={subTask.id}
                  onClick={() => navigate(`/tasks/${subTask.id}`)}
                  className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <StatusBadge state={subTask.state} />
                  </div>
                  <p className="text-sm text-gray-900">{subTask.short_description}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </InfoCard>
  );
}
