import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Flags to prevent duplicate requests
let isValidateScopeInProgress = false;

const handleApiError = (error, defaultMessage) => {
  if (error.response) {
    const message = error.response.data?.detail || 
                   error.response.data?.message || 
                   error.response.statusText;
    throw new Error(`${defaultMessage}: ${message}`);
  }
  if (error.request) {
    throw new Error(`Network error: Unable to connect to server`);
  }
  throw new Error(defaultMessage + ': ' + error.message);
};

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
    handleApiError(error, 'Failed to fetch task details');
  }
};

export const updateTaskContext = async (taskId, answers, queryParams = '') => {
  try {
    const url = `${API_BASE_URL}/tasks/${taskId}/context-questions${queryParams}`;
    const response = await axios.post(url, answers);
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to process context questions');
  }
};

export const getContextQuestions = async (taskId, force = false) => {
  try {
    const shouldForce = force === true;
    const queryParams = shouldForce ? '?force=true' : '';
    
    const data = await updateTaskContext(taskId, null, queryParams);
    return data;
  } catch (error) {
    handleApiError(error, 'Failed to get context questions and evaluate');
  }
};

export const deleteTask = async (taskId) => {
  try {
    await axios.delete(`${API_BASE_URL}/tasks/${taskId}`);
  } catch (error) {
    handleApiError(error, 'Failed to delete task');
  }
};

export const getFormulationQuestions = async (taskId, groupId) => {
  try {
    console.log('Getting formulation questions for task:', taskId, 'and group:', groupId);
    const response = await axios.get(`${API_BASE_URL}/tasks/${taskId}/formulate/${groupId}`);
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to get formulation questions');
  }
};

export const submitFormulationAnswers = async (taskId, groupId, answers) => {
  try {
    console.log('Submitting formulation answers for task:', taskId, 'and group:', groupId, 'with answers:', answers);
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/formulate/${groupId}`, answers);
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to submit formulation answers');
  }
};

export const getDraftScope = async (taskId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/tasks/${taskId}/draft-scope`);
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to get draft scope');
  }
};

export const validateScope = async (taskId, isApproved, feedback = null) => {
  // If there's already a request in progress, ignore this one
  if (isValidateScopeInProgress) {
    console.log('validateScope: Request already in progress, ignoring duplicate call');
    return null;
  }
  
  // Set flag to prevent duplicate requests
  isValidateScopeInProgress = true;
  
  try {
    console.log('validateScope: Making API call', {taskId, isApproved, feedback});
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/validate-scope`, { isApproved, feedback });
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to validate scope');
  } finally {
    // Reset flag after a short delay to catch very fast duplicate clicks
    setTimeout(() => {
      isValidateScopeInProgress = false;
    }, 500);
  }
};

export const generateIFR = async (taskId) => {
  try {
    console.log('Generating IFR for task:', taskId);
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/ifr`);
    console.log('IFR response:', response.data);
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to generate Ideal Final Result');
  }
};

export const generateRequirements = async (taskId) => {
  try {
    console.log('Generating requirements for task:', taskId);
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/requirements`);
    console.log('Requirements response:', response.data);
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to generate Requirements');
  }
};

export const generateNetworkPlan = async (taskId, forceRefresh = false) => {
  try {
    console.log('Generating network plan for task:', taskId);
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/network-plan?force=${forceRefresh}`);
    console.log('Network plan response:', response.data);
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to generate Network Plan');
  }
};

/**
 * Generates Work packages for a specific stage of a task.
 * @param {string} taskId - The ID of the task.
 * @param {string} stageId - The ID of the stage.
 * @returns {Promise<Array>} A promise that resolves to the list of generated Work packages.
 */
export const generateWorkForStage = async (taskId, stageId) => {
  try {
    console.log(`Generating work packages for task ${taskId}, stage ${stageId}`);
    // POST request, no body needed based on the endpoint definition
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/stages/${stageId}/generate-work`, {});
    console.log(`Work packages response for stage ${stageId}:`, response.data);
    // The backend returns the list of work packages directly
    return response.data;
  } catch (error) {
    handleApiError(error, `Failed to generate Work Packages for stage ${stageId}`);
  }
};

export const generateTasksForWork = async (taskId, stageId, workId) => {
  try {
    console.log(`Generating executable tasks for task ${taskId}, stage ${stageId}, work ${workId}`);
    // POST request, no body needed based on the endpoint definition
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/stages/${stageId}/work/${workId}/generate-tasks`, {});
    console.log(`Executable tasks response for work ${workId}:`, response.data);
    // The backend returns the list of executable tasks directly
    return response.data;
  } catch (error) {
    handleApiError(error, `Failed to generate Executable Tasks for work ${workId}`);
  }
};

