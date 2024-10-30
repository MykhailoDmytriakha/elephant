from typing import Dict, Any, Optional

from .database_service import DatabaseService
from src.services.openai_service import OpenAIService, ContextSufficiencyResult
from src.model.task import Task, TaskState
from src.user_interaction import UserInteraction
import re
def extract_level(text):
    match = re.search(r'LEVEL_(\d+)', text)
    if match:
        return int(match.group(1))
    raise ValueError(f"No level found in text: {text}")

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
        
    def typify(self, task: Task):
        typification_result = self.openai_service.typify_task(task)
        complexity_level = typification_result['typification']['classification']['complexity_level']['level']
        task.complexity = extract_level(complexity_level)
        task.typification = typification_result['typification']
        task.update_state(TaskState.TYPIFY)
        self.db_service.updated_task(task)
        
    def clarify_for_approaches(self, task: Task, message: Optional[str] = None) -> dict:
        """Handle the clarification dialogue before approaches generation."""
        if task.state == TaskState.TYPIFY:
            questions = self.openai_service.generate_clarifying_questions(task)
            task.update_state(TaskState.CLARIFYING)
            task.clarification_data = {
                'questions': questions['questions'],
                'stop_criteria': questions['stop_criteria'],
                'current_question_index': 0,
                'answers': {},
                'is_complete': False  # Added is_complete flag here
            }
            self.db_service.updated_task(task)
            return {
                'question': questions['questions'][0],
                'is_complete': task.clarification_data['is_complete']  # Use from clarification_data
            }
        
        elif task.state == TaskState.CLARIFYING:
            if not message:
                current_q = task.clarification_data['questions'][task.clarification_data['current_question_index']]
                return {
                    'question': current_q,
                    'is_complete': task.clarification_data['is_complete']  # Use from clarification_data
                }
            
            # Store the answer
            current_q = task.clarification_data['questions'][task.clarification_data['current_question_index']]
            task.clarification_data['answers'][current_q['question_id']] = message
            
            # Check if we should move to the next question
            next_index = task.clarification_data['current_question_index'] + 1
            if next_index < len(task.clarification_data['questions']):
                task.clarification_data['current_question_index'] = next_index
                next_q = task.clarification_data['questions'][next_index]
                self.db_service.updated_task(task)
                return {
                    'question': next_q,
                    'is_complete': task.clarification_data['is_complete']  # Use from clarification_data
                }
            else:
                task.clarification_data['is_complete'] = True  # Update is_complete in clarification_data
                task.update_state(TaskState.CLARIFICATION_COMPLETE)
                self.db_service.updated_task(task)
                return {
                    'message': 'Clarification complete. Ready to generate approaches.',
                    'is_complete': task.clarification_data['is_complete'],  # Use from clarification_data
                    'answers': task.clarification_data['answers']
                }
        
        # Add default return for other states
        return {
            'message': 'Invalid state for clarification',
            'is_complete': True
        }

    def generate_approaches(self, task: Task):
        approach_definitions = self.openai_service.generate_approaches(task)
        approaches = {
            'tool_categories': approach_definitions['tool_categories'],
            'tool_combinations': approach_definitions['tool_combinations']
        }
        task.approaches = {**approaches}
        task.update_state(TaskState.APPROACH_FORMATION)
        self.db_service.updated_task(task)
        return task.approaches

    def decompose(self, task: Task) -> dict:
        if task.complexity is None:
            level = task.typification['classification']['complexity_level']['level']
            complexity = extract_level(level)
        else:
            complexity = task.complexity

        if complexity > 1:
            print(f"Task complexity is {complexity}. Initiating decomposition.")
            self._decompose_task(task, complexity)
            return {"status": "decomposed"}
        # TODO: we could force decomposition base on user request. This could be implemented later
        else:
            print(f"Task complexity is {complexity}. No decomposition needed.")
            task.update_state(TaskState.DECOMPOSITION)
            self.db_service.updated_task(task)
            return {"status": "no_decomposition_needed"}

    def _decompose_task(self, task: Task, complexity: int):
        if self._is_max_sub_level_reached(task):
            return

        # Call OpenAI service to decompose the task
        decomposed_tasks = self.openai_service.decompose_task(task, complexity)

        # Build the task tree
        self._build_task_tree(decomposed_tasks, task)

        print(f"Task '{task.short_description}' decomposed into {len(task.sub_tasks)} sub-tasks.")

        task.update_state(TaskState.DECOMPOSITION)
        self.db_service.updated_task(task)

        # for sub_task in task.sub_tasks:
        #     self.decompose(sub_task)

    def _build_task_tree(self, task_data: Dict[str, Any], parent_task: Task):
        parent_task.sub_tasks = []
        for sub_task_info in task_data.get('sub_tasks', []):
            sub_task = Task.create_new(sub_task_info['task'], sub_task_info['context'])
            sub_task.sub_level = parent_task.sub_level + 1
            sub_task.short_description = sub_task_info['short_description']
            sub_task.complexity = sub_task_info['complexity']
            sub_task.contribution_to_parent_task = sub_task_info['contribution_to_parent_task']
            sub_task.parent_task = parent_task.id
            parent_task.sub_tasks.append(sub_task.id)
            self.db_service.insert_task(sub_task)

            # Recursively build sub-tasks if they exist
            if 'sub_tasks' in sub_task_info:
                self._build_task_tree(sub_task_info, sub_task)

    def _is_max_sub_level_reached(self, task: Task) -> bool:
        if task.sub_level >= self.MAX_SUB_LEVEL:
            print(f"Reached maximum sub-task level ({task.sub_level}). Skipping further decomposition.")
            return True
        return False
