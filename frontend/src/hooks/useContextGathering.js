import { useState, useEffect, useRef } from 'react';
import { getContextQuestions, updateTaskContext, editContextSummary, deleteContextQuestion } from '../utils/api';
import { useToast } from '../components/common/ToastProvider';

/**
 * Custom hook to handle the context gathering flow
 * @param {string} taskId - The ID of the task
 * @param {Function} onTaskUpdated - Callback when task is updated
 * @param {Object} task - The current task data (optional, for restoration)
 * @returns {Object} Context gathering state and functions
 */
export function useContextGathering(taskId, onTaskUpdated, task = null) {
  const toast = useToast();
  const [contextQuestions, setContextQuestions] = useState([]);
  const [contextAnswers, setContextAnswers] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [isForceRefresh, setIsForceRefresh] = useState(false);
  const [isEditingContext, setIsEditingContext] = useState(false);
  const [contextFeedback, setContextFeedback] = useState('');
  const [isDeletingQuestion, setIsDeletingQuestion] = useState(false);

  // Prevent infinite requests when server is down
  const restoreAttemptsRef = useRef(0);

  // Track when a context gathering operation has been started
  useEffect(() => {
    if (contextQuestions.length > 0) {
      // Questions are loaded, save the initial set of empty answers
      const initialAnswers = contextQuestions.reduce((acc, q) => {
        acc[q.id] = '';
        return acc;
      }, {});
      setContextAnswers(initialAnswers);
    }
  }, [contextQuestions]);

  // Restore pending questions from task data when task is available
  useEffect(() => {
    const restorePendingQuestions = () => {
      // Skip restoration if we're in the middle of a question deletion operation
      if (isDeletingQuestion) {
        console.log('Skipping context restoration - question deletion in progress');
        return;
      }

      console.log('=== CONTEXT RESTORATION DEBUG ===');
      console.log('Task object:', task);
      console.log('Task ID:', task?.id);
      console.log('Task context_answers:', task?.context_answers);
      console.log('Task context_answers length:', task?.context_answers?.length);

      if (!task || !task.context_answers) {
        console.log('No task or context_answers found, skipping restoration');
        return;
      }

      // Prevent infinite requests when server is down or task keeps changing
      if (restoreAttemptsRef.current >= 3) {
        console.warn('Max restore attempts reached, stopping to prevent infinite requests');
        return;
      }

      console.log(`Attempting to restore pending questions from task data (attempt ${restoreAttemptsRef.current + 1}):`, task.id);

      // Filter pending questions (empty answer)
      const pendingAnswers = (task.context_answers || [])
        .filter(a => !a.answer || a.answer.trim() === '');

      console.log('All context_answers:', task.context_answers);
      console.log('Filtered pending answers (empty answer):', pendingAnswers.length, pendingAnswers);
      console.log('Pending answers details:', pendingAnswers.map(a => ({ question: a.question, answer: a.answer, answerLength: a.answer?.length })));

      restoreAttemptsRef.current += 1;

      if (pendingAnswers.length > 0) {
        console.log('Restoring pending questions:', pendingAnswers);
        // Transform to ContextQuestion format
        const questions = pendingAnswers.map((a, idx) => ({
          question: a.question,
          options: a.options || []  // Include options if they exist
        }));
        console.log('Questions before transformation:', questions);
        const transformed = transformQuestions(questions);
        console.log('Transformed questions:', transformed);
        console.log('Setting context questions to state');
        setContextQuestions(transformed);
        restoreAttemptsRef.current = 0; // Reset attempts on success
      } else {
        console.log('No pending questions found in task data');
        // Clear any existing questions if none are pending
        setContextQuestions([]);
      }
    };

    restorePendingQuestions();
  }, [task, isDeletingQuestion]); // Run when task data or deletion state changes

  /**
   * Transform backend question format to frontend format
   * @param {Array} backendQuestions - Questions from backend
   * @returns {Array} Transformed questions for frontend
   */
  const transformQuestions = (backendQuestions) => {
    return (backendQuestions || []).map((question, qIndex) => {
      // Use question text hash as stable ID to prevent re-mounting when order changes
      // Use a simple hash function that works with Unicode characters
      const questionId = `q-${simpleHash(question.question).substring(0, 8)}`;
      return {
        id: questionId,
        text: question.question,
        options: (question.options || []).map((optionText, oIndex) => {
          return {
            id: `${questionId}-opt-${oIndex}`,
            text: optionText
          };
        })
      };
    });
  };

  /**
   * Simple hash function that works with Unicode characters
   * @param {string} str - String to hash
   * @returns {string} Hexadecimal hash
   */
  const simpleHash = (str) => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(16);
  };

  /**
   * Start the context gathering process
   * @param {boolean} shouldForce - Whether to force refresh context
   * @returns {Promise<void>}
   */
  const startContextGathering = async (shouldForce = false) => {
    setIsLoading(true);
    setIsForceRefresh(shouldForce);
    setError(null);

    try {
      console.log(`=== START CONTEXT GATHERING DEBUG ===`);
      console.log(`Starting context gathering. Force refresh: ${shouldForce}`);
      console.log(`Task ID: ${taskId}`);

      const response = await getContextQuestions(taskId, shouldForce);
      console.log('Raw response from context questions API:', response);

      // Handle different possible response formats
      const questionsData = response.questions ? response : { questions: response, is_context_sufficient: false };
      console.log('Extracted questions data:', questionsData);
      console.log('Questions data properties:', Object.keys(questionsData));
      console.log('is_context_sufficient:', questionsData.is_context_sufficient);
      console.log('questions array:', questionsData.questions);
      console.log('questions length:', questionsData.questions?.length);

      if (questionsData.is_context_sufficient || (!questionsData.questions || questionsData.questions.length === 0)) {
        // Context is sufficient or no questions needed
        console.log('Context is sufficient or no questions needed');
        if (shouldForce) {
          toast.showSuccess('Context refresh complete. Task updated.');
        } else {
          toast.showSuccess('Your context is already sufficient. No additional information needed.');
        }
        setContextQuestions([]);

        // Reload the task data to get updated task and context
        console.log("Context is sufficient, reloading task data");
        if (onTaskUpdated) {
          await onTaskUpdated();
        }
      } else {
        // We have questions to answer
        console.log('We have questions to answer');
        const transformedQuestions = transformQuestions(questionsData.questions);
        console.log('Original backend questions:', questionsData.questions);
        console.log('Transformed questions for frontend:', transformedQuestions);
        console.log('Setting context questions to state');
        setContextQuestions(transformedQuestions);

        if (shouldForce) {
          toast.showSuccess('Generating new questions for context refresh.');
        } else {
          toast.showSuccess('Context questions generated. Please provide answers.');
        }
      }
    } catch (error) {
      console.error('Context gathering error:', error);
      const errorMessage = `Failed to ${shouldForce ? 'refresh context' : 'generate questions'}: ${error.message}`;
      toast.showError(errorMessage);
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle changes to context answers
   * @param {string} questionId - The ID of the question
   * @param {string} answer - The answer text
   */
  const handleAnswerChange = (questionId, answer) => {
    setContextAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }));
  };

  /**
   * Format the answers for submission to the API
   * @param {boolean} isForceRefresh - Whether this is a forced refresh
   * @returns {object} Formatted answers
   */
  const formatAnswersForSubmission = (isForceRefresh) => {
    // Map questions and answers to the expected format
    const formattedAnswers = Object.entries(contextAnswers).map(([questionId, answer]) => {
      // Find the corresponding question
      const question = contextQuestions.find(q => q.id === questionId);
      
      // Format the answer based on question type
      let formattedAnswer = answer;
      
      // If answer is an array (for questions with options), join them with commas
      if (Array.isArray(answer)) {
        formattedAnswer = answer.join(', ');
      }
      
      return {
        question: question.text,
        answer: formattedAnswer
      };
    });

    return {
      answers: formattedAnswers,
      force: isForceRefresh // Send the force parameter with correct name
    };
  };

  /**
   * Submit the context answers
   * @returns {Promise<object>} The submission result
   */
  const submitAnswers = async () => {
    // Check if all questions have valid answers
    const hasInvalidAnswers = contextQuestions.some(q => {
      const answer = contextAnswers[q.id];

      // For questions with options - should be an array with at least one selected option
      if (q.options && q.options.length > 0) {
        return !Array.isArray(answer) || answer.length === 0 || answer.some(a => a === '');
      }

      // For text questions - should be a non-empty string
      return !answer || answer.trim() === '';
    });

    if (hasInvalidAnswers) {
      toast.showError('Please complete all questions before submitting');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    // Save current scroll position before updating data
    const currentScrollPosition = window.scrollY;

    try {
      const formattedData = formatAnswersForSubmission(isForceRefresh);
      console.log('Submitting context answers:', formattedData);

      const result = await updateTaskContext(taskId, formattedData);

      if (result.is_context_sufficient) {
        toast.showSuccess('Context is now sufficient! Task details will be updated.');

        // Reload the task data to get updated task and context
        console.log("Context is now sufficient, reloading task data");
        if (onTaskUpdated) {
          await onTaskUpdated();
        }

        // Restore scroll position after data update
        setTimeout(() => {
          window.scrollTo(0, currentScrollPosition);
        }, 100);

        // Clear questions since they're no longer needed
        setContextQuestions([]);
      } else {
        // If we got more questions, show a different message
        if (result.questions && result.questions.length > 0) {
          toast.showInfo('Additional questions required. Please provide more information.');
          const transformedQuestions = transformQuestions(result.questions);
          setContextQuestions(transformedQuestions);
        } else {
          toast.showSuccess('Answers submitted successfully.');
        }
      }

      return result;
    } catch (error) {
      console.error('Error submitting context answers:', error);
      toast.showError(`Failed to submit answers: ${error.message}`);
      setError(`Failed to submit answers: ${error.message}`);
      return null;
    } finally {
      setIsSubmitting(false);
      setIsForceRefresh(false); // Reset force mode after submission
    }
  };

  /**
   * Handle changes to context feedback
   * @param {string} feedback - The feedback text
   */
  const handleContextFeedbackChange = (feedback) => {
    setContextFeedback(feedback);
  };

  /**
   * Submit context edit feedback
   * @returns {Promise<object>} The submission result
   */
  const submitContextFeedback = async () => {
    if (!contextFeedback || contextFeedback.trim() === '') {
      toast.showError('Please provide feedback to improve the context');
      return;
    }

    setIsEditingContext(true);
    setError(null);

    // Save current scroll position before updating data
    const currentScrollPosition = window.scrollY;

    try {
      console.log('Submitting context feedback:', contextFeedback);

      const result = await editContextSummary(taskId, contextFeedback);

      toast.showSuccess('Context updated successfully with your feedback');

      // Reload the task data to get updated task and context
      console.log("Context was updated with feedback, reloading task data");
      if (onTaskUpdated) {
        await onTaskUpdated();
      }

      // Restore scroll position after data update
      setTimeout(() => {
        window.scrollTo(0, currentScrollPosition);
      }, 100);

      // Clear feedback after submission
      setContextFeedback('');

      return result;
    } catch (error) {
      console.error('Error submitting context feedback:', error);
      toast.showError(`Failed to update context: ${error.message}`);
      setError(`Failed to update context: ${error.message}`);
      return null;
    } finally {
      setIsEditingContext(false);
    }
  };

  /**
   * Delete a question from the current context questions
   * @param {number} questionIndex - Index of the question to delete
   */
  const deleteQuestion = async (questionIndex) => {
    const question = contextQuestions[questionIndex];
    if (!question) return;

    const questionText = question.question || question.text;

    // Save current scroll position before any updates
    const currentScrollPosition = window.scrollY;

    // Set deletion flag to prevent useEffect from interfering
    setIsDeletingQuestion(true);

    try {
      // Update local state immediately to avoid UI flicker and maintain scroll position
      setContextQuestions(prev => prev.filter((_, index) => index !== questionIndex));
      setContextAnswers(prev => {
        const newAnswers = { ...prev };
        const questionId = question.id;
        if (questionId) {
          delete newAnswers[questionId];
        }
        return newAnswers;
      });

      // Restore scroll position immediately after local state update
      requestAnimationFrame(() => {
        const restoreScroll = () => window.scrollTo(0, currentScrollPosition);

        // Immediate restoration
        restoreScroll();

        // Multiple follow-up restorations to catch any delayed re-renders
        setTimeout(restoreScroll, 10);
        setTimeout(restoreScroll, 50);
        setTimeout(restoreScroll, 100);
        setTimeout(restoreScroll, 200);
      });

      // Send request to delete from backend asynchronously
      // Don't await to avoid blocking UI updates and scroll restoration
      deleteContextQuestion(taskId, questionText).catch(error => {
        console.error('Failed to delete question on server:', error);
        // If server deletion fails, we could restore the question locally
        // But for now, just log the error - the UI is already updated
      });

      toast.showSuccess('Question deleted successfully');
    } catch (error) {
      console.error('Failed to delete question:', error);
      toast.showError(`Failed to delete question: ${error.message}`);
    } finally {
      // Reset deletion flag
      setIsDeletingQuestion(false);
    }
  };

  return {
    contextQuestions,
    contextAnswers,
    isLoading,
    isSubmitting,
    error,
    isForceRefresh,
    startContextGathering,
    handleAnswerChange,
    submitAnswers,
    // Context editing
    isEditingContext,
    contextFeedback,
    handleContextFeedbackChange,
    submitContextFeedback,
    // Question management
    deleteQuestion
  };
} 