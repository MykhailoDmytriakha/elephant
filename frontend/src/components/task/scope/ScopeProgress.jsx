import React from 'react';
import { Check, ArrowRight, FileText } from 'lucide-react';
import { formatGroupName } from '../../../utils/scopeUtils';

/**
 * Component for displaying the progress of scope definition
 * Shows which question groups have been completed and allows selecting the next group
 * @param {Array} completedGroups - Array of group IDs that have been completed
 * @param {Array} GROUPS - Array of all available group IDs 
 * @param {string} currentGroup - Currently active group ID
 * @param {string|null} selectedGroup - Currently selected group ID (controlled by parent)
 * @param {Function} onSelectedGroupChange - Callback when user selects a different group
 * @param {Function} onContinue - Callback when continue button is clicked
 * @param {boolean} isLoading - Whether the component is in a loading state
 */
export default function ScopeProgress({ 
    completedGroups = [], 
    GROUPS = [], 
    currentGroup,
    selectedGroup,
    onSelectedGroupChange,
    onContinue,
    isLoading = false
}) {
    // Validate inputs to prevent errors
    const safeGroups = Array.isArray(GROUPS) ? GROUPS : [];
    const safeCompletedGroups = Array.isArray(completedGroups) ? completedGroups : [];
    
    // Handle empty groups array
    if (safeGroups.length === 0) {
        return (
            <div className="p-4 bg-gray-50 rounded-md text-center">
                <p className="text-gray-500">No scope groups defined.</p>
            </div>
        );
    }
    
    const allGroupsCompleted = safeCompletedGroups.length === safeGroups.length && safeGroups.length > 0;
    const hasCompletedGroups = safeCompletedGroups.length > 0;
    const hasAvailableGroups = safeGroups.some(group => !safeCompletedGroups.includes(group));
    
    // Handle group selection
    const handleGroupSelect = (group) => {
        // Prevent selection when loading or already completed groups
        if (isLoading || safeCompletedGroups.includes(group)) {
            return;
        }
        
        if (onSelectedGroupChange) {
            onSelectedGroupChange(group === selectedGroup ? null : group);
        }
    };
    
    // Get the appropriate button content
    const getButtonContent = () => {
        if (selectedGroup) {
            return (
                <>
                    <ArrowRight className="w-5 h-5" />
                    Continue with {formatGroupName(selectedGroup)}
                </>
            );
        } 
        
        if (hasCompletedGroups) {
            return (
                <>
                    <ArrowRight className="w-5 h-5" />
                    Continue scope definition
                </>
            );
        }
        
        return (
            <>
                <FileText className="w-5 h-5" />
                Start defining the scope
            </>
        );
    };
    
    return (
        <div className="p-4 bg-gray-50 rounded-md mb-6" role="region" aria-label="Task scope progress">
            {allGroupsCompleted && (
                <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md">
                    <div className="flex items-center text-green-700 font-medium">
                        <Check className="w-5 h-5 mr-2" />
                        All stages completed! You can now generate the task scope.
                    </div>
                </div>
            )}
            
            <div className="flex flex-col gap-2">
                {safeGroups.map(group => {
                    const isCompleted = safeCompletedGroups.includes(group);
                    const isActive = currentGroup === group;
                    const isSelected = selectedGroup === group;
                    const isAvailable = !isCompleted && !isLoading;
                    
                    return (
                        <div key={group} 
                            onClick={() => handleGroupSelect(group)}
                            className={`flex items-center gap-2 p-2 rounded-md 
                                ${isCompleted ? 'bg-green-50' : 
                                  isSelected ? 'bg-blue-100 border-2 border-blue-400' : 
                                  isAvailable ? 'bg-blue-50 border border-blue-200 cursor-pointer hover:bg-blue-100' : 
                                  isLoading ? 'bg-blue-50 border border-blue-200 opacity-70' : ''}
                            `}
                            aria-current={isActive ? 'step' : undefined}
                            role={isAvailable ? 'button' : undefined}
                            tabIndex={isAvailable ? 0 : undefined}
                            aria-disabled={isLoading}
                        >
                            <div className={`flex items-center justify-center w-6 h-6 rounded-full 
                                ${isCompleted ? 'bg-green-500 text-white' : 
                                  isSelected ? 'bg-blue-600 text-white' :
                                  isAvailable ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-500'}`}>
                                {isCompleted ? (
                                    <Check className="w-4 h-4" aria-hidden="true" />
                                ) : (
                                    <span className="text-xs font-bold">{safeGroups.indexOf(group) + 1}</span>
                                )}
                            </div>
                            <span className={`
                                ${isCompleted ? 'text-green-700 font-medium' : 
                                  isSelected ? 'text-blue-800 font-medium' :
                                  isAvailable ? 'text-blue-700 font-medium' : 'text-gray-500'}`}>
                                {formatGroupName(group)}
                            </span>
                            {isCompleted && (
                                <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full ml-auto">
                                    Completed
                                </span>
                            )}
                            {isActive && !isCompleted && (
                                <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full ml-auto">
                                    In Progress
                                </span>
                            )}
                            {isSelected && !isActive && !isCompleted && (
                                <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full ml-auto">
                                    Selected
                                </span>
                            )}
                            {!isSelected && !isActive && isAvailable && (
                                <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full ml-auto">
                                    Available
                                </span>
                            )}
                        </div>
                    );
                })}
            </div>
            
            {/* For showing active progress */}
            {currentGroup && !allGroupsCompleted && (
                <div className="mt-4 text-sm text-gray-500">
                    Current step: {safeGroups.indexOf(currentGroup) + 1} of {safeGroups.length}
                </div>
            )}
            
            {/* Continue button */}
            {!allGroupsCompleted && hasAvailableGroups && (
                <div className="text-center mt-6">
                    <button
                        onClick={onContinue}
                        disabled={isLoading}
                        className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-300 w-full md:w-auto justify-center"
                    >
                        {isLoading ? (
                            <div className="flex items-center gap-2">
                                <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                                Loading...
                            </div>
                        ) : (
                            getButtonContent()
                        )}
                    </button>
                </div>
            )}
            
            {/* Add back the guidance message that appears after completion */}
            {allGroupsCompleted && (
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                    <p className="text-blue-700">
                        <span className="font-medium">Next step:</span> The system will automatically generate a comprehensive scope definition based on your answers.
                    </p>
                </div>
            )}
        </div>
    );
} 