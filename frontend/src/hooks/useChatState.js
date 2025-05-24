import { useState, useCallback, useRef, useEffect } from 'react';

/**
 * Custom hook for managing chat state and functionality
 * Extracts chat logic from components for better modularity
 */
export const useChatState = (initialHistory = []) => {
  const [chatHistory, setChatHistory] = useState(initialHistory);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);
  const [editingMessageIndex, setEditingMessageIndex] = useState(null);
  const [editedMessageContent, setEditedMessageContent] = useState('');
  const [isSavingEdit, setIsSavingEdit] = useState(false);

  // Add a message to chat history
  const addMessage = useCallback((message) => {
    setChatHistory(prev => [...prev, message]);
  }, []);

  // Update streaming message
  const updateStreamingMessage = useCallback((chunk) => {
    setStreamingMessage(prev => prev + chunk);
  }, []);

  // Clear streaming message
  const clearStreamingMessage = useCallback(() => {
    setStreamingMessage('');
  }, []);

  // Start streaming
  const startStreaming = useCallback(() => {
    setIsStreaming(true);
    setError(null);
    clearStreamingMessage();
  }, [clearStreamingMessage]);

  // Stop streaming
  const stopStreaming = useCallback(() => {
    setIsStreaming(false);
  }, []);

  // Set error state
  const setErrorState = useCallback((errorMessage) => {
    setError(errorMessage);
    setIsStreaming(false);
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Reset entire chat
  const resetChat = useCallback(() => {
    setChatHistory([]);
    clearStreamingMessage();
    setIsStreaming(false);
    setError(null);
    setEditingMessageIndex(null);
    setEditedMessageContent('');
    setIsSavingEdit(false);
  }, [clearStreamingMessage]);

  // Start editing a message
  const startEditingMessage = useCallback((index, content) => {
    setEditingMessageIndex(index);
    setEditedMessageContent(content);
  }, []);

  // Cancel editing
  const cancelEditing = useCallback(() => {
    setEditingMessageIndex(null);
    setEditedMessageContent('');
    setIsSavingEdit(false);
  }, []);

  // Update edited message content
  const updateEditedContent = useCallback((content) => {
    setEditedMessageContent(content);
  }, []);

  // Save edited message
  const saveEditedMessage = useCallback(async (saveFunction) => {
    if (editingMessageIndex === null) return;
    
    setIsSavingEdit(true);
    try {
      if (saveFunction) {
        await saveFunction(editingMessageIndex, editedMessageContent);
      }
      
      // Update the message in history
      setChatHistory(prev => {
        const newHistory = [...prev];
        newHistory[editingMessageIndex] = {
          ...newHistory[editingMessageIndex],
          content: editedMessageContent
        };
        return newHistory;
      });
      
      cancelEditing();
    } catch (error) {
      setErrorState(error.message || 'Failed to save edit');
    } finally {
      setIsSavingEdit(false);
    }
  }, [editingMessageIndex, editedMessageContent, cancelEditing, setErrorState]);

  return {
    // State
    chatHistory,
    streamingMessage,
    isStreaming,
    error,
    editingMessageIndex,
    editedMessageContent,
    isSavingEdit,
    
    // Actions
    addMessage,
    updateStreamingMessage,
    clearStreamingMessage,
    startStreaming,
    stopStreaming,
    setErrorState,
    clearError,
    resetChat,
    startEditingMessage,
    cancelEditing,
    updateEditedContent,
    saveEditedMessage,
    setChatHistory
  };
}; 