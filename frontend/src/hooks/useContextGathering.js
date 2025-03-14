import { useState, useEffect } from 'react';
import { getContextQuestions, updateTaskContext } from '../utils/api';
import { useToast } from '../components/common/ToastProvider';

/**
 * Custom hook to handle the context gathering flow
 * @param {string} taskId - The ID of the task
 * @param {Function} onTaskUpdated - Callback when task is updated
 * @returns {Object} Context gathering state and functions
 */
export function useContextGathering(taskId, onTaskUpdated) {
  const toast = useToast();
  const [contextQuestions, setContextQuestions] = useState([]);
  const [contextAnswers, setContextAnswers] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [isForceRefresh, setIsForceRefresh] = useState(false);

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

  /**
   * Transform backend question format to frontend format
   * @param {Array} backendQuestions - Questions from backend
   * @returns {Array} Transformed questions for frontend
   */
  const transformQuestions = (backendQuestions) => {
    return (backendQuestions || []).map((question, qIndex) => {
      return {
        id: `q-${qIndex}`,
        text: question.question,
        options: (question.options || []).map((optionText, oIndex) => {
          return {
            id: `option-${qIndex}-${oIndex}`,
            text: optionText
          };
        })
      };
    });
  };

  /**
   * Reset the context gathering state
   */
  const resetState = () => {
    setContextQuestions([]);
    setContextAnswers({});
    setError(null);
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
      console.log(`Starting context gathering. Force refresh: ${shouldForce}`);
      const response = await getContextQuestions(taskId, shouldForce);
      console.log('Raw response from context questions API:', response);
      
      // Handle different possible response formats
      const questionsData = response.questions ? response : { questions: response, is_context_sufficient: false };
      console.log('Extracted questions data:', questionsData);
      
      if (questionsData.is_context_sufficient || (!questionsData.questions || questionsData.questions.length === 0)) {
        // Context is sufficient or no questions needed
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
        const transformedQuestions = transformQuestions(questionsData.questions);
        console.log('Original backend questions:', questionsData.questions);
        console.log('Transformed questions for frontend:', transformedQuestions);
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

  return {
    contextQuestions,
    contextAnswers,
    isLoading,
    isSubmitting,
    error,
    isForceRefresh,
    startContextGathering,
    handleAnswerChange,
    submitAnswers
  };
} 