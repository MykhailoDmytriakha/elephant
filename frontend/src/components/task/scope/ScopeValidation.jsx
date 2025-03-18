import React, { useState } from 'react';
import { RefreshCcw, FileText, Check, ChevronRight, AlertCircle } from 'lucide-react';
import { validateScope } from '../../../utils/api';

/**
 * Component for validating and approving a task scope
 * Handles all validation logic, API calls, and UI for reviewing the scope
 * 
 * @param {Object} task - The task object
 * @param {Object|string} draftScope - The draft scope to be validated
 * @param {Array} validationCriteria - Criteria used to validate the scope
 * @param {Array} changes - Any changes made to the scope
 * @param {boolean} isTaskApproved - Whether the task has been approved on the server
 * @param {boolean} isLocallyApproved - Whether the task has been approved locally
 * @param {string|null} feedback - User feedback on the scope
 * @param {boolean} isLoading - Whether any API call is in progress
 * @param {string} errorMessage - Any error message to display
 * @param {Function} onUpdateDraftScope - Function to update draft scope
 * @param {Function} onSetFeedback - Function to update feedback
 * @param {Function} onSetChanges - Function to update changes
 * @param {Function} onSetLocallyApproved - Function to update local approval state
 * @param {Function} onSetErrorMessage - Function to update error message
 * @param {Function} onSetLoading - Function to update loading state
 * @param {Function} onSetFlowState - Function to update flow state
 */
