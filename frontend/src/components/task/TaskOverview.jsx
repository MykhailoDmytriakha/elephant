// src/components/task/TaskOverview.jsx
import React, { useState, useEffect, useMemo } from 'react';
import { MessageCircle, AlertCircle, X, Send } from 'lucide-react';
import { CollapsibleSection } from './TaskComponents';
import { TaskStates } from '../../constants/taskStates';

const ChatMessage = ({ message, isUser }) => (
  <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
    <div className={`max-w-[80%] p-3 rounded-lg ${isUser ? 'bg-blue-600 text-white rounded-br-none' : 'bg-gray-100 text-gray-900 rounded-bl-none'}`}>{message.content || message.message}</div>
  </div>
);

const ContextChat = ({ messages = [], onSendMessage, disabled = false }) => {
  const [newMessage, setNewMessage] = useState('');
  const messagesEndRef = React.useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (newMessage.trim() && !disabled) {
      onSendMessage(newMessage);
      setNewMessage('');
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 mt-4">
      <div className="p-4 max-h-96 overflow-y-auto">
        {messages.map((msg, index) => (
          <ChatMessage
            key={index}
            message={msg}
            isUser={msg.role === 'user'}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form
        onSubmit={handleSubmit}
        className="border-t border-gray-200 p-4"
      >
        <div className="flex gap-2">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder={disabled ? 'Context gathering completed' : 'Type your message...'}
            className={`flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${disabled ? 'bg-gray-100' : 'bg-white'}`}
            disabled={disabled}
          />
          <button
            type="submit"
            disabled={disabled || !newMessage.trim()}
            className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${disabled || !newMessage.trim() ? 'bg-gray-300 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 text-white'}`}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  );
};

const TaskOverview = ({ task, followUpQuestion, onSendMessage }) => {
  const [isChatVisible, setIsChatVisible] = React.useState(!task.is_context_sufficient);
  const [localMessages, setLocalMessages] = useState([]);
  const [isMessagePending, setIsMessagePending] = useState(false);

  // Combine server messages with local pending messages
  const chatMessages = useMemo(() => {
    const serverMessages = [
      ...(task?.user_interaction || [])
        .map((interaction) => [
          { role: 'assistant', content: interaction.query },
          { role: 'user', content: interaction.answer },
        ])
        .flat(),
      ...(followUpQuestion ? [{ role: 'assistant', content: followUpQuestion }] : []),
    ];

    // Only add local messages that aren't yet in server messages
    const pendingMessages = localMessages.filter((localMsg) => !serverMessages.some((serverMsg) => serverMsg.content === localMsg.content && serverMsg.role === localMsg.role));

    return [...serverMessages, ...pendingMessages];
  }, [task?.user_interaction, followUpQuestion, localMessages]);

  // Reset local messages when task is updated
  useEffect(() => {
    if (!isMessagePending) {
      setLocalMessages([]);
    }
  }, [task, isMessagePending]);

  const handleSendMessage = async (message) => {
    try {
      setIsMessagePending(true);
      // Immediately add the message to local state
      setLocalMessages((prev) => [...prev, { role: 'user', content: message }]);

      // Send to server
      await onSendMessage(message);
    } catch (error) {
      // If there's an error, remove the message from local state
      setLocalMessages((prev) => prev.filter((msg) => msg.content !== message));
      // Could add error handling here if needed
    } finally {
      setIsMessagePending(false);
    }
  };

  return (
    <CollapsibleSection title="Overview">
      <div className="space-y-4">
        {task.sub_level > 0 && (
          <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 mb-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-200 text-blue-700 text-sm font-medium">{task.sub_level}</span>
              <span className="text-sm text-blue-700 font-medium">Subtask Level</span>
            </div>
            {task.contribution_to_parent_task && (
              <div className="text-sm text-blue-800">
                <span className="font-medium">Contribution to Parent Task:</span>
                <p className="mt-1">{task.contribution_to_parent_task}</p>
              </div>
            )}
          </div>
        )}

        <div>
          <h3 className="text-sm font-medium text-gray-500">Description</h3>
          <p className="mt-1 text-gray-900">{task.short_description}</p>
        </div>

        {task.task && (
          <div>
            <h3 className="text-sm font-medium text-gray-500">Task</h3>
            <p className="mt-1 text-gray-900 whitespace-pre-line">{task.task}</p>
          </div>
        )}

        {task.level && (
          <div>
            <h3 className="text-sm font-medium text-gray-500">Level</h3>
            <p className="mt-1 text-gray-900">{task.level}</p>
          </div>
        )}

        {task.eta_to_complete && (
          <div>
            <h3 className="text-sm font-medium text-gray-500">ETA to Complete</h3>
            <p className="mt-1 text-gray-900">{task.eta_to_complete}</p>
          </div>
        )}

        <div>
          <h3 className="text-sm font-medium text-gray-500">Context</h3>
          <div className="flex items-start justify-between gap-4">
            <p className="mt-1 text-gray-900 flex-grow whitespace-pre-line">{task.context || 'No context provided'}</p>
            {task.is_context_sufficient && (
              <button
                onClick={() => setIsChatVisible(!isChatVisible)}
                className="inline-flex items-center gap-1 px-3 py-1.5 text-sm bg-gray-50 text-gray-600 rounded-md hover:bg-gray-100 transition-colors"
              >
                <MessageCircle className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        {(!task.is_context_sufficient || task.state === TaskStates.CONTEXT_GATHERING) && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-yellow-800">Additional Context Needed</h4>
                <button
                  onClick={() => setIsChatVisible(!isChatVisible)}
                  className="mt-3 inline-flex items-center gap-2 px-4 py-2 bg-yellow-100 text-yellow-800 rounded-lg hover:bg-yellow-200 transition-colors"
                >
                  {isChatVisible ? (
                    <>
                      <X className="w-5 h-5" />
                      <span>Hide Conversation</span>
                    </>
                  ) : (
                    <>
                      <MessageCircle className="w-5 h-5" />
                      <span>Continue Conversation</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {isChatVisible && (
          <ContextChat
            messages={chatMessages}
            onSendMessage={handleSendMessage}
            disabled={task.is_context_sufficient || isMessagePending}
          />
        )}
      </div>
    </CollapsibleSection>
  );
};

export default TaskOverview;
