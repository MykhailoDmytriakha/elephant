// frontend/src/utils/api.js
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Flags to prevent duplicate requests (Keep as is for now)
let isValidateScopeInProgress = false;

/**
 * Centralized API error handling. Throws an Error object.
 * @param {Error} error - The error object caught (usually from Axios).
 * @param {string} contextMessage - A message describing the context of the API call (e.g., "Failed to fetch queries").
 * @returns {never} - This function never returns normally, it always throws.
 */
const handleApiError = (error, contextMessage) => {
  let errorMessage = contextMessage || 'An API error occurred';
  let statusCode = null;
  let details = null;

  if (axios.isAxiosError(error)) {
    // Error from Axios (network or HTTP error)
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      statusCode = error.response.status;
      const responseData = error.response.data;
      // Try to extract a meaningful detail message from the response body
      details = responseData?.detail || responseData?.message || JSON.stringify(responseData);
      errorMessage = `${contextMessage}: Server responded with status ${statusCode}. ${details ? `Details: ${details}` : ''}`;
      console.error(`API Error Response (${statusCode}):`, responseData);
    } else if (error.request) {
      // The request was made but no response was received
      errorMessage = `${contextMessage}: No response received from server. Check network connection or server status.`;
      console.error('API Error Request:', error.request);
    } else {
      // Something happened in setting up the request that triggered an Error
      errorMessage = `${contextMessage}: Error setting up request: ${error.message}`;
      console.error('API Error Setup:', error.message);
    }
  } else {
    // Non-Axios error (e.g., programming error in response handling)
    errorMessage = `${contextMessage}: An unexpected error occurred: ${error.message}`;
    console.error('Non-API Error:', error);
  }

  // Create a new Error object with structured information
  const customError = new Error(errorMessage);
  customError.statusCode = statusCode; // Attach status code if available
  customError.details = details; // Attach details if available
  customError.originalError = error; // Keep reference to original error

  // Always throw the structured error
  throw customError;
};


// --- API functions remain the same, but now use the improved handleApiError ---

export const fetchQueries = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/user-queries`);
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to fetch queries');
  }
};

export const createQuery = async (query) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/user-queries/`, { query });
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to create query');
  }
};

export const fetchTaskDetails = async (taskId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/tasks/${taskId}`);
    return response.data;
  } catch (error) {
    // Add task ID to context message for better debugging
    handleApiError(error, `Failed to fetch details for task ${taskId}`);
  }
};

export const updateTaskContext = async (taskId, answers, queryParams = '') => {
  try {
    const url = `${API_BASE_URL}/tasks/${taskId}/context-questions${queryParams}`;
    const response = await axios.post(url, answers);
    return response.data;
  } catch (error) {
    handleApiError(error, `Failed to process context questions for task ${taskId}`);
  }
};

export const getContextQuestions = async (taskId, force = false) => {
  try {
    const shouldForce = force === true;
    const queryParams = shouldForce ? '?force=true' : '';
    // Using updateTaskContext with null answers to trigger the GET-like behavior
    const data = await updateTaskContext(taskId, null, queryParams);
    return data;
  } catch (error) {
    // Error is already handled by updateTaskContext, just re-throw if needed
    // Or adjust message specific to this function's context
    handleApiError(error, `Failed to get context questions and evaluate for task ${taskId}`);
  }
};

export const deleteTask = async (taskId) => {
  try {
    await axios.delete(`${API_BASE_URL}/tasks/${taskId}`);
  } catch (error) {
    handleApiError(error, `Failed to delete task ${taskId}`);
  }
};

export const getFormulationQuestions = async (taskId, groupId) => {
  try {
    console.log('Getting formulation questions for task:', taskId, 'and group:', groupId);
    const response = await axios.get(`${API_BASE_URL}/tasks/${taskId}/formulate/${groupId}`);
    return response.data;
  } catch (error) {
    handleApiError(error, `Failed to get formulation questions for task ${taskId}, group ${groupId}`);
  }
};

export const submitFormulationAnswers = async (taskId, groupId, answers) => {
  try {
    console.log('Submitting formulation answers for task:', taskId, 'and group:', groupId); // Removed answers from log for brevity/privacy
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/formulate/${groupId}`, answers);
    return response.data;
  } catch (error) {
    handleApiError(error, `Failed to submit formulation answers for task ${taskId}, group ${groupId}`);
  }
};

