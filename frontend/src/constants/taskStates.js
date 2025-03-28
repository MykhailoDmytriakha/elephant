// frontend/src/constants/taskStates.js

// Match the values exactly with the backend TaskState enum
export const TaskStates = {
  NEW: "1. New",
  CONTEXT_GATHERING: "2. Context Gathering",
  CONTEXT_GATHERED: "3. Context Gathered",
  TASK_FORMATION: "3.5. Task Formation",
  IFR_GENERATED: "4. IFR Generated",
  REQUIREMENTS_GENERATED: "5. Requirements Defined",
  NETWORK_PLAN_GENERATED: "6. Network (Stages) Plan Generated",
  HIERARCHICAL_DECOMPOSITION_COMPLETE: "7. Hierarchical Decomposition Complete",
  COMPLETED: "8. Completed",
};

// Create a map for efficient lookup of state properties
const stateProperties = {
  [TaskStates.NEW]: { number: 1, color: 'bg-gray-100 text-gray-700 border-gray-200', readable: 'New' },
  [TaskStates.CONTEXT_GATHERING]: { number: 2, color: 'bg-blue-100 text-blue-700 border-blue-200', readable: 'Context Gathering' },
  [TaskStates.CONTEXT_GATHERED]: { number: 3, color: 'bg-blue-100 text-blue-700 border-blue-200', readable: 'Context Gathered' },
  [TaskStates.TASK_FORMATION]: { number: 3.5, color: 'bg-cyan-100 text-cyan-700 border-cyan-200', readable: 'Task Formation' },
  [TaskStates.IFR_GENERATED]: { number: 4, color: 'bg-indigo-100 text-indigo-700 border-indigo-200', readable: 'IFR Generated' },
  [TaskStates.REQUIREMENTS_GENERATED]: { number: 5, color: 'bg-purple-100 text-purple-700 border-purple-200', readable: 'Requirements Defined' },
  [TaskStates.NETWORK_PLAN_GENERATED]: { number: 6, color: 'bg-purple-100 text-purple-700 border-purple-200', readable: 'Network Plan Generated' },
  [TaskStates.HIERARCHICAL_DECOMPOSITION_COMPLETE]: { number: 7, color: 'bg-yellow-100 text-yellow-700 border-yellow-200', readable: 'Decomposition Complete' },
  [TaskStates.COMPLETED]: { number: 8, color: 'bg-green-100 text-green-700 border-green-200', readable: 'Completed' },
};

const defaultState = { number: 0, color: 'bg-gray-100 text-gray-700 border-gray-200', readable: 'Unknown' };

// Helper function to get state number (more robust)
export const getStateNumber = (state) => {
  return stateProperties[state]?.number ?? defaultState.number;
};

// Helper function to get state color (more robust)
export const getStateColor = (state) => {
  return stateProperties[state]?.color ?? defaultState.color;
};

// Helper function to get readable state name (more robust)
export const getReadableState = (state) => {
  // Handle potential null/undefined state gracefully
  if (!state) {
    return defaultState.readable;
  }
  // Find the readable name from the map, fallback to parsing if not found (legacy support)
  return stateProperties[state]?.readable ?? state.split('. ')[1] ?? defaultState.readable;
};

// Function to check if a state represents completion or a late stage
export const isLateStage = (state) => {
    const stateNum = getStateNumber(state);
    // Consider stages 6 and onwards as late stages
    return stateNum >= 6;
};