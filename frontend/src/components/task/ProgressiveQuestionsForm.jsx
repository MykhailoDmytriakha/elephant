import React from 'react';
import { AlertCircle, Loader2, RefreshCw, X } from 'lucide-react';

/**
 * A form that displays questions progressively and allows the user to answer them
 */
const ProgressiveQuestionsForm = ({
  questions = [],
  answers = {},
  onAnswerChange,
  onSubmit,
  isSubmitting = false,
  error = null,
  onRetry,
  isForceRefresh = false
}) => {
  // Debug log to see what's coming in
  console.log('ProgressiveQuestionsForm received questions:', questions);
  console.log('Current answers:', answers);

  if (!questions || questions.length === 0) {
    return (
      <div className="p-4 border rounded-md">
        <p className="text-gray-500">No questions available. Click "Generate Questions" to start the context gathering process.</p>
      </div>
    );
  }

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit();
  };

  const handleAnswerChange = (questionId, value) => {
    onAnswerChange(questionId, value);
  };

  // Check if all questions have valid answers
  const allAnswered = questions.every(q => {
    const answer = answers[q.id];
    
    // If there are options, answer should be an array with at least one item
    if (q.options && Array.isArray(q.options) && q.options.length > 0) {
      return Array.isArray(answer) && answer.length > 0 && !answer.some(a => a === '');
    }
    
    // Otherwise, it should be a non-empty string
    return answer && typeof answer === 'string' && answer.trim() !== '';
  });

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Force Mode Banner */}
      {isForceRefresh && (
        <div className="flex items-center p-3 mb-4 border-l-4 border-blue-500 bg-blue-50">
          <RefreshCw className="text-blue-600 w-5 h-5 mr-2" />
          <div>
            <p className="font-medium text-blue-700">Context Refresh In Progress</p>
            <p className="text-sm text-blue-600">
              You're refreshing your task's context. All previous context will be replaced with the new information.
            </p>
          </div>
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="p-3 border border-red-200 bg-red-50 rounded-md flex items-start">
          <AlertCircle className="w-5 h-5 text-red-500 mr-2 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-red-700 font-medium">Error</p>
            <p className="text-sm text-red-600">{error}</p>
            {onRetry && (
              <button 
                type="button"
                onClick={onRetry}
                className="mt-2 px-3 py-1.5 text-sm bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 rounded-md"
              >
                Try Again
              </button>
            )}
          </div>
        </div>
      )}

      {/* Questions list */}
      <div className="space-y-6">
        {questions.map((question, index) => (
          <div key={question.id} className="p-4 border rounded-md bg-white">
            <div className="mb-2 flex items-center">
              <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded-full mr-2">
                {index + 1}/{questions.length}
              </span>
              <h3 className="text-gray-900 font-medium">{question.question || question.text}</h3>
            </div>
            
            <div className="mt-3">
              {/* If question has options, show checkboxes */}
              {question.options && Array.isArray(question.options) && question.options.length > 0 ? (
                <div className="space-y-2">
                  {/* List of predefined options */}
                  {question.options.map((option, optIndex) => {
                    // Handle both object format {id, text} and string format
                    const optionId = option.id || `option-${index}-${optIndex}`;
                    const optionText = option.text || option;
                    
                    return (
                      <div key={optionId} className="flex items-center">
                        <input
                          type="checkbox"
                          id={`${question.id}-${optionId}`}
                          name={question.id}
                          value={optionText}
                          checked={Array.isArray(answers[question.id]) && answers[question.id].includes(optionText)}
                          onChange={(e) => {
                            const currentAnswers = answers[question.id] || [];
                            const newAnswers = Array.isArray(currentAnswers) ? [...currentAnswers] : [currentAnswers].filter(a => a);
                            
                            if (e.target.checked) {
                              // Add the option if it's not already in the array
                              if (!newAnswers.includes(optionText)) {
                                handleAnswerChange(question.id, [...newAnswers, optionText]);
                              }
                            } else {
                              // Remove the option if it's in the array
                              handleAnswerChange(
                                question.id, 
                                newAnswers.filter(text => text !== optionText)
                              );
                            }
                          }}
                          className="h-4 w-4 text-blue-600 rounded focus:ring-blue-500"
                          disabled={isSubmitting}
                        />
                        <label
                          htmlFor={`${question.id}-${optionId}`}
                          className="ml-3 block text-gray-700"
                        >
                          {optionText}
                        </label>
                      </div>
                    );
                  })}
                  
                  {/* "Other" option */}
                  <div className="flex items-start mt-4">
                    <div className="flex items-center h-5">
                      <input
                        type="checkbox"
                        id={`${question.id}-custom`}
                        checked={Array.isArray(answers[question.id]) && answers[question.id].some(a => 
                          !question.options.some(opt => 
                            (typeof opt === 'string' ? opt : opt.text) === a
                          )
                        )}
                        onChange={(e) => {
                          const currentAnswers = answers[question.id] || [];
                          const newAnswers = Array.isArray(currentAnswers) ? [...currentAnswers] : [currentAnswers].filter(a => a);
                          const customAnswers = newAnswers.filter(a => 
                            !question.options.some(opt => 
                              (typeof opt === 'string' ? opt : opt.text) === a
                            )
                          );
                          
                          if (e.target.checked) {
                            if (customAnswers.length === 0) {
                              handleAnswerChange(question.id, [...newAnswers, '']);
                            }
                          } else {
                            handleAnswerChange(
                              question.id, 
                              newAnswers.filter(a => question.options.some(opt => 
                                (typeof opt === 'string' ? opt : opt.text) === a
                              ))
                            );
                          }
                        }}
                        className="h-4 w-4 text-blue-600 rounded focus:ring-blue-500"
                        disabled={isSubmitting}
                      />
                    </div>
                    <div className="ml-3 text-sm w-full">
                      <label
                        htmlFor={`${question.id}-custom`}
                        className="font-medium text-gray-700"
                      >
                        Other (please specify)
                      </label>
                      
                      {Array.isArray(answers[question.id]) && answers[question.id].some(a => 
                        !question.options.some(opt => 
                          (typeof opt === 'string' ? opt : opt.text) === a
                        )
                      ) && (
                        <div className="mt-2 space-y-2">
                          {answers[question.id].filter(a => 
                            !question.options.some(opt => 
                              (typeof opt === 'string' ? opt : opt.text) === a
                            )
                          ).map((customAnswer, idx) => (
                            <div key={idx} className="flex items-center gap-2">
                              <input
                                type="text"
                                value={customAnswer}
                                onChange={(e) => {
                                  const customAnswers = answers[question.id].filter(a => 
                                    !question.options.some(opt => 
                                      (typeof opt === 'string' ? opt : opt.text) === a
                                    )
                                  );
                                  customAnswers[idx] = e.target.value;
                                  
                                  handleAnswerChange(
                                    question.id, 
                                    [
                                      ...answers[question.id].filter(a => question.options.some(opt => 
                                        (typeof opt === 'string' ? opt : opt.text) === a
                                      )),
                                      ...customAnswers
                                    ]
                                  );
                                }}
                                className={`mt-1 block w-full rounded-md shadow-sm text-sm
                                  ${customAnswer === '' ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'}`}
                                placeholder="Please specify"
                                disabled={isSubmitting}
                              />
                              
                              <button
                                type="button"
                                onClick={() => {
                                  const customAnswers = answers[question.id].filter(a => 
                                    !question.options.some(opt => 
                                      (typeof opt === 'string' ? opt : opt.text) === a
                                    )
                                  );
                                  customAnswers.splice(idx, 1);
                                  
                                  handleAnswerChange(
                                    question.id, 
                                    [
                                      ...answers[question.id].filter(a => question.options.some(opt => 
                                        (typeof opt === 'string' ? opt : opt.text) === a
                                      )),
                                      ...customAnswers
                                    ]
                                  );
                                }}
                                className="p-1 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600"
                                disabled={isSubmitting}
                              >
                                <X className="w-4 h-4" />
                              </button>
                            </div>
                          ))}
                          
                          <button
                            type="button"
                            onClick={() => {
                              handleAnswerChange(question.id, [...(answers[question.id] || []), '']);
                            }}
                            className="flex items-center text-sm text-blue-600 hover:text-blue-700"
                            disabled={isSubmitting}
                          >
                            <span className="text-lg mr-1">+</span> Add another
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                // If no options, show textarea
                <textarea
                  id={question.id}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Type your answer here..."
                  value={answers[question.id] || ''}
                  onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                  disabled={isSubmitting}
                />
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Submit button */}
      <div className="flex justify-between items-center">
        <button
          type="submit"
          disabled={!allAnswered || isSubmitting}
          className={`px-4 py-2 rounded-md text-white ${
            !allAnswered || isSubmitting 
              ? 'bg-gray-400 cursor-not-allowed' 
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {isSubmitting ? (
            <><Loader2 className="w-4 h-4 mr-2 inline animate-spin" />Submitting...</>
          ) : (
            <>Submit Questions</>
          )}
        </button>
        
        <span className="text-sm text-gray-500">
          {questions.filter(q => {
            const answer = answers[q.id];
            if (!answer) return false;
            
            // For option-type questions
            if (q.options && Array.isArray(q.options) && q.options.length > 0) {
              return Array.isArray(answer) && answer.length > 0 && !answer.some(a => a === '');
            }
            
            // For text-type questions
            return typeof answer === 'string' && answer.trim() !== '';
          }).length} of {questions.length} answered
        </span>
      </div>
    </form>
  );
};

export default ProgressiveQuestionsForm; 