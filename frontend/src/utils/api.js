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

/**
 * Generic API request wrapper to reduce code duplication.
 * @param {string} method - HTTP method (get, post, delete, etc.)
 * @param {string} endpoint - API endpoint path (without base URL)
 * @param {Object} data - Request payload (for POST, PUT, etc.)
 * @param {string} errorMessage - Error message context
 * @param {Object} options - Additional options like query params, logging, etc.
 * @returns {Promise<any>} - API response data
 */
const apiRequest = async (method, endpoint, data = null, errorMessage, options = {}) => {
  const { queryParams = '', logging = false } = options;
  const url = `${API_BASE_URL}${endpoint}${queryParams}`;
  
  if (logging) {
    console.log(`${method.toUpperCase()} request to ${endpoint}`, data ? '(with payload)' : '');
  }
  
  try {
    const config = {};
    const response = await axios[method](url, data, config);
    
    if (logging) {
      console.log(`Response received from ${endpoint}`, {
        status: response.status,
        dataType: typeof response.data,
        isArray: Array.isArray(response.data),
        dataLength: Array.isArray(response.data) ? response.data.length : null,
        preview: Array.isArray(response.data) ? `Array[${response.data.length}]` : (typeof response.data === 'object' ? 'Object' : response.data)
      });
    }
    
    return response.data;
  } catch (error) {
    handleApiError(error, errorMessage);
  }
};

// --- API functions using the new apiRequest wrapper ---

export const fetchQueries = async () => {
  return apiRequest('get', '/user-queries', null, 'Failed to fetch queries');
};

export const createQuery = async (query) => {
  return apiRequest('post', '/user-queries/', { query }, 'Failed to create query');
};

export const fetchTaskDetails = async (taskId) => {
  return apiRequest('get', `/tasks/${taskId}`, null, `Failed to fetch details for task ${taskId}`);
};

export const loadTaskDataOnly = async (taskId) => {
  return apiRequest('get', `/tasks/${taskId}`, null, `Failed to fetch data for task ${taskId}`);
};

export const updateTaskContext = async (taskId, answers, queryParams = '') => {
  return apiRequest(
    'post', 
    `/tasks/${taskId}/context-questions`, 
    answers, 
    `Failed to process context questions for task ${taskId}`,
    { queryParams }
  );
};

export const getContextQuestions = async (taskId, force = false) => {
  const shouldForce = force === true;
  const queryParams = shouldForce ? '?force=true' : '';
  return apiRequest(
    'post', 
    `/tasks/${taskId}/context-questions`, 
    null, 
    `Failed to get context questions and evaluate for task ${taskId}`,
    { queryParams }
  );
};

export const deleteTask = async (taskId) => {
  return apiRequest('delete', `/tasks/${taskId}`, null, `Failed to delete task ${taskId}`);
};

export const getFormulationQuestions = async (taskId, groupId) => {
  return apiRequest(
    'get', 
    `/tasks/${taskId}/formulate/${groupId}`, 
    null, 
    `Failed to get formulation questions for task ${taskId}, group ${groupId}`,
    { logging: true }
  );
};

export const submitFormulationAnswers = async (taskId, groupId, answers) => {
  return apiRequest(
    'post', 
    `/tasks/${taskId}/formulate/${groupId}`, 
    answers, 
    `Failed to submit formulation answers for task ${taskId}, group ${groupId}`,
    { logging: true }
  );
};

export const getDraftScope = async (taskId) => {
  return apiRequest('get', `/tasks/${taskId}/draft-scope`, null, `Failed to get draft scope for task ${taskId}`);
};

export const validateScope = async (taskId, isApproved, feedback = null) => {
  if (isValidateScopeInProgress) {
    console.warn('validateScope: Request already in progress, ignoring duplicate call');
    return null;
  }
  
  isValidateScopeInProgress = true;
  try {
    const result = await apiRequest(
      'post', 
      `/tasks/${taskId}/validate-scope`, 
      { isApproved, feedback }, 
      `Failed to validate scope for task ${taskId}`,
      { logging: true }
    );
    return result;
  } finally {
    setTimeout(() => { isValidateScopeInProgress = false; }, 500);
  }
};

export const generateIFR = async (taskId) => {
  return apiRequest(
    'post',
    `/tasks/${taskId}/ifr`,
    null,
    `Failed to generate IFR for task ${taskId}`,
    { logging: true }
  );
};

export const generateRequirements = async (taskId) => {
  return apiRequest(
    'post',
    `/tasks/${taskId}/requirements`,
    null,
    `Failed to generate Requirements for task ${taskId}`,
    { logging: true }
  );
};

export const generateNetworkPlan = async (taskId, forceRefresh = false) => {
  const queryParams = forceRefresh ? '?force=true' : '';
  return apiRequest(
    'post',
    `/tasks/${taskId}/network-plan`,
    null,
    `Failed to generate Network Plan for task ${taskId}`,
    { queryParams, logging: true }
  );
};

// --- Decomposition API calls ---

// Generates work for a SINGLE stage
export const generateWorkForStage = async (taskId, stageId) => {
  return apiRequest(
    'post',
    `/tasks/${taskId}/stages/${stageId}/generate-work`,
    null,
    `Failed to generate Work Packages for stage ${stageId} in task ${taskId}`,
    { logging: true }
  );
};

