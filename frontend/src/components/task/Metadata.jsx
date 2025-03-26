import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { InfoCard, StatusBadge, ProgressBar } from './TaskComponents';
import { RefreshCcw } from "lucide-react";
import { fetchTaskDetails } from '../../utils/api';
import { TaskStates, getStateNumber, getReadableState } from '../../constants/taskStates';

export default function Metadata({ task }) {
  const navigate = useNavigate();
  const [copied, setCopied] = useState(false);
  const [subtaskDetails, setSubtaskDetails] = useState([]);
  const [isLoadingSubtasks, setIsLoadingSubtasks] = useState(false);

  useEffect(() => {
    const loadSubtaskDetails = async () => {
      if (!task.sub_tasks?.length) return;
      
      setIsLoadingSubtasks(true);
      try {
        const details = await Promise.all(
          task.sub_tasks.map(taskId => fetchTaskDetails(taskId))
        );
        setSubtaskDetails(details);
      } catch (error) {
        console.error('Failed to fetch subtask details:', error);
      } finally {
        setIsLoadingSubtasks(false);
      }
    };

    loadSubtaskDetails();
  }, [task.sub_tasks]);

  return (
    <div className="sticky top-4">
      <InfoCard title="Metadata">
        <div className="space-y-3">
          <div>
            <h3 className="text-sm font-medium text-gray-500">Task ID</h3>
            <div className="flex items-center gap-2 mt-1">
              <p className="text-gray-900 font-mono">{task.id}</p>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(task.id);
                  setCopied(true);
                  setTimeout(() => setCopied(false), 2000); // Reset after 2 seconds
                }}
                className="p-1 text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100"
              >
                {copied ? (
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-7 h-7">
                    <path fillRule="evenodd" d="M19.916 4.626a.75.75 0 0 1 .208 1.04l-9 13.5a.75.75 0 0 1-1.154.114l-6-6a.75.75 0 0 1 1.06-1.06l5.353 5.353 8.493-12.739a.75.75 0 0 1 1.04-.208Z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-7 h-7">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 0 1-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 0 1 1.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 0 0-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 0 1-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 0 0-3.375-3.375h-1.5a1.125 1.125 0 0 1-1.125-1.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H9.75" />
                  </svg>
                )}
              </button>
            </div>
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
          {/* show stages */}
          {task.network_plan && (
            <>
              <hr className="my-3 border-gray-200" />
              <div>
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-gray-500">Stages</h3>
                </div>
                {task.network_plan?.stages && task.network_plan.stages.length > 0 && (
                  <div className="mt-3">
                    <div className="space-y-1.5">
                      {task.network_plan.stages.map((stage, index) => (
                        <div 
                          key={index} 
                          className="flex items-center p-2 rounded-md hover:bg-gray-50 cursor-pointer transition-colors border border-transparent hover:border-gray-200"
                        >
                          <span className="text-sm font-medium text-gray-900">{index + 1}. {stage.name}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </InfoCard>
    </div>
  );
}
