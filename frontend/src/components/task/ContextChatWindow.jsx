import React, { useState } from 'react';
import { X, Send } from 'lucide-react';
import { InfoCard } from './TaskComponents';

const ChatMessage = ({ message, isUser }) => (
  <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
    <div
      className={`max-w-[80%] p-3 rounded-lg ${
        isUser 
          ? 'bg-blue-600 text-white rounded-br-none' 
          : 'bg-gray-100 text-gray-900 rounded-bl-none'
      }`}
    >
      {message.content || message.message}
    </div>
  </div>
);

const ContextChat = ({ messages = [], onSendMessage, disabled = false }) => {
  const [newMessage, setNewMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (newMessage.trim()) {
      onSendMessage(newMessage);
      setNewMessage('');
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-4 max-h-96 overflow-y-auto">
        {messages.map((msg, index) => (
          <ChatMessage
            key={index}
            message={msg}
            isUser={msg.role === 'user'}
          />
        ))}
      </div>
      
      <form onSubmit={handleSubmit} className="border-t border-gray-200 p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder={disabled ? "Context gathering completed" : "Type your message..."}
            className={`flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              disabled ? 'bg-gray-100' : 'bg-white'
            }`}
            disabled={disabled}
          />
          <button
            type="submit"
            disabled={disabled || !newMessage.trim()}
            className={`px-4 py-2 rounded-lg transition-colors flex items-center justify-center ${
              disabled || !newMessage.trim()
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  );
};

export default function ContextChatWindow({ 
  isOpen,
  messages,
  onSendMessage,
  onClose,
  isContextSufficient 
}) {
  if (!isOpen) return null;

  return (
    <InfoCard title={
      <div className="flex justify-between items-center">
        <span>Context Discussion</span>
        <button 
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>
    }>
      <ContextChat 
        messages={messages}
        onSendMessage={onSendMessage}
        disabled={isContextSufficient}
      />
    </InfoCard>
  );
}

export { ContextChat, ChatMessage };
