// src/components/task/TaskOverview.jsx
import React from 'react';
import { 
  FileText, 
  AlignLeft, 
  Target, 
  Compass, 
  Clock, 
  Microscope, 
  Lightbulb, 
  CheckCircle, 
  Check, 
  TrendingUp 
} from 'lucide-react';

const TaskOverview = ({ task }) => {
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
            <h3 className="text-sm font-medium text-gray-600 flex items-center mb-2">
              <AlignLeft className="w-4 h-4 mr-1.5 text-gray-500" />
              Initial User Query
            </h3>
            <p className="mt-1 text-gray-900 whitespace-pre-line bg-gray-50 p-3 rounded-md">{task.short_description || ''}</p>
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
          
          
          {/* Task metadata */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {task.level && (
              <div className="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
                <h3 className="text-sm font-medium text-gray-600 flex items-center mb-1">
                  <Target className="w-4 h-4 mr-1.5 text-gray-500" />
                  Level
                </h3>
                <p className="bg-gray-50 p-2 rounded-md border border-gray-100 text-gray-900 font-medium">{task.level}</p>
              </div>
            )}

            {task.eta_to_complete && (
              <div className="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
                <h3 className="text-sm font-medium text-gray-600 flex items-center mb-1">
                  <Clock className="w-4 h-4 mr-1.5 text-gray-500" />
                  ETA to Complete
                </h3>
                <p className="bg-gray-50 p-2 rounded-md border border-gray-100 text-gray-900 font-medium">{task.eta_to_complete}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaskOverview;
