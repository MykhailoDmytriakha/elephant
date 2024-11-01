import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

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

export const updateTaskContext = async (taskId, request) => {
  try {
    // Only include the message in the request body if it's not empty
    const requestBody = request ? request : { "query": "", "answer": "" };
    const response = await axios.put(`${API_BASE_URL}/tasks/${taskId}/context`, requestBody);
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to update task context');
  }
};

export const deleteTask = async (taskId) => {
  try {
    await axios.delete(`${API_BASE_URL}/tasks/${taskId}`);
  } catch (error) {
    handleApiError(error, 'Failed to delete task');
  }
};

export const formulate_task = async (taskId) => {
  try {
      const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/formulate`);
      return response.data;
  } catch (error) {
      throw new Error('Failed to formulate task');
  }
};

export const analyzeTask = async (taskId, isReanalyze = false) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/analyze?reAnalyze=${isReanalyze}`);
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to analyze task');
  }
};

export const generateApproaches = async (taskId) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/approaches`);
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to generate approaches');
  }
};

export const typifyTask = async (taskId, isRetypify = false) => {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/tasks/${taskId}/typify${isRetypify ? '?reTypify=true' : ''}`
    );
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to typify task');
  }
};

export const clarifyTask = async (taskId, message = null) => {
  try {
    console.log('Sending clarification request:', { taskId, message });
    const response = await axios.post(
      `${API_BASE_URL}/tasks/${taskId}/clarify`,
      message ? { message: message } : {}
    );
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to clarify task');
  }
};

export const decomposeTask = async (taskId, selecedApproaches, isRedecompose = false) => {
  // verify that selecedApproach has tools, methods, frameworks
  if (!selecedApproaches.analytical_tools || !selecedApproaches.practical_methods || !selecedApproaches.frameworks) {
    throw new Error('Selected approach must include tools, methods, and frameworks');
  }
  try {
    const response = await axios.post(
      `${API_BASE_URL}/tasks/${taskId}/decompose${isRedecompose ? '?redecompose=true' : ''}`,
      selecedApproaches
    );
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to decompose task');
  }
};