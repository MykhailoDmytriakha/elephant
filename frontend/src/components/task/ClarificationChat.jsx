import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send } from 'lucide-react';
import { CollapsibleSection } from './TaskComponents';

export default function ClarificationChat({
  isOpen,
  onSendMessage,
  currentQuestion,
  isLoading,
  clarificationData,
  allQuestionsAnswered
}) {
  const [message, setMessage] = useState('');
  const chatEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const inputRef = useRef(null); // Add this new ref for the input element

  // Add this debug logging to help track the data
  useEffect(() => {
    console.log('Clarification Data:', clarificationData);
    console.log('Current Question:', currentQuestion);
    console.log('Answers:', clarificationData?.answers);
  }, [clarificationData, currentQuestion]);

  // Replace the previous useEffects with this single one
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [clarificationData, currentQuestion, message]); // Scroll when content changes or message is sent

  // Add new useEffect for auto-focus
  useEffect(() => {
    if (currentQuestion && !allQuestionsAnswered && !isLoading && inputRef.current) {
      inputRef.current.focus();
    }
  }, [currentQuestion, allQuestionsAnswered, isLoading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (message.trim() && currentQuestion && !allQuestionsAnswered) {
      await onSendMessage(message);
      setMessage('');
    }
  };

  if (!isOpen) return null;

  // Update how we calculate progress and indices
  const totalQuestions = clarificationData?.questions?.length || 0;
  const answers = clarificationData?.answers || {};
  const answeredQuestions = Object.keys(answers).length;
  const currentIndex = clarificationData?.questions?.findIndex(
    q => q.question_id === currentQuestion?.question_id
  ) || 0;
  const progress = totalQuestions > 0 ? (answeredQuestions / totalQuestions) * 100 : 0;

  return (
    <div className="relative bg-white rounded-lg shadow-sm border p-4">
      {/* Instructions */}
      <div className="mb-4 bg-gray-50 border border-gray-200 rounded-lg p-3">
        <p className="text-sm text-gray-600">
          Please answer the following questions to help us better understand your needs and generate more accurate approaches.
          Your answers will help tailor the solution to your specific requirements.
        </p>
      </div>

      {/* Progress bar */}
      <div className="mb-4">
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
        <div className="flex justify-between text-sm text-gray-600 mt-1">
          <p>
            Question {currentIndex + 1} of {totalQuestions}
          </p>
          <p>
            Progress: {Math.round(progress)}%
          </p>
        </div>
      </div>

      {/* Chat container with max height and scrolling */}
      <div 
        ref={chatContainerRef}
        className="space-y-4 max-h-[600px] overflow-y-auto mb-4 pr-2"
      >
        {/* Previous answers */}
        {answeredQuestions > 0 && (
          <div className="space-y-4">
            {clarificationData?.questions?.map((question, index) => {
              const answer = answers[question.question_id];
              // Only show questions that have been answered
              if (!answer) return null;
              
              return (
                <div key={question.question_id} className="space-y-2">
                  {/* Question */}
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0">
                      <MessageCircle className="w-6 h-6 text-gray-400" />
                    </div>
                    <div className="flex-grow">
                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-gray-800">{question.question}</p>
                        <div className="mt-2 space-y-1 text-sm text-gray-600">
                          {question.purpose && (
                            <p>
                              <span className="font-medium">Purpose:</span> {question.purpose}
                            </p>
                          )}
                          {question.expected_value && (
                            <p>
                              <span className="font-medium">Expected:</span> {question.expected_value}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                  {/* Answer */}
                  <div className="flex items-start gap-3 pl-12">
                    <div className="flex-grow">
                      <div className="bg-blue-50 rounded-lg p-3">
                        <p className="text-gray-800">{answer}</p>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Current question */}
        {currentQuestion && !allQuestionsAnswered && (
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0">
              <MessageCircle className="w-6 h-6 text-blue-500" />
            </div>
            <div className="flex-grow">
              <div className="bg-blue-50 rounded-lg p-3">
                <p className="text-gray-800">{currentQuestion.question}</p>
                <div className="mt-2 space-y-1 text-sm text-gray-600">
                  {currentQuestion.purpose && (
                    <p>
                      <span className="font-medium">Purpose:</span> {currentQuestion.purpose}
                    </p>
                  )}
                  {currentQuestion.expected_value && (
                    <p>
                      <span className="font-medium">Expected:</span> {currentQuestion.expected_value}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Invisible element for scrolling */}
        <div ref={chatEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          ref={inputRef}
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder={allQuestionsAnswered ? "All questions have been answered" : "Type your answer..."}
          className="flex-grow px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          disabled={isLoading || allQuestionsAnswered}
        />
        <button
          type="submit"
          disabled={!message.trim() || isLoading || allQuestionsAnswered}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-300 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <Send className="w-4 h-4" />
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
}
