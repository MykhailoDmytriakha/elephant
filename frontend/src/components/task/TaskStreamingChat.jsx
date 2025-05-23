import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send, Brain, RefreshCw, AlertTriangle, Pencil, RotateCcw, Check, X, Edit3, Keyboard, Copy } from 'lucide-react';

/**
 * A streaming chat component that supports history and reasoning with OpenAI agents
 * Now using server-side session management via Google ADK
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
  const [isSavingEdit, setIsSavingEdit] = useState(false);
  const [dismissedError, setDismissedError] = useState(false);
  const [isCopySuccess, setIsCopySuccess] = useState(false);
  
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

  // Handle global escape key to cancel editing
  useEffect(() => {
    const handleGlobalEscape = (e) => {
      if (e.key === 'Escape' && editingMessageIndex !== null) {
        handleCancelEdit();
      }
    };

    if (editingMessageIndex !== null) {
      document.addEventListener('keydown', handleGlobalEscape);
      return () => document.removeEventListener('keydown', handleGlobalEscape);
    }
  }, [editingMessageIndex]);

  // Reset dismissed error when a new error appears
  useEffect(() => {
    if (displayError) {
      setDismissedError(false);
    }
  }, [displayError]);

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
      
      // Let parent component handle everything - no need to send message_history anymore
      // since we're using server-side session management
      try {
        // Note: We're no longer passing messageHistory since it's tracked on the server
        await onSendMessage(trimmedMessage, {}, []);
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
      // Call the parent component's message handler
      await onSendMessage(trimmedMessage, { 
        onChunk: (chunk) => {
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
          
          // Only add non-session errors to chat history to avoid duplication
          if (!err.message?.includes('Session not found') && !err.message?.includes('session')) {
            setChatHistory(prev => [...prev, { 
              role: 'system', 
              content: err.message || 'Failed to get a response'
            }]);
          }
        }
      }, []);  // Empty history, since we're using server-side session management
    } catch (error) {
      console.error('Error sending message:', error);
      setError(error.message || 'Failed to send message');
      
      // Only add non-session errors to chat history to avoid duplication
      if (!error.message?.includes('Session not found') && !error.message?.includes('session')) {
        setChatHistory(prev => [...prev, { 
          role: 'system', 
          content: error.message || 'Failed to get a response'
        }]);
      }
      setIsStreaming(false);
    }
  };

  // --- Handlers for Edit Start/Cancel ---
  const handleEditClick = (index, content) => {
    setEditingMessageIndex(index);
    setEditedMessageContent(content);
    // Focus and auto-resize the textarea after a short delay
    setTimeout(() => {
      const textarea = document.getElementById(`edit-textarea-${index}`);
      if (textarea) {
        textarea.focus();
        // Auto-resize textarea to content
        textarea.style.height = 'auto';
        textarea.style.height = Math.max(60, Math.min(200, textarea.scrollHeight)) + 'px';
      }
    }, 50);
  };

  const handleCancelEdit = () => {
    setEditingMessageIndex(null);
    setEditedMessageContent('');
  };

  // Auto-resize edit textarea
  const handleEditTextareaChange = (e, index) => {
    setEditedMessageContent(e.target.value);
    // Auto-resize
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = Math.max(60, Math.min(200, textarea.scrollHeight)) + 'px';
  };

  // Handle keyboard shortcuts in edit mode
  const handleEditKeyDown = (e, index) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSaveEdit(index);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleCancelEdit();
    }
  };

  // --- Handler for Saving Edit ---
  const handleSaveEdit = async (index) => {
    const trimmedEditedMessage = editedMessageContent.trim();
    if (!trimmedEditedMessage || isLoading || isStreaming || isSavingEdit) return;

    setIsSavingEdit(true);

    if (isExternallyManaged) {
      try {
        // Reset edit state immediately
        setEditingMessageIndex(null);
        setEditedMessageContent('');

        // Call the parent's onSendMessage with the edited content
        await onSendMessage(trimmedEditedMessage, {}, []);
      } catch (error) {
        console.error('Error sending edited message:', error);
        // Restore edit state on error
        setEditingMessageIndex(index);
        setEditedMessageContent(trimmedEditedMessage);
      } finally {
        setIsSavingEdit(false);
      }
    } else {
      // Internal state management (less common now)
      try {
        const newChatHistory = [ 
            ...chatHistory.slice(0, index), 
            { role: 'user', content: trimmedEditedMessage } 
        ];
        setChatHistory(newChatHistory);

        // Reset edit state
        setEditingMessageIndex(null);
        setEditedMessageContent('');

        // Make a new request with the edited message
        setIsStreaming(true);
        setStreamingMessage('');
        setError(null);
        
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
            console.error('Error in chat response:', err);
            setError(err.message || 'An error occurred while getting a response');
            setIsStreaming(false);
            
            // Only add non-session errors to chat history to avoid duplication
            if (!err.message?.includes('Session not found') && !err.message?.includes('session')) {
              setChatHistory(prev => [...prev, { 
                role: 'system', 
                content: err.message || 'Failed to get a response'
              }]);
            }
          }
        }, []);  // Empty history, using server-side session management
      } catch (error) {
        console.error('Error sending edited message:', error);
        setError(error.message || 'Failed to send edited message');
        
        // Only add non-session errors to chat history to avoid duplication
        if (!error.message?.includes('Session not found') && !error.message?.includes('session')) {
          setChatHistory(prev => [...prev, { 
            role: 'system', 
            content: error.message || 'Failed to get a response'
          }]);
        }
        setIsStreaming(false);
        // Restore edit state on error
        setEditingMessageIndex(index);
        setEditedMessageContent(trimmedEditedMessage);
      } finally {
        setIsSavingEdit(false);
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // Prevent newline
      handleSubmit();
    }
  };

  const handleResetChat = () => {
    if (isExternallyManaged) {
      if (onResetChat) onResetChat();
    } else {
      setChatHistory([]);
      setStreamingMessage('');
      setError(null);
      setIsStreaming(false);
    }
  };

  const handleCopyChatHistory = async () => {
    const historyToCopy = displayChatHistory
      .filter(msg => {
        // Filter out session error messages from chat if they're already shown in banner
        if (msg.role === 'system' && displayError && 
            (msg.content.includes('Session not found') || msg.content.includes('session'))) {
          return false;
        }
        return true;
      });

    if (historyToCopy.length === 0 && !displayStreamingMessage) {
      // Nothing to copy
      return;
    }

    let chatText = "# Chat History\n\n";
    
    historyToCopy.forEach((msg, index) => {
      const role = msg.role === 'user' ? 'You' : msg.role === 'assistant' ? 'Assistant' : 'System';
      const content = msg.content.replace(/^Error:\s*/i, '').replace(/^⚠️\s*Error:\s*/i, '');
      chatText += `**${role}:**\n${content}\n\n`;
    });

    // Add streaming message if present
    if (displayStreamingMessage) {
      chatText += `**Assistant (streaming):**\n${displayStreamingMessage}\n\n`;
    }

    chatText += `---\n*Chat copied on ${new Date().toLocaleString()}*`;

    try {
      await navigator.clipboard.writeText(chatText);
      
      // Show success feedback
      setIsCopySuccess(true);
      setTimeout(() => setIsCopySuccess(false), 2000);
      
      console.log('Chat history copied to clipboard');
    } catch (error) {
      console.error('Failed to copy chat history:', error);
      // Fallback: create a temporary textarea for older browsers
      try {
        const tempTextarea = document.createElement('textarea');
        tempTextarea.value = chatText;
        document.body.appendChild(tempTextarea);
        tempTextarea.select();
        document.execCommand('copy');
        document.body.removeChild(tempTextarea);
        
        // Show success feedback for fallback too
        setIsCopySuccess(true);
        setTimeout(() => setIsCopySuccess(false), 2000);
        
        console.log('Chat history copied using fallback method');
      } catch (fallbackError) {
        console.error('Failed to copy using fallback method:', fallbackError);
      }
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
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopyChatHistory}
            disabled={displayChatHistory.length === 0 && !displayStreamingMessage}
            className={`transition-colors ${
              isCopySuccess 
                ? 'text-green-600' 
                : 'text-gray-500 hover:text-gray-700 disabled:text-gray-300 disabled:cursor-not-allowed'
            }`}
            title={
              isCopySuccess 
                ? "Copied!" 
                : displayChatHistory.length === 0 && !displayStreamingMessage 
                  ? "No chat history to copy" 
                  : "Copy full chat history"
            }
          >
            {isCopySuccess ? (
              <Check className="w-4 h-4" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>
          <button 
            onClick={handleResetChat}
            className="text-gray-500 hover:text-gray-700 transition-colors"
            title="Reset conversation"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* Error message banner if there's an error */}
      {displayError && !dismissedError && (
        <div className="flex-shrink-0 flex items-center gap-2 bg-amber-50 px-4 py-2 border-b border-amber-100">
          <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0" />
          <div className="flex-grow text-sm text-amber-700 break-words">
            {displayError.includes('Session not found') || displayError.includes('session') ? 
              'Your chat session has expired. Please reset to continue.' :
              (displayError.startsWith('⚠️ Error:') ? displayError.substring(10) : displayError)
            }
          </div>
          <div className="flex items-center gap-2">
            {(displayError.includes('Session not found') || displayError.includes('session')) && (
              <button
                onClick={handleResetChat}
                className="px-2 py-1 text-xs bg-amber-100 text-amber-700 rounded hover:bg-amber-200 transition-colors"
                title="Reset conversation to fix session issues"
              >
                Reset Chat
              </button>
            )}
            <button
              onClick={() => setDismissedError(true)}
              className="p-1 text-amber-500 hover:text-amber-700 hover:bg-amber-100 rounded transition-colors"
              title="Dismiss"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
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
            <div className="w-16 h-16 bg-gradient-to-br from-purple-100 to-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Brain className="w-8 h-8 text-purple-600" />
            </div>
            <h3 className="text-lg font-medium text-gray-700 mb-2">Hi! I'm your Task Assistant 👋</h3>
            <p className="text-gray-600 mb-1">Ask me anything about this task or how to implement it.</p>
            <p className="text-sm text-gray-500">I can help with reasoning, suggestions, and implementation details.</p>
          </div>
        )}
        
        {/* Chat history */}
        {displayChatHistory
          .filter(msg => {
            // Hide session error messages from chat if they're already shown in banner
            if (msg.role === 'system' && displayError && 
                (msg.content.includes('Session not found') || msg.content.includes('session'))) {
              return false;
            }
            return true;
          })
          .map((msg, index) => (
          <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex items-start gap-2 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : ''} ${editingMessageIndex === index ? 'max-w-[95%]' : ''}`}>
              <div className="flex-shrink-0 mt-1">
                {msg.role === 'user' ? (
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                    <span className="text-blue-600 text-sm font-medium">You</span>
                  </div>
                ) : msg.role === 'system' ? (
                  <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center">
                    <AlertTriangle className="w-5 h-5 text-amber-600" />
                  </div>
                ) : (
                  <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
                    <Brain className="w-5 h-5 text-purple-600" />
                  </div>
                )}
              </div>
              <div 
                className={`p-3 rounded-lg ${ msg.role === 'user' ? 'bg-blue-100 text-gray-800 hover:bg-blue-200' : msg.role === 'system' ? 'bg-amber-50 text-amber-700 border border-amber-200' : 'bg-gray-100 text-gray-800' } overflow-hidden max-w-full relative group transition-all duration-200 ${editingMessageIndex === index ? 'bg-gradient-to-br from-blue-50 to-white border-2 border-blue-300 shadow-lg' : msg.role === 'user' ? 'hover:shadow-sm' : ''}`}
                style={{ maxWidth: editingMessageIndex === index ? '100%' : '100%', marginTop: '8px', marginRight: msg.role === 'user' ? '8px' : '0' }}
              >
                {/* --- EDITING VIEW --- */}
                {msg.role === 'user' && editingMessageIndex === index ? (
                  <div className="w-full max-w-lg animate-in fade-in-0 duration-300">
                    {/* Edit header */}
                    <div className="flex items-center justify-between mb-3 pb-2 border-b border-blue-200">
                      <div className="flex items-center gap-2">
                        <Edit3 className="w-4 h-4 text-blue-600 animate-pulse" />
                        <span className="text-sm font-medium text-blue-800">Editing message</span>
                      </div>
                      <div className="flex items-center gap-1 text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded-full">
                        <Keyboard className="w-3 h-3" />
                        <span>Ctrl+Enter to save</span>
                      </div>
                    </div>
                    
                    {/* Edit textarea */}
                    <div className="relative">
                      <textarea 
                        id={`edit-textarea-${index}`}
                        value={editedMessageContent}
                        onChange={(e) => handleEditTextareaChange(e, index)}
                        onKeyDown={(e) => handleEditKeyDown(e, index)}
                        className="w-full p-3 border-2 border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none transition-all duration-200 text-sm bg-gradient-to-br from-blue-50 to-white focus:from-blue-100 focus:to-blue-50"
                        placeholder="Edit your message..."
                        rows="3"
                        style={{ minHeight: '60px', maxHeight: '200px' }}
                      />
                      
                      {/* Character counter */}
                      <div className="absolute bottom-2 right-2 text-xs text-gray-400 bg-white px-1 rounded shadow-sm">
                        {editedMessageContent.length}
                      </div>
                    </div>
                    
                    {/* Action buttons */}
                    <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
                      <div className="text-xs text-gray-500 flex items-center gap-1">
                        <span>💡</span>
                        <span>Use markdown for formatting</span>
                      </div>
                      <div className="flex gap-2">
                        <button 
                          onClick={handleCancelEdit}
                          disabled={isSavingEdit}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-50 transition-all duration-200 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <X className="w-3.5 h-3.5" />
                          Cancel
                        </button>
                        <button 
                          onClick={() => handleSaveEdit(index)}
                          disabled={!editedMessageContent.trim() || isLoading || displayIsStreaming || isSavingEdit}
                          className="flex items-center gap-1.5 px-4 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md"
                        >
                          {isSavingEdit ? (
                            <>
                              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                              Saving...
                            </>
                          ) : (
                            <>
                              <Check className="w-3.5 h-3.5" />
                              Save & Send
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  /* --- NORMAL VIEW --- */
                  <div className="relative">
                    <div 
                      className="whitespace-pre-wrap font-sans text-sm break-words overflow-x-hidden leading-relaxed"
                      style={{ overflowWrap: 'break-word', wordBreak: 'break-word' }}
                      dangerouslySetInnerHTML={{ 
                        __html: msg.role === 'assistant' ? processContent(msg.content) : 
                                msg.role === 'system' ? msg.content.replace(/^Error:\s*/i, '').replace(/^⚠️\s*Error:\s*/i, '') : 
                                msg.content 
                      }}
                    />
                    {/* Subtle edit indicator */}
                    {msg.role === 'user' && (
                      <div className="absolute inset-0 rounded-lg border-2 border-transparent group-hover:border-blue-200 transition-all duration-200 pointer-events-none opacity-0 group-hover:opacity-30"></div>
                    )}
                  </div>
                )}
                {/* --- Edit Button (Only for User's messages & not currently editing) --- */}
                {msg.role === 'user' && editingMessageIndex !== index && (
                  <div className="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100 transition-all duration-300 transform group-hover:scale-100 scale-95">
                    <button
                      onClick={() => handleEditClick(index, msg.content)}
                      className="flex items-center justify-center w-7 h-7 bg-white text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-full shadow-md hover:shadow-lg border border-gray-200 hover:border-blue-300 transition-all duration-200 hover:scale-110 active:scale-95"
                      title="Edit message"
                    >
                      <Pencil className="w-3 h-3" />
                    </button>
                  </div>
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