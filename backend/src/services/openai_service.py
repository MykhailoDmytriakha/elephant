import json
import logging
from typing import TypedDict, List, Dict
from src.model.context import ContextSufficiencyResult, ContextQuestion
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
from src.model.context import ClarifiedTask
from src.ai_agents import context_sufficiency_agent, summarize_context_agent

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
    
    async def summarize_context(self, task: Task) -> ClarifiedTask:
        """
        Summarizes the context of the task base on user answers about the context.
        
        Args:
            task: The task containing the context information
            
        Returns:
            str: Summary of the context
        """
        logger.info("Called summarize_context method")
        try:
            # Use the extracted agent logic from the dedicated module
            return await summarize_context_agent.summarize_context(task)
        except ImportError as e:
            logger.warning(f"OpenAI Agents SDK not installed: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Error in summarize_context: {str(e)}")
            raise e

    
    async def is_context_sufficient(self, task: Task) -> ContextSufficiencyResult:
        """
        Determines if the gathered context is sufficient to understand and proceed with the task.
        
        Args:
            task: The task containing the context information
            
        Returns:
            ContextSufficiencyResult: Result indicating if context is sufficient and any follow-up questions with options
        """
        logger.info("Called is_context_sufficient method")
        
        try:
            # Use the extracted agent logic from the dedicated module
            return await context_sufficiency_agent.analyze_context_sufficiency(task)
        except ImportError as e:
            logger.warning(f"OpenAI Agents SDK not installed: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Error in is_context_sufficient: {str(e)}")
            raise e
            

    def formulate_task(self, task: Task) -> dict:
        """Formulate clear task definition based on gathered context"""
        try:
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
                fallback_result: Dict[str, object] = {
                    "task": task.short_description,
                    "is_context_sufficient": False,
                    "follow_up_question": "Could you provide more details about what needs to be accomplished?",
                    "scope": {}
                }
                logger.warning(f"OpenAI API fallback response: {fallback_result}")
                return fallback_result
        except Exception as e:
            logger.error(f"OpenAI API error in formulate_task: {str(e)}")
            fallback_result = {
                "task": task.short_description or "Task undefined due to technical issue",
                "is_context_sufficient": False,
                "follow_up_question": "I'm experiencing some technical difficulties with the task formulation. Could you provide more details about what you're trying to accomplish?",
                "scope": {}
            }
            logger.warning(f"OpenAI API error fallback response: {fallback_result}")
            return fallback_result

    def analyze_task(self, task: Task) -> dict:
        logger.info("Called analyze_task method")
        try:
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
        except Exception as e:
            logger.error(f"OpenAI API error in analyze_task: {str(e)}")
            fallback_result = {
                "error": "Unable to analyze task due to technical difficulties",
                "analysis": {
                    "parameters_constraints": "Technical difficulties occurred while analyzing parameters and constraints",
                    "available_resources": ["Technical issue encountered"],
                    "required_resources": ["Technical issue encountered"],
                    "ifr": "Technical difficulties occurred while determining ideal final result",
                    "missing_information": ["Please try again later"]
                }
            }
            logger.warning(f"OpenAI API error fallback response: {fallback_result}")
            return fallback_result
    
    def typify_task(self, task: Task) -> dict:
        logger.info("Called typify_task method")
        try:
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
        except Exception as e:
            logger.error(f"OpenAI API error in typify_task: {str(e)}")
            # Create a structured fallback for error cases
            error_fallback_result: Dict[str, Dict[str, object]] = {
                "typification": {
                    "classification": {
                        "domain": "Unknown due to technical issue",
                        "category": "Unknown due to technical issue",
                        "complexity_level": {"level": "LEVEL_1", "explanation": "Default due to technical issue"}
                    },
                    "eta": {"time": "Unknown", "explanation": "Technical difficulties encountered"},
                    "uncertainty_indicators": ["Technical issue encountered"]
                }
            }
            logger.warning(f"OpenAI API error fallback response: {error_fallback_result}")
            return error_fallback_result
    
    def generate_clarifying_questions(self, task: Task) -> dict:
        """Generate clarifying questions based on analysis and typification"""
        try:
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
        except Exception as e:
            logger.error(f"OpenAI API error in generate_clarifying_questions: {str(e)}")
            fallback_result = {
                "questions": [{
                    "question_id": "error_q1",
                    "question": "We're experiencing some technical difficulties. Could you provide more details about your requirements while we resolve this issue?",
                    "purpose": "Handle technical error",
                    "expected_value": "User requirements",
                    "priority": 1
                }],
                "stop_criteria": ["Technical issue handled"]
            }
            logger.warning(f"OpenAI API error fallback response: {fallback_result}")
            return fallback_result

    def generate_approaches(self, task: Task) -> dict:
        logger.info("Called generate_approaches method")
        try:
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
                fallback_result: Dict[str, object] = {
                    "approaches": None,
                    "tool_categories": [],
                    "tool_combinations": []
                }
                logger.warning(f"OpenAI API fallback response: {fallback_result}")
                return fallback_result
        except Exception as e:
            logger.error(f"OpenAI API error in generate_approaches: {str(e)}")
            fallback_result = {
                "approaches": None,
                "tool_categories": [
                    {
                        "category": "Technical Issue",
                        "explanation": "We're experiencing some technical difficulties",
                        "tools": [
                            {
                                "name": "Standard approach",
                                "description": "Default approach due to technical issue",
                                "benefits": ["Simplicity"],
                                "limitations": ["Generic solution"]
                            }
                        ]
                    }
                ],
                "tool_combinations": [
                    {
                        "name": "Standard Approach",
                        "tools": ["Standard approach"],
                        "workflow": "Technical issue encountered - using standard approach",
                        "benefits": ["Available despite technical difficulties"],
                        "limitations": ["Generic solution"]
                    }
                ]
            }
            logger.warning(f"OpenAI API error fallback response: {fallback_result}")
            return fallback_result

    def decompose_task(self, task: Task) -> dict:
        logger.info("Called decompose_task method")
        try:
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
                fallback_result: Dict[str, object] = {
                    "sub_tasks": None
                }
                logger.warning(f"OpenAI API fallback response: {fallback_result}")
                return fallback_result
        except Exception as e:
            logger.error(f"OpenAI API error in decompose_task: {str(e)}")
            # Create a basic subtask structure for default response
            error_fallback_result: Dict[str, List[Dict[str, object]]] = {
                "sub_tasks": [
                    {
                        "task": task.short_description or "Task",
                        "short_description": "Technical issue encountered",
                        "context": "We're experiencing technical difficulties",
                        "complexity_level": "LEVEL_1",
                        "order": 1,
                        "contribution_to_parent_task": "Full task (technical issue)",
                        "eta": {"time": "Unknown", "explanation": "Technical issue"},
                        "scope": {}
                    }
                ]
            }
            logger.warning(f"OpenAI API error fallback response: {error_fallback_result}")
            return error_fallback_result

    


