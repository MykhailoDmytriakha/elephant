/**
 * Utility functions for task scope functionality
 */

/**
 * Format a group ID to display name
 * @param {string} group - Group ID to format (what, why, who, etc.)
 * @returns {string} Display name for the group
 */
export const formatGroupName = (group) => {
    return group === 'what' ? 'What' :
           group === 'why' ? 'Why' :
           group === 'who' ? 'Who' :
           group === 'where' ? 'Where' :
           group === 'when' ? 'When' :
           group === 'how' ? 'How' : group;
};

/**
 * Find the next unanswered group
 * @param {Array} GROUPS - All available groups
 * @param {Array} completedGroups - Groups that have been completed
 * @returns {string|null} Next unanswered group or null if all completed
 */
export const findNextUnansweredGroup = (GROUPS, completedGroups) => {
    for (const group of GROUPS) {
        if (!completedGroups.includes(group)) {
            return group;
        }
    }
    return null; // All groups are completed
}; 