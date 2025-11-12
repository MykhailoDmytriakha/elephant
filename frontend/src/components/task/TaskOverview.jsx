// src/components/task/TaskOverview.jsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { updateTask } from '../../utils/api';
import {
  FileText,
  AlignLeft,
  Target,
  Compass,
  Microscope,
  Lightbulb,
  CheckCircle,
  Check,
  TrendingUp,
  ChevronDown,
  ChevronUp,
  Info,
  Copy,
  Edit2,
  Save,
  X
} from 'lucide-react';

const TaskOverview = ({ task, onTaskUpdated }) => {
  const [metadataExpanded, setMetadataExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  const [isEditingQuery, setIsEditingQuery] = useState(false);
  const [editedQuery, setEditedQuery] = useState('');

  // Load metadata expanded state from localStorage on mount
  useEffect(() => {
    const savedState = localStorage.getItem(`taskOverview_metadata_expanded_${task.id}`);
    if (savedState !== null) {
      setMetadataExpanded(JSON.parse(savedState));
    }
  }, [task.id]);

  // Save metadata expanded state to localStorage when it changes
  useEffect(() => {
    localStorage.setItem(`taskOverview_metadata_expanded_${task.id}`, JSON.stringify(metadataExpanded));
  }, [metadataExpanded, task.id]);

  const handleCopy = () => {
    navigator.clipboard.writeText(task.id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const toggleMetadata = () => {
    setMetadataExpanded(!metadataExpanded);
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      toggleMetadata();
    }
  };

  const startEditingQuery = () => {
    setEditedQuery(task.short_description || '');
    setIsEditingQuery(true);
  };

  const cancelEditingQuery = () => {
    setIsEditingQuery(false);
    setEditedQuery('');
  };

  const saveEditedQuery = async () => {
    try {
      await updateTask(task.id, { short_description: editedQuery });
      setIsEditingQuery(false);
      // Refresh task data after successful save
      if (onTaskUpdated) {
        await onTaskUpdated();
      }
    } catch (error) {
      console.error('Failed to save edited query:', error);
      // Handle error (show toast, etc.)
    }
  };

  return (
    <div className="bg-white shadow-sm rounded-lg overflow-hidden border border-gray-200">
      <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-white">
        <h2 className="text-xl font-semibold text-gray-900 flex items-center">
          <FileText className="w-5 h-5 mr-2 text-blue-600" />
          Task Overview
        </h2>
      </div>
      
      <div className="p-6">
        <div className="space-y-6">
          {/* Subtask information if applicable */}
          {task.sub_level > 0 && (
            <div className="bg-blue-50 border border-blue-100 rounded-lg p-5 mb-5">
              <div className="flex items-center gap-2 mb-3">
                <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-blue-600 text-white text-sm font-medium">{task.sub_level}</span>
                <span className="text-sm text-blue-700 font-semibold">Subtask Level</span>
              </div>
              {task.contribution_to_parent_task && (
                <div className="text-sm text-blue-800">
                  <span className="font-medium">Contribution to Parent Task:</span>
                  <p className="mt-1 bg-white/70 p-3 rounded-md border border-blue-100">{task.contribution_to_parent_task}</p>
                </div>
              )}
            </div>
          )}

          {/* Task description */}
          <div className="bg-white p-5 rounded-lg border border-gray-100 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600 flex items-center">
                <AlignLeft className="w-4 h-4 mr-1.5 text-gray-500" />
                Initial User Query
              </h3>
              {!isEditingQuery && (
                <button
                  onClick={startEditingQuery}
                  className="text-gray-400 hover:text-gray-600 p-1 rounded-md hover:bg-gray-100 transition-colors"
                  title="Edit query"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
              )}
            </div>
            {isEditingQuery ? (
              <div className="space-y-3">
                <textarea
                  value={editedQuery}
                  onChange={(e) => setEditedQuery(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                  rows={4}
                  placeholder="Enter your query..."
                />
                <div className="flex gap-2">
                  <button
                    onClick={saveEditedQuery}
                    className="flex items-center gap-1 px-3 py-1 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
                  >
                    <Save className="w-3 h-3" />
                    Save
                  </button>
                  <button
                    onClick={cancelEditingQuery}
                    className="flex items-center gap-1 px-3 py-1 bg-gray-500 text-white rounded-md hover:bg-gray-600 transition-colors text-sm"
                  >
                    <X className="w-3 h-3" />
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <p className="mt-1 text-gray-900 whitespace-pre-line bg-gray-50 p-3 rounded-md">{task.short_description || ''}</p>
            )}
          </div>

          {/* Task data */}
          {task.task && (
            <div className="bg-white p-5 rounded-lg border border-gray-100 shadow-sm">
              <h3 className="text-sm font-medium text-gray-600 flex items-center mb-2">
                <Target className="w-4 h-4 mr-1.5 text-gray-500" />
                Task
              </h3>
              <p className="mt-1 text-gray-900 whitespace-pre-line bg-gray-50 p-3 rounded-md">{task.task}</p>
            </div>
          )}

          {/* Task context */}
          <div className="bg-white p-5 rounded-lg border border-gray-100 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600 flex items-center">
                <Compass className="w-4 h-4 mr-1.5 text-gray-500" />
                Context
              </h3>
              <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                task.is_context_sufficient 
                  ? 'bg-green-100 text-green-800 border border-green-200' 
                  : 'bg-amber-100 text-amber-800 border border-amber-200'
              }`}>
                {task.is_context_sufficient ? 'Sufficient' : 'Insufficient'}
              </span>
            </div>
            
            <div className="mt-1 bg-gray-50 p-3 rounded-md border border-gray-100">
              {task.context 
                ? <p className="text-gray-900 whitespace-pre-line">{task.context}</p>
                : <p className="text-gray-500 italic">No context provided yet.</p>
              }
            </div>
          </div>

          {/* Task Scope - Check if scope exists otherwise don't render */}
          {task.scope && (
            <div className="bg-white p-5 rounded-lg border border-gray-100 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-gray-600 flex items-center">
                  <Microscope className="w-4 h-4 mr-1.5 text-gray-500" />
                  Scope
                </h3>
                <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                  task.scope.status === 'approved'
                    ? 'bg-green-100 text-green-800 border border-green-200' 
                    : 'bg-amber-100 text-amber-800 border border-amber-200'
                }`}>
                  {task.scope.status === 'approved' ? 'Approved' : 'Pending'}
                </span>
              </div>
              <div className="mt-1 bg-gray-50 p-3 rounded-md border border-gray-100">
                {task.scope.scope ? (
                  <p className="text-gray-900 whitespace-pre-line">{task.scope.scope}</p>
                ) : (
                  <p className="text-gray-500 italic">No scope defined yet.</p>
                )}
              </div>
            </div>
          )}

          {/* Task IFR */}
          <div className="bg-white p-5 rounded-lg border border-gray-100 shadow-sm">
            <h3 className="text-sm font-medium text-gray-600 flex items-center mb-2">
              <Lightbulb className="w-4 h-4 mr-1.5 text-gray-500" />
              IFR
            </h3>
            <div className="mt-1 bg-gray-50 p-3 rounded-md border border-gray-100">
              {task.ifr ? (
                <p className="text-gray-900 whitespace-pre-line">{task.ifr.ideal_final_result}</p>
              ) : (
                <p className="text-gray-500 italic">No IFR defined yet.</p>
              )}
            </div>
          </div>

          {/* Task Expected Outcomes */}
          {task.ifr && task.ifr.expected_outcomes && (
            <div className="bg-white p-5 rounded-lg border border-gray-100 shadow-sm">
              <h3 className="text-sm font-medium text-gray-600 flex items-center mb-2">
                <TrendingUp className="w-4 h-4 mr-1.5 text-gray-500" />
                Expected Outcomes
              </h3>
              <div className="mt-1 bg-gray-50 p-3 rounded-md border border-gray-100 space-y-2">
                {task.ifr.expected_outcomes.map((outcome, index) => (
                  <div key={index} className="flex items-start">
                    <Check className="w-4 h-4 mt-1 mr-2 text-gray-400 flex-shrink-0" />
                    <p className="text-gray-900 whitespace-pre-line">{outcome}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Task Success Criteria */}
          {task.ifr && task.ifr.success_criteria && (
            <div className="bg-white p-5 rounded-lg border border-gray-100 shadow-sm">
              <h3 className="text-sm font-medium text-gray-600 flex items-center mb-2">
                <CheckCircle className="w-4 h-4 mr-1.5 text-gray-500" />
                Success Criteria
              </h3>
              <div className="mt-1 bg-gray-50 p-3 rounded-md border border-gray-100 space-y-2">
                {task.ifr.success_criteria.map((criteria, index) => (
                  <div key={index} className="flex items-start">
                    <Check className="w-4 h-4 mt-1 mr-2 text-gray-400 flex-shrink-0" />
                    <p className="text-gray-900 whitespace-pre-line">{criteria}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Collapsible Metadata Section */}
          <div className="border-t border-gray-200 mt-6">
            <button
              id="metadata-toggle"
              onClick={toggleMetadata}
              onKeyDown={handleKeyDown}
              className="w-full flex justify-between items-center py-3 px-1 hover:bg-gray-50 transition-colors cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-inset"
              aria-expanded={metadataExpanded}
              aria-label="Toggle metadata visibility"
              aria-controls="metadata-content"
            >
              <span className="text-sm font-medium text-gray-600 flex items-center gap-2">
                <Info className="w-4 h-4" />
                Metadata
              </span>
              {metadataExpanded ?
                <ChevronUp className="w-4 h-4 text-gray-400" /> :
                <ChevronDown className="w-4 h-4 text-gray-400" />
              }
            </button>

            {metadataExpanded && (
              <div
                id="metadata-content"
                className="px-4 pb-4 space-y-3 bg-gray-50 rounded-b-lg transition-all duration-200"
                role="region"
                aria-labelledby="metadata-toggle"
              >
                {/* Task ID */}
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Task ID</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <p className="text-gray-900 font-mono text-xs bg-white p-2 rounded border break-all">
                      {task.id}
                    </p>
                    <button
                      onClick={handleCopy}
                      className="p-1 text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100"
                      title="Copy Task ID"
                    >
                      {copied ? (
                        <Check className="w-4 h-4 text-green-600" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Created At */}
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Created</h3>
                  <p className="mt-1 text-gray-900 text-sm">
                    {new Date(task.created_at).toLocaleString()}
                  </p>
                </div>

                {/* Updated At */}
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Last Updated</h3>
                  <p className="mt-1 text-gray-900 text-sm">
                    {new Date(task.updated_at).toLocaleString()}
                  </p>
                </div>

                {/* Level */}
                {task.level && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Level</h3>
                    <p className="mt-1 text-gray-900 text-sm bg-white p-2 rounded border">
                      {task.level}
                    </p>
                  </div>
                )}

                {/* ETA to Complete */}
                {task.eta_to_complete && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">ETA to Complete</h3>
                    <p className="mt-1 text-gray-900 text-sm bg-white p-2 rounded border">
                      {task.eta_to_complete}
                    </p>
                  </div>
                )}

                {/* Stages List */}
                {task.network_plan?.stages && task.network_plan.stages.length > 0 && (
                  <>
                    <hr className="my-3 border-gray-200" />
                    <div>
                      <h3 className="text-sm font-medium text-gray-500 mb-2">Stages</h3>
                      <div className="space-y-1">
                        {task.network_plan.stages.map((stage) => (
                          <Link
                            key={stage.id}
                            to={`/tasks/${task.id}/stages/${stage.id}`}
                            state={{
                              stage: stage,
                              taskShortDescription: task.short_description,
                              taskId: task.id,
                              task: task
                            }}
                            className="block p-2 rounded-md hover:bg-gray-100 cursor-pointer transition-colors border border-transparent hover:border-gray-200"
                          >
                            <span className="text-sm font-medium text-blue-700 hover:text-blue-900">
                              {stage.id}. {stage.name}
                            </span>
                          </Link>
                        ))}
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaskOverview;
