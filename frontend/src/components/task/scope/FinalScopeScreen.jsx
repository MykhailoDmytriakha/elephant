import React, { useState } from 'react';
import { RefreshCcw, Check, ChevronRight, AlertCircle } from 'lucide-react';

export default function FinalScopeScreen({
  task,
  draftScope,
  groups = [],
  isTaskApproved = false,
  onGenerateDraft,
  isLoading = false,
  errorMessage = ''
}) {
  // State for showing/hiding validation criteria
  const [showCriteria, setShowCriteria] = useState(!isTaskApproved);
  
  // Get the validation criteria regardless of structure - prioritize draftScope first
  const validationCriteria = 
      (draftScope && typeof draftScope === 'object' && draftScope.validation_criteria) ? 
        draftScope.validation_criteria :
        task?.scope?.validation_criteria || 
        task?.scope?.scope?.validation_criteria || [];
  
  // Get the scope text regardless of structure - prioritize draftScope if it exists
  const getScopeText = () => {
    // First check if draftScope contains the most recent scope
    if (typeof draftScope === 'string' && draftScope.trim()) {
      return draftScope;
    } 
    // Check if draftScope is an object with scope property
    else if (draftScope && typeof draftScope === 'object') {
      if (draftScope.scope && typeof draftScope.scope === 'string') {
        return draftScope.scope;
      } else if (draftScope.updatedScope && typeof draftScope.updatedScope === 'string') {
        return draftScope.updatedScope;
      }
    }
    // Fall back to task.scope
    else if (task?.scope) {
      if (typeof task.scope === 'string') {
        return task.scope;
      } else if (task.scope.scope && typeof task.scope.scope === 'string') {
        return task.scope.scope;
      }
    }
    
    return '';
  };
  
  const scopeText = getScopeText();
  
  return (
    <div className="bg-white p-4 rounded-lg border">
      {/* Progress indicator and Generate Draft Scope button - Only show if no validation criteria */}
      {validationCriteria.length === 0 && (
        <div className="p-4 bg-gray-50 rounded-md mb-6">
          <h4 className="text-md font-medium mb-3">Task Definition Progress:</h4>
          
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md">
            <div className="flex items-center text-green-700 font-medium">
              <Check className="w-5 h-5 mr-2" />
              All stages completed and scope defined!
            </div>
          </div>
          
          <div className="flex flex-col gap-2">
            {groups.map(group => (
              <div key={group} className="flex items-center gap-2 p-2 rounded-md">
                <div className="flex items-center justify-center w-6 h-6 rounded-full bg-green-500 text-white">
                  <Check className="w-4 h-4" />
                </div>
                <span className="text-green-700 font-medium">
                  {group === 'what' ? 'What' :
                  group === 'why' ? 'Why' :
                  group === 'who' ? 'Who' :
                  group === 'where' ? 'Where' :
                  group === 'when' ? 'When' :
                  group === 'how' ? 'How' : group}
                </span>
                <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full ml-auto">
                  Completed
                </span>
              </div>
            ))}
          </div>
          
          {/* Add button to generate draft scope */}
          <div className="mt-4 flex justify-center">
            <button
              onClick={onGenerateDraft}
              disabled={isLoading}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-md hover:shadow-lg"
            >
              {isLoading ? (
                <>
                  <RefreshCcw className="w-5 h-5 animate-spin inline mr-2" />
                  Generating...
                </>
              ) : (
                <>
                  Generate Draft Scope
                </>
              )}
            </button>
          </div>
        </div>
      )}
      
      {/* Error/Success Message */}
      {errorMessage && (
        <div className={`mb-4 p-3 rounded-md flex items-start ${
          errorMessage.includes('approved') || errorMessage.includes('success')
            ? 'bg-green-50 text-green-700'
            : 'bg-red-50 text-red-700'
        }`}>
          {errorMessage.includes('approved') || errorMessage.includes('success')
            ? <Check className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
            : <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
          }
          <p>{typeof errorMessage === 'string' ? errorMessage : 'An error occurred'}</p>
        </div>
      )}
      
      {/* Display validation criteria if available - folded when task is approved */}
      {validationCriteria.length > 0 && (
        <div className="border rounded-lg mb-6 overflow-hidden">
          <div 
            className="bg-blue-50 p-4 flex justify-between items-center cursor-pointer"
            onClick={() => setShowCriteria(!showCriteria)}
          >
            <h4 className="font-medium text-blue-800">Validation Criteria</h4>
            <button className="p-1 hover:bg-blue-100 rounded-full">
              <ChevronRight 
                className={`w-5 h-5 text-blue-700 transform transition-transform duration-200 ${showCriteria ? 'rotate-90' : ''}`} 
              />
            </button>
          </div>
          
          {/* Collapsed content */}
          {showCriteria && (
            <div className="p-4 bg-blue-50">
              <div className="space-y-3">
                {validationCriteria.map((criteria, index) => (
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
      
      {/* Display scope text */}
      {scopeText ? (
        <div className="border rounded-lg p-4 mb-6 bg-gray-50">
          <h4 className="font-medium text-gray-700 mb-2">Generated Scope:</h4>
          <pre className="text-gray-900 whitespace-pre-wrap">{scopeText}</pre>
        </div>
      ) : typeof task.scope === 'string' ? (
        <pre className="text-gray-900 whitespace-pre-wrap">{task.scope}</pre>
      ) : (
        <div className="bg-gray-50 p-4 rounded-lg">
          <p className="text-sm text-gray-500 mb-2">Task scope has been defined with the following parameters:</p>
          <div className="space-y-4">
            {Object.entries(task.scope || {}).map(([group, items]) => {
              if (group !== 'what' && group !== 'why' && group !== 'who' && group !== 'where' && group !== 'when' && group !== 'how') return null;
              
              return (
                <div key={group} className="border-b pb-3">
                  <h5 className="font-medium text-gray-700 capitalize mb-2">{group} Questions</h5>
                  <div className="ml-4">
                    {Array.isArray(items) && items.map((item, index) => (
                      <div key={index} className="mb-3">
                        <p className="text-gray-800 font-medium">{item.question}</p>
                        <p className="text-gray-600 pl-4">Answer: {item.answer}</p>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
} 