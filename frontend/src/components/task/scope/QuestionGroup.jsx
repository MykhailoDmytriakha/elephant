// File: frontend/src/components/task/QuestionGroup.jsx

import React, { useState } from 'react';
import { RefreshCcw, ChevronRight, AlertCircle } from 'lucide-react';

export default function QuestionGroup({
  groupId,
  questions,
  onSubmit,
  isSubmitting,
  progress,
  isLastGroup = false
}) {
  // Local state for this group's answers - this will be managed here but passed to parent on submit
  const [answers, setAnswers] = useState({});
  const [errorMessage, setErrorMessage] = useState('');
  
  const handleAnswerChange = (questionId, value, isMultiSelect = false) => {
    setAnswers(prev => {
      if (isMultiSelect) {
        // For multi-select, toggle the value in an array
        const currentValues = Array.isArray(prev[questionId]) ? prev[questionId] : [];
        
        if (currentValues.includes(value)) {
          // Remove if already selected
          return {
            ...prev,
            [questionId]: currentValues.filter(v => v !== value)
          };
        } else {
          // Add if not selected
          return {
            ...prev,
            [questionId]: [...currentValues, value]
          };
        }
      } else {
        // For single custom value or prefilled
        // Special handling for custom text values - preserve the array structure
        // and store the custom text separately
        if (prev[`${questionId}_custom_text`] !== undefined || hasCustomAnswer(questionId)) {
          return {
            ...prev,
            [`${questionId}_custom_text`]: value
          };
        } else {
          return {
            ...prev,
            [questionId]: value
          };
        }
      }
    });
  };

  const isOptionSelected = (questionId, option) => {
    const answer = answers[questionId];
    if (Array.isArray(answer)) {
      return answer.includes(option);
    }
    return false;
  };

  const hasCustomAnswer = (questionId) => {
    const answer = answers[questionId];
    if (Array.isArray(answer)) {
      return answer.includes('__custom__');
    }
    return false;
  };

  const getCustomAnswer = (questionId) => {
    // Get the custom text from the separate storage field
    const customText = answers[`${questionId}_custom_text`];
    if (customText !== undefined) {
      return customText;
    }
    
    // Fallback for backward compatibility
    const answer = answers[questionId];
    if (!Array.isArray(answer) && answer && typeof answer === 'string') {
      return answer;
    }
    return '';
  };

  const validateAnswers = () => {
    // Check if all questions in the current group have been answered
    const unansweredQuestions = questions.filter(
      question => !answers[question.id] || 
                 (Array.isArray(answers[question.id]) && answers[question.id].length === 0) ||
                 (Array.isArray(answers[question.id]) && 
                 answers[question.id].includes('__custom__') && 
                 !getCustomAnswer(question.id))
    );
    
    if (unansweredQuestions.length > 0) {
      const missingItems = unansweredQuestions.map(q => `• ${q.question}`).join('\n');
      setErrorMessage(`Please answer all questions before proceeding. Missing:\n${missingItems}`);
      return false;
    }
    
    setErrorMessage('');
    return true;
  };

  const handleSubmit = () => {
    // Validate answers
    if (!validateAnswers()) {
      return;
    }
    
    // Format answers for API submission
    const formattedAnswers = formatAnswersForSubmission();
    
    // Call the parent component's submit handler
    onSubmit(formattedAnswers);
  };
  
  const formatAnswersForSubmission = () => {
    const formattedAnswers = [];
    
    // Process each question's answer
    questions.forEach(question => {
      const questionId = question.id;
      const answer = answers[questionId];
      
      if (!answer) return;
      
      let formattedAnswer;
      
      if (Array.isArray(answer)) {
        // Handle multi-select answers
        const selectedOptions = answer
          .filter(option => option !== '__custom__')
          .map(option => option);
          
        // Add custom text if present
        if (answer.includes('__custom__')) {
          const customText = getCustomAnswer(questionId);
          if (customText) {
            selectedOptions.push(customText);
          }
        }
        
        formattedAnswer = selectedOptions.join(', ');
      } else {
        // Handle single-select or text answers
        formattedAnswer = answer;
      }
      
      // Add to the formatted answers array
      if (formattedAnswer) {
        formattedAnswers.push({
          question: question.question,
          answer: formattedAnswer
        });
      }
    });
    
    return { answers: formattedAnswers };
  };

  // Helper to get group title
  const getGroupTitle = () => {
    switch (groupId) {
      case 'what': return 'What Questions';
      case 'why': return 'Why Questions';
      case 'who': return 'Who Questions';
      case 'where': return 'Where Questions';
      case 'when': return 'When Questions';
      case 'how': return 'How Questions';
      default: return 'Task Questions';
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg border">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">{getGroupTitle()}</h3>
        <span className="text-sm text-gray-500 font-medium px-3 py-1 bg-gray-100 rounded-full">
          {progress}
        </span>
      </div>
      
      <div className="space-y-6">
        {questions.map(question => (
          <div key={question.id} className="border rounded-lg p-4">
            <h4 className="font-medium mb-2">{question.question}</h4>
            
            <div className="space-y-2">
              {/* Options */}
              {question.options && question.options.length > 0 ? (
                <>
                  {question.options.map(option => (
                    <div key={option} className="p-3 border rounded-md">
                      <label className="flex items-center">
                        <input 
                          type="checkbox" 
                          className="mr-3"
                          checked={isOptionSelected(question.id, option)}
                          onChange={() => handleAnswerChange(question.id, option, true)}
                          disabled={isSubmitting}
                        />
                        <span>{option}</span>
                      </label>
                    </div>
                  ))}
                  
                  {/* Custom option */}
                  <div className="p-3 border rounded-md">
                    <label className="flex items-start">
                      <input 
                        type="checkbox" 
                        className="mt-1 mr-3"
                        checked={hasCustomAnswer(question.id)}
                        onChange={() => handleAnswerChange(question.id, '__custom__', true)}
                        disabled={isSubmitting}
                      />
                      <div className="w-full">
                        <div className="font-medium">Other</div>
                        {hasCustomAnswer(question.id) && (
                          <div className="mt-2">
                            <textarea 
                              className="w-full p-2 border rounded-md" 
                              rows="2"
                              placeholder="Enter your custom response..."
                              value={getCustomAnswer(question.id)}
                              onChange={(e) => handleAnswerChange(question.id, e.target.value, false)}
                              disabled={isSubmitting}
                            />
                          </div>
                        )}
                      </div>
                    </label>
                  </div>
                </>
              ) : (
                // For questions without options, just show a text input
                <div className="p-3 border rounded-md">
                  <textarea 
                    className="w-full p-2 border rounded-md" 
                    rows="3"
                    placeholder="Enter your response..."
                    value={answers[question.id] || ''}
                    onChange={(e) => handleAnswerChange(question.id, e.target.value, false)}
                    disabled={isSubmitting}
                  />
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {errorMessage && (
        <div className="mt-6 mb-4 p-3 bg-red-50 text-red-700 rounded-md flex items-start">
          <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
          <p className="whitespace-pre-line">{errorMessage}</p>
        </div>
      )}
      
      <div className="mt-6 flex justify-end">
        <button
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-300"
        >
          {isSubmitting ? (
            <>
              <RefreshCcw className="w-5 h-5 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              {isLastGroup ? "Complete" : "Save answers"} <ChevronRight className="w-5 h-5" />
            </>
          )}
        </button>
      </div>
    </div>
  );
}