import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send, Brain, RefreshCw, AlertTriangle, Pencil } from 'lucide-react';

/**
 * A streaming chat component that supports history and reasoning with OpenAI agents
 */
export default function TaskStreamingChat({
  taskId,
  onSendMessage,
  isLoading,
  onResetChat,
  // External state management props
  chatHistory: externalChatHistory,
  streamingMessage: externalStreamingMessage,
  error: externalError,
  isStreaming: externalIsStreaming,
  isExternallyManaged = false
}) {
  // Only use these states if not externally managed
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);
  const [editingMessageIndex, setEditingMessageIndex] = useState(null);
  const [editedMessageContent, setEditedMessageContent] = useState('');
  
  // Use the appropriate values based on isExternallyManaged
  const displayChatHistory = isExternallyManaged ? externalChatHistory : chatHistory;
  const displayStreamingMessage = isExternallyManaged ? externalStreamingMessage : streamingMessage;
  const displayError = isExternallyManaged ? externalError : error;
  const displayIsStreaming = isExternallyManaged ? externalIsStreaming : isStreaming;
  
  const chatEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const textareaRef = useRef(null);

  // Function to adjust textarea height
  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'; // Reset height to calculate scrollHeight
      const scrollHeight = textareaRef.current.scrollHeight;
      
      // Calculate height based on line-height and padding (approximate 1.5rem line-height + padding)
      // This needs refinement based on actual CSS
      const lineHeight = parseFloat(getComputedStyle(textareaRef.current).lineHeight);
      const maxHeight = lineHeight * 7; // Max 7 rows
      
      textareaRef.current.style.height = `${Math.min(scrollHeight, maxHeight)}px`;
      textareaRef.current.style.overflowY = scrollHeight > maxHeight ? 'auto' : 'hidden';
    }
  };

  // Adjust height on message change
  useEffect(() => {
    adjustTextareaHeight();
  }, [message]);

  // Process content to handle code blocks with proper formatting and wrapping
  const processContent = (content) => {
    // Replace markdown code blocks with styled divs
    if (!content) return '';
    
    // Escape HTML first to prevent unexpected HTML rendering or XSS
    const escapeHTML = (text) => {
      return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    };
    
    const escapedContent = escapeHTML(content);
    
    // Add specific styling for code blocks
    return escapedContent
      .replace(/```([\s\S]*?)```/g, (match, codeContent) => {
        const formattedCode = codeContent.trim();
        return `<div class="bg-gray-800 text-gray-100 p-2 rounded my-2 overflow-x-auto max-w-full"><code>${formattedCode}</code></div>`;
      })
      .replace(/`([^`]+)`/g, (match, inlineCode) => {
        return `<span class="bg-gray-200 text-gray-800 px-1 rounded font-mono text-xs">${inlineCode}</span>`;
      })
      // Convert line breaks to <br> tags
      .replace(/\n/g, '<br>');
  };

  // Auto-scroll when chat content changes
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [displayChatHistory, displayStreamingMessage, displayError]);

  // Auto-focus the input field when component mounts
  useEffect(() => {
    if (textareaRef.current && !isLoading && !isStreaming) {
      textareaRef.current.focus();
    }
  }, [isLoading, isStreaming]);

  const handleSubmit = async (e) => {
    if (e) e.preventDefault(); // Allow calling without event (e.g., from keydown)
    
    const trimmedMessage = message.trim(); // Trim the message
    if (!trimmedMessage || isLoading || isStreaming) return; // Check trimmed message
    
    // For externally managed state, we just call onSendMessage and let the parent handle state updates
    if (isExternallyManaged) {
      // Clear input and expect parent to handle state
      setMessage('');
      requestAnimationFrame(() => {
        if (textareaRef.current) {
          textareaRef.current.style.height = 'auto';
          textareaRef.current.style.overflowY = 'hidden';
        }
      });
      
      // Format chat history for the API
      const messageHistory = externalChatHistory.map(msg => ({
        role: msg.role,
        content: msg.content
      }));
      
      // Let parent component handle everything
      try {
        await onSendMessage(trimmedMessage, {}, messageHistory);
      } catch (error) {
        console.error('Error sending message:', error);
      }
      
      return;
    }
    
    // Original internal state management (when not externally managed)
    setError(null);
    const userMessage = { role: 'user', content: trimmedMessage };
    setChatHistory(prev => [...prev, userMessage]);
    setMessage('');
    setIsStreaming(true);
    setStreamingMessage('');
    
    // Reset textarea height after sending
    requestAnimationFrame(() => {
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
        textareaRef.current.style.overflowY = 'hidden';
      }
    });
    
    try {
      // Format chat history for the API
      const messageHistory = chatHistory.map(msg => ({
        role: msg.role,
        content: msg.content
      }));
      
      // Call the parent component's message handler
      await onSendMessage(trimmedMessage, { // Send trimmed message
        onChunk: (chunk) => {
          // Check if the chunk contains an error message
          if (chunk.includes('⚠️ Error:')) {
            setError(chunk.replace('⚠️ Error:', '').trim());
          }
          setStreamingMessage(prev => prev + chunk);
        },
        onComplete: (fullResponse) => {
          // Add assistant's response to chat history and clear streaming state
          setChatHistory(prev => [...prev, { role: 'assistant', content: fullResponse }]);
          setStreamingMessage('');
          setIsStreaming(false);
        },
        onError: (err) => {
          console.error('Error in chat response:', err);
          setError(err.message || 'An error occurred while getting a response');
          setIsStreaming(false);
          
          // Add error to chat history
          setChatHistory(prev => [...prev, { 
            role: 'system', 
            content: `Error: ${err.message || 'Failed to get a response'}`
          }]);
        }
      }, messageHistory);
    } catch (error) {
      console.error('Error sending message:', error);
      setError(error.message || 'Failed to send message');
      setChatHistory(prev => [...prev, { 
        role: 'system', 
        content: `Error: ${error.message || 'Failed to get a response'}`
      }]);
      setIsStreaming(false);
    }
  };

  // --- NEW: Handlers for Edit Start/Cancel ---
  const handleEditClick = (index, content) => {
    setEditingMessageIndex(index);
    setEditedMessageContent(content);
    // Optionally focus the textarea after a short delay
    setTimeout(() => {
      const textarea = document.getElementById(`edit-textarea-${index}`);
      if (textarea) textarea.focus();
    }, 50);
  };

  const handleCancelEdit = () => {
    setEditingMessageIndex(null);
    setEditedMessageContent('');
  };
  // --- END: Handlers for Edit Start/Cancel ---

  // --- NEW: Handler for Saving Edit ---
  const handleSaveEdit = async (index) => {
    const trimmedEditedMessage = editedMessageContent.trim();
    if (!trimmedEditedMessage || isLoading || isStreaming) return;

    if (isExternallyManaged) {
      // Calculate the history up to the edited message
      const truncatedHistory = displayChatHistory.slice(0, index).map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      // Reset edit state immediately
      setEditingMessageIndex(null);
      setEditedMessageContent('');

      // Call the parent's onSendMessage with the edited content and truncated history
      // The parent component (AllStagesPage) will handle updating its history and calling the API
      try {
        await onSendMessage(trimmedEditedMessage, {}, truncatedHistory);
      } catch (error) {
        console.error('Error sending edited message:', error);
        // Consider how to display this error - perhaps back to the parent?
      }

    } else {
      // Internal state management (less common for this component now)
      // Update local chat history: replace the message and remove subsequent ones
      const newChatHistory = [ 
          ...chatHistory.slice(0, index), 
          { role: 'user', content: trimmedEditedMessage } 
      ];
      setChatHistory(newChatHistory);

      // Reset edit state
      setEditingMessageIndex(null);
      setEditedMessageContent('');
      setError(null);
      setIsStreaming(true);
      setStreamingMessage('');
      
      // Call the API using the updated local history
      try {
        const messageHistoryForApi = newChatHistory.map(msg => ({ // Use the updated history
          role: msg.role,
          content: msg.content
        }));
        
        await onSendMessage(trimmedEditedMessage, {
          onChunk: (chunk) => {
            if (chunk.includes('⚠️ Error:')) {
              setError(chunk.replace('⚠️ Error:', '').trim());
            }
            setStreamingMessage(prev => prev + chunk);
          },
          onComplete: (fullResponse) => {
            setChatHistory(prev => [...prev, { role: 'assistant', content: fullResponse }]);
            setStreamingMessage('');
            setIsStreaming(false);
          },
          onError: (err) => {
            setError(err.message || 'An error occurred');
            setChatHistory(prev => [...prev, { role: 'system', content: `Error: ${err.message}` }]);
            setIsStreaming(false);
          }
        }, messageHistoryForApi); // Send the correct history
      } catch (error) {
        setError(error.message || 'Failed to send message');
        setChatHistory(prev => [...prev, { role: 'system', content: `Error: ${error.message}` }]);
        setIsStreaming(false);
      }
    }
  };
  // --- END: Handler for Saving Edit ---

  const handleKeyDown = (e) => {
    // Send on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // Prevent default newline behavior
      handleSubmit();
    } 
    // If Shift+Enter, the default behavior (newline) is already handled by the textarea
    // No specific action needed here for Shift+Enter
  };

  const handleResetChat = () => {
    if (isExternallyManaged) {
      // Let parent component handle the reset
      if (onResetChat) onResetChat();
    } else {
      // Handle locally
      setChatHistory([]);
      setStreamingMessage('');
      setIsStreaming(false);
      setError(null);
      if (onResetChat) onResetChat();
    }
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="flex-shrink-0 flex items-center justify-between border-b border-gray-200 px-4 py-3">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-purple-600" />
          <h2 className="font-medium text-gray-800">Task Assistant</h2>
        </div>
        <button 
          onClick={handleResetChat}
          className="text-gray-500 hover:text-gray-700"
          title="Reset conversation"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>
      
      {/* Error message banner if there's an error */}
      {displayError && (
        <div className="flex-shrink-0 flex items-center gap-2 bg-red-50 px-4 py-2 border-b border-red-100">
          <AlertTriangle className="w-4 h-4 text-red-500" />
          <p className="text-sm text-red-700">{displayError}</p>
        </div>
      )}
      
      {/* Chat container */}
      <div 
        ref={chatContainerRef}
        className="flex-grow overflow-y-auto p-4 space-y-4"
        style={{ overflowWrap: 'break-word', wordBreak: 'break-word' }}
      >
        {/* Welcome message if chat is empty */}
        {displayChatHistory.length === 0 && !displayStreamingMessage && (
          <div className="text-center p-6 text-gray-500">
            <p>Ask any questions about this task or how to implement it.</p>
            <p className="text-sm mt-2">The AI assistant will help with reasoning, suggestions, and implementation details.</p>
          </div>
        )}
        
        {/* Chat history */}
        {displayChatHistory.map((msg, index) => (
          <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex items-start gap-2 max-w-[80%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className="flex-shrink-0 mt-1">
                {msg.role === 'user' ? (
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                    <span className="text-blue-600 text-sm font-medium">You</span>
                  </div>
                ) : msg.role === 'system' ? (
                  <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center">
                    <AlertTriangle className="w-5 h-5 text-red-600" />
                  </div>
                ) : (
                  <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
                    <Brain className="w-5 h-5 text-purple-600" />
                  </div>
                )}
              </div>
              <div 
                className={`p-3 rounded-lg ${ msg.role === 'user' ? 'bg-blue-100 text-gray-800' : msg.role === 'system' ? 'bg-red-50 text-red-700' : 'bg-gray-100 text-gray-800' } overflow-hidden max-w-full relative group`}
                style={{ maxWidth: '100%' }}
              >
                {/* --- EDITING VIEW --- */}
                {msg.role === 'user' && editingMessageIndex === index ? (
                  <div className="w-[400px]">
                    <textarea 
                      id={`edit-textarea-${index}`}
                      value={editedMessageContent}
                      onChange={(e) => setEditedMessageContent(e.target.value)}
                      className="w-full p-2 border border-blue-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-transparent resize-y min-h-[60px] text-sm"
                      rows="3"
                    />
                    <div className="flex justify-end gap-2 mt-2">
                      <button 
                        onClick={handleCancelEdit}
                        className="text-xs px-2 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                      >
                        Cancel
                      </button>
                      <button 
                        onClick={() => handleSaveEdit(index)}
                        disabled={!editedMessageContent.trim() || isLoading || displayIsStreaming}
                        className="text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Save & Submit
                      </button>
                    </div>
                  </div>
                ) : (
                  /* --- NORMAL VIEW --- */
                  <div 
                    className="whitespace-pre-wrap font-sans text-sm break-words overflow-x-hidden"
                    style={{ overflowWrap: 'break-word', wordBreak: 'break-word' }}
                    dangerouslySetInnerHTML={{ 
                      __html: msg.role === 'assistant' ? processContent(msg.content) : msg.content 
                    }}
                  />
                )}
                {/* --- Edit Button (Only for User's messages & not currently editing) --- */}
                {msg.role === 'user' && editingMessageIndex !== index && (
                  <button
                    onClick={() => handleEditClick(index, msg.content)}
                    className="absolute top-1 right-1 p-1 text-gray-400 hover:text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Edit message"
                  >
                    <Pencil className="w-3 h-3" />
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
        
        {/* Streaming message */}
        {displayStreamingMessage && (
          <div className="flex justify-start">
            <div className="flex items-start gap-2 max-w-[80%]">
              <div className="flex-shrink-0 mt-1">
                <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
                  <Brain className="w-5 h-5 text-purple-600" />
                </div>
              </div>
              <div className="p-3 rounded-lg bg-gray-100 text-gray-800 overflow-hidden max-w-full">
                <div 
                  className="whitespace-pre-wrap font-sans text-sm break-words overflow-x-hidden"
                  style={{ overflowWrap: 'break-word', wordBreak: 'break-word' }}
                  dangerouslySetInnerHTML={{ 
                    __html: processContent(displayStreamingMessage) 
                  }}
                />
              </div>
            </div>
          </div>
        )}
        
        {/* Invisible element for scrolling */}
        <div ref={chatEndRef} />
      </div>
      
      {/* Input area */}
      <form onSubmit={handleSubmit} className="flex-shrink-0 border-t border-gray-200 p-4">
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
            className="w-full p-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none overflow-auto min-h-[45px]"
            style={{ maxHeight: '200px' }}
            disabled={isLoading || displayIsStreaming}
          />
          <button
            type="submit"
            className={`absolute right-3 bottom-3 rounded-full p-1 ${
              !message.trim() || isLoading || displayIsStreaming
                ? 'text-gray-400 cursor-not-allowed'
                : 'text-purple-600 hover:text-purple-800'
            }`}
            disabled={!message.trim() || isLoading || displayIsStreaming}
          >
            {isLoading || displayIsStreaming ? (
              <RefreshCw className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
        <div className="text-xs text-gray-500 mt-1 flex justify-between">
          <span>Enter to send, Shift+Enter for new line</span>
          {displayIsStreaming && <span className="text-purple-600">AI is responding...</span>}
        </div>
      </form>
    </div>
  );
} 