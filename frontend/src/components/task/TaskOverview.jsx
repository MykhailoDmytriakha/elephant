// src/components/task/TaskOverview.jsx
import React, { useMemo } from "react";
import { MessageCircle, AlertCircle, X, Send } from "lucide-react";
import { CollapsibleSection } from "./TaskComponents";
import { TaskStates } from "../../constants/taskStates";

const getMessageContent = (message) => {
  if (!message) return '';
  return message.content || message.message || '';
};

const ChatMessage = ({ message, isUser }) => (
  <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
    <div className={`max-w-[80%] p-3 rounded-lg ${
      isUser 
        ? 'bg-blue-600 text-white rounded-br-none' 
        : 'bg-gray-100 text-gray-900 rounded-bl-none'
    }`}>
      {getMessageContent(message)}
    </div>
  </div>
);

const ContextChat = ({ messages = [], onSendMessage, disabled = false }) => {
  const [newMessage, setNewMessage] = React.useState('');
  const messagesEndRef = React.useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (newMessage.trim()) {
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
            className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
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

const TaskOverview = ({
  task,
  followUpQuestion,
  onSendMessage,
}) => {
  //Todo: get isContextSufficient from task

  const [isChatVisible, setIsChatVisible] = React.useState(!task.is_context_sufficient);

  // Move chatMessages logic here
  const chatMessages = useMemo(() => {
    return [
      ...(task?.user_interaction || [])
        .map((interaction) => [
          { role: 'assistant', content: interaction.query },
          { role: 'user', content: interaction.answer },
        ])
        .flat(),
      ...(followUpQuestion ? [{ role: 'assistant', content: followUpQuestion }] : []),
    ];
  }, [task?.user_interaction, followUpQuestion]);

  return (
    <CollapsibleSection title="Overview">
      <div className="space-y-4">
        <div>
          <h3 className="text-sm font-medium text-gray-500">Description</h3>
          <p className="mt-1 text-gray-900">{task.short_description}</p>
        </div>

        {task.task && (
          <div>
            <h3 className="text-sm font-medium text-gray-500">Task</h3>
            <p className="mt-1 text-gray-900">{task.task}</p>
          </div>
        )}

        <div>
          <h3 className="text-sm font-medium text-gray-500">Context</h3>
          <div className="flex items-start justify-between gap-4">
            <p className="mt-1 text-gray-900 flex-grow whitespace-pre-line">
              {task.context || "No context provided"}
            </p>
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

        {(!task.is_context_sufficient ||
          task.state === TaskStates.CONTEXT_GATHERING) && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-yellow-800">
                  Additional Context Needed
                </h4>
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
            onSendMessage={onSendMessage}
            disabled={task.is_context_sufficient}
          />
        )}
      </div>
    </CollapsibleSection>
  );
};

export default TaskOverview;