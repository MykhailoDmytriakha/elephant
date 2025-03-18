import React, { useEffect, useCallback, useState } from 'react';
import { CollapsibleSection } from './TaskComponents';
import { RefreshCcw, FileText, Check, ArrowRight, AlertCircle } from 'lucide-react';
import { getFormulationQuestions, submitFormulationAnswers, getDraftScope, validateScope } from '../../utils/api';
import ScopeValidation from './scope/ScopeValidation';
import FinalScopeScreen from './scope/FinalScopeScreen';
import ScopeQuestionsSection from './scope/ScopeQuestionsSection';
import ScopeProgress from './scope/ScopeProgress';
import useTaskScopeState from '../../hooks/useTaskScopeState';
import { formatGroupName, findNextUnansweredGroup as findNext } from '../../utils/scopeUtils';

export default function TaskScope({
    task,
    isContextGathered,
    defaultOpen = true
}) {
    // Use our custom hook to manage all state
    const {
        // State variables
        flowState,
        currentGroup,
        currentQuestions,
        draftScope,
        isLoading,
        isSubmitting,
        feedback,
        errorMessage,
        completedGroups,
        changes,
        isLocallyApproved,
        isTaskApproved,
        GROUPS,
        
        // State setters
        setFlowState,
        setCurrentGroup,
        setCurrentQuestions,
        setDraftScope,
        setIsLoading,
        setIsSubmitting,
        setFeedback,
        setErrorMessage,
        setCompletedGroups,
        setChanges,
        setIsLocallyApproved
    } = useTaskScopeState(task);

    // Track which group is selected in the progress view
    const [selectedGroup, setSelectedGroup] = useState(null);

    // Reset selected group when task changes
    useEffect(() => {
        // Reset state when task changes
        setSelectedGroup(null);
    }, [task?.id]);

    // Helper function to check if the task has a valid scope
    const hasValidScope = useCallback(() => {
        
        // If no scope at all, it's not valid
        if (!task?.scope) {
            return false;
        }
        
        // If scope is an object, check if it has a completely filled structure
        if (typeof task.scope === 'object') {
            // If at least one group is not completed, scope is not final
            const hasCompleteGroups = GROUPS.every(group => {
                const groupData = task.scope[group];
                const isComplete = groupData && 
                    ((Array.isArray(groupData) && groupData.length > 0) || 
                     (typeof groupData === 'object' && Object.keys(groupData).length > 0));
                
                return isComplete;
            });
            
            // Only return true if ALL groups are complete
            return hasCompleteGroups;
        }
        
        return false;
    }, [task, GROUPS]);

    // Helper function to determine completed groups from task scope
    const determineCompletedGroups = useCallback(() => {
        
        // Check if scope is an object
        if (task?.scope && typeof task.scope === 'object') {
            const completed = [];
            
            // For each group, check if it exists as a key in the scope object and has content
            GROUPS.forEach(group => {
                if (task.scope[group] && 
                    ((Array.isArray(task.scope[group]) && task.scope[group].length > 0) || 
                     (typeof task.scope[group]) === 'object' && Object.keys(task.scope[group]).length > 0)) {
                    completed.push(group);
                }
            });
            
            return completed;
        }
        
        // Return empty array if no completed groups found
        return [];
    }, [task, GROUPS]);

    // Reset flow state and completed groups when task changes
    useEffect(() => {
        // Log the scope status for debugging
        const scopeStatus = task?.scope?.status?.toLowerCase() || 'none';
        console.log(`Task scope status: ${scopeStatus}`);
        
        if (hasValidScope()) {
            // Determine which screen to show based on scope status
            if (scopeStatus === 'draft') {
                // Show ValidationScreen only for draft status
                console.log('Setting flow state to validation based on draft status');
                setFlowState('validation');
            } else if (scopeStatus === 'approved') {
                // Show FinalScopeScreen for approved status 
                console.log('Setting flow state to final based on approved status');
                setFlowState('final');
            } else {
                // Default to final if status is missing but scope exists
                console.log('Setting flow state to final (default for valid scope)');
                setFlowState('final');
            }
        } else {
            // If scope is empty, there are no completedGroups
            if (!task?.scope) {
                setCompletedGroups([]);
                setFlowState('initial');
                return;
            }
            
            // Determine completed groups from task scope
            const completed = determineCompletedGroups();
            setCompletedGroups(completed);
            setFlowState('initial');
        }
        
        // Reset changes array when task changes
        setChanges([]);
    }, [task, hasValidScope, determineCompletedGroups]);

    // Effects to ensure consistency between flowState and scope validity
    useEffect(() => {
        // If we're in final state but have no valid scope, go back to initial
        if (flowState === 'final' && !hasValidScope()) {
            setFlowState('initial');
        }
    }, [flowState, task, hasValidScope]);

    // Update draftScope whenever task scope changes and we're in final state
    useEffect(() => {
        if ((flowState === 'final' || flowState === 'validation') && task?.scope) {
            if (typeof task.scope === 'string') {
                setDraftScope(task.scope);
            } else if (task.scope.scope && typeof task.scope.scope === 'string') {
                // Set draftScope as an object with both scope and validation_criteria
                setDraftScope({
                    scope: task.scope.scope,
                    validation_criteria: task.scope.validation_criteria || []
                });
            }
        }
    }, [task?.scope, flowState]);

    // Automatically generate draft when all groups are completed
    useEffect(() => {
        // If all groups are completed and we're in initial state, automatically generate the draft
        if (completedGroups.length === GROUPS.length && flowState === 'initial' && !isLoading) {
            handleGenerateDraft();
        }
    }, [completedGroups, GROUPS, flowState, isLoading]);

    // Handler for generating draft scope
    const handleGenerateDraft = async () => {
        setFlowState('draftLoading');
        setIsLoading(true);
        setChanges([]); // Clear any existing changes
        try {
            const draftData = await getDraftScope(task.id);
            setDraftScope(draftData);
            setFlowState('validation');
        } catch (error) {
            console.error('Error getting draft scope:', error);
            setErrorMessage('Failed to generate scope. Please try again.');
            setFlowState('initial');
        } finally {
            setIsLoading(false);
        }
    };

    if (!isContextGathered) {
        return null;
    }

    // Helper function to find the next unanswered group
    const findNextUnansweredGroup = () => {
        return findNext(GROUPS, completedGroups);
    };

    // Handler for starting formulation for the selected group
    const startFormulation = async () => {
        // If a group is selected in the progress view, use that
        // Otherwise find the next unanswered group as before
        const groupToStart = selectedGroup || findNextUnansweredGroup() || GROUPS[0];
        
        setIsLoading(true);
        setErrorMessage('');
        try {
            let questions;
            try {
                questions = await getFormulationQuestions(task.id, groupToStart);
                setCurrentGroup(groupToStart);
            } catch (initialError) {
                console.error('Error getting questions:', initialError);
                throw initialError;
            }
            
            if (!questions || !Array.isArray(questions) || questions.length === 0) {
                throw new Error('Invalid response format from server');
            }
            
            // Format the questions based on the new response structure
            const formattedQuestions = questions.map((questionData, index) => ({
                id: `${questionData.group}_question_${index}`,
                question: questionData.question,
                options: questionData.options || []
            }));
            
            setCurrentQuestions(formattedQuestions);
            setSelectedGroup(null); // Reset selected group after starting
            setFlowState('questions');
        } catch (error) {
            console.error('Error starting formulation:', error);
            setErrorMessage(`Failed to start formulation process: ${error.message || 'Please try again.'}`);
        } finally {
            setIsLoading(false);
        }
    };

    // Handler for group selection from ScopeProgress
    const handleSelectedGroupChange = (group) => {
        setSelectedGroup(group);
    };

    const submitAnswers = async (formattedAnswers) => {
        setIsSubmitting(true);
        setErrorMessage('');
        try {
            await submitFormulationAnswers(task.id, currentGroup, formattedAnswers);
            
            // Add current group to completed groups
            setCompletedGroups(prev => {
                if (!prev.includes(currentGroup)) {
                    return [...prev, currentGroup];
                }
                return prev;
            });
            
            // Check if this was the last group
            const updatedCompletedGroups = completedGroups.includes(currentGroup) 
                ? completedGroups 
                : [...completedGroups, currentGroup];
            
            if (updatedCompletedGroups.length === GROUPS.length) {
                // All groups completed, automatically generate draft
                setFlowState('draftLoading');
                
                try {
                    const draftData = await getDraftScope(task.id);
                    setDraftScope(draftData);
                    setFlowState('validation');
                } catch (error) {
                    console.error('Error getting draft scope:', error);
                    setErrorMessage('Failed to generate scope. Please try again.');
                    setFlowState('initial');
                }
            } else {
                // Return to initial state where user can select next group
                setFlowState('initial');
                setCurrentGroup(null);
                setCurrentQuestions([]);
            }
            
        } catch (error) {
            console.error('Error submitting answers:', error);
            setErrorMessage('Failed to submit answers. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    const renderQuestionGroup = () => {
        return (
            <ScopeQuestionsSection
                currentGroup={currentGroup}
                currentQuestions={currentQuestions}
                submitAnswers={submitAnswers}
                isSubmitting={isSubmitting}
                progress={`Step ${GROUPS.indexOf(currentGroup) + 1} of ${GROUPS.length}`}
                GROUPS={GROUPS}
            />
        );
    };

    const renderValidation = () => {
        // Extract validation criteria from draftScope if available
        let validationCriteria = [];
        if (draftScope && typeof draftScope === 'object' && draftScope.validation_criteria) {
            validationCriteria = draftScope.validation_criteria;
        } else if (task?.scope?.validation_criteria) {
            validationCriteria = task.scope.validation_criteria;
        }
        
        return (
            <ScopeValidation
                task={task}
                draftScope={draftScope}
                validationCriteria={validationCriteria}
                changes={changes}
                isTaskApproved={isTaskApproved}
                isLocallyApproved={isLocallyApproved}
                feedback={feedback}
                isLoading={isLoading}
                errorMessage={errorMessage}
                onUpdateDraftScope={setDraftScope}
                onSetFeedback={setFeedback}
                onSetChanges={setChanges}
                onSetLocallyApproved={setIsLocallyApproved}
                onSetErrorMessage={setErrorMessage}
                onSetLoading={setIsLoading}
                onSetFlowState={setFlowState}
            />
        );
    };

    const renderFinalScope = () => {
        // Check if the task has been approved - combine server and local approval states
        const isApproved = isTaskApproved || isLocallyApproved;
                                
        return (
            <FinalScopeScreen
                task={task}
                draftScope={draftScope}
                completedGroups={completedGroups}
                groups={GROUPS}
                changes={changes}
                isTaskApproved={isApproved}
                onApprove={() => {
                    // No longer needed as we use the ScopeValidation component for validation
                    console.log('Final scope already approved');
                }}
                onRequestChanges={(isApproved, feedbackText) => {
                    // Move back to validation state if changes requested from final screen
                    setFeedback(feedbackText);
                    setFlowState('validation');
                }}
                onGenerateDraft={handleGenerateDraft}
                isLoading={isLoading}
                errorMessage={errorMessage}
                feedback={feedback}
                onFeedbackChange={setFeedback}
            />
        );
    };

    const renderDraftLoading = () => {
        return (
            <div className="bg-white p-6 rounded-lg border">
                <div className="text-center py-16">
                    <RefreshCcw className="w-12 h-12 animate-spin mx-auto mb-6 text-blue-600" />
                    <h3 className="text-xl font-semibold mb-2">Creating draft and validating it</h3>
                    <p className="text-gray-600">
                        We're compiling your answers into a comprehensive scope definition...
                    </p>
                </div>
            </div>
        );
    };

    const renderProgress = () => {
        return (
            <ScopeProgress 
                completedGroups={completedGroups}
                GROUPS={GROUPS}
                currentGroup={currentGroup}
                selectedGroup={selectedGroup}
                onSelectedGroupChange={handleSelectedGroupChange}
                onContinue={startFormulation}
                isLoading={isLoading}
            />
        );
    };

    const renderInitialState = () => {
        const allGroupsCompleted = completedGroups.length === GROUPS.length;
        
        return (
            <div className="bg-white p-6 rounded-lg border">
                {/* Always show progress */}
                {renderProgress()}
                
                {errorMessage && (
                    <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md flex items-start">
                        <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
                        <p>{typeof errorMessage === 'string' ? errorMessage : 'An error occurred'}</p>
                    </div>
                )}
                
                <div className="text-center py-4">
                    {allGroupsCompleted && !isLoading && (
                        <div className="text-center">
                            <div className="p-4 bg-blue-50 border border-blue-200 rounded-md mb-4">
                                <p className="text-blue-800 font-medium">
                                    You've answered all the required questions. Generating draft scope...
                                </p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        );
    };

    const renderContent = () => {
        // First check if we're in final state which should take precedence
        if (flowState === 'final') {
            return renderFinalScope();
        }
        
        // Then check other specific states
        switch (flowState) {
            case 'questions':
                return renderQuestionGroup();
            case 'validation':
                return renderValidation();
            case 'draftLoading':
                return renderDraftLoading();
            case 'initial':
            default:
                return renderInitialState();
        }
    };

    return (
        <CollapsibleSection 
            title={
                <div className="flex items-center">
                    <span>Define scope of the task</span>
                    {isTaskApproved && (
                        <span className="ml-2 text-xs bg-green-100 text-green-800 py-0.5 px-2 rounded-full">
                            Complete
                        </span>
                    )}
                </div>
            } 
            defaultOpen={defaultOpen}
        >
            <div className="space-y-4">
                {renderContent()}
            </div>
        </CollapsibleSection>
    );
}