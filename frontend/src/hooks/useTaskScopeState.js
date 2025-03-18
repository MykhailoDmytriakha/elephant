import { useState, useMemo } from 'react';

/**
 * Custom hook to manage all state variables for the TaskScope component
 * 
 * Workflow:
 * 1. User answers questions for each group (what, why, who, where, when, how)
 * 2. After completing all groups, draft scope is automatically generated
 * 3. User validates or requests changes to the draft scope
 * 4. Once approved, the scope is finalized
 * 
 * @param {Object} task - The task object from the parent component
 * @returns {Object} All state variables and setters needed for TaskScope
 */
export default function useTaskScopeState(task) {
    // Main workflow state
    const [flowState, setFlowState] = useState('initial'); // initial, questions, validation, final, draftLoading
    
    // Question and answer tracking
    const [currentGroup, setCurrentGroup] = useState(null);
    const [currentQuestions, setCurrentQuestions] = useState([]);
    const [completedGroups, setCompletedGroups] = useState([]); // Track which groups have been completed
    
    // Scope data
    const [draftScope, setDraftScope] = useState('');
    const [changes, setChanges] = useState([]); // Store the changes array from validation response
    
    // UI states
    const [isLoading, setIsLoading] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false); // For tracking submission state specifically
    const [feedback, setFeedback] = useState(null); // null if no changes requested, string otherwise
    const [errorMessage, setErrorMessage] = useState('');
    const [isLocallyApproved, setIsLocallyApproved] = useState(false); // Track local approval state
    
    // Define our 6 fixed groups - wrapped in useMemo to keep it stable
    const GROUPS = useMemo(() => ['what', 'why', 'who', 'where', 'when', 'how'], []);
    
    // Check if the task has been approved
    const isTaskApproved = String(task?.scope?.status).toLowerCase() === "approved";

    return {
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
    };
} 