/**
 * Utility functions for handling status display and logic
 * Centralizes status-related functionality to avoid duplication
 */

// Status color mappings for execution statuses
export const getExecutionStatusClasses = (status) => {
  switch (status?.toLowerCase()) {
    case 'completed':
      return 'bg-green-100 text-green-800 border-green-300';
    case 'failed':
      return 'bg-red-100 text-red-800 border-red-300';
    case 'in progress':
      return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    case 'waiting':
      return 'bg-blue-100 text-blue-800 border-blue-300';
    case 'cancelled':
      return 'bg-purple-100 text-purple-800 border-purple-300';
    case 'pending':
    default:
      return 'bg-gray-100 text-gray-700 border-gray-300';
  }
};

// Get border and background classes for different statuses
export const getStatusBorderClasses = (status) => {
  switch (status?.toLowerCase()) {
    case 'completed':
      return 'border-green-400 bg-green-50';
    case 'failed':
      return 'border-red-400 bg-red-50';
    case 'in progress':
      return 'border-yellow-400 bg-yellow-50';
    case 'waiting':
      return 'border-blue-400 bg-blue-50';
    case 'cancelled':
      return 'border-purple-400 bg-purple-50';
    default:
      return 'border-gray-300 bg-gray-50';
  }
};

// Get badge classes for status display
export const getStatusBadgeClasses = (status) => {
  switch (status?.toLowerCase()) {
    case 'completed':
      return 'bg-green-200 text-green-800 border border-green-300';
    case 'failed':
      return 'bg-red-200 text-red-800 border border-red-300';
    case 'in progress':
      return 'bg-yellow-200 text-yellow-800 border border-yellow-300';
    case 'waiting':
      return 'bg-blue-200 text-blue-800 border border-blue-300';
    case 'cancelled':
      return 'bg-purple-200 text-purple-800 border border-purple-300';
    default:
      return 'bg-gray-200 text-gray-700 border border-gray-300';
  }
};

// Format timestamps consistently
export const formatTimestamp = (isoString) => {
  if (!isoString) return null;
  try {
    return new Date(isoString).toLocaleString();
  } catch (error) {
    return 'Invalid date';
  }
};

// Check if any work packages exist in stages
export const checkWorkPackagesExist = (stages) => {
  if (!stages || !Array.isArray(stages)) return false;
  
  return stages.some(stage => 
    stage.work_packages && 
    Array.isArray(stage.work_packages) && 
    stage.work_packages.length > 0
  );
};

// Check if any tasks exist in stages
export const checkTasksExist = (stages) => {
  if (!stages || !Array.isArray(stages)) return false;
  
  return stages.some(stage =>
    stage.work_packages &&
    Array.isArray(stage.work_packages) &&
    stage.work_packages.some(work =>
      work.tasks &&
      Array.isArray(work.tasks) &&
      work.tasks.length > 0
    )
  );
};

// Generate hierarchical numbering for items
export const generateItemNumber = (stageIndex, workIndex = null, taskIndex = null, subtaskIndex = null) => {
  let number = `${stageIndex + 1}`;
  
  if (workIndex !== null) {
    number += `.${workIndex + 1}`;
  }
  
  if (taskIndex !== null) {
    number += `.${taskIndex + 1}`;
  }
  
  if (subtaskIndex !== null) {
    number += `.${subtaskIndex + 1}`;
  }
  
  return number;
};

// Get display name for items with fallbacks
export const getItemDisplayName = (item, fallbackPrefix = 'Item', maxLength = 30) => {
  const name = item.name || item.task_name || item.subtask_name || item.description;
  
  if (!name) {
    return `${fallbackPrefix} ${item.id}`;
  }
  
  if (name.length > maxLength) {
    return name.slice(0, maxLength) + "...";
  }
  
  return name;
}; 