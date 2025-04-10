import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send, Brain, RefreshCw, AlertTriangle } from 'lucide-react';

/**
 * A streaming chat component that supports history and reasoning with OpenAI agents
 */
export default function TaskStreamingChat({
  taskId,
  onSendMessage,
  isLoading,
  onResetChat
}) {
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);
  
  const chatEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll when chat content changes
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chatHistory, streamingMessage, error]);

  // Auto-focus the input field when component mounts
  useEffect(() => {
    if (inputRef.current && !isLoading && !isStreaming) {
      inputRef.current.focus();
    }
  }, [isLoading, isStreaming]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim() || isLoading || isStreaming) return;
    
    // Clear any previous error
    setError(null);
    
    // Add user message to chat history
    const userMessage = { role: 'user', content: message };
    setChatHistory(prev => [...prev, userMessage]);
    
    // Clear input and start streaming
    setMessage('');
    setIsStreaming(true);
    setStreamingMessage('');
    
    try {
      // Format chat history for the API
      const messageHistory = chatHistory.map(msg => ({
        role: msg.role,
        content: msg.content
      }));
      
      // Call the parent component's message handler
      await onSendMessage(message, {
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

  const handleResetChat = () => {
    setChatHistory([]);
    setStreamingMessage('');
    setIsStreaming(false);
    setError(null);
    if (onResetChat) onResetChat();
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
      {error && (
        <div className="flex-shrink-0 flex items-center gap-2 bg-red-50 px-4 py-2 border-b border-red-100">
          <AlertTriangle className="w-4 h-4 text-red-500" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}
      
      {/* Chat container */}
      <div 
        ref={chatContainerRef}
        className="flex-grow overflow-y-auto p-4 space-y-4"
      >
        {/* Welcome message if chat is empty */}
        {chatHistory.length === 0 && !streamingMessage && (
          <div className="text-center p-6 text-gray-500">
            <p>Ask any questions about this task or how to implement it.</p>
            <p className="text-sm mt-2">The AI assistant will help with reasoning, suggestions, and implementation details.</p>
          </div>
        )}
        
        {/* Chat history */}
        {chatHistory.map((msg, index) => (
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
                className={`p-3 rounded-lg ${
                  msg.role === 'user' 
                    ? 'bg-blue-100 text-gray-800' 
                    : msg.role === 'system'
                      ? 'bg-red-50 text-red-700'
                      : 'bg-gray-100 text-gray-800'
                }`}
              >
                <pre className="whitespace-pre-wrap font-sans text-sm">
                  {msg.content}
                </pre>
              </div>
            </div>
          </div>
        ))}
        
        {/* Streaming message */}
        {streamingMessage && (
          <div className="flex justify-start">
            <div className="flex items-start gap-2 max-w-[80%]">
              <div className="flex-shrink-0 mt-1">
                <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
                  <Brain className="w-5 h-5 text-purple-600" />
                </div>
              </div>
              <div className="p-3 rounded-lg bg-gray-100 text-gray-800">
                <pre className="whitespace-pre-wrap font-sans text-sm">
                  {streamingMessage}
                  <span className="animate-pulse">▋</span>
                </pre>
              </div>
            </div>
          </div>
        )}
        
        {/* Invisible element for scrolling */}
        <div ref={chatEndRef} />
      </div>
      
      {/* Input area */}
      <div className="flex-shrink-0 border-t border-gray-200 p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type your message..."
            className="flex-grow px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            disabled={isLoading || isStreaming}
          />
          <button
            type="submit"
            disabled={!message.trim() || isLoading || isStreaming}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:bg-purple-300 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isLoading || isStreaming ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            {isLoading || isStreaming ? 'Processing...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  );
} 