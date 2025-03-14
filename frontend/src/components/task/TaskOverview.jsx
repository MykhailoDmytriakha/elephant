// src/components/task/TaskOverview.jsx
import React, { useState, useEffect, useMemo } from 'react';
import { MessageCircle, AlertCircle, X, Send, Loader2, Check, RefreshCw } from 'lucide-react';
import { CollapsibleSection, InlineErrorWithRetry } from './TaskComponents';
import { TaskStates } from '../../constants/taskStates';

const ChatMessage = ({ message, isUser }) => (
  <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
    <div className={`max-w-[80%] p-3 rounded-lg ${isUser ? 'bg-blue-600 text-white rounded-br-none' : 'bg-gray-100 text-gray-900 rounded-bl-none'}`}>{message.content || message.message}</div>
  </div>
);

const ContextChat = ({ 
  messages = [], 
  onSendMessage, 
  disabled = false, 
  isLoading = false,
  error = null,
  onRetry = null
}) => {
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
    if (newMessage.trim() && !disabled && !error) {
      onSendMessage(newMessage);
      setNewMessage('');
    }
  };

  // Don't render anything when loading
  if (isLoading) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 mt-4">
      <div className="p-4 max-h-96 overflow-y-auto">
        {/* Removed conditional rendering for empty messages with isLoading since we now return null when loading */}
        <>
          {messages.map((msg, index) => (
            <ChatMessage
              key={index}
              message={msg}
              isUser={msg.role === 'user'}
            />
          ))}
          
          {/* Show error message as a system message in the chat */}
          {error && (
            <div className="flex justify-center mb-4">
              <div className="max-w-[90%] p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-center">
                <AlertCircle className="w-5 h-5 text-red-500 mx-auto mb-2" />
                <p className="mb-2 text-sm font-medium">Error: {error}</p>
                {onRetry && (
                  <button 
                    onClick={onRetry}
                    className="px-3 py-1 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-xs flex items-center gap-1 mx-auto mt-1"
                  >
                    <RefreshCw className="w-3 h-3" />
                    Try Again
                  </button>
                )}
              </div>
            </div>
          )}
        </>
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
            placeholder={disabled ? 'Context gathering completed' : error ? 'Please resolve the error before continuing' : isLoading ? '' : 'Type your message...'}
            className={`flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${disabled || isLoading || error ? 'bg-gray-100' : 'bg-white'}`}
            disabled={disabled || isLoading || error}
          />
          <button
            type="submit"
            disabled={disabled || isLoading || error || !newMessage.trim()}
            className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${disabled || isLoading || error || !newMessage.trim() ? 'bg-gray-300 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 text-white'}`}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  );
};

const ContextQuestionsForm = ({ 
  questions = [], 
  answers = {}, 
  onAnswerChange, 
  onSubmit, 
  isSubmitting = false,
  isLoading = false,
  error = null,
  onRetry = null
}) => {
  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit();
  };

  // Check if all required answers are provided and valid
  const hasAllValidAnswers = () => {
    // First check if all questions have at least one answer
    if (Object.keys(answers).length < questions.length) {
      return false;
    }
    
    // Check each question's answers
    for (const question of questions) {
      if (!question || !question.id) {
        return false; // Invalid question format
      }
      
      const questionAnswers = answers[question.id];
      
      // If no answers are selected for this question
      if (!questionAnswers || (Array.isArray(questionAnswers) && questionAnswers.length === 0)) {
        return false;
      }
      
      // For multi-select, ensure that if "Other" is selected, it has a non-empty value
      if (Array.isArray(questionAnswers)) {
        const hasOtherOption = questionAnswers.some(answer => 
          question.options && !question.options.some(opt => opt.text === answer) && answer !== '');
          
        const hasEmptyOtherOption = questionAnswers.some(answer => answer === '');
        
        if (hasOtherOption && hasEmptyOtherOption) {
          return false;
        }
      }
    }
    
    return true;
  };

  if (isLoading) {
    return null;
  }

  if (questions.length === 0) {
    return null;
  }

  // Calculate if all answers are valid once to use in multiple places
  const allAnswersValid = hasAllValidAnswers();

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 mt-4">
      <div className="p-5">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Context Questions</h3>
        <p className="text-sm text-gray-600 mb-6">
          Please answer the following questions to help us better understand your task's context.
          You may select multiple options where applicable.
        </p>
        
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-start">
              <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 mr-3 flex-shrink-0" />
              <div className="flex-1">
                <h4 className="text-sm font-medium text-red-800 mb-1">Error Submitting Answers</h4>
                <p className="text-sm text-red-700 mb-3">{error}</p>
                {onRetry && (
                  <button 
                    onClick={onRetry}
                    className="px-3 py-1.5 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-sm flex items-center gap-1 w-fit"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    Try Again
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="space-y-6">
            {questions.map((question) => (
              <div key={question.id} className="border border-gray-200 rounded-lg p-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {question.text}
                </label>
                
                {question.options && question.options.length > 0 ? (
                  <div className="space-y-2">
                    {question.options.map((option) => (
                      <div key={option.id} className="flex items-center">
                        <input
                          type="checkbox"
                          id={`${question.id}-${option.id}`}
                          name={question.id}
                          value={option.text}
                          checked={Array.isArray(answers[question.id]) && answers[question.id].includes(option.text)}
                          onChange={(e) => {
                            const currentAnswers = answers[question.id] || [];
                            const newAnswers = Array.isArray(currentAnswers) ? [...currentAnswers] : [currentAnswers].filter(a => a);
                            
                            if (e.target.checked) {
                              // Add the option if it's not already in the array
                              if (!newAnswers.includes(option.text)) {
                                newAnswers.push(option.text);
                              }
                            } else {
                              // Remove the option if it's in the array
                              const index = newAnswers.indexOf(option.text);
                              if (index !== -1) {
                                newAnswers.splice(index, 1);
                              }
                            }
                            
                            onAnswerChange(question.id, newAnswers);
                          }}
                          className="h-4 w-4 text-blue-600 rounded focus:ring-blue-500"
                          disabled={!!error || isSubmitting}
                        />
                        <label
                          htmlFor={`${question.id}-${option.id}`}
                          className="ml-3 block text-sm text-gray-700"
                        >
                          {option.text}
                        </label>
                      </div>
                    ))}
                    
                    <div className="flex items-center mt-4">
                      <input
                        type="checkbox"
                        id={`${question.id}-custom`}
                        name={question.id}
                        checked={
                          Array.isArray(answers[question.id]) && 
                          answers[question.id].some(answer => 
                            !(question.options && question.options.some(opt => opt.text === answer))
                          ) && 
                          answers[question.id].some(answer => answer !== '')
                        }
                        onChange={(e) => {
                          const currentAnswers = answers[question.id] || [];
                          const newAnswers = Array.isArray(currentAnswers) ? [...currentAnswers] : [currentAnswers].filter(a => a);
                          
                          // Find existing "Other" answers (those not matching any option)
                          const otherAnswers = newAnswers.filter(answer => 
                            !(question.options && question.options.some(opt => opt.text === answer)) && answer !== ''
                          );
                          
                          if (e.target.checked) {
                            // Add an empty "Other" placeholder if no other answers exist yet
                            if (otherAnswers.length === 0) {
                              newAnswers.push('');
                            }
                          } else {
                            // Remove all "Other" answers
                            const filteredAnswers = newAnswers.filter(answer => 
                              question.options && question.options.some(opt => opt.text === answer)
                            );
                            onAnswerChange(question.id, filteredAnswers);
                            return;
                          }
                          
                          onAnswerChange(question.id, newAnswers);
                        }}
                        className="h-4 w-4 text-blue-600 rounded focus:ring-blue-500"
                        disabled={!!error || isSubmitting}
                      />
                      <label
                        htmlFor={`${question.id}-custom`}
                        className="ml-3 block text-sm text-gray-700"
                      >
                        Other (specify):
                      </label>
                    </div>
                    
                    {/* Make the custom answer input visible whenever there's at least one "Other" value */}
                    {Array.isArray(answers[question.id]) && 
                     answers[question.id].some(answer => 
                       !(question.options && question.options.some(opt => opt.text === answer))
                     ) && (
                      <div className="ml-6 mt-2 space-y-2">
                        {answers[question.id]
                          .filter(answer => 
                            !(question.options && question.options.some(opt => opt.text === answer))
                          )
                          .map((otherAnswer, index, filteredOtherAnswers) => (
                            <div key={`other-${index}`} className="flex items-center gap-2">
                              <input
                                type="text"
                                value={otherAnswer}
                                onChange={(e) => {
                                  const currentAnswers = [...answers[question.id]];
                                  const otherAnswers = currentAnswers.filter(answer => 
                                    !(question.options && question.options.some(opt => opt.text === answer))
                                  );
                                  
                                  // Replace this specific "Other" value
                                  otherAnswers[index] = e.target.value;
                                  
                                  // Rebuild the complete answers array
                                  const updatedAnswers = [
                                    ...currentAnswers.filter(answer => 
                                      question.options && question.options.some(opt => opt.text === answer)
                                    ),
                                    ...otherAnswers
                                  ];
                                  
                                  onAnswerChange(question.id, updatedAnswers);
                                }}
                                className={`block w-full px-4 py-2 border rounded-md shadow-sm text-sm focus:ring-blue-500 focus:border-blue-500 ${
                                  otherAnswer.trim() === '' 
                                    ? 'border-red-500 bg-red-50' 
                                    : 'border-gray-300'
                                }`}
                                placeholder="Your custom answer"
                                disabled={!!error || isSubmitting}
                                autoFocus={index === filteredOtherAnswers.length - 1}
                              />
                              
                              {/* Add a remove button for each "Other" input */}
                              <button
                                type="button"
                                onClick={() => {
                                  const currentAnswers = [...answers[question.id]];
                                  const otherAnswers = currentAnswers.filter(answer => 
                                    !(question.options && question.options.some(opt => opt.text === answer))
                                  );
                                  
                                  // Remove this specific "Other" value
                                  otherAnswers.splice(index,
                                   1);
                                  
                                  // Rebuild the complete answers array
                                  const updatedAnswers = [
                                    ...currentAnswers.filter(answer => 
                                      question.options && question.options.some(opt => opt.text === answer)
                                    ),
                                    ...otherAnswers
                                  ];
                                  
                                  onAnswerChange(question.id, updatedAnswers);
                                }}
                                className="p-2 text-gray-500 hover:text-red-500"
                                disabled={!!error || isSubmitting}
                              >
                                <X className="w-4 h-4" />
                              </button>
                            </div>
                          ))}
                        
                        {/* Add button to add another "Other" option */}
                        <button
                          type="button"
                          onClick={() => {
                            const currentAnswers = answers[question.id] || [];
                            onAnswerChange(question.id, [...currentAnswers, '']);
                          }}
                          className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
                          disabled={!!error || isSubmitting}
                        >
                          + Add another custom answer
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  <textarea
                    value={Array.isArray(answers[question.id]) ? answers[question.id].join(', ') : (answers[question.id] || '')}
                    onChange={(e) => onAnswerChange(question.id, e.target.value)}
                    rows="3"
                    className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    placeholder="Type your answer here"
                    disabled={!!error || isSubmitting}
                  />
                )}
              </div>
            ))}
          </div>
          
          <div className="mt-6 flex items-center justify-between">
            <div>
              {error && (
                <span className="text-sm text-red-600">Please try again or refresh the page.</span>
              )}
              {!error && !allAnswersValid && (
                <span className="text-sm text-amber-600">
                  {questions.length > Object.keys(answers).length 
                    ? "Please answer all questions before submitting."
                    : "Please provide text for all 'Other' answers or select a different option."}
                </span>
              )}
            </div>
            <button
              type="submit"
              disabled={isSubmitting || !allAnswersValid || !!error}
              className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white ${
                isSubmitting || !allAnswersValid || !!error
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
              }`}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  <Check className="w-4 h-4 mr-2" />
                  Submit Answers
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const TaskOverview = ({ 
  task, 
  followUpQuestion, 
  onSendMessage, 
  onStartContextGathering, 
  isContextGatheringLoading,
  contextQuestions = [],
  contextAnswers = {},
  onAnswerChange,
  onSubmitAnswers,
  isSubmittingAnswers = false,
  error = null
}) => {
  const [isChatVisible, setIsChatVisible] = React.useState(false);
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

  const handleToggleChat = () => {
    // If chat is already visible, just hide it
    if (isChatVisible) {
      setIsChatVisible(false);
      return;
    }
    
    // Always toggle visibility, regardless of error state
    setIsChatVisible(true);
    
    // Only start context gathering if there's no error
    if (!task.is_context_sufficient && !error) {
      onStartContextGathering();
    }
  };

  const handleRetry = () => {
    // Reset any error state and retry context gathering
    onStartContextGathering();
  };

  // Don't automatically close chat on error - let user see the error in context
  // We'll just disable the inputs

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
          </div>
        </div>

        {(!task.is_context_sufficient || task.state === TaskStates.CONTEXT_GATHERING) && (
          <div className={`${error ? 'bg-red-50 border-red-200' : 'bg-yellow-50 border-yellow-200'} border rounded-lg p-4`}>
            <div className="flex items-start gap-3">
              <AlertCircle className={`w-5 h-5 ${error ? 'text-red-600' : 'text-yellow-600'} mt-0.5`} />
              <div className="flex-1">
                <h4 className={`text-sm font-medium ${error ? 'text-red-800' : 'text-yellow-800'}`}>
                  {error ? 'Error Gathering Context' : 'Additional Context Needed'}
                </h4>
                {error && <p className="text-sm text-red-700 mt-1 mb-2">{error}</p>}
                
                <div className="flex flex-wrap gap-2 mt-3">
                  {error ? (
                    <button
                      onClick={handleRetry}
                      disabled={isContextGatheringLoading || isSubmittingAnswers}
                      className="inline-flex items-center gap-2 px-4 py-2 bg-red-100 text-red-800 hover:bg-red-200 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isContextGatheringLoading ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin" />
                        </>
                      ) : (
                        <>
                          <RefreshCw className="w-5 h-5" />
                          <span>Try Again</span>
                        </>
                      )}
                    </button>
                  ) : (
                    <>
                      {contextQuestions.length === 0 && (
                        <button
                          onClick={handleToggleChat}
                          disabled={isContextGatheringLoading || isSubmittingAnswers}
                          className="inline-flex items-center gap-2 px-4 py-2 bg-yellow-100 text-yellow-800 hover:bg-yellow-200 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {isContextGatheringLoading ? (
                            <>
                              <Loader2 className="w-5 h-5 animate-spin" />
                              <span>Getting questions to clarify context...</span>
                            </>
                          ) : isChatVisible ? (
                            <>
                              <X className="w-5 h-5" />
                              <span>Hide Conversation</span>
                            </>
                          ) : (
                            <>
                              {/* <MessageCircle className="w-5 h-5" /> */}
                              <span>Provide Additional Context</span>
                            </>
                          )}
                        </button>
                      )}
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Show the batch questions if available and no error */}
        {contextQuestions.length > 0 && (
          <ContextQuestionsForm
            questions={contextQuestions}
            answers={contextAnswers}
            onAnswerChange={onAnswerChange}
            onSubmit={onSubmitAnswers}
            isSubmitting={isSubmittingAnswers}
            isLoading={isContextGatheringLoading}
            error={error}
            onRetry={handleRetry}
          />
        )}

        {/* Only show chat if there's no contextQuestions, not loading, and visible */}
        {isChatVisible && !isContextGatheringLoading && contextQuestions.length === 0 && (
          <ContextChat
            messages={chatMessages}
            onSendMessage={handleSendMessage}
            disabled={task.is_context_sufficient || isMessagePending || error}
            isLoading={isContextGatheringLoading}
            error={error}
            onRetry={handleRetry}
          />
        )}
      </div>
    </CollapsibleSection>
  );
};

export default TaskOverview;
