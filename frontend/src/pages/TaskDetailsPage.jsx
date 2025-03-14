// src/pages/TaskDetailsPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Trash2 } from 'lucide-react';
import { LoadingSpinner, ErrorDisplay } from '../components/task/TaskComponents';
import { 
  fetchTaskDetails, 
  updateTaskContext, 
  deleteTask, 
  analyzeTask, 
  generateApproaches, 
  typifyTask, 
  clarifyTask, 
  decomposeTask,
  getContextQuestions,
  formulate_task
} from '../utils/api';
import { getStateColor, TaskStates } from '../constants/taskStates';
import TaskOverview from '../components/task/TaskOverview';
import Analysis from '../components/task/Analysis';
import Metadata from '../components/task/Metadata';
import ApproachFormation from '../components/task/ApproachFormation';
import Typification from '../components/task/Typification';
import ClarificationSection from '../components/task/ClarificationSection';
import Decomposition from '../components/task/Decomposition';
import TaskFormulation from '../components/task/TaskFormulation';
import Breadcrumbs from '../components/task/Breadcrumbs';
import { useToast } from '../components/common/ToastProvider';

export default function TaskDetailsPage() {
  const { taskId } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [followUpQuestion, setFollowUpQuestion] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isStartingClarificationLoading, setIsStartingClarificationLoading] = useState(false);
  const [isGeneratingConcepts, setIsGeneratingConcepts] = useState(false);
  const [isRegeneratingApproaches, setIsRegeneratingApproaches] = useState(false);
  const [isTypifying, setIsTypifying] = useState(false);
  const [isClarifying, setIsClarifying] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [clarificationData, setClarificationData] = useState(null);
  const [isDecomposing, setIsDecomposing] = useState(false);
  const [selectedApproachItems, setSelectedApproachItems] = useState({
    analytical_tools: [],
    practical_methods: [],
    frameworks: [],
  });
  const [isDecompositionStarted, setIsDecompositionStarted] = useState(false);
  const [isFormulating, setIsFormulating] = useState(false);
  const [isContextGatheringLoading, setIsContextGatheringLoading] = useState(false);
  const [contextQuestions, setContextQuestions] = useState([]);
  const [contextAnswers, setContextAnswers] = useState({});
  const [isSubmittingAnswers, setIsSubmittingAnswers] = useState(false);

  const loadTask = async () => {
    try {
      setLoading(true);
      setError(null);
      const task = await fetchTaskDetails(taskId);
      setTask(task);
      
      // No longer setting default message or automatically sending context update requests
    } catch (err) {
      toast.showError(`Failed to load task: ${err.message}`);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTask();
  }, [taskId]);

  const handleBack = () => {
    navigate('/');
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      try {
        await deleteTask(taskId);
        toast.showSuccess('Task deleted successfully');
        navigate('/');
      } catch (error) {
        toast.showError(`Failed to delete task: ${error.message}`);
        setError('Failed to delete task: ' + error.message);
      }
    }
  };

  const handleSendMessage = async (message) => {
    try {
      // Normal flow for all messages now that we get the specific question from API first
      const updatedContext = await updateTaskContext(taskId, {
        query: followUpQuestion,
        answer: message,
      });

      // Load the updated task
      const updatedTask = await fetchTaskDetails(taskId);
      setTask(updatedTask);

      // Update followUpQuestion based on context sufficiency
      if (updatedTask.is_context_sufficient) {
        setFollowUpQuestion(null);
        toast.showSuccess('Context gathering completed');
      } else {
        setFollowUpQuestion(updatedContext.follow_up_question);
      }
    } catch (error) {
      toast.showError(`Failed to send message: ${error.message}`);
      setError('Failed to send message: ' + error.message);
      throw error; // Propagate error to allow component to handle it
    }
  };

  const handleFormulate = async (isReformulate = false) => {
    try {
      setIsFormulating(true);
      await formulate_task(taskId);
      await loadTask();
      toast.showSuccess('Task formulated successfully');
    } catch (err) {
      toast.showError(`Failed to formulate task: ${err.message}`);
      setError('Failed to formulate task: ' + err.message);
    } finally {
      setIsFormulating(false);
    }
  };

  const handleClarification = async (message = null) => {
    try {
      setIsStartingClarificationLoading(true);

      // If this is the initial clarification (no message), set isClarifying
      if (!message) {
        setIsClarifying(true);
      }
      await clarifyTask(taskId, message);
      loadTask();
      if (message) {
        toast.showSuccess('Clarification response sent');
      }
    } catch (error) {
      toast.showError(`Failed to process clarification: ${error.message}`);
      setError('Failed to process clarification: ' + error.message);
    } finally {
      setIsStartingClarificationLoading(false);
    }
  };

  const handleAnalyze = async (isReanalyze = false) => {
    try {
      setIsAnalyzing(true);
      await analyzeTask(taskId, isReanalyze);
      await loadTask();
      toast.showSuccess(isReanalyze ? 'Task reanalyzed successfully' : 'Task analyzed successfully');
    } catch (err) {
      toast.showError(`Failed to analyze task: ${err.message}`);
      setError('Failed to analyze task: ' + err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleRegenerateApproaches = async () => {
    try {
      setIsRegeneratingApproaches(true);
      await generateApproaches(taskId);
      await loadTask();
      toast.showSuccess('Approaches regenerated successfully');
    } catch (err) {
      toast.showError(`Failed to regenerate approaches: ${err.message}`);
      setError('Failed to regenerate approaches: ' + err.message);
    } finally {
      setIsRegeneratingApproaches(false);
    }
  };

  const handleTypify = async (isRetypify = false) => {
    try {
      setIsTypifying(true);
      await typifyTask(taskId, isRetypify);
      await loadTask();
      toast.showSuccess(isRetypify ? 'Task retypified successfully' : 'Task typified successfully');
    } catch (err) {
      toast.showError(`Failed to typify task: ${err.message}`);
      setError('Failed to typify task: ' + err.message);
    } finally {
      setIsTypifying(false);
    }
  };

  const handleDecompose = async (selectedApproachItems, isRedecompose = false) => {
    try {
      setIsDecomposing(true);
      setIsDecompositionStarted(true);
      await decomposeTask(taskId, selectedApproachItems, isRedecompose);
      await loadTask();
      toast.showSuccess(isRedecompose ? 'Task redecomposed successfully' : 'Task decomposed successfully');
    } catch (err) {
      toast.showError(`Failed to decompose task: ${err.message}`);
      setError('Failed to decompose task: ' + err.message);
      setIsDecompositionStarted(false);
    } finally {
      setIsDecomposing(false);
    }
  };

  const handleApproachSelectionChange = (selections) => {
    setSelectedApproachItems(selections);
  };

  const handleStartContextGathering = async () => {
    try {
      setIsContextGatheringLoading(true);
      // Clear any previous questions, answers, and errors
      setContextQuestions([]);
      setContextAnswers({});
      setError(null); // Clear any existing error state
      
      // Get initial batch of context questions using the combined method
      const questionsData = await getContextQuestions(taskId);
      
      if (questionsData.is_context_sufficient) {
        // Context is already sufficient
        await loadTask();
        toast.showSuccess('Context is already sufficient');
      } else {
        // Transform the backend questions format to match frontend expectations
        const transformedQuestions = (questionsData.questions || []).map((question, qIndex) => {
          // Create a formatted question object
          return {
            id: `q-${qIndex}`, // Generate an ID for the question
            text: question.question, // Set question text from the 'question' field
            options: (question.options || []).map((optionText, oIndex) => {
              // Create a formatted option object
              return {
                id: `option-${qIndex}-${oIndex}`, // Generate an ID for each option
                text: optionText // Use the option text directly
              };
            })
          };
        });
        
        // Set the transformed questions for display
        setContextQuestions(transformedQuestions);
      }
    } catch (error) {
      toast.showError(`Failed to start context gathering: ${error.message}`);
      setError(`Failed to start context gathering: ${error.message}`);
      // Make sure no questions or chat is shown in error state
      setContextQuestions([]);
      setFollowUpQuestion(null);
    } finally {
      setIsContextGatheringLoading(false);
    }
  };

  const handleAnswerChange = (questionId, answer) => {
    setContextAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }));
  };

  const handleSubmitAnswers = async () => {
    try {
      setIsSubmittingAnswers(true);
      setError(null); // Clear any existing error state
      
      // Map the questions to get the original questions for submission
      const questionMap = contextQuestions.reduce((acc, q) => {
        acc[q.id] = q.text;
        return acc;
      }, {});
      
      // Process answers before submission, handling the free-form answers
      const processedAnswers = {
        answers: Object.entries(contextAnswers)
          .filter(([questionId, answer]) => {
            // Skip the special _text keys that are handled with their parent
            return !questionId.endsWith('_text');
          })
          .map(([questionId, answer]) => {
            return {
              question: questionMap[questionId] || questionId, // Use the original question text
              answer
            };
          })
      };
      
      // Submit all answers using the same combined method with processed answers parameter
      const result = await updateTaskContext(taskId, processedAnswers);
      
      if (result.is_context_sufficient) {
        // If context is now sufficient, reload the task
        await loadTask();
        // Clear questions since we're done
        setContextQuestions([]);
        toast.showSuccess('Context gathering completed');
      } else {
        // Transform the backend questions format to match frontend expectations
        const transformedQuestions = (result.questions || []).map((question, qIndex) => {
          // Create a formatted question object
          return {
            id: `q-${qIndex}`, // Generate an ID for the question
            text: question.question, // Set question text from the 'question' field
            options: (question.options || []).map((optionText, oIndex) => {
              // Create a formatted option object
              return {
                id: `option-${qIndex}-${oIndex}`, // Generate an ID for each option
                text: optionText // Use the option text directly
              };
            })
          };
        });
        
        // Set the transformed questions for display
        setContextQuestions(transformedQuestions);
        
        // Clear previous answers
        setContextAnswers({});
        toast.showInfo('Additional context needed');
      }
    } catch (error) {
      toast.showError(`Failed to submit answers: ${error.message}`);
      setError(`Failed to submit answers: ${error.message}`);
      // Make sure no questions or chat is shown in error state
      setContextQuestions([]);
      setFollowUpQuestion(null);
    } finally {
      setIsSubmittingAnswers(false);
    }
  };

  if (loading) return <LoadingSpinner />;
  
  // If we have an error but also have task data, don't show the error UI
  // The error has already been shown as a toast notification
  if (!task) {
    if (error) {
      // If task loading failed completely, show a more subtle error UI
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Error Loading Task</h2>
            <p className="text-gray-600 mb-4">{error}</p>
            <button
              onClick={() => navigate('/')}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Go Back to Tasks
            </button>
          </div>
        </div>
      );
    }
    return <LoadingSpinner />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="sticky top-0 z-50 bg-white border-b border-gray-200">
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="h-16 flex items-center">
              <button
                onClick={handleBack}
                className="mr-4 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div className="flex-1">
                <Breadcrumbs task={task} />
                <h1 className="text-2xl font-bold text-gray-900 mt-1">Task Details</h1>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-gray-600 mr-2">Task State:</span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStateColor(task.state)}`}>{task.state}</span>
                <button
                  onClick={handleDelete}
                  className="text-red-600 hover:text-red-700 flex items-center gap-2"
                >
                  <Trash2 className="w-5 h-5" />
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="col-span-2 space-y-6">
            <TaskOverview
              task={task}
              followUpQuestion={followUpQuestion}
              onSendMessage={handleSendMessage}
              onStartContextGathering={handleStartContextGathering}
              isContextGatheringLoading={isContextGatheringLoading}
              contextQuestions={contextQuestions}
              contextAnswers={contextAnswers}
              onAnswerChange={handleAnswerChange}
              onSubmitAnswers={handleSubmitAnswers}
              isSubmittingAnswers={isSubmittingAnswers}
              error={error}
            />

            {task.sub_level === 0 && (
              <TaskFormulation
                task={task}
                isContextGathered={task.state === TaskStates.CONTEXT_GATHERED}
                onFormulate={handleFormulate}
                isFormulating={isFormulating}
              />
            )}

            <Analysis
              analysis={task.analysis}
              isContextSufficient={task.is_context_sufficient}
              isAnalyzing={isAnalyzing}
              onAnalyze={handleAnalyze}
            />

            {(task.complexity == null || task.complexity > 1) && (
              <Typification
                typification={task.typification}
                isContextSufficient={task.is_context_sufficient}
                isTypifying={isTypifying}
                onTypify={handleTypify}
                taskState={task.state}
              />
            )}

            {task.complexity > 1 && (
              <ClarificationSection
                taskState={task.state}
                clarification_data={task.clarification_data}
                onStartClarification={() => handleClarification()}
                isStartingClarificationLoading={isStartingClarificationLoading}
                onSendMessage={handleClarification}
                isLoading={loading}
              />
            )}

            <ApproachFormation
              approaches={task.approaches}
              onRegenerateApproaches={handleRegenerateApproaches}
              isRegenerating={isRegeneratingApproaches}
              taskState={task.state}
              onSelectionChange={handleApproachSelectionChange}
              selectedItems={selectedApproachItems}
              isDecompositionStarted={isDecompositionStarted}
            />

            {task.complexity > 1 && (
              <Decomposition
                task={task}
                taskState={task.state}
                isDecomposing={isDecomposing}
                onDecompose={handleDecompose}
                selectedItems={selectedApproachItems}
              />
            )}

            {/* {task.complexity === 1 && (
              <SolutionDevelopment
                task={task}
                taskState={task.state}
                isDecomposing={isDecomposing}
                onDecompose={handleDecompose}
                selectedItems={selectedApproachItems}
              />
            )} */}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <div className="sticky top-24">
              <Metadata task={task} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
