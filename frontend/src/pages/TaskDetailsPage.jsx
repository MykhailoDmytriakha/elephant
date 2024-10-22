// src/pages/TaskDetailsPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, AlertCircle, Trash2, ExternalLink, RefreshCcw, Send, MessageCircle, X, BarChart2 } from 'lucide-react';
import { 
  StatusBadge, 
  InfoCard, 
  ContextChat, 
  LoadingSpinner,
  ErrorDisplay,
  ConceptBadge,
  ThemeBadge,
  ProgressBar
} from '../components/TaskComponents';
import { fetchTaskDetails, updateTaskContext, deleteTask, analyzeTask } from '../utils/api';
import { TaskStates } from '../constants/taskStates';

export default function TaskDetailsPage() {
  const { taskId } = useParams();
  const navigate = useNavigate();
  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [followUpQuestion, setFollowUpQuestion] = useState(null);
  const [isContextSufficient, setIsContextSufficient] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const loadTask = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchTaskDetails(taskId);
      console.log("Task data:", data);
      setTask(data);
      setIsContextSufficient(data.is_context_sufficient);
      if (!data.is_context_sufficient) {
        setIsChatOpen(true);
        const contextUpdate = await updateTaskContext(taskId);
        console.log("Context update:", contextUpdate);
        setFollowUpQuestion(contextUpdate.follow_up_question);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTask();
  }, [taskId]);

  const handleBack = () => {
    navigate('/');
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      try {
        await deleteTask(taskId);
        navigate('/');
      } catch (error) {
        setError('Failed to delete task: ' + error.message);
      }
    }
  };

  const handleSendMessage = async (message) => {
    try {
      const updatedContext = await updateTaskContext(taskId, { "query": followUpQuestion, "answer": message });
      console.log("Updated context:", updatedContext);
      
      // Handle the case when context becomes sufficient
      if (updatedContext.is_context_sufficient && !updatedContext.follow_up_question) {
        setIsContextSufficient(true);
        setFollowUpQuestion(null);
        // setIsChatOpen(false);  // Close the chat window
        
        // Refresh the task data to get the latest state
        const updatedTask = await fetchTaskDetails(taskId);
        setTask(updatedTask);
      } else {
        // Handle normal follow-up questions
        setFollowUpQuestion(updatedContext.follow_up_question);
        const updatedTask = await fetchTaskDetails(taskId);
        setTask(updatedTask);
      }
    } catch (error) {
      setError('Failed to send message: ' + error.message);
    }
  };

  const toggleChatWindow = () => {
    setIsChatOpen(prevState => !prevState);
  };

  const handleCloseChatWindow = () => {
    setIsChatOpen(false);
  };

  const handleOpenChatWindow = () => {
    setIsChatOpen(true);
  };

  // Update this part to correctly handle the user interaction and follow-up question
  const chatMessages = [
    ...(task?.user_interaction || []).map(interaction => [
      { role: 'assistant', content: interaction.query },
      { role: 'user', content: interaction.answer }
    ]).flat(),
    ...(followUpQuestion ? [{ role: 'assistant', content: followUpQuestion }] : [])
  ];

  const handleAnalyze = async () => {
    try {
      setIsAnalyzing(true);
      await analyzeTask(taskId);
      await loadTask(); // Reload task to get updated analysis
    } catch (err) {
      setError('Failed to analyze task: ' + err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const renderAnalysisSection = () => {
    if (!isContextSufficient) {
      return null;
    }

    // Check if analysis is empty object or null/undefined
    if (!task.analysis || Object.keys(task.analysis).length === 0) {
      return (
        <InfoCard title="Analysis">
          <div className="text-center py-8">
            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-300"
            >
              {isAnalyzing ? (
                <>
                  <RefreshCcw className="w-5 h-5 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <BarChart2 className="w-5 h-5" />
                  Start Analysis
                </>
              )}
            </button>
          </div>
        </InfoCard>
      );
    }

    return (
      <InfoCard title="Analysis Results">
        <div className="space-y-6">
          {/* Keep existing sentiment distribution section if needed */}
          {task.analysis.sentiment_distribution && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-4">Sentiment Distribution</h3>
              <div className="grid grid-cols-3 gap-4">
                {Object.entries(task.analysis.sentiment_distribution).map(([sentiment, percentage]) => (
                  <div key={sentiment}>
                    <div className="text-2xl font-semibold">{percentage}%</div>
                    <div className="text-gray-500 capitalize">{sentiment}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Parameters and Constraints */}
          {task.analysis.parameters_constraints && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Parameters & Constraints</h3>
              <p className="text-gray-700">{task.analysis.parameters_constraints}</p>
            </div>
          )}

          {/* Available Resources */}
          {task.analysis.available_resources?.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Available Resources</h3>
              <ul className="list-disc list-inside space-y-1">
                {task.analysis.available_resources.map((resource, index) => (
                  <li key={index} className="text-gray-700">{resource}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Required Resources */}
          {task.analysis.required_resources?.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Required Resources</h3>
              <ul className="list-disc list-inside space-y-1">
                {task.analysis.required_resources.map((resource, index) => (
                  <li key={index} className="text-gray-700">{resource}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Ideal Final Result */}
          {task.analysis.ideal_final_result && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Ideal Final Result</h3>
              <p className="text-gray-700">{task.analysis.ideal_final_result}</p>
            </div>
          )}

          {/* Missing Information */}
          {task.analysis.missing_information?.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Missing Information</h3>
              <ul className="list-disc list-inside space-y-1">
                {task.analysis.missing_information.map((info, index) => (
                  <li key={index} className="text-gray-700">{info}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Complexity */}
          {task.analysis.complexity && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Complexity Level</h3>
              <p className="text-gray-700">{task.analysis.complexity}</p>
            </div>
          )}

          {/* Keep existing themes and insights sections if needed */}
          {/* ... existing theme and insights code ... */}
        </div>
      </InfoCard>
    );
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay message={error} />;
  if (!task) return <ErrorDisplay message="Task not found" />;

  const isContextGatheringCompleted = task.state !== TaskStates.CONTEXT_GATHERING && task.is_context_sufficient;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <button 
                onClick={handleBack}
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <h1 className="text-2xl font-bold text-gray-900">Task Details</h1>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-gray-600 mr-2">Task State:</span>
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                <span className="w-2 h-2 mr-2 rounded-full bg-blue-400"></span>
                {task.state}
              </span>
              <button 
                onClick={handleDelete}
                className="text-red-600 hover:text-red-700 flex items-center gap-2"
              >
                <Trash2 className="w-5 h-5" />
                Delete
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="col-span-2 space-y-6">
            <InfoCard title="Overview">
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
                  <p className="mt-1 text-gray-900">{task.context || 'No context provided'}</p>
                </div>
                {(!isContextSufficient || task.state === TaskStates.CONTEXT_GATHERING) && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                      <div>
                        <h4 className="text-sm font-medium text-yellow-800">Additional Context Needed</h4>
                        <p className="text-sm text-yellow-700">What specific time period should we analyze?</p>
                        <button
                          onClick={toggleChatWindow}
                          className="mt-3 inline-flex items-center gap-2 px-4 py-2 bg-yellow-100 text-yellow-800 rounded-lg hover:bg-yellow-200 transition-colors"
                        >
                          {isChatOpen ? (
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
              </div>
            </InfoCard>

            {isChatOpen && (
              <InfoCard title={
                <div className="flex justify-between items-center">
                  <span>Context Discussion</span>
                  <button 
                    onClick={toggleChatWindow}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              }>
                <ContextChat 
                  messages={chatMessages}
                  onSendMessage={handleSendMessage}
                  disabled={isContextSufficient}
                />
              </InfoCard>
            )}

            {renderAnalysisSection()}

            {task.concepts?.length > 0 && (
              <InfoCard title="Related Concepts">
                <div className="flex flex-wrap gap-2">
                  {['Sentiment Analysis', 'Natural Language Processing', 'Topic Modeling'].map((concept) => (
                    <a
                      key={concept}
                      href="#"
                      className="inline-flex items-center text-blue-600 hover:text-blue-800"
                    >
                      {concept}
                      <svg className="w-4 h-4 ml-1" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" />
                        <path d="M15 3h6v6" />
                        <path d="M10 14L21 3" />
                      </svg>
                    </a>
                  ))}
                </div>
              </InfoCard>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <InfoCard title="Metadata">
              <div className="space-y-3">
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Task ID</h3>
                  <p className="mt-1 text-gray-900 font-mono">{task.id}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Created</h3>
                  <p className="mt-1 text-gray-900">
                    {new Date(task.created_at).toLocaleString()}
                  </p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Last Updated</h3>
                  <p className="mt-1 text-gray-900">
                    {new Date(task.updated_at).toLocaleString()}
                  </p>
                </div>
                {task.progress !== undefined && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Progress</h3>
                    <ProgressBar progress={task.progress} />
                  </div>
                )}
                {task.sub_tasks?.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Sub Tasks</h3>
                    <div className="mt-2 space-y-2">
                      {task.sub_tasks.map(subTask => (
                        <div 
                          key={subTask.id}
                          onClick={() => navigate(`/tasks/${subTask.id}`)}
                          className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <StatusBadge state={subTask.state} />
                          </div>
                          <p className="text-sm text-gray-900">{subTask.short_description}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </InfoCard>
          </div>
        </div>
      </div>
    </div>
  );
}
