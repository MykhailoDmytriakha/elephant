import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../components/common/ToastProvider';
import { useTaskOperation } from './useTaskOperation';
import { useContextGathering } from './useContextGathering';
import {
  fetchTaskDetails,
  deleteTask,
  deleteContextAnswer,
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
  const loadAttemptsRef = useRef(0);
  const isLoadingRef = useRef(false);

  // Load task details
  const loadTask = useCallback(async () => {
    // Prevent duplicate requests while loading
    if (isLoadingRef.current) {
      console.log('Load already in progress, skipping duplicate request');
      return;
    }

    // Prevent infinite requests when server is down
    if (loadAttemptsRef.current >= 3) {
      console.warn('Max load attempts reached, stopping to prevent infinite requests');
      setLoading(false);
      setError('Failed to load task after multiple attempts. Please check server connection.');
      return;
    }

    try {
      isLoadingRef.current = true;
      setLoading(true);
      setError(null);
      loadAttemptsRef.current += 1;
      console.log(`Loading task data (attempt ${loadAttemptsRef.current}): ${taskId}`);
      const taskData = await fetchTaskDetails(taskId);
      setTask(taskData);
      loadAttemptsRef.current = 0; // Reset attempts on success
      console.log('Task data loaded successfully:', taskData.id);
    } catch (err) {
      console.error(`Failed to load task (attempt ${loadAttemptsRef.current}):`, err.message);
      toast.showError(`Failed to load task: ${err.message}`);
      setError(err.message);
    } finally {
      isLoadingRef.current = false;
      setLoading(false);
    }
  }, [taskId, toast]);

  // Initialize task loading
  useEffect(() => {
    // Only load if we don't have task data yet
    if (!task) {
    loadTask();
    }
  }, [loadTask, task]);

  // Context gathering hook - loadTask is used to refresh task data after context operations
  const contextGathering = useContextGathering(taskId, loadTask, task);

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

  const handleDelete = useCallback(async () => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      try {
        await deleteTask(taskId);
        toast.showSuccess('Task deleted successfully');
        navigate('/');
      } catch (error) {
        toast.showError(`Failed to delete task: ${error.message}`);
      }
    }
    // User cancelled - do nothing
  }, [taskId, navigate, toast]);

  const handleBack = () => {
    navigate('/');
  };

  const [handleDeleteAnswer, isDeletingAnswer] = useTaskOperation(
    (answerIndex) => deleteContextAnswer(taskId, answerIndex),
    loadTask,
    {
      successMessage: 'Context answer deleted successfully',
      errorMessage: 'Failed to delete context answer'
    }
  );

  const [handleGenerateNetworkPlan, isGeneratingNetworkPlan] = useTaskOperation(
    (forceRefresh = false) => generateNetworkPlan(taskId, forceRefresh),
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
    setTask,
    
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
    // Context answer deletion
    handleDeleteAnswer,
    isDeletingAnswer,
    // Network Plan
    isGeneratingNetworkPlan,
    handleGenerateNetworkPlan,
  };
} 