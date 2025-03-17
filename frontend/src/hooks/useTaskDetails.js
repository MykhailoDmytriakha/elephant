import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../components/common/ToastProvider';
import { useTaskOperation } from './useTaskOperation';
import { useContextGathering } from './useContextGathering';
import { 
  fetchTaskDetails, 
  deleteTask, 
  analyzeTask, 
  generateApproaches, 
  typifyTask, 
  clarifyTask, 
  decomposeTask,
  formulate_task,
  generateIFR,
} from '../utils/api';

/**
 * Hook to manage task details and operations
 * @param {string} taskId - The ID of the task
 * @returns {Object} Task state and operation functions
 */
export function useTaskDetails(taskId) {
  const navigate = useNavigate();
  const toast = useToast();
  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedApproachItems, setSelectedApproachItems] = useState({
    analytical_tools: [],
    practical_methods: [],
    frameworks: [],
  });
  const [isDecompositionStarted, setIsDecompositionStarted] = useState(false);

  // Load task details
  const loadTask = async () => {
    try {
      setLoading(true);
      setError(null);
      const taskData = await fetchTaskDetails(taskId);
      setTask(taskData);
    } catch (err) {
      toast.showError(`Failed to load task: ${err.message}`);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Initialize task loading
  useEffect(() => {
    loadTask();
  }, [taskId]);

  // Context gathering hook - loadTask is used to refresh task data after context operations
  const contextGathering = useContextGathering(taskId, loadTask);

  // Task operation hooks
  const [handleFormulate, isFormulating] = useTaskOperation(
    (isReformulate = false) => formulate_task(taskId), 
    loadTask,
    { successMessage: 'Task formulated successfully', errorMessage: 'Failed to formulate task' }
  );

  const [handleAnalyze, isAnalyzing] = useTaskOperation(
    (isReanalyze = false) => analyzeTask(taskId, isReanalyze),
    loadTask,
    { 
      successMessage: (args) => args[0] ? 'Task reanalyzed successfully' : 'Task analyzed successfully',
      errorMessage: 'Failed to analyze task'
    }
  );

  const [handleGenerateIFR, isGeneratingIFR] = useTaskOperation(
    () => generateIFR(taskId),
    loadTask,
    {
      successMessage: 'Ideal Final Result generated successfully',
      errorMessage: 'Failed to generate Ideal Final Result'
    }
  );

  const [handleTypify, isTypifying] = useTaskOperation(
    (isRetypify = false) => typifyTask(taskId, isRetypify),
    loadTask,
    {
      successMessage: (args) => args[0] ? 'Task retypified successfully' : 'Task typified successfully',
      errorMessage: 'Failed to typify task'
    }
  );

  const [handleRegenerateApproaches, isRegeneratingApproaches] = useTaskOperation(
    () => generateApproaches(taskId),
    loadTask,
    { successMessage: 'Approaches regenerated successfully', errorMessage: 'Failed to regenerate approaches' }
  );

  const [handleClarification, isStartingClarificationLoading] = useTaskOperation(
    (message = null) => clarifyTask(taskId, message),
    loadTask,
    { 
      successMessage: (args) => args[0] ? 'Clarification response sent' : '',
      errorMessage: 'Failed to process clarification',
      showToasts: (args) => !!args[0] // Only show toast for messages, not initial clarification
    }
  );

  const [handleDecompose, isDecomposing] = useTaskOperation(
    (selectedItems, isRedecompose = false) => {
      setIsDecompositionStarted(true);
      return decomposeTask(taskId, selectedItems, isRedecompose);
    },
    loadTask,
    {
      successMessage: (args) => args[1] ? 'Task redecomposed successfully' : 'Task decomposed successfully',
      errorMessage: 'Failed to decompose task'
    }
  );

  const [handleDelete] = useTaskOperation(
    async () => {
      if (window.confirm('Are you sure you want to delete this task?')) {
        return deleteTask(taskId);
      }
      return Promise.reject(new Error('Delete cancelled'));
    },
    () => navigate('/'),
    { successMessage: 'Task deleted successfully', errorMessage: 'Failed to delete task' }
  );

  const handleBack = () => {
    navigate('/');
  };

  const handleApproachSelectionChange = (selections) => {
    setSelectedApproachItems(selections);
  };

  return {
    // State
    task,
    loading,
    error,
    selectedApproachItems,
    isDecompositionStarted,
    
    // Operations
    loadTask,
    handleBack,
    handleDelete,
    handleFormulate,
    isFormulating,
    handleAnalyze,
    isAnalyzing,
    handleGenerateIFR,
    isGeneratingIFR,
    handleTypify,
    isTypifying,
    handleRegenerateApproaches,
    isRegeneratingApproaches,
    handleClarification,
    isStartingClarificationLoading,
    handleDecompose,
    isDecomposing,
    handleApproachSelectionChange,
    
    // Context gathering
    ...contextGathering,
    // Track if we're in force refresh mode
    isForceRefreshMode: contextGathering.isForceRefreshMode,
    // Add an alias for retry handler for better semantics
    onRetryContextGathering: () => contextGathering.startContextGathering(false)
  };
} 