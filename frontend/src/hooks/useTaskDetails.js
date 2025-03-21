import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../components/common/ToastProvider';
import { useTaskOperation } from './useTaskOperation';
import { useContextGathering } from './useContextGathering';
import { 
  fetchTaskDetails, 
  deleteTask, 
  generateIFR,
  generateRequirements,
  generateNetworkPlan
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

  const [handleGenerateIFR, isGeneratingIFR] = useTaskOperation(
    () => generateIFR(taskId),
    loadTask,
    {
      successMessage: 'Ideal Final Result generated successfully',
      errorMessage: 'Failed to generate Ideal Final Result'
    }
  );

  const [handleGenerateRequirements, isGeneratingRequirements] = useTaskOperation(
    () => generateRequirements(taskId),
    loadTask,
    {
      successMessage: 'Requirements generated successfully',
      errorMessage: 'Failed to generate Requirements'
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

  const [handleGenerateNetworkPlan, isGeneratingNetworkPlan] = useTaskOperation(
    () => generateNetworkPlan(taskId),
    loadTask,
    {
      successMessage: 'Network Plan generated successfully',
      errorMessage: 'Failed to generate Network Plan'
    }
  );

  return {
    // State
    task,
    loading,
    error,
    
    // Operations
    loadTask,
    handleBack,
    handleDelete,
    handleGenerateIFR,
    isGeneratingIFR,
    handleGenerateRequirements,
    isGeneratingRequirements,
    // Context gathering
    ...contextGathering,
    // Track if we're in force refresh mode
    isForceRefreshMode: contextGathering.isForceRefreshMode,
    // Add an alias for retry handler for better semantics
    onRetryContextGathering: () => contextGathering.startContextGathering(false),
    // Network Plan
    isGeneratingNetworkPlan,
    handleGenerateNetworkPlan,
  };
} 