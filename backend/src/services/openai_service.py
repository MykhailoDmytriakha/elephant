import json
import logging
from typing import TypedDict
from src.model.context import ContextSufficiencyResult
from openai import OpenAI
from src.services.prompts.analyze_task_prompt import ANALYZE_TASK_FUNCTIONS, ANALYZE_TASK_TOOLS, get_analyze_task_prompt
from src.services.prompts.typify_task_prompt import TYPIFY_TASK_FUNCTIONS, TYPIFY_TASK_TOOLS, get_typify_task_prompt
from src.services.prompts.clarifying_questions_prompt import CLARIFYING_QUESTIONS_FUNCTIONS, CLARIFYING_QUESTIONS_TOOLS, get_clarifying_questions_prompt
from src.services.prompts.context_sufficient_prompt import CONTEXT_SUFFICIENT_FUNCTIONS, CONTEXT_SUFFICIENT_TOOLS, get_context_sufficient_prompt
from src.services.prompts.generate_approaches_prompt import GENERATE_APPROACHES_FUNCTIONS, GENERATE_APPROACHES_TOOLS, get_generate_approaches_prompt
from src.services.prompts.decompose_task_prompt import DECOMPOSE_TASK_FUNCTIONS, DECOMPOSE_TASK_TOOLS, get_decompose_task_prompt
from src.services.prompts.formulate_task_prompt import FORMULATE_TASK_FUNCTIONS, FORMULATE_TASK_TOOLS, get_formulate_task_prompt
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
            # TODO: we need to get from parent context field if it is not None
            # current_task = current_task.parent_task
            current_task = None
        return "\n".join(contexts) if contexts else ""
    
    def is_context_sufficient(self, task: Task) -> ContextSufficiencyResult:
        logger.info("Called is_context_sufficient method")

        summarized_context = self.summarize_context(task.formatted_user_interaction, task.context) if not task.is_context_sufficient else (task.context or "")
        prompt = get_context_sufficient_prompt(task, summarized_context)
        logger.debug(f"OpenAI API prompt: {prompt}")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            tools=CONTEXT_SUFFICIENT_TOOLS,
            tool_choice={"type": "function", "function": {"name":"context_analysis"}}
        )
        function = response.choices[0].message.tool_calls[0].function
        if function:
            result = json.loads(function.arguments)
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

    def formulate_task(self, task: Task) -> dict:
        """Formulate clear task definition based on gathered context"""
        prompt = get_formulate_task_prompt(task)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            tools=FORMULATE_TASK_TOOLS,
            tool_choice={"type": "function", "function": {"name":"formulate_task"}}
        )

        function = response.choices[0].message.tool_calls[0].function
        if function:
            result = json.loads(function.arguments)
            logger.debug(f"OpenAI API response: {result}")
            return result
        else:
            fallback_result = {
                "task": task.short_description,
                "is_context_sufficient": False,
                "follow_up_question": "Could you provide more details about what needs to be accomplished?"
            }
            logger.warning(f"OpenAI API fallback response: {fallback_result}")
            return fallback_result

    def analyze_task(self, task: Task) -> dict:
        logger.info("Called analyze_task method")
        context = self._gather_context(task)
        prompt = get_analyze_task_prompt(task_description=task.task or task.short_description or "", context=context, scope=task.scope or {})
        logger.debug(f"OpenAI API prompt: {prompt}")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            tools = ANALYZE_TASK_TOOLS,
            tool_choice={"type": "function", "function": {"name":"analyze_task"}}
        )
        function = response.choices[0].message.tool_calls[0].function
        if function:
            result = json.loads(function.arguments)
            logger.debug(f"OpenAI API response: {result}")
            return result
        else:
            fallback_result = {
                "error": "Unable to formulate task",
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

        prompt = get_typify_task_prompt(task)
        logger.debug(f"OpenAI API prompt: {prompt}")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            tools=TYPIFY_TASK_TOOLS,
            tool_choice={"type": "function", "function": {"name":"typify_task"}}
        )
        function = response.choices[0].message.tool_calls[0].function
        if function:
            result = json.loads(function.arguments)
            logger.debug(f"OpenAI API response: {result}")
            return result
        else:
            fallback_result = {"error": "Unable to typify task"}
            logger.warning(f"OpenAI API fallback response: {fallback_result}")
            return fallback_result
    
    def generate_clarifying_questions(self, task: Task) -> dict:
        """Generate clarifying questions based on analysis and typification"""

        prompt = get_clarifying_questions_prompt(task)

        logger.debug(f"OpenAI API prompt: {prompt}")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            tools=CLARIFYING_QUESTIONS_TOOLS,
            tool_choice={"type": "function", "function": {"name":"generate_questions"}}
        )

        function = response.choices[0].message.tool_calls[0].function
        if function:
            result = json.loads(function.arguments)
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

        context = self._gather_context(task)
        prompt = get_generate_approaches_prompt(task, context)
        logger.debug(f"OpenAI API prompt: {prompt}")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt},],
            tools=GENERATE_APPROACHES_TOOLS,
            tool_choice={"type": "function", "function": {"name":"generate_approaches"}}
        )

        function = response.choices[0].message.tool_calls[0].function
        if function:
            result = json.loads(function.arguments)
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

        context = self._gather_context(task)
        prompt = get_decompose_task_prompt(task, context)

        logger.debug(f"OpenAI API prompt: {prompt}")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            tools=DECOMPOSE_TASK_TOOLS,
            tool_choice={"type": "function", "function": {"name":"decompose_task"}}
        )

        function = response.choices[0].message.tool_calls[0].function
        if function:
            result = json.loads(function.arguments)
            logger.debug(f"OpenAI API response: {result}")
            return result
        else:
            fallback_result = {
                "sub_tasks": None
            }
            logger.warning(f"OpenAI API fallback response: {fallback_result}")
            return fallback_result

    


