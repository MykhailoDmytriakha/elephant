/**
 * Predefined color palette for consistent theming across the application
 */
export const COLOR_PALETTE = {
  BLUE: '#3b82f6',      // blue-500
  PURPLE: '#8b5cf6',    // purple-500
  GREEN: '#22c55e',     // green-500
  AMBER: '#f59e0b',     // amber-500
  ROSE: '#f43f5e',      // rose-500
  INDIGO: '#6366f1',    // indigo-500
  CYAN: '#06b6d4',      // cyan-500
  EMERALD: '#10b981',   // emerald-500
  ORANGE: '#f97316',    // orange-500
  PINK: '#ec4899'       // pink-500
};

/**
 * Array of colors for easy iteration
 */
export const COLORS_ARRAY = Object.values(COLOR_PALETTE);

/**
 * Get color based on an ID with consistent mapping
 * @param {string|number} id - The ID to map to a color
 * @returns {string} - Hex color code
 */
export const getColorById = (id) => {
  const numericId = typeof id === 'string' ? parseInt(id, 10) : id;
  if (isNaN(numericId)) {
    return COLOR_PALETTE.BLUE; // Default color
  }
  return COLORS_ARRAY[(numericId - 1) % COLORS_ARRAY.length];
};

/**
 * Get edge color based on stage ID (alias for backward compatibility)
 * @param {string|number} stageId - The stage ID
 * @returns {string} - Hex color code
 */
export const getEdgeColor = (stageId) => getColorById(stageId);

/**
 * Get status color based on status type
 * @param {string} status - Status type
 * @returns {string} - Hex color code
 */
export const getStatusColor = (status) => {
  const statusColors = {
    'pending': COLOR_PALETTE.AMBER,
    'in-progress': COLOR_PALETTE.BLUE,
    'completed': COLOR_PALETTE.GREEN,
    'failed': COLOR_PALETTE.ROSE,
    'blocked': COLOR_PALETTE.PURPLE,
    'ready-for-validation': COLOR_PALETTE.CYAN
  };
  
  return statusColors[status?.toLowerCase()] || COLOR_PALETTE.BLUE;
};

/**
 * Generate a lighter version of a color for backgrounds
 * @param {string} color - Hex color code
 * @param {number} opacity - Opacity value (0-1)
 * @returns {string} - RGBA color string
 */
export const getColorWithOpacity = (color, opacity = 0.1) => {
  // Convert hex to RGB
  const r = parseInt(color.slice(1, 3), 16);
  const g = parseInt(color.slice(3, 5), 16);
  const b = parseInt(color.slice(5, 7), 16);
  
  return `rgba(${r}, ${g}, ${b}, ${opacity})`;
};

/**
 * Get contrasting text color (black or white) for a given background color
 * @param {string} backgroundColor - Hex color code
 * @returns {string} - 'black' or 'white'
 */
export const getContrastingTextColor = (backgroundColor) => {
  // Convert hex to RGB
  const r = parseInt(backgroundColor.slice(1, 3), 16);
  const g = parseInt(backgroundColor.slice(3, 5), 16);
  const b = parseInt(backgroundColor.slice(5, 7), 16);
  
  // Calculate relative luminance
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  
  return luminance > 0.5 ? 'black' : 'white';
}; 