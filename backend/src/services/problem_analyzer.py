from typing import Dict, Any

from .database_service import DatabaseService
from src.services.openai_service import OpenAIService, ContextSufficiencyResult
from src.model.task import Task, TaskState
from src.user_interaction import UserInteraction


class ProblemAnalyzer:
    MAX_SUB_LEVEL = 1

    def __init__(self, openai_service: OpenAIService, db_service: DatabaseService):
        self.openai_service = openai_service
        self.db_service = db_service

    def clarify_context(self, task: Task) -> ContextSufficiencyResult:
        task.update_state(TaskState.CONTEXT_GATHERING)
        result = self.openai_service.is_context_sufficient(task)
        
        # Ensure result has the expected structure
        if not isinstance(result, dict) or 'is_context_sufficient' not in result:
            return {"is_context_sufficient": False, "follow_up_question": "Could you please provide more context about the task?"}
            
        if result["is_context_sufficient"]:
            task.is_context_sufficient = True
            summarized_context = self.openai_service.summarize_context(task.formatted_user_interaction, task.context)
            task.context = summarized_context
            task.update_state(TaskState.CONTEXT_GATHERED)
            self.db_service.updated_task(task)
                    
        return result

    def analyze(self, task: Task, reAnalyze: bool = False):
        if self._is_max_sub_level_reached(task):
            return
        analysis_result = self.openai_service.analyze_task(task)

        task.task = analysis_result['task']
        task.analysis = analysis_result['analysis']
        if not reAnalyze:
            task.update_state(TaskState.ANALYSIS)
        self.db_service.updated_task(task)

    def concept_definition(self, task: Task):
        concept_definitions = self.openai_service.generate_concepts(task)
        concepts = concept_definitions[0]['concepts']
        concepts['approach'] = concept_definitions[1]['approach']
        task.concepts = concepts
        task.update_state(TaskState.CONCEPT_DEFINITION)
        self.db_service.updated_task(task)
        return concepts

    def decompose(self, task: Task) -> dict:
        complexity = int(task.analysis['complexity'])

        if complexity > 1:
            print(f"Task complexity is {complexity}. Initiating decomposition.")
            self._decompose_task(task)
            return {"status": "decomposed", "sub_tasks": [sub_task.to_dict() for sub_task in task.sub_tasks]}
        # TODO: we could force decomposition base on user request. This could be implemented later
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

        # Build the task tree
        self._build_task_tree(decomposed_tasks, task)

        print(f"Task '{task.short_description}' decomposed into {len(task.sub_tasks)} sub-tasks.")

        task.update_state(TaskState.DECOMPOSED)
        self.db_service.updated_task(task)

        for sub_task in task.sub_tasks:
            self.decompose(sub_task)

    def _build_task_tree(self, task_data: Dict[str, Any], parent_task: Task):
        for sub_task_info in task_data.get('sub_tasks', []):
            sub_task = Task.create_new(sub_task_info['task'], sub_task_info['context'])
            sub_task.sub_level = parent_task.sub_level + 1
            sub_task.short_description = sub_task_info['short_description']
            sub_task.analysis['complexity'] = sub_task_info['complexity']
            sub_task.concepts['contribution_to_parent_task'] = sub_task_info['contribution_to_parent_task']
            sub_task.parent_task = parent_task
            parent_task.sub_tasks.append(sub_task)
            self.db_service.insert_task(sub_task)

            # Recursively build sub-tasks if they exist
            if 'sub_tasks' in sub_task_info:
                self._build_task_tree(sub_task_info, sub_task)

    def _is_max_sub_level_reached(self, task: Task) -> bool:
        if task.sub_level >= self.MAX_SUB_LEVEL:
            print(f"Reached maximum sub-task level ({task.sub_level}). Skipping further decomposition.")
            return True
        return False
