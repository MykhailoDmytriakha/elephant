// src/components/TaskComponents.jsx
import React, { useState } from 'react';
import { Clock, CheckCircle2, AlertCircle, Send, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';
import { getStateColor, getReadableState } from '../constants/taskStates';

export const StatusBadge = ({ state }) => {
  const getStatusIcon = () => {
    const stateNumber = parseInt(state?.split('.')[0]);
    if (state?.includes('12.')) return <CheckCircle2 className="w-4 h-4" />;
    if (state?.includes('1.')) return <Clock className="w-4 h-4" />;
    if (stateNumber >= 9) return <CheckCircle2 className="w-4 h-4" />;
    return <Clock className="w-4 h-4" />;
  };

  return (
    <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full border ${getStateColor(state)}`}>
      {getStatusIcon()}
      <span className="text-sm font-medium">{getReadableState(state)}</span>
    </div>
  );
};

export const InfoCard = ({ title, children, className = '' }) => (
  <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
    <h2 className="text-lg font-semibold text-gray-900 mb-4">{title}</h2>
    {children}
  </div>
);

export const ChatMessage = ({ message, isUser }) => (
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

export const ContextChat = ({ messages = [], onSendMessage, disabled = false }) => {
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

export const LoadingSpinner = () => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="flex flex-col items-center gap-2">
      <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
      <div className="text-gray-500">Loading...</div>
    </div>
  </div>
);

export const ErrorDisplay = ({ message }) => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="bg-red-50 text-red-700 p-4 rounded-lg max-w-md text-center">
      <AlertCircle className="w-6 h-6 mx-auto mb-2" />
      <p>{message}</p>
    </div>
  </div>
);

export const ConceptBadge = ({ concept }) => (
  <div className="flex items-center gap-2 px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm group hover:bg-blue-100 transition-colors">
    <span>{concept}</span>
    <ExternalLink className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
  </div>
);

export const ThemeBadge = ({ theme }) => (
  <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
    {theme}
  </span>
);

export const ProgressBar = ({ progress }) => (
  <div className="mt-2">
    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
      <div
        className="h-full bg-blue-500 rounded-full transition-all duration-500"
        style={{ width: `${progress}%` }}
      />
    </div>
    <span className="mt-1 text-sm text-gray-600">{progress}% Complete</span>
  </div>
);

export const CollapsibleSection = ({ title, children }) => {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div 
        className="flex justify-between items-center cursor-pointer p-4 border-b border-gray-200"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
        {isExpanded ? <ChevronUp className="w-5 h-5 text-gray-500" /> : <ChevronDown className="w-5 h-5 text-gray-500" />}
      </div>
      {isExpanded && (
        <div className="p-4 transition-all duration-200">
          {children}
        </div>
      )}
    </div>
  );
};