export default function ScopeValidation({
  task,
  draftScope,
  validationCriteria = [],
  changes = [],
  isTaskApproved = false,
  isLocallyApproved = false,
  feedback = null,
  isLoading = false,
  errorMessage = '',
  onUpdateDraftScope,
  onSetFeedback, 
  onSetChanges,
  onSetLocallyApproved,
  onSetErrorMessage,
  onSetLoading,
  onSetFlowState
}) {
  // State for showing/hiding validation criteria
  const [showValidationCriteria, setShowValidationCriteria] = useState(true);
  
  // Helper to determine if feedback form should be shown
  const showFeedbackForm = feedback !== null;
  
  // Extract validation criteria from draftScope if available
  const effectiveValidationCriteria = 
    (draftScope && typeof draftScope === 'object' && draftScope.validation_criteria) ?
    draftScope.validation_criteria : validationCriteria;
  
  // Helper to get the scope text, handling different formats
  const getScopeText = () => {
    // If it's a string, return it directly
    if (typeof draftScope === 'string') {
      return draftScope;
    }
    
    // If it's an object, try to find the scope text
    if (draftScope && typeof draftScope === 'object') {
      // Check for a direct scope property
      if (draftScope.scope && typeof draftScope.scope === 'string') {
        return draftScope.scope;
      }
      
      // Check for updatedScope property
      if (draftScope.updatedScope && typeof draftScope.updatedScope === 'string') {
        return draftScope.updatedScope;
      }
    }
    
    // Nothing found
    return '';
  };

  // Handler for approval/changes
  const handleValidation = async (isApproved, feedbackText = null) => {
    onSetLoading(true);
    onSetErrorMessage('');
    
    try {
      // If feedbackText is provided, use it; otherwise use the feedback state
      const feedbackToSubmit = feedbackText !== null ? feedbackText : feedback;
      
      const response = await validateScope(task.id, isApproved, feedbackToSubmit);
      
      if (isApproved) {
        try {
          // Final scope approved - set local approval state
          onSetLocallyApproved(true);
          
          // Extract and preserve validation criteria if it exists in the draft scope
          if (typeof draftScope === 'object' && draftScope.validation_criteria) {
            // Keep draft scope with validation criteria
            onUpdateDraftScope(draftScope);
          } else if (typeof draftScope === 'string') {
            // If draftScope is just a string, we need to create an object with validation criteria
            const currentCriteria = task?.scope?.validation_criteria || [];
            onUpdateDraftScope({
              scope: draftScope,
              validation_criteria: currentCriteria
            });
          }
          
          // When user explicitly approves, always go to final state
          // Don't check task.scope.status as it contains the old value
          onSetFlowState('final');
          
          // Clear feedback
          onSetFeedback(null);
        } catch (error) {
          console.error('Error finalizing task:', error);
          // Still show final scope screen even if API fails
          onSetLocallyApproved(true);
          onSetFlowState('final');
          onSetFeedback(null); // Clear feedback
          onSetErrorMessage('Scope approved, but there was an issue finalizing the task. The scope is still saved.');
        }
      } else {
        // Display updated scope and stay on validation screen
        if (response && response.updatedScope) {
          // Preserve validation criteria when updating draft scope
          const currentCriteria = 
            (typeof draftScope === 'object' && draftScope.validation_criteria) ? 
            draftScope.validation_criteria : 
            task?.scope?.validation_criteria || [];
          
          // Update draft scope as an object with both updatedScope and validation criteria
          onUpdateDraftScope({
            scope: response.updatedScope,
            validation_criteria: currentCriteria
          });
          
          // Clear feedback form - explicitly set to null to close the form
          onSetFeedback(null);
          
          // Show a success message
          onSetErrorMessage('Feedback submitted. Please review the updated scope.');
          
          // Store changes if present in the response
          if (response.changes && Array.isArray(response.changes)) {
            onSetChanges(response.changes);
          } else {
            onSetChanges([]);
          }
        } else {
          // Handle case where response doesn't contain updated scope
          onSetErrorMessage('Feedback submitted, but no updates were provided by the server.');
        }
        // Always stay on validation screen, never go back to questions
      }
    } catch (error) {
      console.error('Error validating scope:', error);
      onSetErrorMessage(`Failed to validate scope: ${error.message || 'Please try again.'}`);
      // Don't clear feedback on error so user can try again
    } finally {
      onSetLoading(false);
    }
  };
  
  // Handler for submitting feedback
  const handleSubmitFeedback = () => {
    if (feedback?.trim()) {
      handleValidation(false, feedback);
    }
  };
  
  const scopeText = getScopeText();
  
  return (
    <div className="bg-white p-6 rounded-lg border">
      <h3 className="text-lg font-semibold mb-2">
        {isTaskApproved || isLocallyApproved ? 'Approved Scope' : 'Scope Validation'}
      </h3>
      {!isTaskApproved && !isLocallyApproved && (
        <p className="text-gray-600 mb-4">
          Review the generated scope. Is this definition acceptable or do you need to make changes?
        </p>
      )}
      
      {/* Error/Success Message */}
      {errorMessage && (
        <div className={`mb-4 p-3 rounded-md flex items-start ${
          errorMessage.includes('submitted') || errorMessage.includes('success')
            ? 'bg-green-50 text-green-700'
            : 'bg-red-50 text-red-700'
        }`}>
          {errorMessage.includes('submitted') || errorMessage.includes('success')
            ? <Check className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
            : <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
          }
          <p>{typeof errorMessage === 'string' ? errorMessage : 'An error occurred'}</p>
        </div>
      )}
      
      {/* Validation Criteria Section */}
      {effectiveValidationCriteria && effectiveValidationCriteria.length > 0 && (
        <div className="border rounded-lg mb-6 overflow-hidden">
          <div 
            className="bg-blue-50 p-4 flex justify-between items-center cursor-pointer"
            onClick={() => setShowValidationCriteria(!showValidationCriteria)}
          >
            <h4 className="font-medium text-blue-800">Validation Criteria</h4>
            <button className="p-1 hover:bg-blue-100 rounded-full">
              <ChevronRight 
                className={`w-5 h-5 text-blue-700 transform transition-transform duration-200 ${showValidationCriteria ? 'rotate-90' : ''}`} 
              />
            </button>
          </div>
          
          {/* Collapsed content */}
          {showValidationCriteria && (
            <div className="p-4 bg-blue-50">
              <div className="space-y-3">
                {effectiveValidationCriteria.map((criteria, index) => (
                  <div key={index} className="p-3 bg-white rounded-md border border-blue-200">
                    <p className="font-medium text-gray-800 mb-1">{criteria.question}</p>
                    <p className="text-gray-600 pl-3">{criteria.answer}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Generated Scope */}
      <div className="border rounded-lg p-4 mb-6 bg-gray-50">
        <h4 className="font-medium text-gray-700 mb-2">Generated Scope:</h4>
        <pre className="whitespace-pre-wrap">{scopeText}</pre>
      </div>
      
      {/* Changes Made */}
      {changes && changes.length > 0 && (
        <div className="border rounded-lg p-4 mb-6 bg-yellow-50">
          <h4 className="font-medium text-yellow-800 mb-3">Changes Made:</h4>
          <ul className="list-disc pl-5 space-y-2">
            {changes.map((change, index) => (
              <li key={index} className="text-gray-700">{change}</li>
            ))}
          </ul>
        </div>
      )}
      
      {/* Approval Buttons - only show if task is not already approved */}
      {!isTaskApproved && !isLocallyApproved && (
        <>
          <div className="flex gap-4 mb-6">
            {!showFeedbackForm && (
              <button
                onClick={() => handleValidation(true, null)}
                className="flex-1 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                disabled={isLoading}
              >
                Approve
              </button>
            )}
            
            <button
              onClick={() => onSetFeedback('')}
              className={`${!showFeedbackForm ? 'flex-1' : 'w-full'} py-3 text-white rounded-lg transition-colors 
                ${showFeedbackForm 
                  ? 'bg-red-700 ring-2 ring-red-400' 
                  : 'bg-red-600 hover:bg-red-700'}`}
              disabled={isLoading}
            >
              Request Changes
            </button>
          </div>
          
          {/* Feedback Form - Only show after Request Changes is clicked */}
          {showFeedbackForm && (
            <div>
              <h4 className="text-lg font-medium mb-3">What aspects need changes?</h4>
              <textarea
                className="w-full p-3 border rounded-md mb-4"
                rows="3"
                placeholder="Please describe what needs to be changed (e.g., 'The what section needs more clarity', 'The timeline is incorrect')..."
                value={feedback}
                onChange={(e) => onSetFeedback(e.target.value)}
                disabled={isLoading}
              />
              <div className="flex justify-end">
                <button
                  onClick={handleSubmitFeedback}
                  disabled={!feedback?.trim() || isLoading}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-60"
                >
                  <span className="flex items-center gap-2">
                    {isLoading ? (
                      <RefreshCcw className="w-5 h-5 animate-spin" />
                    ) : (
                      <FileText className="w-5 h-5" />
                    )}
                    Submit Feedback
                  </span>
                </button>
              </div>
            </div>
          )}
        </>
      )}
      
      {/* Show approved message when task is already approved */}
      {(isTaskApproved || isLocallyApproved) && (
        <div className="p-3 bg-green-50 text-green-700 rounded-md flex items-start mb-4">
          <Check className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
          <p>This task scope has been approved.</p>
        </div>
      )}
    </div>
  );
} 