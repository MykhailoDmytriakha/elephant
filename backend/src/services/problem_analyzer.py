from typing import Dict, Any, Optional

from .database_service import DatabaseService
from src.services.openai_service import OpenAIService, ContextSufficiencyResult
from src.model.task import Task, TaskState
from src.user_interaction import UserInteraction
import re
import logging

logger = logging.getLogger(__name__)

def extract_level(text):
    match = re.search(r'LEVEL_(\d+)', text)
    if match:
        return int(match.group(1))
    raise ValueError(f"No level found in text: {text}")

class ProblemAnalyzer:
    MAX_SUB_LEVEL = 2

    def __init__(self, openai_service: OpenAIService, db_service: DatabaseService):
        self.openai_service = openai_service
        self.db_service = db_service

    def clarify_context(self, task: Task) -> ContextSufficiencyResult:
        if task.is_context_sufficient:
            task.update_state(TaskState.CONTEXT_GATHERED)
            return {"is_context_sufficient": True, "follow_up_question": "I understand your task. Let's proceed with the analysis."}
        
        """Initial context gathering method"""
        task.update_state(TaskState.CONTEXT_GATHERING)
        result = self.openai_service.is_context_sufficient(task)
        
        if not isinstance(result, dict) or 'is_context_sufficient' not in result:
            return {"is_context_sufficient": False, "follow_up_question": "Could you please provide more details about what you're trying to accomplish?"}
            
        if result["is_context_sufficient"]:
            task.is_context_sufficient = True
            summarized_context = self.openai_service.summarize_context(task.formatted_user_interaction, task.context)
            task.context = summarized_context
            task.update_state(TaskState.CONTEXT_GATHERED)
            self.db_service.updated_task(task)
            
            # After context is gathered, process it to formulate the task
            return self.process_context(task)
                    
        return result

    def process_context(self, task: Task) -> ContextSufficiencyResult:
        """Process gathered context and formulate task"""
        if task.state != TaskState.CONTEXT_GATHERED:
            return {
                "is_context_sufficient": False,
                "follow_up_question": "We need more information about your task. Could you elaborate?"
            }

        # Formulate the task based on gathered context
        formulation = self.openai_service.formulate_task(task)
        task.task = formulation["task"]
        task.scope = formulation["scope"]

        if formulation["is_context_sufficient"]:
            task.update_state(TaskState.TASK_FORMATION)
            self.db_service.updated_task(task)
            
            return {
                "is_context_sufficient": True,
                "follow_up_question": "I understand your task. Let's proceed with the analysis."
            }
        else:
            task.is_context_sufficient = False
            task.update_state(TaskState.CONTEXT_GATHERING)
            self.db_service.updated_task(task)
            return {
                "is_context_sufficient": False,
                "follow_up_question": formulation.get(
                    "follow_up_question",
                    "Could you provide more details about your requirements?"
                )
            }

    def analyze(self, task: Task, reAnalyze: bool = False):
        """Analyze the task and update its state"""
        if self._is_max_sub_level_reached(task):
            return
            
        analysis_result = self.openai_service.analyze_task(task)

        # Update task with analysis results
        task.analysis = analysis_result['analysis']
        
        if not reAnalyze:
            # Only update state if this is not a re-analysis
            task.update_state(TaskState.ANALYSIS)
        
        if task.complexity == 1 or (task.level and "LEVEL_1" in task.level):
            task.update_state(TaskState.CLARIFICATION_COMPLETE)
        
        self.db_service.updated_task(task)
        
    def typify(self, task: Task):
        typification_result = self.openai_service.typify_task(task)
        complexity_level = typification_result['typification']['classification']['complexity_level']['level']
        task.level = complexity_level
        task.complexity = extract_level(complexity_level)
        task.eta_to_complete = typification_result['typification']['eta']['time']
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

    def decompose(self, task: Task, redecompose: bool = False) -> dict:
        if redecompose:
            #  we neew to delete all sub-tasks recursively in like a tree
            for sub_task in task.sub_tasks:
                self.db_service.delete_task_by_id(sub_task)
            task.sub_tasks = []
            self.db_service.updated_task(task)
        if task.complexity is None:
            complexity = extract_level(task.level)
        else:
            complexity = task.complexity

        if complexity > 1:
            print(f"Task complexity is {complexity}. Initiating decomposition.")
            self._decompose_task(task)
            return {"status": "decomposed"}
        # TODO: we could force decomposition base on user request. This could be implemented later
        else:
            print(f"Task complexity is {complexity}. No decomposition needed.")
            task.update_state(TaskState.DECOMPOSITION)
            self.db_service.updated_task(task)
            return {"status": "no_decomposition_needed"}

    def _decompose_task(self, task: Task):
        if self._is_max_sub_level_reached(task):
            return

        # Call OpenAI service to decompose the task
        decomposed_tasks = self.openai_service.decompose_task(task)
        task.decomposed_tasks = decomposed_tasks['sub_tasks']

        # Build the task tree
        self._build_task_tree(decomposed_tasks, task)

        print(f"Task '{task.short_description}' decomposed into {len(task.sub_tasks)} sub-tasks.")

        task.update_state(TaskState.DECOMPOSITION)
        self.db_service.updated_task(task)

        # for sub_task in task.sub_tasks:
        #     self.decompose(sub_task)

    def _build_task_tree(self, task_data: Dict[str, Any], parent_task: Task):
        for sub_task_info in task_data.get('sub_tasks', []):
            sub_task = Task.create_new(sub_task_info['task'], sub_task_info['context'])
            sub_task.short_description = sub_task_info['short_description']
            sub_task.sub_level = parent_task.sub_level + 1
            sub_task.level = sub_task_info['complexity_level']
            sub_task.complexity = extract_level(sub_task.level)
            sub_task.order = sub_task_info['order']
            sub_task.contribution_to_parent_task = sub_task_info['contribution_to_parent_task']
            sub_task.eta_to_complete = sub_task_info['eta']['time']
            sub_task.scope = sub_task_info['scope']
            sub_task.parent_task = parent_task.id
            sub_task.is_context_sufficient = True
            sub_task.update_state(TaskState.CONTEXT_GATHERED)
            parent_task.sub_tasks.append(sub_task.id)
            self.db_service.insert_task(sub_task)

            # Recursively build sub-tasks if they exist
            # if 'sub_tasks' in sub_task_info:
            #     self._build_task_tree(sub_task_info, sub_task)

    def _is_max_sub_level_reached(self, task: Task) -> bool:
        if task.sub_level >= self.MAX_SUB_LEVEL:
            logger.warning(f"Reached maximum sub-task level ({task.sub_level}). Skipping further decomposition.")
            return True
        return False
