import React from "react";
import { MessageCircle, RefreshCcw } from "lucide-react";
import { CollapsibleSection } from "./TaskComponents";
import { TaskStates } from "../../constants/taskStates";
import ClarificationChat from "./ClarificationChat";
import { getStateNumber } from "../../constants/taskStates";

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
  const isTypificationStageOrLater = getStateNumber(taskState) >= getStateNumber(TaskStates.TYPIFY);

  if (!isTypificationStageOrLater) {
    return null;
  }

  return (
    <CollapsibleSection title="Clarification">
      {clarification_data && Object.keys(clarification_data).length > 0 ? (
        <>
          {/* Move variable declarations before the JSX */}
          {(() => {
            const questionIndex = clarification_data.current_question_index;
            const currentQuestion = clarification_data.questions[questionIndex];
            const allQuestionsAnswered = clarification_data.is_complete;
            
            return (
              <ClarificationChat
                isOpen={true}
                onSendMessage={onSendMessage}
                currentQuestion={currentQuestion}
                isLoading={isLoading}
                clarificationData={clarification_data}
                allQuestionsAnswered={allQuestionsAnswered}
              />
            );
          })()}
        </>
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
