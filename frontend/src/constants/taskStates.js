// src/constants/taskStates.js
export const TaskStates = {
  NEW: "1. New",
  CONTEXT_GATHERING: "2. Context Gathering",
  CONTEXT_GATHERED: "3. Context Gathered",
  TASK_FORMATION: "3.5. Task Formation",
  IFR_GENERATED: "4. IFR Generated",
  REQUIREMENTS_GENERATED: "5. Requirements Defined",
  ANALYSIS: "6. Analysis",
  TYPIFY: "7. Typify",
  CLARIFYING: "8. Clarifying",
  CLARIFICATION_COMPLETE: "9. Clarification Complete",
  APPROACH_FORMATION: "10. Approach Formation",
  METHOD_SELECTION: "11. Method Selection",
  DECOMPOSITION: "12. Decomposition",
  METHOD_APPLICATION: "13. Method Application",
  SOLUTION_DEVELOPMENT: "14. Solution Development",
  EVALUATION: "15. Evaluation",
  INTEGRATION: "16. Integration",
  OUTPUT_GENERATION: "17. Output Generation",
  COMPLETED: "18. Completed"
};

  export const getStateNumber = (state) => {
    return parseInt(state?.split('.')[0]);
  };
  
  // Helper function to get state color
  export const getStateColor = (state) => {
    const stateNumber = parseInt(state?.split('.')[0]);
    
    if (state === TaskStates.COMPLETED) {
      return 'bg-green-100 text-green-700 border-green-200';
    }
    if (state === TaskStates.NEW) {
      return 'bg-gray-100 text-gray-700 border-gray-200';
    }
    // States 2-4 are early stages
    if (stateNumber >= 2 && stateNumber <= 4) {
      return 'bg-blue-100 text-blue-700 border-blue-200';
    }
    // States 5-8 are middle stages
    if (stateNumber >= 5 && stateNumber <= 8) {
      return 'bg-purple-100 text-purple-700 border-purple-200';
    }
    // States 9-11 are final stages
    if (stateNumber >= 9 && stateNumber <= 11) {
      return 'bg-yellow-100 text-yellow-700 border-yellow-200';
    }
    
    return 'bg-gray-100 text-gray-700 border-gray-200';
  };
  
  // Helper function to get readable state name
  export const getReadableState = (state) => {
    return state?.split('. ')[1] || 'Unknown';
  };
