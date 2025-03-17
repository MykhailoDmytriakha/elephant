import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { CollapsibleSection } from './TaskComponents';
import { RefreshCcw, FileText, Check, ChevronRight, ArrowRight, AlertCircle } from 'lucide-react';
import { getFormulationQuestions, submitFormulationAnswers, getDraftScope, validateScope } from '../../utils/api';

export default function TaskFormulation({
    task,
    isContextGathered,
    onFormulate,
    isFormulating
}) {
    console.log('TaskFormulation received task:', task);
    console.log('TaskFormulation task.status:', task?.status);
    console.log('TaskFormulation task.status type:', typeof task?.status);
    console.log('TaskFormulation task.status === "approved":', task?.status === "approved");
    
    // Check if the task has been approved - use multiple possible locations
    const isTaskApproved = 
        String(task?.status).toLowerCase() === "approved" || 
        String(task?.scope?.status).toLowerCase() === "approved" ||
        (typeof task?.scope === 'object' && String(task?.scope?.scope?.status).toLowerCase() === "approved");
    
    const [flowState, setFlowState] = useState('initial'); // initial, questions, validation, final, draftLoading
    const [currentGroup, setCurrentGroup] = useState(null);
    const [currentQuestions, setCurrentQuestions] = useState([]);
    const [answers, setAnswers] = useState({});
    const [draftScope, setDraftScope] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false); // For tracking submission state specifically
    const [feedback, setFeedback] = useState(null); // null if no changes requested, string otherwise
    const [errorMessage, setErrorMessage] = useState('');
    const [completedGroups, setCompletedGroups] = useState([]); // Track which groups have been completed
    const [changes, setChanges] = useState([]); // Store the changes array from validation response
    
    // Separate state variables for showing validation criteria in different views
    const [showFinalCriteria, setShowFinalCriteria] = useState(!isTaskApproved); // Expanded by default if not approved
    const [showValidationCriteria, setShowValidationCriteria] = useState(true); // Always expanded in validation view
    
    // Define our 6 fixed groups - wrapped in useMemo to keep it stable
    const GROUPS = useMemo(() => ['what', 'why', 'who', 'where', 'when', 'how'], []);

    // Helper function to check if the task has a valid scope
    const hasValidScope = useCallback(() => {
        console.log('Checking if task has valid scope:', task?.scope);
        
        // If no scope at all, it's not valid
        if (!task?.scope) {
            return false;
        }
        
        // If scope is a string, it's the final processed scope and is valid
        if (typeof task.scope === 'string' && task.scope.trim()) {
            console.log('Task has a string scope, considered valid');
            return true;
        }
        
        // If scope is an object, check if it has a completely filled structure
        if (typeof task.scope === 'object') {
            // If at least one group is not completed, scope is not final
            const hasCompleteGroups = GROUPS.every(group => {
                const groupData = task.scope[group];
                const isComplete = groupData && 
                    ((Array.isArray(groupData) && groupData.length > 0) || 
                     (typeof groupData === 'object' && Object.keys(groupData).length > 0));
                
                console.log(`Group ${group} completion status:`, isComplete);
                return isComplete;
            });
            
            console.log('Are all groups complete?', hasCompleteGroups);
            
            // Only return true if ALL groups are complete
            return hasCompleteGroups;
        }
        
        return false;
    }, [task, GROUPS]);

    // Helper function to determine completed groups from task scope
    const determineCompletedGroups = useCallback(() => {
        console.log('Determining completed groups from scope:', task?.scope);
        
        // Check if scope is an object
        if (task?.scope && typeof task.scope === 'object') {
            const completed = [];
            
            // For each group, check if it exists as a key in the scope object and has content
            GROUPS.forEach(group => {
                if (task.scope[group] && 
                    ((Array.isArray(task.scope[group]) && task.scope[group].length > 0) || 
                     (typeof task.scope[group] === 'object' && Object.keys(task.scope[group]).length > 0))) {
                    console.log(`Group ${group} is completed:`, task.scope[group]);
                    completed.push(group);
                } else {
                    console.log(`Group ${group} is not completed:`, task.scope[group]);
                }
            });
            
            console.log('Completed groups determined from scope:', completed);
            return completed;
        }
        
        // Return empty array if no completed groups found
        console.log('No completed groups found from scope');
        return [];
    }, [task, GROUPS]);

    // Reset flow state and completed groups when task changes
    useEffect(() => {
        console.log('Task changed, evaluating scope state:', task?.scope);
        
        if (hasValidScope()) {
            console.log('Task has valid scope, setting final state');
            setFlowState('final');
        } else {
            // If scope is empty, there are no completedGroups
            if (!task?.scope) {
                console.log('Task has no scope, setting empty completedGroups');
                setCompletedGroups([]);
                setFlowState('initial');
                return;
            }
            
            // Determine completed groups from task scope
            const completed = determineCompletedGroups();
            console.log('Setting completed groups:', completed);
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
        if (flowState === 'final' && task?.scope) {
            if (typeof task.scope === 'string') {
                setDraftScope(task.scope);
            } else if (task.scope.scope && typeof task.scope.scope === 'string') {
                setDraftScope(task.scope.scope);
            }
        }
    }, [task?.scope, flowState]);

    if (!isContextGathered) {
        return null;
    }

    // Helper function to find the next unanswered group
    const findNextUnansweredGroup = () => {
        for (const group of GROUPS) {
            if (!completedGroups.includes(group)) {
                return group;
            }
        }
        return null; // All groups are completed
    };

    const startFormulation = async () => {
        setIsLoading(true);
        setErrorMessage('');
        try {
            // Start with the first group ('what') or the next unanswered group
            const nextGroup = findNextUnansweredGroup() || GROUPS[0];
            
            console.log('Starting formulation with group:', nextGroup);
            console.log('Task ID:', task.id);
            console.log('Current completed groups:', completedGroups);
            
            let questions;
            try {
                questions = await getFormulationQuestions(task.id, nextGroup);
                setCurrentGroup(nextGroup);
            } catch (initialError) {
                console.error('Error getting questions:', initialError);
                throw initialError;
            }
            
            console.log('Questions response:', questions);
            
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
            
            // Initialize empty answers object
            setAnswers({});
            
            setFlowState('questions');
        } catch (error) {
            console.error('Error starting formulation:', error);
            setErrorMessage(`Failed to start formulation process: ${error.message || 'Please try again.'}`);
        } finally {
            setIsLoading(false);
        }
    };

    const handleAnswerChange = (questionId, value, isMultiSelect = false) => {
        setAnswers(prev => {
            if (isMultiSelect) {
                // For multi-select, toggle the value in an array
                const currentValues = Array.isArray(prev[questionId]) ? prev[questionId] : [];
                
                if (currentValues.includes(value)) {
                    // Remove if already selected
                    return {
                        ...prev,
                        [questionId]: currentValues.filter(v => v !== value)
                    };
                } else {
                    // Add if not selected
                    return {
                        ...prev,
                        [questionId]: [...currentValues, value]
                    };
                }
            } else {
                // For single custom value or prefilled
                // Special handling for custom text values - preserve the array structure
                // and store the custom text separately
                if (prev[`${questionId}_custom_text`] !== undefined || hasCustomAnswer(questionId)) {
                    return {
                        ...prev,
                        [`${questionId}_custom_text`]: value
                    };
                } else {
                    return {
                        ...prev,
                        [questionId]: value
                    };
                }
            }
        });
    };

    const isOptionSelected = (questionId, option) => {
        const answer = answers[questionId];
        if (Array.isArray(answer)) {
            return answer.includes(option);
        }
        return false;
    };

    const hasCustomAnswer = (questionId) => {
        const answer = answers[questionId];
        if (Array.isArray(answer)) {
            return answer.includes('__custom__');
        }
        return false;
    };

    const getCustomAnswer = (questionId) => {
        // Get the custom text from the separate storage field
        const customText = answers[`${questionId}_custom_text`];
        if (customText !== undefined) {
            return customText;
        }
        
        // Fallback for backward compatibility
        const answer = answers[questionId];
        if (!Array.isArray(answer) && answer && typeof answer === 'string') {
            return answer;
        }
        return '';
    };

    const validateAnswers = () => {
        // Check if all questions in the current group have been answered
        const unansweredQuestions = currentQuestions.filter(
            question => !answers[question.id] || 
                       (Array.isArray(answers[question.id]) && answers[question.id].length === 0) ||
                       (Array.isArray(answers[question.id]) && 
                       answers[question.id].includes('__custom__') && 
                       !getCustomAnswer(question.id))
        );
        
        if (unansweredQuestions.length > 0) {
            const missingItems = unansweredQuestions.map(q => `• ${q.question}`).join('\n');
            setErrorMessage(`Please answer all questions before proceeding. Missing:\n${missingItems}`);
            return false;
        }
        
        setErrorMessage('');
        return true;
    };

    const submitAnswers = async () => {
        // Validate answers before submission
        if (!validateAnswers()) {
            return;
        }
        
        setIsSubmitting(true);
        setErrorMessage('');
        try {
            // Process answers to format them for the API as a list of UserAnswer objects
            const answersList = [];
            
            // First, create a map of question IDs to their full text for easy lookup
            const questionTextMap = {};
            currentQuestions.forEach(question => {
                questionTextMap[question.id] = question.question;
            });
            
            // Group answers by question ID first
            const groupedAnswers = {};
            
            Object.keys(answers).forEach(answerId => {
                // Skip any custom_text entries, they're handled separately
                if (answerId.endsWith('_custom_text')) {
                    return;
                }
                
                const answer = answers[answerId];
                // Only process if there's an actual answer
                if (!answer || (Array.isArray(answer) && answer.length === 0)) {
                    return;
                }
                
                // Get the full question text for this answer
                const questionText = questionTextMap[answerId] || answerId;
                
                // Initialize array for this question if not exists
                if (!groupedAnswers[questionText]) {
                    groupedAnswers[questionText] = [];
                }
                
                // Add all selected options to the array
                if (Array.isArray(answer)) {
                    // Add regular selections
                    answer.forEach(option => {
                        if (option !== '__custom__') {
                            groupedAnswers[questionText].push(option);
                        } else {
                            // If "Other" is selected, add the custom text
                            const customText = answers[`${answerId}_custom_text`];
                            if (customText) {
                                groupedAnswers[questionText].push(customText);
                            }
                        }
                    });
                } else if (typeof answer === 'string') {
                    // Handle non-array answers
                    groupedAnswers[questionText].push(answer);
                }
            });
            
            // Convert grouped answers to the final format
            Object.keys(groupedAnswers).forEach(questionText => {
                answersList.push({
                    question: questionText,
                    answer: groupedAnswers[questionText].join(', ')
                });
            });
            
            // Format the data to match the expected UserAnswers model
            const userAnswers = {
                answers: answersList
            };
            
            console.log('Submitting answers:', JSON.stringify(userAnswers));
            await submitFormulationAnswers(task.id, currentGroup, userAnswers);
            
            // Add current group to completed groups
            setCompletedGroups(prev => {
                if (!prev.includes(currentGroup)) {
                    return [...prev, currentGroup];
                }
                return prev;
            });
            
            // Find the index of the current group and determine if there's a next group
            const currentIndex = GROUPS.indexOf(currentGroup);
            
            if (currentIndex < GROUPS.length - 1) {
                // Load next group in sequence
                const nextGroup = GROUPS[currentIndex + 1];
                const questions = await getFormulationQuestions(task.id, nextGroup);
                setCurrentGroup(nextGroup);
                
                // Ensure questions are properly formatted and create questions
                if (Array.isArray(questions)) {
                    const formattedQuestions = questions.map((questionData, index) => ({
                        id: `${questionData.group}_question_${index}`,
                        question: questionData.question,
                        options: questionData.options || []
                    }));
                    
                    setCurrentQuestions(formattedQuestions);
                    
                    // Initialize empty answers for the new questions
                    setAnswers({});
                } else {
                    console.error('Invalid questions format for next group:', questions);
                    setErrorMessage('Error loading next question group. Please try again.');
                }
            } else {
                // All questions answered, show loading state
                setFlowState('draftLoading');
                
                // After a delay, fetch the draft scope and transition to validation
                try {
                    setChanges([]); // Clear any existing changes
                    const draftData = await getDraftScope(task.id);
                    setDraftScope(draftData);
                    setFlowState('validation');
                } catch (error) {
                    console.error('Error getting draft scope:', error);
                    setErrorMessage('Failed to generate scope. Please try again.');
                    setFlowState('initial');
                } finally {
                    setIsLoading(false);
                    setIsSubmitting(false);
                }
                
                return; // Don't reset isSubmitting yet, as we're still processing
            }
        } catch (error) {
            console.error('Error submitting answers:', error);
            setErrorMessage('Failed to submit answers. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleValidation = async (isApproved) => {
        setIsLoading(true);
        setErrorMessage('');
        try {
            const response = await validateScope(task.id, isApproved, feedback);
            console.log('Validation response:', JSON.stringify(response, null, 2));
            if (isApproved) {
                try {
                    // Store changes if present in the response
                    if (response && response.changes && Array.isArray(response.changes)) {
                        setChanges(response.changes);
                    }
                    
                    // If there's an updated scope in the approval response, use it
                    if (response && response.updatedScope) {
                        setDraftScope(response.updatedScope);
                        console.log('Updated draft scope on approval with:', response.updatedScope);
                    }
                    
                    // Final scope approved
                    setFlowState('final');
                    
                    // Update parent component
                    if (typeof onFormulate === 'function') {
                        onFormulate(false);
                    }
                } catch (formError) {
                    console.error('Error in formulate_task:', formError);
                    // Still show final scope screen even if formulate_task fails
                    setFlowState('final');
                    setErrorMessage('Scope approved, but there was an issue finalizing the task. The scope is still saved.');
                }
            } else {
                // Display updated scope and stay on validation screen
                if (response && response.updatedScope) {
                    // Set the updated scope text as a string, not an object
                    setDraftScope(response.updatedScope);
                    console.log('Updated draft scope with:', response.updatedScope);
                    
                    // Clear feedback form and show the updated scope
                    setFeedback(null);
                    // Show a success message
                    setErrorMessage('Feedback submitted. Please review the updated scope.');
                    
                    // Store changes if present in the response
                    if (response.changes && Array.isArray(response.changes)) {
                        setChanges(response.changes);
                    } else {
                        setChanges([]);
                    }
                }
                // Always stay on validation screen, never go back to questions
            }
        } catch (error) {
            console.error('Error validating scope:', error);
            setErrorMessage('Failed to validate scope. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const getGroupTitle = () => {
        switch (currentGroup) {
            case 'what': return 'What Questions';
            case 'why': return 'Why Questions';
            case 'who': return 'Who Questions';
            case 'where': return 'Where Questions';
            case 'when': return 'When Questions';
            case 'how': return 'How Questions';
            default: return 'Task Questions';
        }
    };

    const getCurrentProgress = () => {
        const groupIndex = GROUPS.indexOf(currentGroup);
        return `Step ${groupIndex + 1} of ${GROUPS.length}`;
    };

    const renderQuestionGroup = () => {
        if (!currentQuestions || !currentQuestions.length) {
            return <div className="text-center py-4">Loading questions...</div>;
        }

        return (
            <div className="bg-white p-6 rounded-lg border">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold">{getGroupTitle()}</h3>
                    <span className="text-sm text-gray-500 font-medium px-3 py-1 bg-gray-100 rounded-full">
                        {getCurrentProgress()}
                    </span>
                </div>
                
                {errorMessage && (
                    <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md flex items-start">
                        <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
                        <p className="whitespace-pre-line">{typeof errorMessage === 'string' ? errorMessage : 'An error occurred'}</p>
                    </div>
                )}
                
                <div className="space-y-6">
                    {currentQuestions.map(question => (
                        <div key={question.id} className="border rounded-lg p-4">
                            <h4 className="font-medium mb-2">{question.question}</h4>
                            
                            <div className="space-y-2">
                                {/* Options */}
                                {question.options && question.options.map(option => (
                                    <div key={option} className="p-3 border rounded-md">
                                        <label className="flex items-center">
                                            <input 
                                                type="checkbox" 
                                                className="mr-3"
                                                checked={isOptionSelected(question.id, option)}
                                                onChange={() => handleAnswerChange(question.id, option, true)}
                                                disabled={isSubmitting}
                                            />
                                            <span>{option}</span>
                                        </label>
                                    </div>
                                ))}
                                
                                {/* Other (custom) option */}
                                <div className="p-3 border rounded-md">
                                    <label className="flex items-start">
                                        <input 
                                            type="checkbox" 
                                            className="mt-1 mr-3"
                                            checked={hasCustomAnswer(question.id)}
                                            onChange={() => handleAnswerChange(question.id, '__custom__', true)}
                                            disabled={isSubmitting}
                                        />
                                        <div className="w-full">
                                            <div className="font-medium">Other</div>
                                            {hasCustomAnswer(question.id) && (
                                                <div className="mt-2">
                                                    <textarea 
                                                        className="w-full p-2 border rounded-md" 
                                                        rows="2"
                                                        placeholder="Enter your custom response..."
                                                        value={getCustomAnswer(question.id)}
                                                        onChange={(e) => handleAnswerChange(question.id, e.target.value, false)}
                                                        disabled={isSubmitting}
                                                    />
                                                </div>
                                            )}
                                        </div>
                                    </label>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
                
                <div className="mt-6 flex justify-end">
                    <button
                        onClick={submitAnswers}
                        disabled={isLoading || isSubmitting}
                        className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-300"
                    >
                        {isLoading || isSubmitting ? (
                            <>
                                <RefreshCcw className="w-5 h-5 animate-spin" />
                                Processing...
                            </>
                        ) : (
                            <>
                                Next Group <ChevronRight className="w-5 h-5" />
                            </>
                        )}
                    </button>
                </div>
            </div>
        );
    };

    const renderValidation = () => {
        const showFeedbackForm = feedback !== null;
        
        // Check if the task has been approved - try multiple possible locations for status
        const isTaskApproved = 
            String(task?.status).toLowerCase() === "approved" || 
            String(task?.scope?.status).toLowerCase() === "approved" ||
            (typeof task?.scope === 'object' && String(task?.scope?.scope?.status).toLowerCase() === "approved");
        
        console.log('Rendering validation with draftScope:', draftScope, 'Type:', typeof draftScope);
        console.log('Task status in renderValidation:', task?.status);
        console.log('Scope status (if available):', task?.scope?.status);
        console.log('Is task approved (any source):', isTaskApproved);
        
        return (
            <div className="bg-white p-6 rounded-lg border">
                <h3 className="text-lg font-semibold mb-2">Scope Validation</h3>
                <p className="text-gray-600 mb-4">
                    Review the generated scope. Is this definition acceptable or do you need to make changes?
                </p>
                
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
                
                {/* Display validation criteria if available */}
                {draftScope && typeof draftScope === 'object' && draftScope.validation_criteria && (
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
                                    {draftScope.validation_criteria.map((criteria, index) => (
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
                
                <div className="border rounded-lg p-4 mb-6 bg-gray-50">
                    <h4 className="font-medium text-gray-700 mb-2">Generated Scope:</h4>
                    <pre className="whitespace-pre-wrap">{(() => {
                        // First check if draftScope is a simple string
                        if (typeof draftScope === 'string') {
                            return draftScope;
                        }
                        
                        // If it's an object, try to find the scope text
                        if (draftScope && typeof draftScope === 'object') {
                            // First check for a direct scope property
                            if (draftScope.scope && typeof draftScope.scope === 'string') {
                                return draftScope.scope;
                            }
                            
                            // If there's an updatedScope property (from API response)
                            if (draftScope.updatedScope && typeof draftScope.updatedScope === 'string') {
                                return draftScope.updatedScope;
                            }
                        }
                        
                        // Nothing found
                        return '';
                    })()}</pre>
                </div>
                
                {/* Show changes if they exist */}
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
                {!isTaskApproved && (
                    <>
                        <div className="flex gap-4 mb-6">
                            {!showFeedbackForm && (
                                <button
                                    onClick={() => handleValidation(true)}
                                    className="flex-1 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                                >
                                    Approve
                                </button>
                            )}
                            
                            <button
                                onClick={() => setFeedback('')}
                                className={`${!showFeedbackForm ? 'flex-1' : 'w-full'} py-3 text-white rounded-lg transition-colors 
                                    ${showFeedbackForm 
                                        ? 'bg-red-700 ring-2 ring-red-400' 
                                        : 'bg-red-600 hover:bg-red-700'}`}
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
                                    onChange={(e) => setFeedback(e.target.value)}
                                    disabled={isLoading}
                                />
                                <div className="flex justify-end">
                                    <button
                                        onClick={() => handleValidation(false)}
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
                {isTaskApproved && (
                    <div className="p-3 bg-green-50 text-green-700 rounded-md flex items-start mb-4">
                        <Check className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
                        <p>This task scope has been approved.</p>
                    </div>
                )}
            </div>
        );
    };

    const renderFinalScope = () => {
        console.log('Rendering final scope with task scope:', task?.scope);
        console.log('Current draftScope value:', draftScope, 'Type:', typeof draftScope);
        console.log('Task status:', task?.status);
        console.log('Scope status (if available):', task?.scope?.status);
        
        // Check if the task has been approved - try multiple possible locations for status
        const isTaskApproved = 
            String(task?.status).toLowerCase() === "approved" || 
            String(task?.scope?.status).toLowerCase() === "approved" ||
            (typeof task?.scope === 'object' && String(task?.scope?.scope?.status).toLowerCase() === "approved");
        
        console.log('Is task approved (any source):', isTaskApproved);
        
        // Check if the outer scope has a 'scope' object with a nested structure
        // or if it's a new format where validation_criteria appears at the top level
        const hasValidationCriteria = Array.isArray(task?.scope?.validation_criteria) || 
                                    Array.isArray(task?.scope?.scope?.validation_criteria);
        
        // Get the validation criteria regardless of structure
        const validationCriteria = task?.scope?.validation_criteria || 
                                  task?.scope?.scope?.validation_criteria || [];
        
        // Get the scope text regardless of structure - prioritize draftScope if it exists
        let scopeText = '';
        
        // First check if draftScope contains the most recent scope
        if (typeof draftScope === 'string' && draftScope.trim()) {
            scopeText = draftScope;
        } 
        // Check if draftScope is an object with scope property
        else if (draftScope && typeof draftScope === 'object') {
            if (draftScope.scope && typeof draftScope.scope === 'string') {
                scopeText = draftScope.scope;
            } else if (draftScope.updatedScope && typeof draftScope.updatedScope === 'string') {
                scopeText = draftScope.updatedScope;
            }
        }
        // Fall back to task.scope
        else if (task?.scope) {
            if (typeof task.scope === 'string') {
                scopeText = task.scope;
            } else if (task.scope.scope && typeof task.scope.scope === 'string') {
                scopeText = task.scope.scope;
            }
        }
        
        console.log('Has validation criteria:', hasValidationCriteria);
        console.log('Final resolved scopeText:', scopeText ? 'Found text' : 'No text found');
        
        const showFeedbackForm = feedback !== null;
        
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
                            {GROUPS.map(group => (
                                <div key={group} className="flex items-center gap-2 p-2 rounded-md">
                                    <div className="flex items-center justify-center w-6 h-6 rounded-full bg-green-500 text-white">
                                        <Check className="w-4 h-4" />
                                    </div>
                                    <span className="text-green-700 font-medium">
                                        {group === 'what' ? 'What (Что)' :
                                        group === 'why' ? 'Why (Почему)' :
                                        group === 'who' ? 'Who (Кто)' :
                                        group === 'where' ? 'Where (Где)' :
                                        group === 'when' ? 'When (Когда)' :
                                        group === 'how' ? 'How (Как)' : group}
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
                                onClick={async () => {
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
                                }}
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
                            onClick={() => setShowFinalCriteria(!showFinalCriteria)}
                        >
                            <h4 className="font-medium text-blue-800">Validation Criteria</h4>
                            <button className="p-1 hover:bg-blue-100 rounded-full">
                                <ChevronRight 
                                    className={`w-5 h-5 text-blue-700 transform transition-transform duration-200 ${showFinalCriteria ? 'rotate-90' : ''}`} 
                                />
                            </button>
                        </div>
                        
                        {/* Collapsed content */}
                        {showFinalCriteria && (
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
                
                {/* Always display the scope text if available */}
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
                            {Object.entries(task.scope).map(([group, items]) => {
                                // Skip the 'scope' property if it exists (to avoid showing the nested structure twice)
                                if (group === 'scope') return null;
                                
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
                
                {/* Show changes if they exist */}
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
                {!isTaskApproved && (
                    <>
                        <div className="flex gap-4 mb-6">
                            {!showFeedbackForm && (
                                <button
                                    onClick={() => handleValidation(true)}
                                    className="flex-1 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                                >
                                    Approve
                                </button>
                            )}
                            
                            <button
                                onClick={() => setFeedback('')}
                                className={`${!showFeedbackForm ? 'flex-1' : 'w-full'} py-3 text-white rounded-lg transition-colors 
                                    ${showFeedbackForm 
                                        ? 'bg-red-700 ring-2 ring-red-400' 
                                        : 'bg-red-600 hover:bg-red-700'}`}
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
                                    onChange={(e) => setFeedback(e.target.value)}
                                    disabled={isLoading}
                                />
                                <div className="flex justify-end">
                                    <button
                                        onClick={() => handleValidation(false)}
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
                {isTaskApproved && (
                    <div className="p-3 bg-green-50 text-green-700 rounded-md flex items-start mb-4">
                        <Check className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
                        <p>This task scope has been approved.</p>
                    </div>
                )}
            </div>
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
        console.log('Rendering progress with completedGroups:', completedGroups);
        const allGroupsCompleted = completedGroups.length === GROUPS.length;
        
        return (
            <div className="p-4 bg-gray-50 rounded-md mb-6">
                {/* <h4 className="text-md font-medium mb-3">Формулировка задачи - прогресс:</h4> */}
                
                {allGroupsCompleted && (
                    <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md">
                        <div className="flex items-center text-green-700 font-medium">
                            <Check className="w-5 h-5 mr-2" />
                            All stages completed! You can now generate the task scope.
                        </div>
                    </div>
                )}
                
                <div className="flex flex-col gap-2">
                    {GROUPS.map(group => {
                        const isCompleted = completedGroups.includes(group);
                        const isNext = !isCompleted && completedGroups.length > 0 && 
                                      GROUPS.indexOf(group) === GROUPS.indexOf(completedGroups[completedGroups.length - 1]) + 1;
                        
                        return (
                            <div key={group} 
                                className={`flex items-center gap-2 p-2 rounded-md ${isNext ? 'bg-blue-50 border border-blue-200' : ''}`}>
                                <div className={`flex items-center justify-center w-6 h-6 rounded-full 
                                    ${isCompleted ? 'bg-green-500 text-white' : 
                                      isNext ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-500'}`}>
                                    {isCompleted ? (
                                        <Check className="w-4 h-4" />
                                    ) : (
                                        <span className="text-xs font-bold">{GROUPS.indexOf(group) + 1}</span>
                                    )}
                                </div>
                                <span className={`
                                    ${isCompleted ? 'text-green-700 font-medium' : 
                                      isNext ? 'text-blue-700 font-medium' : 'text-gray-500'}`}>
                                    {group === 'what' ? 'What' :
                                     group === 'why' ? 'Why' :
                                     group === 'who' ? 'Who' :
                                     group === 'where' ? 'Where' :
                                     group === 'when' ? 'When' :
                                     group === 'how' ? 'How' : group}
                                </span>
                                {isCompleted && (
                                    <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full ml-auto">
                                        Completed
                                    </span>
                                )}
                                {isNext && (
                                    <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full ml-auto">
                                        Next step
                                    </span>
                                )}
                            </div>
                        );
                    })}
                </div>
                
                {allGroupsCompleted && (
                    <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                        <p className="text-blue-700">
                            <span className="font-medium">Next step:</span> Click the "Generate Task Scope" button below to create a comprehensive scope definition based on your answers.
                        </p>
                    </div>
                )}
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
            case 'draftLoading':
                return renderDraftLoading();
            case 'validation':
                return renderValidation();
            case 'initial':
                // Check if there are any completed groups
                const hasCompletedGroups = completedGroups.length > 0;
                const allGroupsCompleted = completedGroups.length === GROUPS.length;
                const nextGroup = findNextUnansweredGroup();
                
                console.log('Initial state rendering with:', { 
                    hasCompletedGroups, 
                    allGroupsCompleted, 
                    nextGroup,
                    completedGroups 
                });
                
                return (
                    <div className="bg-white p-6 rounded-lg border">
                        {/* <h3 className="text-lg font-semibold mb-4">Определение области задачи</h3> */}
                        
                        {/* Always show progress */}
                        {renderProgress()}
                        
                        {errorMessage && (
                            <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md flex items-start">
                                <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
                                <p>{typeof errorMessage === 'string' ? errorMessage : 'An error occurred'}</p>
                            </div>
                        )}
                        
                        <div className="text-center py-4">
                            {!allGroupsCompleted && (
                                <button
                                    onClick={() => startFormulation()}
                                    disabled={isLoading}
                                    className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-300"
                                >
                                    {isLoading ? (
                                        <>
                                            <RefreshCcw className="w-5 h-5 animate-spin" />
                                            Initializing...
                                        </>
                                    ) : hasCompletedGroups ? (
                                        <>
                                            <ArrowRight className="w-5 h-5" />
                                            Continue with {nextGroup === 'what' ? 'What' :
                                                         nextGroup === 'why' ? 'Why' :
                                                         nextGroup === 'who' ? 'Who' :
                                                         nextGroup === 'where' ? 'Where' :
                                                         nextGroup === 'when' ? 'When' :
                                                         nextGroup === 'how' ? 'How' : nextGroup}
                                        </>
                                    ) : (
                                        <>
                                            <FileText className="w-5 h-5" />
                                            Start defining the scope
                                        </>
                                    )}
                                </button>
                            )}
                            
                            {allGroupsCompleted && (
                                <div className="text-center">
                                    <div className="mb-4 p-3 bg-green-50 text-green-700 rounded-md inline-flex items-center">
                                        <Check className="w-5 h-5 mr-2" />
                                        All question groups completed! You can now generate the task scope.
                                    </div>
                                    <div className="p-4 bg-blue-50 border border-blue-200 rounded-md mb-4">
                                        <p className="text-blue-800 font-medium">
                                            You've answered all the required questions. The next step is to generate a draft scope for your task based on these answers.
                                        </p>
                                    </div>
                                    <div className="mt-2">
                                        <button
                                            onClick={async () => {
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
                                            }}
                                            disabled={isLoading}
                                            className="px-8 py-4 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium text-lg shadow-md hover:shadow-lg animate-pulse"
                                        >
                                            {isLoading ? (
                                                <>
                                                    <RefreshCcw className="w-5 h-5 animate-spin inline mr-2" />
                                                    Generating...
                                                </>
                                            ) : (
                                                <>
                                                    <ArrowRight className="w-6 h-6 inline-block mr-2" />
                                                    Generate Task Scope Now
                                                </>
                                            )}
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                );
            default:
                return null;
        }
    };

    return (
        <CollapsibleSection title="Define scope of the task">
            <div className="space-y-4">
                {renderContent()}
            </div>
        </CollapsibleSection>
    );
}