import json
import logging
from typing import TypedDict
from src.model.context import ContextSufficiencyResult
from openai import OpenAI
from src.services.prompts.analyze_task_prompt import ANALYZE_TASK_FUNCTIONS, get_analyze_task_prompt
from src.services.prompts.typify_task_prompt import TYPIFY_TASK_FUNCTIONS, get_typify_task_prompt
from src.services.prompts.clarifying_questions_prompt import CLARIFYING_QUESTIONS_FUNCTIONS, get_clarifying_questions_prompt
from src.services.prompts.context_sufficient_prompt import CONTEXT_SUFFICIENT_FUNCTIONS, get_context_sufficient_prompt
from src.services.prompts.generate_approaches_prompt import GENERATE_APPROACHES_FUNCTIONS, get_generate_approaches_prompt
from src.core.config import settings
from src.model.task import Task

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        logger.info("Initializing OpenAIService")
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        if not self.api_key:
            logger.error("OpenAI API key is not set!")
            raise ValueError("OpenAI API key is not set!")
        self.client = OpenAI(api_key=self.api_key)

    def summarize_context(self, formatted_user_interaction: str, context: str) -> str:
        logger.info("Called summarize_context method")
        # Handle None values by converting to empty string
        context_str = context or ""
        formatted_interaction_str = formatted_user_interaction or ""
        if not context_str and not formatted_interaction_str:
            logger.info("Context is empty. Skipping summarization.")
            return ""
        prompt = f"Summarize the following context: \n- {context_str}\n- {formatted_interaction_str}"
        logger.debug(f"OpenAI API prompt: {prompt}")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.choices[0].message.content
        logger.debug(f"OpenAI API response: {result}")
        return result

    @staticmethod
    def _gather_context(task: Task) -> str:
        contexts = []
        current_task: Task | None = task
        while current_task:
            if current_task.context:
                contexts.append(current_task.context)
            current_task = current_task.parent_task
        return "\n".join(contexts) if contexts else ""
    
    def is_context_sufficient(self, task: Task) -> ContextSufficiencyResult:
        logger.info("Called is_context_sufficient method")
        functions = CONTEXT_SUFFICIENT_FUNCTIONS

        summarized_context = self.summarize_context(task.formatted_user_interaction, task.context) if not task.is_context_sufficient else (task.context or "")
        prompt = get_context_sufficient_prompt(task, summarized_context)
        logger.debug(f"OpenAI API prompt: {prompt}")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            functions=functions,
            function_call={"name": "context_analysis"}
        )
        function_call = response.choices[0].message.function_call
        if function_call:
            result = json.loads(function_call.arguments)
            logger.debug(f"OpenAI API response: {result}")
            return ContextSufficiencyResult(
                is_context_sufficient=result["is_context_sufficient"],
                follow_up_question=result["follow_up_question"]
            )
        else:
            fallback_result = ContextSufficiencyResult(
                is_context_sufficient=False,
                follow_up_question="Can you provide more details about the problem?"
            )
            logger.warning(f"OpenAI API fallback response: {fallback_result}")
            return fallback_result

    def analyze_task(self, task: Task) -> dict:
        logger.info("Called analyze_task method")
        functions = ANALYZE_TASK_FUNCTIONS

        context = self._gather_context(task)
        prompt = get_analyze_task_prompt(task_description=task.task or task.short_description or "", context=context)
        logger.debug(f"OpenAI API prompt: {prompt}")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            functions=functions,
            function_call={"name": "analyze_task"}
        )
        function_call = response.choices[0].message.function_call
        if function_call:
            result = json.loads(function_call.arguments)
            logger.debug(f"OpenAI API response: {result}")
            return result
        else:
            fallback_result = {
                "error": "Unable to formulate task",
                "task": "Unable to formulate task",
                "analysis": {
                    "parameters_constraints": "Unable to determine parameters and constraints",
                    "available_resources": ["Unable to determine available resources"],
                    "required_resources": ["Unable to determine required resources"],
                    "ifr": "Unable to determine ideal final result",
                    "missing_information": ["Unable to determine missing information"]
                }
            }
            logger.warning(f"OpenAI API fallback response: {fallback_result}")
            return fallback_result
    
    def typify_task(self, task: Task) -> dict:
        logger.info("Called typify_task method")
        functions = TYPIFY_TASK_FUNCTIONS

        prompt = get_typify_task_prompt(task)
        logger.debug(f"OpenAI API prompt: {prompt}")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            functions=functions,
            function_call={"name": "typify_task"}
        )
        function_call = response.choices[0].message.function_call
        if function_call:
            result = json.loads(function_call.arguments)
            logger.debug(f"OpenAI API response: {result}")
            return result
        else:
            fallback_result = {"error": "Unable to typify task"}
            logger.warning(f"OpenAI API fallback response: {fallback_result}")
            return fallback_result
    
    def generate_clarifying_questions(self, task: Task) -> dict:
        """Generate clarifying questions based on analysis and typification"""
        functions = CLARIFYING_QUESTIONS_FUNCTIONS

        prompt = get_clarifying_questions_prompt(task)

        logger.debug(f"OpenAI API prompt: {prompt}")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            functions=functions,
            function_call={"name": "generate_questions"}
        )

        function_call = response.choices[0].message.function_call
        if function_call:
            result = json.loads(function_call.arguments)
            logger.debug(f"OpenAI API response: {result}")
            return result
        else:
            fallback_result = {
                "questions": [{
                    "question_id": "fallback_q1",
                    "question": "Could you provide more details about your requirements?",
                    "purpose": "Gather basic requirements",
                    "expected_value": "User requirements",
                    "priority": 1
                }],
                "stop_criteria": ["Basic information gathered"]
            }
            logger.warning(f"OpenAI API fallback response: {fallback_result}")
            return fallback_result

    def generate_approaches(self, task: Task) -> dict:
        logger.info("Called generate_approaches method")
        functions = GENERATE_APPROACHES_FUNCTIONS

        context = self._gather_context(task)
        prompt = get_generate_approaches_prompt(task, context)
        logger.debug(f"OpenAI API prompt: {prompt}")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt},
            ],
            functions=functions,
            function_call={"name": "generate_approaches"}
        )

        function_call = response.choices[0].message.function_call
        if function_call:
            result = json.loads(function_call.arguments)
            logger.debug(f"OpenAI API response: {result}")
            return result
        else:
            fallback_result = {
                "approaches": None
            }
            logger.warning(f"OpenAI API fallback response: {fallback_result}")
            return fallback_result

    def decompose_task(self, task: Task) -> dict:
        logger.info("Called decompose_task method")
        functions = [
            {
                "name": "decompose_task",
                "description": "Decompose a complex task into smaller, manageable sub-tasks with meaningful granularity.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sub_tasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "task": {
                                        "type": "string",
                                        "description": "The comprehensive description of the sub-task to be performed"
                                    },
                                    "context": {
                                        "type": "string",
                                        "description": "Additional context for the sub-task"
                                    },
                                    "complexity": {
                                        "type": "string",
                                        "enum": ["1", "2", "3", "4", "5"],
                                        "description": "Estimated complexity of the sub-task (1: simple, 2: low, 3: medium, 4: high, 5: very high)"
                                    },
                                    "short_description": {
                                        "type": "string",
                                        "description": "Short description of the sub-task"
                                    },
                                    "contribution_to_parent_task": {
                                        "type": "string",
                                        "description": "Explanation of how this sub-task contributes to achieving the overall goal of the parent task"
                                    }
                                },
                                "required": ["task", "context", "complexity", "short_description", "contribution_to_parent_task"]
                            },
                            "description": "List of sub-tasks derived from the main task"
                        }
                    },
                    "required": ["sub_tasks"]
                }
            }
        ]

        context = self._gather_context(task)
        original_complexity = task.analysis.get('complexity', '4')  # Default to high if not specified
        prompt = f"""
        Decompose the following complex task into smaller, manageable sub-tasks:
        Task: {task.task}
        Ideal Final Result: {task.analysis.get('ideal_final_result', 'N/A')}
        Context: {context}
        Analysis: {json.dumps(task.analysis, ensure_ascii=False)}
        Original Task Complexity: {original_complexity}

        Provide a list of sub-tasks, each with its own description, context, and complexity.
        Ensure that each sub-task has a lower complexity than the original task (complexity {original_complexity}).
        The complexity levels are:
        1 - Simple
        2 - Low complexity
        3 - Medium complexity
        4 - High complexity
        5 - Very high complexity
        """

        logger.debug(f"OpenAI API prompt: {prompt}")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            functions=functions,
            function_call={"name": "decompose_task"}
        )

        function_call = response.choices[0].message.function_call
        if function_call:
            result = json.loads(function_call.arguments)
            logger.debug(f"OpenAI API response: {result}")
            return result
        else:
            fallback_result = {
                "sub_tasks": [
                    {
                        "task": "Unable to decompose task",
                        "context": "Task decomposition failed",
                        "complexity": "1",
                        "short_description": "Decomposition failure"
                    }
                ]
            }
            logger.warning(f"OpenAI API fallback response: {fallback_result}")
            return fallback_result

    


