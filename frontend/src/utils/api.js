import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const fetchQueries = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/user-queries`);
    return response.data;
  } catch (error) {
    throw new Error('Failed to fetch queries');
  }
};

export const createQuery = async (query) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/user-queries/`, { query });
    return response.data;
  } catch (error) {
    throw new Error('Failed to create query');
  }
};

export const fetchTaskDetails = async (taskId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/tasks/${taskId}`);
    return response.data;
  } catch (error) {
    throw new Error('Failed to fetch task details');
  }
};

export const updateTaskContext = async (taskId, request) => {
  try {
    // Only include the message in the request body if it's not empty
    const requestBody = request ? request : { "query": "", "answer": "" };
    const response = await axios.put(`${API_BASE_URL}/tasks/${taskId}/context`, requestBody);
    return response.data;
  } catch (error) {
    throw new Error('Failed to update task context');
  }
};

export const deleteTask = async (taskId) => {
  try {
    await axios.delete(`${API_BASE_URL}/tasks/${taskId}`);
  } catch (error) {
    throw new Error('Failed to delete task');
  }
};

export const analyzeTask = async (taskId, isReanalyze = false) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/analyze?reAnalyze=${isReanalyze}`);
    return response.data;
  } catch (error) {
    throw new Error('Failed to analyze task');
  }
};

export const generateApproaches = async (taskId) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/tasks/${taskId}/approaches`);
    return response.data;
  } catch (error) {
    throw new Error('Failed to generate approaches');
  }
};

export const typifyTask = async (taskId, isRetypify = false) => {
  try {
    const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/typify${isRetypify ? '?retypify=true' : ''}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to typify task');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error typifying task:', error);
    throw error;
  }
};

// Add new function
export const clarifyTask = async (taskId, message = null) => {
  try {
    console.log('Sending clarification request:', { taskId, message });
    const response = await axios.post(
      `${API_BASE_URL}/tasks/${taskId}/clarify`, 
      message ? { message: message } : {}  // Изменено здесь
    );
    return response.data;
  } catch (error) {
    throw new Error('Failed to clarify task');
  }
};
