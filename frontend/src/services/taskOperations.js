/**
 * Service module for task operations
 * Centralizes business logic and API calls related to task management
 */

import { 
  generateAllWorkPackages, 
  generateTasksForAllStages, 
  chatWithTaskAssistant, 
  loadTaskDataOnly 
} from '../utils/api';

/**
 * Service class for task operations
 * Provides a clean interface for task-related business logic
 */
export class TaskOperationsService {
  constructor(toastService) {
    this.toast = toastService;
  }

  /**
   * Generate work packages for all stages
   */
  async generateWorkPackages(taskId, onSuccess, onError) {
    try {
      await generateAllWorkPackages(taskId);
      this.toast?.showSuccess('Successfully generated work packages for all stages.');
      if (onSuccess) await onSuccess();
    } catch (error) {
      console.error("Error generating all work packages:", error);
      const errorMessage = `Failed to generate work packages: ${error.message || 'Unknown error'}`;
      this.toast?.showError(errorMessage);
      if (onError) onError(error);
      throw error;
    }
  }

  /**
   * Generate tasks for all stages
   */
  async generateTasks(taskId, onSuccess, onError) {
    try {
      await generateTasksForAllStages(taskId);
      this.toast?.showSuccess('Successfully generated tasks for all stages.');
      if (onSuccess) await onSuccess();
    } catch (error) {
      console.error("Error generating tasks for all stages:", error);
      const errorMessage = `Failed to generate tasks: ${error.message || 'Unknown error'}`;
      this.toast?.showError(errorMessage);
      if (onError) onError(error);
      throw error;
    }
  }

  /**
   * Load task data without affecting UI state
   */
  async loadTaskData(taskId, onSuccess, onError) {
    try {
      const updatedTask = await loadTaskDataOnly(taskId);
      if (onSuccess) onSuccess(updatedTask);
      return updatedTask;
    } catch (error) {
      console.error("Error loading task data:", error);
      const errorMessage = `Failed to load task data: ${error.message || 'Unknown error'}`;
      this.toast?.showError(errorMessage);
      if (onError) onError(error);
      throw error;
    }
  }

  /**
   * Send chat message with proper error handling
   */
  async sendChatMessage(taskId, message, callbacks, messageHistory) {
    try {
      return await chatWithTaskAssistant(taskId, message, callbacks, messageHistory);
    } catch (error) {
      console.error("Error in chat:", error);
      const errorMessage = error.message || 'Unknown error';
      
      // Handle session errors with auto-recovery suggestion
      if (errorMessage.includes('Session not found') || errorMessage.includes('session')) {
        throw new Error('Your chat session has expired. Please reset to continue.');
      }
      
      throw error;
    }
  }
}

/**
 * Factory function to create task operations service
 */
export const createTaskOperationsService = (toastService) => {
  return new TaskOperationsService(toastService);
};

/**
 * Hook-like function for task operations (can be converted to actual hook later)
 */
export const useTaskOperations = (toastService) => {
  const service = createTaskOperationsService(toastService);

  return {
    generateWorkPackages: service.generateWorkPackages.bind(service),
    generateTasks: service.generateTasks.bind(service),
    loadTaskData: service.loadTaskData.bind(service),
    sendChatMessage: service.sendChatMessage.bind(service)
  };
}; 