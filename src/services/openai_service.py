import json
import logging
from typing import TypedDict
from src.model.context import ContextSufficiencyResult
import openai

from src.core.config import settings
from src.model.task import Task

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



class OpenAIService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL

    def summarize_context(self, formatted_user_interaction: str, context: str) -> str:
        logging.info("Called summarize_context method")
        if not context and not formatted_user_interaction:
            logging.info("Context is empty. Skipping summarization.")
            return ""
        prompt = f"Summarize the following context: \n- {context}\n- {formatted_user_interaction}"
        logging.debug(f"OpenAI API prompt: {prompt}")
        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.choices[0].message.content
        logging.debug(f"OpenAI API response: {result}")
        return result

    @staticmethod
    def _gather_context(task: Task) -> str:
        contexts = []
        current_task = task
        while current_task:
            if current_task.context:
                contexts.append(current_task.context)
            current_task = current_task.parent_task
        return "\n".join(contexts) if contexts else ""
    
    def is_context_sufficient(self, task: Task) -> ContextSufficiencyResult:
        logging.info("Called is_context_sufficient method")
        functions = [
            {
                "name": "context_analysis",
                "description": "Analyze if the given context is sufficient for the problem and suggest a question if more information is needed.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "is_context_sufficient": {
                            "type": "boolean",
                            "description": "Whether the given context is sufficient for analysis"
                        },
                        "follow_up_question": {
                            "type": "string",
                            "description": "A question to ask the user if more context is needed. In addition to follow-up questions, suggest possible context to add or variations of relevant context or scopes. If context is sufficient, provide a summary instead."
                        }
                    },
                    "required": ["is_context_sufficient", "follow_up_question"]
                }
            }
        ]

        summarized_context = self.summarize_context(task.formatted_user_interaction, task.context) if not task.is_context_sufficient else task.context
        prompt = f"""
        Given the following problem and context, determine if the context is sufficient for analysis:
        Problem: {task.task or task.short_description}
        Context: {summarized_context}

        If the context is not sufficient, provide a follow-up question to gather more information.
        If the context is sufficient, provide a brief summary of the context instead.
        """
        logging.debug(f"OpenAI API prompt: {prompt}")
        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            functions=functions,
            function_call={"name": "context_analysis"}
        )
        function_call = response.choices[0].message.function_call
        if function_call:
            result = json.loads(function_call.arguments)
            logging.debug(f"OpenAI API response: {result}")
            return ContextSufficiencyResult(
                is_context_sufficient=result["is_context_sufficient"],
                follow_up_question=result["follow_up_question"]
            )
        else:
            fallback_result = ContextSufficiencyResult(
                is_context_sufficient=False,
                follow_up_question="Can you provide more details about the problem?"
            )
            logging.warning(f"OpenAI API fallback response: {fallback_result}")
            return fallback_result

    def analyze_task(self, task: Task) -> dict:
        logging.info("Called analyze_task method")
        functions = [
            {
                "name": "analyze_task",
                "description": "Analyze the given task and context, providing a structured analysis.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "The original query with context converted to a task"
                        },
                        "analysis": {
                            "type": "object",
                            "properties": {
                                "parameters_constraints": {
                                    "type": "string",
                                    "description": "Key parameters and constraints that affect the task"
                                },
                                "available_resources": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Details of the resources available for solving the task"
                                },
                                "required_resources": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Details of the resources required for solving the task"
                                },
                                "ideal_final_result": {
                                    "type": "string",
                                    "description": "Ideal Final Result - The specific goals or results expected from solving the task"
                                },
                                "missing_information": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Information that is missing and required to solve the task"
                                },
                                "complexity": {
                                    "type": "string",
                                    "enum": ["1", "2", "3", "4", "5"],
                                    "description": "Level of complexity of the task (1: simple, 2: low, 3: medium, 4: high, 5: very high)"
                                }
                            },
                            "required": ["parameters_constraints", "available_resources", "required_resources", "ifr",
                                         "missing_information", "complexity"]
                        }
                    },
                    "required": ["task", "analysis"]
                }
            }
        ]

        context = self._gather_context(task)
        prompt = f"""
        Analyze the following task and context:
        Task: {task.task}
        Context: {context}

        Provide a detailed analysis of the task, including task formulation, key parameters, resources, ideal final result, missing information, and complexity level.
        """
        logging.debug(f"OpenAI API prompt: {prompt}")
        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            functions=functions,
            function_call={"name": "analyze_task"}
        )
        function_call = response.choices[0].message.function_call
        if function_call:
            result = json.loads(function_call.arguments)
            logging.debug(f"OpenAI API response: {result}")
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
                    "missing_information": ["Unable to determine missing information"],
                    "complexity": "0"
                }
            }
            logging.warning(f"OpenAI API fallback response: {fallback_result}")
            return fallback_result

    def decompose_task(self, task: Task) -> dict:
        logging.info("Called decompose_task method")
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
                                        "description": "The sub-task description"
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
        Analysis: {json.dumps(task.analysis)}
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

        logging.debug(f"OpenAI API prompt: {prompt}")
        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            functions=functions,
            function_call={"name": "decompose_task"}
        )

        function_call = response.choices[0].message.function_call
        if function_call:
            result = json.loads(function_call.arguments)
            logging.debug(f"OpenAI API response: {result}")
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
            logging.warning(f"OpenAI API fallback response: {fallback_result}")
            return fallback_result

    def generate_concepts(self, task: Task) -> dict:
        logging.info("Called generate_concepts method")
        functions = [
            {
                "name": "generate_concepts",
                "description": "Generate concepts and ideas to solve the given task.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "concepts": {
                            "type": "object",
                            "properties": {
                                "contribution_to_parent_task": {
                                    "type": "string",
                                    "description": "Description of how the concept contributes to solving the parent task"
                                },
                                "ideas": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of ideas generated to solve the problem"
                                },
                                "TOP_TRIZ_principles": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "TRIZ, ARIZ, TOP-TRIZ principles that should be applied to generate innovative solutions."
                                },
                                "solution_approaches": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Different approaches that could potentially solve the problem in format: {TOP_TRIZ_principle}: {approach description}"
                                },
                                "resources_per_concept": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "concept": {
                                                "type": "string",
                                                "description": "Concept or idea to solve the problem"
                                            },
                                            "resources": {
                                                "type": "string",
                                                "description": "Analysis of resources required for each potential solution concept"
                                            }
                                        },
                                        "required": ["concept", "resources"]
                                    },
                                    "description": "Analysis of resources required for each potential solution concept"
                                }
                            },
                            "required": ["contribution_to_parent_task", "ideas", "TOP_TRIZ_applied", "solution_approaches", "resources_per_concept"]
                        }
                    },
                    "required": ["concepts"]
                }
            }
        ]

        context = self._gather_context(task)
        prompt = f"""
        Generate concepts and ideas to solve the following task:
        Task: {task.task}
        Ideal Final Result: {task.analysis.get('ideal_final_result', 'N/A')}
        Short Description: {task.short_description}
        Context: {context}
        Analysis: {json.dumps(task.analysis)}

        Provide a list of concepts and ideas that could potentially solve the problem.
        Include a description of how each concept contributes to solving the parent task.
        """
        logging.debug(f"OpenAI API prompt: {prompt}")
        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            functions=functions,
            function_call={"name": "generate_concepts"}
        )

        function_call = response.choices[0].message.function_call
        if function_call:
            result = json.loads(function_call.arguments)
            logging.debug(f"OpenAI API response: {result}")
            return result
        else:
            fallback_result = {
                "concepts": {
                    "contribution_to_parent_task": "Unable to generate concepts",
                    "ideas": ["Concept generation failed"],
                    "TOP_TRIZ_applied": False,
                    "solution_approaches": ["Concept generation failed"],
                    "resources_per_concept": [
                        {
                            "concept": "Concept generation failed",
                            "resources": "N/A"
                        }
                    ]
                }
            }
            logging.warning(f"OpenAI API fallback response: {fallback_result}")
            return fallback_result