export const generateSubtasksForTask = async (taskId, stageId, workId, executableTaskId) => {
  try {
    console.log(`Generating subtasks for task ${taskId}, stage ${stageId}, work ${workId}, execTask ${executableTaskId}`);
    // POST request, no body needed based on the endpoint definition
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/stages/${stageId}/work/${workId}/tasks/${executableTaskId}/generate-subtasks`, {});
    console.log(`Subtasks response for executable task ${executableTaskId}:`, response.data);
    // The backend returns the list of subtasks directly
    return response.data;
  } catch (error) {
    handleApiError(error, `Failed to generate Subtasks for executable task ${executableTaskId}`);
  }
};

/**
 * Generates Executable Tasks for ALL tasks within a specific Work package.
 * @param {string} taskId - The ID of the task.
 * @param {string} stageId - The ID of the stage.
 * @param {string} workId - The ID of the work package.
 * @returns {Promise<Array>} A promise that resolves to the updated list of Executable Tasks for the Work package.
 */
export const generateAllTasksForWork = async (taskId, stageId, workId) => {
  try {
    console.log(`Generating ALL executable tasks for task ${taskId}, stage ${stageId}, work ${workId}`);
    // Note: This endpoint name in the backend seems slightly misleading based on its path.
    // It generates tasks for *all* tasks within the specified work_id, not *all* works in the stage.
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/stages/${stageId}/work/${workId}/generate-tasks`, {}); // Reusing the existing endpoint as it generates all tasks for the specified work
    console.log(`Executable tasks response for ALL tasks in work ${workId}:`, response.data);
    // Backend returns the list of executable tasks for this work package
    return response.data;
  } catch (error) {
    handleApiError(error, `Failed to generate ALL Executable Tasks for work ${workId}`);
  }
};


/**
 * Generates Subtasks for ALL Executable Tasks within a specific Work package.
 * @param {string} taskId - The ID of the task.
 * @param {string} stageId - The ID of the stage.
 * @param {string} workId - The ID of the work package.
 * @returns {Promise<Array>} A promise that resolves to the updated list of Executable Tasks (containing subtasks) for the Work package.
 */
export const generateAllSubtasksForWork = async (taskId, stageId, workId) => {
  try {
    console.log(`Generating ALL subtasks for task ${taskId}, stage ${stageId}, work ${workId}`);
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/stages/${stageId}/work/${workId}/tasks/generate-subtasks`, {});
    console.log(`Subtasks response for ALL tasks in work ${workId}:`, response.data);
    // Backend returns the updated list of Executable Tasks for the work package, now containing subtasks
    return response.data;
  } catch (error) {
    handleApiError(error, `Failed to generate ALL Subtasks for work ${workId}`);
  }
};

/**
 * Generates Executable Tasks for ALL Work packages within a specific Stage.
 * Calls the POST /tasks/{task_id}/stages/{stage_id}/works/generate-tasks endpoint.
 * @param {string} taskId - The ID of the task.
 * @param {string} stageId - The ID of the stage.
 * @returns {Promise<Array>} A promise that resolves to the updated list of Work packages for the stage.
 */
export const generateAllTasksForStage = async (taskId, stageId) => {
  try {
    console.log(`Generating ALL executable tasks for task ${taskId}, stage ${stageId}`);
    // POST request to the endpoint for generating tasks for all works in a stage
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/stages/${stageId}/works/generate-tasks`, {});
    console.log(`Executable tasks response for ALL works in stage ${stageId}:`, response.data);
    // Backend returns the updated list of Work packages for the stage
    return response.data;
  } catch (error) {
    handleApiError(error, `Failed to generate ALL Executable Tasks for stage ${stageId}`);
  }
};
