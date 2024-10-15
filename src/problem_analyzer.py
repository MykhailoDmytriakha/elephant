from .database_service import DatabaseService
from .openai_service import OpenAiService
from .task import Task, TaskState
from .user_interaction import UserInteraction


class ProblemAnalyzer:
    MAX_RETRY = 4
    MAX_SUB_LEVEL = 3

    def __init__(self, openai_service: OpenAiService, db_service: DatabaseService):
        self.openai_service = openai_service
        self.db_service = db_service

    def clarify_context(self, task: Task):
        task.update_state(TaskState.CONTEXT)
        for _ in range(self.MAX_RETRY):
            if self._is_context_sufficient(task):
                break
        else:
            if not task.is_context_sufficient:
                summarized_context = self.openai_service.summarize_context(task.formatted_user_interaction, task.context)
                task.context = summarized_context
                task.is_context_sufficient = True
            print(f"Max retries ({self.MAX_RETRY}) reached. Proceeding with available context.")
        self.db_service.updated_task(task)

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

    def analyze(self, task: Task):
        if self._is_max_sub_level_reached(task):
            return
        task.update_state(TaskState.ANALYSIS)
        analysis_result = self.openai_service.analyze_task(task)

        task.task = analysis_result['task']
        task.analysis = analysis_result['analysis']
        task.update_state(TaskState.ANALYZED)
        self.db_service.updated_task(task)

        # self._analyze_complexity_and_decompose(task)  # TODO: use it by the request from user

    def _analyze_complexity_and_decompose(self, task: Task) -> dict:
        complexity = int(task.analysis['complexity'])

        if complexity > 1:
            print(f"Task complexity is {complexity}. Initiating decomposition.")
            self._decompose_task(task)
            return {"status": "decomposed", "sub_tasks": [sub_task.to_dict() for sub_task in task.sub_tasks]}
        else:
            print(f"Task complexity is {complexity}. No decomposition needed.")
            task.update_state(TaskState.DECOMPOSED)
            self.db_service.updated_task(task)
            return {"status": "no_decomposition_needed"}

    def _decompose_task(self, task: Task):
        if self._is_max_sub_level_reached(task):
            return
        # Call OpenAI service to decompose the task
        decomposed_tasks = self.openai_service.decompose_task(task)
        for sub_task_info in decomposed_tasks.get('sub_tasks', []):
            sub_task = Task(sub_task_info['task'], sub_task_info['context'])
            sub_task.short_description = sub_task_info['short_description']
            sub_task.parent_task = task
            sub_task.sub_level = task.sub_level + 1
            task.sub_tasks.append(sub_task)
            self.db_service.insert_task(sub_task)

        print(f"Task {task.short_description} decomposed into {len(task.sub_tasks)} sub-tasks.")

        task.update_state(TaskState.DECOMPOSED)
        self.db_service.updated_task(task)

        # Recursively analyze each sub-task
        # for sub_task in task.sub_tasks:  # TODO: remove it, it should be trigered from UI
        #     self.analyze(sub_task)

    def _is_max_sub_level_reached(self, task: Task) -> bool:
        if task.sub_level >= self.MAX_SUB_LEVEL:
            print(f"Reached maximum sub-task level ({task.sub_level}). Skipping further decomposition.")
            return True
        return False
