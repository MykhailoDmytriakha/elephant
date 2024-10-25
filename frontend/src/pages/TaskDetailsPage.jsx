// src/pages/TaskDetailsPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Trash2 } from 'lucide-react';
import { 
  LoadingSpinner,
  ErrorDisplay} from '../components/task/TaskComponents';
import { fetchTaskDetails, updateTaskContext, deleteTask, analyzeTask, generateConcepts } from '../utils/api';
import { TaskStates } from '../constants/taskStates';
import ConceptDefinition from '../components/task/ConceptDefinition';
import TaskOverview from '../components/task/TaskOverview';
import Analysis from '../components/task/Analysis';
import ContextChatWindow from '../components/task/ContextChatWindow';
import Metadata from '../components/task/Metadata';

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
  const [isGeneratingConcepts, setIsGeneratingConcepts] = useState(false);

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


  // Update this part to correctly handle the user interaction and follow-up question
  const chatMessages = [
    ...(task?.user_interaction || []).map(interaction => [
      { role: 'assistant', content: interaction.query },
      { role: 'user', content: interaction.answer }
    ]).flat(),
    ...(followUpQuestion ? [{ role: 'assistant', content: followUpQuestion }] : [])
  ];

  const handleAnalyze = async (isReanalyze = false) => {
    try {
      setIsAnalyzing(true);
      await analyzeTask(taskId, isReanalyze);
      await loadTask(); // Reload task to get updated analysis
    } catch (err) {
      setError('Failed to analyze task: ' + err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleGenerateConcepts = async () => {
    try {
      setIsGeneratingConcepts(true);
      console.log("Starting concept generation...");
      const conceptResponse = await generateConcepts(taskId);
      console.log("Generate concepts response:", conceptResponse);
      
      // Add a small delay before fetching updated task
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Fetch and log the updated task data
      const updatedTask = await fetchTaskDetails(taskId);
      console.log("Updated task after generating concepts:", updatedTask);
      setTask(updatedTask);
    } catch (err) {
      console.error("Error generating concepts:", err);
      setError('Failed to generate concepts: ' + err.message);
    } finally {
      setIsGeneratingConcepts(false);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay message={error} />;
  if (!task) return <ErrorDisplay message="Task not found" />;


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
            <TaskOverview
              task={task}
              isContextSufficient={isContextSufficient}
              isChatOpen={isChatOpen}
              toggleChatWindow={toggleChatWindow}
            />

            <ContextChatWindow 
              isOpen={isChatOpen}
              messages={chatMessages}
              onSendMessage={handleSendMessage}
              onClose={handleCloseChatWindow}
              isContextSufficient={isContextSufficient}
            />

            <Analysis 
              analysis={task.analysis}
              isContextSufficient={isContextSufficient}
              isAnalyzing={isAnalyzing}
              onAnalyze={handleAnalyze}
            />

            <ConceptDefinition
              concepts={task.concepts}
              isLoading={isGeneratingConcepts}
              onGenerateConcepts={handleGenerateConcepts}
              taskState={task.state}
              isContextSufficient={isContextSufficient}
            />
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Metadata task={task} />
          </div>
        </div>
      </div>
    </div>
  );
}
