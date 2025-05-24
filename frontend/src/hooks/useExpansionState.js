import { useState, useCallback } from 'react';

/**
 * Custom hook for managing expansion state of hierarchical items
 * Provides consistent toggle functionality across components
 */
export const useExpansionState = (initialState = {}, defaultExpanded = false) => {
  const [expandedItems, setExpandedItems] = useState(initialState);

  // Toggle a single item's expansion state
  const toggleItem = useCallback((itemId) => {
    setExpandedItems(prev => ({
      ...prev,
      [itemId]: !prev[itemId]
    }));
  }, []);

  // Set expansion state for a specific item
  const setItemExpanded = useCallback((itemId, isExpanded) => {
    setExpandedItems(prev => ({
      ...prev,
      [itemId]: isExpanded
    }));
  }, []);

  // Expand all items from a list
  const expandAll = useCallback((itemIds) => {
    const newState = {};
    itemIds.forEach(id => {
      newState[id] = true;
    });
    setExpandedItems(prev => ({ ...prev, ...newState }));
  }, []);

  // Collapse all items
  const collapseAll = useCallback(() => {
    setExpandedItems({});
  }, []);

  // Check if an item is expanded
  const isExpanded = useCallback((itemId) => {
    return expandedItems[itemId] ?? defaultExpanded;
  }, [expandedItems, defaultExpanded]);

  // Initialize expansion state for a list of items
  const initializeExpansion = useCallback((itemIds, expanded = defaultExpanded) => {
    const newState = {};
    itemIds.forEach(id => {
      newState[id] = expanded;
    });
    setExpandedItems(newState);
  }, [defaultExpanded]);

  return {
    expandedItems,
    toggleItem,
    setItemExpanded,
    expandAll,
    collapseAll,
    isExpanded,
    initializeExpansion,
    setExpandedItems
  };
}; 