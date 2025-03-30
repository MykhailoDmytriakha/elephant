import React from 'react';
import { X, Loader2 } from 'lucide-react';

/**
 * Modal for editing task context
 */
export default function ContextEditModal({
  isOpen,
  onClose,
  task,
  contextFeedback,
  onContextFeedbackChange,
  onSubmitFeedback,
  isSubmitting
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">Edit Context</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* Body */}
        <div className="p-6 flex-1 overflow-y-auto">
          <div className="space-y-4">
            <div>
              <h4 className="font-medium text-gray-700 mb-1">Current Task Description</h4>
              <div className="p-3 bg-gray-50 border border-gray-200 rounded-md text-gray-700">
                {task.task || "No task description available"}
              </div>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-700 mb-1">Current Context</h4>
              <div className="p-3 bg-gray-50 border border-gray-200 rounded-md text-gray-700 max-h-40 overflow-y-auto">
                {task.context || "No context available"}
              </div>
            </div>
            
            <div>
              <label htmlFor="feedback" className="block font-medium text-gray-700 mb-1">
                Your Feedback
              </label>
              <p className="text-sm text-gray-500 mb-2">
                Provide specific feedback on how to improve the task description and context. 
                For example: "Focus more on mobile features", "Remove mention of XYZ", or "Add details about ABC".
              </p>
              <textarea
                id="feedback"
                value={contextFeedback}
                onChange={(e) => onContextFeedbackChange(e.target.value)}
                placeholder="Enter your feedback here..."
                className="w-full h-32 p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
        </div>
        
        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-white border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={onSubmitFeedback}
            disabled={!contextFeedback.trim() || isSubmitting}
            className={`px-4 py-2 bg-blue-600 text-white rounded-md flex items-center ${
              !contextFeedback.trim() || isSubmitting ? 'opacity-50 cursor-not-allowed' : 'hover:bg-blue-700'
            }`}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Updating...
              </>
            ) : (
              'Update Context'
            )}
          </button>
        </div>
      </div>
    </div>
  );
} 