from .task import Task, TaskState
from .openai_service import OpenAiService
from .user_interaction import UserInteraction

class ProblemAnalyzer:
    def __init__(self, openai_service: OpenAiService):
        self.openai_service = openai_service

    def analyze(self, task: Task):
        task.update_state(TaskState.ANALYSIS)
        
        max_retry = 3
        retry_count = 0
        while not self._is_context_sufficient(task) and retry_count < max_retry:
            retry_count += 1

        analysis_result = self.openai_service.analyze_problem(
            task.origin_query,
            task.context
        )
        
        task.analysis = analysis_result
        task.update_state(TaskState.ANALYZED)

    def _is_context_sufficient(self, task: Task) -> bool:
        result = self.openai_service.is_context_sufficient(task)
        if result["is_context_sufficient"]:
            print("Context is sufficient. Proceeding with analysis.")
            return True
        else:
            follow_up_question = result["follow_up_question"]
            print("Need more information.")
            print("Follow-up question:", follow_up_question)
            additional_context = UserInteraction.get_input(result["follow_up_question"])
            task.add_context(follow_up_question, additional_context)
            return False