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