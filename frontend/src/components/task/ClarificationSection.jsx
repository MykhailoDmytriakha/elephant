import React from "react";
import { MessageCircle, RefreshCcw } from "lucide-react";
import { CollapsibleSection } from "./TaskComponents";
import { TaskStates } from "../../constants/taskStates";
import ClarificationChat from "./ClarificationChat";

export default function ClarificationSection({
  taskState,
  clarification_data,
  onStartClarification,
  isStartingClarificationLoading,
  onSendMessage,
  isLoading,
}) {
  // Only show the section when typification is complete and we're in TYPIFY state
  // or when we're already in clarification mode
  const showSection =
    (clarification_data &&
      Object.keys(clarification_data).length > 0 &&
      taskState === TaskStates.TYPIFY) ||
    taskState === TaskStates.CLARIFYING;

  const questionIndex = clarification_data.current_question_index;
  const currentQuestion = clarification_data.questions[questionIndex];

  if (!showSection) {
    return null;
  }

  return (
    <CollapsibleSection title="Clarification">
      {clarification_data ? (
        <ClarificationChat
          isOpen={true}
          onSendMessage={onSendMessage}
          currentQuestion={currentQuestion}
          isLoading={isLoading}
          clarificationData={clarification_data}
        />
      ) : (
        <div className="text-center py-8">
          <button
            onClick={onStartClarification}
            disabled={isStartingClarificationLoading}
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-400"
          >
            {isStartingClarificationLoading ? (
              <>
                <RefreshCcw className="w-5 h-5 animate-spin" />
                Starting Clarification...
              </>
            ) : (
              <>
                <MessageCircle className="w-5 h-5" />
                Start Clarification Questions
              </>
            )}
          </button>
        </div>
      )}
    </CollapsibleSection>
  );
}