export const getDraftScope = async (taskId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/tasks/${taskId}/draft-scope`);
    return response.data;
  } catch (error) {
    handleApiError(error, `Failed to get draft scope for task ${taskId}`);
  }
};

export const validateScope = async (taskId, isApproved, feedback = null) => {
  if (isValidateScopeInProgress) {
    console.warn('validateScope: Request already in progress, ignoring duplicate call'); // Changed to warn
    return null; // Return null to indicate no action taken
  }
  isValidateScopeInProgress = true;
  try {
    console.log('validateScope: Making API call', {taskId, isApproved, feedback: feedback ? 'provided' : 'none'}); // Simplified log
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/validate-scope`, { isApproved, feedback });
    return response.data;
  } catch (error) {
    handleApiError(error, `Failed to validate scope for task ${taskId}`);
    return null; // Ensure it returns null on error after handling
  } finally {
    setTimeout(() => { isValidateScopeInProgress = false; }, 500);
  }
};

export const generateIFR = async (taskId) => {
  try {
    console.log('Generating IFR for task:', taskId);
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/ifr`);
    console.log('IFR response received for task:', taskId); // Simplified log
    return response.data;
  } catch (error) {
    handleApiError(error, `Failed to generate IFR for task ${taskId}`);
  }
};

export const generateRequirements = async (taskId) => {
  try {
    console.log('Generating requirements for task:', taskId);
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/requirements`);
    console.log('Requirements response received for task:', taskId); // Simplified log
    return response.data;
  } catch (error) {
    handleApiError(error, `Failed to generate Requirements for task ${taskId}`);
  }
};

export const generateNetworkPlan = async (taskId, forceRefresh = false) => {
  try {
    console.log(`Generating network plan for task: ${taskId} (force=${forceRefresh})`);
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/network-plan?force=${forceRefresh}`);
    console.log('Network plan response received for task:', taskId); // Simplified log
    return response.data;
  } catch (error) {
    handleApiError(error, `Failed to generate Network Plan for task ${taskId}`);
  }
};

// --- Decomposition API calls ---

export const generateWorkForStage = async (taskId, stageId) => {
  try {
    console.log(`Generating work packages for task ${taskId}, stage ${stageId}`);
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/stages/${stageId}/generate-work`); // Body removed as it was empty
    console.log(`Work packages response received for stage ${stageId}`);
    return response.data;
  } catch (error) {
    handleApiError(error, `Failed to generate Work Packages for stage ${stageId} in task ${taskId}`);
  }
};

export const generateTasksForWork = async (taskId, stageId, workId) => {
  try {
    console.log(`Generating executable tasks for task ${taskId}, stage ${stageId}, work ${workId}`);
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/stages/${stageId}/work/${workId}/generate-tasks`);
    console.log(`Executable tasks response received for work ${workId}`);
    return response.data;
  } catch (error) {
    handleApiError(error, `Failed to generate Executable Tasks for work ${workId}`);
  }
};

export const generateSubtasksForTask = async (taskId, stageId, workId, executableTaskId) => {
  try {
    console.log(`Generating subtasks for task ${taskId}, stage ${stageId}, work ${workId}, execTask ${executableTaskId}`);
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/stages/${stageId}/work/${workId}/tasks/${executableTaskId}/generate-subtasks`);
    console.log(`Subtasks response received for executable task ${executableTaskId}`);
    return response.data;
  } catch (error) {
    handleApiError(error, `Failed to generate Subtasks for executable task ${executableTaskId}`);
  }
};

export const generateAllTasksForWork = async (taskId, stageId, workId) => {
  try {
    console.log(`Generating ALL executable tasks for task ${taskId}, stage ${stageId}, work ${workId}`);
    // Using the specific work endpoint seems correct here based on backend structure
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/stages/${stageId}/work/${workId}/generate-tasks`);
    console.log(`ALL Executable tasks response received for work ${workId}`);
    return response.data;
  } catch (error) {
    handleApiError(error, `Failed to generate ALL Executable Tasks for work ${workId}`);
  }
};

export const generateAllSubtasksForWork = async (taskId, stageId, workId) => {
  try {
    console.log(`Generating ALL subtasks for task ${taskId}, stage ${stageId}, work ${workId}`);
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/stages/${stageId}/work/${workId}/tasks/generate-subtasks`);
    console.log(`ALL Subtasks response received for work ${workId}`);
    return response.data;
  } catch (error) {
    handleApiError(error, `Failed to generate ALL Subtasks for work ${workId}`);
  }
};

export const generateAllTasksForStage = async (taskId, stageId) => {
  try {
    console.log(`Generating ALL executable tasks for task ${taskId}, stage ${stageId}`);
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/stages/${stageId}/works/generate-tasks`);
    console.log(`ALL Executable tasks response received for stage ${stageId}`);
    return response.data;
  } catch (error) {
    handleApiError(error, `Failed to generate ALL Executable Tasks for stage ${stageId}`);
  }
};