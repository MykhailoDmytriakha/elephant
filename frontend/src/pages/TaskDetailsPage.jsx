// src/pages/TaskDetailsPage.jsx
import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Trash2 } from "lucide-react";
import {
  LoadingSpinner,
  ErrorDisplay,
} from "../components/task/TaskComponents";
import {
  fetchTaskDetails,
  updateTaskContext,
  deleteTask,
  analyzeTask,
  generateApproaches,
  typifyTask,
  clarifyTask,
} from "../utils/api";
import { TaskStates, getStateColor } from "../constants/taskStates";
import TaskOverview from "../components/task/TaskOverview";
import Analysis from "../components/task/Analysis";
import ContextChatWindow from "../components/task/ContextChatWindow";
import Metadata from "../components/task/Metadata";
import ApproachFormation from "../components/task/ApproachFormation";
import Typification from "../components/task/Typification";
import ClarificationSection from "../components/task/ClarificationSection";

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
  const [isStartingClarificationLoading, setIsStartingClarificationLoading] =
    useState(false);
  const [isGeneratingConcepts, setIsGeneratingConcepts] = useState(false);
  const [isRegeneratingApproaches, setIsRegeneratingApproaches] =
    useState(false);
  const [isTypifying, setIsTypifying] = useState(false);
  const [isClarifying, setIsClarifying] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [clarificationData, setClarificationData] = useState(null);

  // Add debug logging for state changes
  useEffect(() => {
    console.log("Task State:", task?.state);
    console.log("Is Clarifying:", isClarifying);
    console.log("Current Question:", currentQuestion);
    console.log("Clarification Data:", clarificationData);
  }, [task?.state, isClarifying, currentQuestion, clarificationData]);

  const loadTask = async () => {
    try {
      // Store current scroll position
      const scrollPosition = window.scrollY;
      
      setLoading(true);
      setError(null);
      const data = await fetchTaskDetails(taskId);
      setTask(data);
      setIsContextSufficient(data.is_context_sufficient);
      if (!data.is_context_sufficient) {
        setIsChatOpen(true);
        const contextUpdate = await updateTaskContext(taskId);
        setFollowUpQuestion(contextUpdate.follow_up_question);
      }

      // Restore scroll position after state updates
      requestAnimationFrame(() => {
        window.scrollTo({
          top: scrollPosition,
          behavior: 'instant'
        });
      });
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
    navigate("/");
  };

  const handleDelete = async () => {
    if (window.confirm("Are you sure you want to delete this task?")) {
      try {
        await deleteTask(taskId);
        navigate("/");
      } catch (error) {
        setError("Failed to delete task: " + error.message);
      }
    }
  };

  const handleSendMessage = async (message) => {
    try {
      const updatedContext = await updateTaskContext(taskId, {
        query: followUpQuestion,
        answer: message,
      });
      console.log("Updated context:", updatedContext);
      setIsContextSufficient(updatedContext.is_context_sufficient);
      if (updatedContext.is_context_sufficient) {
        setFollowUpQuestion(null);
      } else {
        setFollowUpQuestion(updatedContext.follow_up_question);
      }
      const updatedTask = await fetchTaskDetails(taskId);
      setTask(updatedTask);
    } catch (error) {
      setError("Failed to send message: " + error.message);
    }
  };

  const toggleChatWindow = () => {
    setIsChatOpen((prevState) => !prevState);
  };

  const handleCloseChatWindow = () => {
    setIsChatOpen(false);
  };

  const handleClarification = async (message = null) => {
    try {
      setIsStartingClarificationLoading(true);

      // If this is the initial clarification (no message), set isClarifying
      if (!message) {
        setIsClarifying(true);
      }
      await clarifyTask(taskId, message);
      loadTask();

      // Scroll to the end of the page after the task is loaded
      setTimeout(() => {
        window.scrollTo({
          top: document.body.scrollHeight,
          behavior: 'smooth'
        });
      }, 100);
    } catch (error) {
      setError("Failed to process clarification: " + error.message);
    } finally {
      setIsStartingClarificationLoading(false);
    }
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
      await loadTask();
    } catch (err) {
      setError("Failed to analyze task: " + err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleGenerateConcepts = async () => {
    try {
      setIsGeneratingConcepts(true);
      await generateApproaches(taskId);
      await loadTask();
    } catch (err) {
      setError("Failed to generate concepts: " + err.message);
    } finally {
      setIsGeneratingConcepts(false);
    }
  };

  const handleRegenerateApproaches = async () => {
    try {
      setIsRegeneratingApproaches(true);
      await generateApproaches(taskId);
      await loadTask();
    } catch (err) {
      setError("Failed to regenerate approaches: " + err.message);
    } finally {
      setIsRegeneratingApproaches(false);
    }
  };

  const handleTypify = async (isRetypify = false) => {
    try {
      setIsTypifying(true);
      await typifyTask(taskId, isRetypify);
      await loadTask();
    } catch (err) {
      setError("Failed to typify task: " + err.message);
    } finally {
      setIsTypifying(false);
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
              <span
                className={`px-3 py-1 rounded-full text-sm font-medium ${getStateColor(
                  task.state
                )}`}
              >
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

            <Typification
              typification={task.typification}
              isContextSufficient={isContextSufficient}
              isTypifying={isTypifying}
              onTypify={handleTypify}
              taskState={task.state}
            />

            <ClarificationSection
              taskState={task.state}
              clarification_data={task.clarification_data}
              onStartClarification={() => handleClarification()}
              isStartingClarificationLoading={isStartingClarificationLoading}
              onSendMessage={handleClarification}
              isLoading={loading}
            />

            <ApproachFormation
              approaches={task.approaches}
              onRegenerateApproaches={handleRegenerateApproaches}
              isRegenerating={isRegeneratingApproaches}
              taskState={task.state}
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
