from .task import Task, TaskState
from .openai_service import OpenAiService
from .user_interaction import UserInteraction

class ProblemAnalyzer:
    MAX_RETRY = 4

    def __init__(self, openai_service: OpenAiService):
        self.openai_service = openai_service
        
    def clarify_context(self, task: Task):
        task.update_state(TaskState.CONSTEXT)
        for _ in range(self.MAX_RETRY):
            if self._is_context_sufficient(task):
                break
        else:
            if not task.is_context_sufficient:
                summarized_context = self.openai_service.summarize_context(task.formatted_user_interaction, task.context)
                task.context = summarized_context
                task.is_context_sufficient = True
            print(f"Max retries ({self.MAX_RETRY}) reached. Proceeding with available context.")
 

    def analyze(self, task: Task):
        task.update_state(TaskState.ANALYSIS)
        analysis_result = self.openai_service.analyze_task(task)
        
        task.task = analysis_result['task']
        task.analysis = analysis_result['analysis']
        task.update_state(TaskState.ANALYZED)
        
        self._analyze_complexity_and_decompose(task)

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
            task.add_user_interaction(follow_up_question, additional_context)
            return False
    
    def _analyze_complexity_and_decompose(self, task: Task):
        complexity = int(task.analysis['complexity'])
        
        if complexity > 1:
            print(f"Task complexity is {complexity}. Initiating decomposition.")
            self._decompose_task(task)
        else:
            print(f"Task complexity is {complexity}. No decomposition needed.")
    
    def _decompose_task(self, task: Task):
        # Call OpenAI service to decompose the task
        sub_tasks_info = self.openai_service.decompose_task(task)
        if task.sub_level >= 2: #TODO: remove limitations
            print(f"Reached maximum sub-task level ({task.sub_level}). Skipping further decomposition.")
            return
        
        for sub_task_info in sub_tasks_info.get('sub_tasks', []):
            sub_task = Task(task.origin_query, sub_task_info['task'], sub_task_info['context'])
            sub_task.parent_task = task
            sub_task.sub_level = task.sub_level + 1
            task.sub_tasks.append(sub_task)
        
        print(f"Task decomposed into {len(task.sub_tasks)} sub-tasks.")
        
        # Recursively analyze each sub-task
        for sub_task in task.sub_tasks:
            self.analyze(sub_task)