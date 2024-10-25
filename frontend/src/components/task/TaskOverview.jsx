import React from "react";
import { MessageCircle, AlertCircle, X } from "lucide-react";
import { CollapsibleSection } from "./TaskComponents";
import { TaskStates } from "../../constants/taskStates";

const TaskOverview = ({
  task,
  isContextSufficient,
  isChatOpen,
  toggleChatWindow,
}) => {
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
            {isContextSufficient && (
              <button
                onClick={toggleChatWindow}
                className="inline-flex items-center gap-1 px-3 py-1.5 text-sm bg-gray-50 text-gray-600 rounded-md hover:bg-gray-100 transition-colors"
              >
                <MessageCircle className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        {(!isContextSufficient ||
          task.state === TaskStates.CONTEXT_GATHERING) && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-yellow-800">
                  Additional Context Needed
                </h4>
                {/* <p className="text-sm text-yellow-700">
                  What specific time period should we analyze?
                </p> */}
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
    </CollapsibleSection>
  );
};

export default TaskOverview;