// NEW FUNCTION: Generates work for ALL stages
export const generateAllWorkPackages = async (taskId) => {
  return apiRequest(
    'post',
    `/tasks/${taskId}/stages/generate-work`, // Note: no stageId here
    null,
    `Failed to generate Work Packages for all stages in task ${taskId}`,
    { logging: true }
  );
};

export const generateTasksForWork = async (taskId, stageId, workId) => {
  return apiRequest(
    'post',
    `/tasks/${taskId}/stages/${stageId}/work/${workId}/generate-tasks`,
    null,
    `Failed to generate Executable Tasks for work ${workId}`,
    { logging: true }
  );
};

export const generateSubtasksForTask = async (taskId, stageId, workId, executableTaskId) => {
  return apiRequest(
    'post',
    `/tasks/${taskId}/stages/${stageId}/work/${workId}/tasks/${executableTaskId}/generate-subtasks`,
    null,
    `Failed to generate Subtasks for executable task ${executableTaskId}`,
    { logging: true }
  );
};

export const generateAllTasksForWork = async (taskId, stageId, workId) => {
  // Using the specific work endpoint
  return apiRequest(
    'post',
    `/tasks/${taskId}/stages/${stageId}/work/${workId}/generate-tasks`,
    null,
    `Failed to generate ALL Executable Tasks for work ${workId}`,
    { logging: true }
  );
};

export const generateAllSubtasksForWork = async (taskId, stageId, workId) => {
  return apiRequest(
    'post',
    `/tasks/${taskId}/stages/${stageId}/work/${workId}/tasks/generate-subtasks`,
    null,
    `Failed to generate ALL Subtasks for work ${workId}`,
    { logging: true }
  );
};

export const generateAllTasksForStage = async (taskId, stageId) => {
  return apiRequest(
    'post',
    `/tasks/${taskId}/stages/${stageId}/works/generate-tasks`,
    null,
    `Failed to generate ALL Executable Tasks for stage ${stageId}`,
    { logging: true }
  );
};

export const editContextSummary = async (taskId, feedback) => {
  return apiRequest(
    'post',
    `/tasks/${taskId}/edit-context`,
    { feedback },
    `Failed to update context with feedback for task ${taskId}`,
    { logging: true }
  );
};

// NEW FUNCTION: Generates tasks for ALL stages
export const generateTasksForAllStages = async (taskId) => {
  return apiRequest(
    'post',
    `/tasks/${taskId}/stages/generate-all-tasks`, // The new endpoint
    null,
    `Failed to generate Tasks for all stages in task ${taskId}`,
    { logging: true }
  );
};

// Function to stream assistant responses using Server-Sent Events
export const chatWithTaskAssistant = async (taskId, message, callbacks = {}, messageHistory = []) => {
  const { onChunk, onComplete, onError } = callbacks;
  const endpoint = `${API_BASE_URL}/tasks/${taskId}/chat/stream`;
  
  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        message,
        message_history: messageHistory
      }),
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage;
      try {
        // Try to parse error as JSON
        const errorJson = JSON.parse(errorText);
        errorMessage = errorJson.detail || errorJson.message || `HTTP error! status: ${response.status}`;
      } catch (e) {
        // If parsing fails, use the raw text
        errorMessage = errorText || `HTTP error! status: ${response.status}`;
      }
      throw new Error(errorMessage);
    }
    
    // Process the stream using the EventSource API
    const reader = response.body.getReader();
    let fullResponse = '';
    const decoder = new TextDecoder();
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      // Decode the chunk
      const text = decoder.decode(value, { stream: true });
      
      // Process SSE format (data: {...})
      const lines = text.split('\n\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.substring(6));
            
            if (data.chunk) {
              fullResponse += data.chunk;
              if (onChunk) onChunk(data.chunk);
            }
            
            if (data.done) {
              if (onComplete) onComplete(fullResponse);
              break;
            }
            
            if (data.error) {
              // Handle error data from the stream
              const errorMessage = data.error;
              console.error('Stream error:', errorMessage);
              if (onError) {
                onError(new Error(errorMessage));
              } else {
                // If no error callback, send it to the chunk stream with error formatting
                const errorChunk = `\n\n⚠️ Error: ${errorMessage}`;
                if (onChunk) onChunk(errorChunk);
                fullResponse += errorChunk;
              }
            }
          } catch (e) {
            console.warn('Error parsing SSE data:', e);
            // Send parse error to stream if no error handler
            if (!onError && onChunk) {
              const errorChunk = `\n\n⚠️ Error parsing stream data`;
              onChunk(errorChunk);
              fullResponse += errorChunk;
            }
          }
        }
      }
    }
    
    return fullResponse;
  } catch (error) {
    console.error('Error in chatWithTaskAssistant:', error);
    
    // Format a user-friendly error message
    const errorMessage = error.message || 'Failed to connect to assistant';
    
    // If there's an error callback, use it
    if (onError) {
      onError(error);
    } else if (onChunk) {
      // Otherwise display the error in the chat stream
      onChunk(`\n\n⚠️ Error: ${errorMessage}`);
    }
    
    // Rethrow after handling to allow the component to handle it
    throw error;
  }
};