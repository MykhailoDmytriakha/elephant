import openai
import json
import os
import logging
from typing import Optional
from .task import Task, TaskState

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class OpenAiService:
    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.model = self._get_openai_model()

    def _get_openai_model(self) -> str:
        model = os.getenv('OPENAI_MODEL')
        if not model:
            raise ValueError("OPENAI_MODEL environment variable is not set")
        return model
    
    def summarize_context(self, formatted_user_interaction:str, context: str) -> str:
        logging.info("Called summarize_context method")
        if not context and not formatted_user_interaction:
            logging.info("Context is empty. Skipping summarization.")
            return ""
        prompt = f"Summarize the following context:\n{context}\n{formatted_user_interaction}"
        logging.info(f"OpenAI API prompt: {prompt}")
        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.choices[0].message.content
        logging.info(f"OpenAI API response: {result}")
        return result

    def _gather_context(self, task: Task) -> str:
        contexts = []
        current_task = task
        while current_task:
            if current_task.context:
                contexts.append(current_task.context)
            current_task = current_task.parent_task
        return "\n".join(contexts) if contexts else ""
    
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
                                "ifr": {
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
                                    "enum": ["1", "2", "3"],
                                    "description": "Level of complexity of the task (1: low, 2: medium, 3: high)"
                                }
                            },
                            "required": ["parameters_constraints", "available_resources", "required_resources", "ifr", "missing_information", "complexity"]
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
        logging.info(f"OpenAI API prompt: {prompt}")
        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            functions=functions,
            function_call={"name": "analyze_task"}
        )
        function_call = response.choices[0].message.function_call
        if function_call:
            result = json.loads(function_call.arguments)
            logging.info(f"OpenAI API response: {result}")
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
            logging.info(f"OpenAI API fallback response: {fallback_result}")
            return fallback_result

    def is_context_sufficient(self, task: Task) -> dict:
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
                            "description": "A question to ask the user if more context is needed. If context is sufficient, provide a summary instead."
                        }
                    },
                    "required": ["is_context_sufficient", "follow_up_question"]
                }
            }
        ]

        summarized_context = self.summarize_context(task.formatted_user_interaction, task.context) if not task.is_context_sufficient else task.context
        prompt = f"""
        Given the following problem and context, determine if the context is sufficient for analysis:
        Problem: {task.task or task.origin_query}
        Context: {summarized_context}

        If the context is not sufficient, provide a follow-up question to gather more information.
        If the context is sufficient, provide a brief summary of the context instead.
        """
        logging.info(f"OpenAI API prompt: {prompt}")
        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            functions=functions,
            function_call={"name": "context_analysis"}
        )
        function_call = response.choices[0].message.function_call
        if function_call:
            result = json.loads(function_call.arguments)
            logging.info(f"OpenAI API response: {result}")
            if result["is_context_sufficient"]:
                task.context = summarized_context
                task.is_context_sufficient = True
            return result
        else:
            fallback_result = {
                "is_context_sufficient": False,
                "follow_up_question": "Can you provide more details about the problem?"
            }
            logging.info(f"OpenAI API fallback response: {fallback_result}")
            return fallback_result

    def decompose_task(self, task: Task) -> dict:
        logging.info("Called decompose_task method")
        functions = [
            {
                "name": "decompose_task",
                "description": "Decompose a complex task into smaller, manageable sub-tasks.",
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
                                    }
                                },
                                "required": ["task", "context"]
                            },
                            "description": "List of sub-tasks derived from the main task, maximum 2" #TODO: remove limitation
                        }
                    },
                    "required": ["sub_tasks"]
                }
            }
        ]

        context = self._gather_context(task)
        prompt = f"""
        Decompose the following complex task into smaller, manageable sub-tasks:
        Task: {task.task}
        Context: {context}
        Analysis: {json.dumps(task.analysis)}

        Provide a list of sub-tasks, each with its own description and context.
        """
        logging.info(f"OpenAI API prompt: {prompt}")
        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            functions=functions,
            function_call={"name": "decompose_task"}
        )
        function_call = response.choices[0].message.function_call
        if function_call:
            result = json.loads(function_call.arguments)
            logging.info(f"OpenAI API response: {result}")
            return result
        else:
            fallback_result = {
                "sub_tasks": [
                    {
                        "origin_query": "Unable to decompose task",
                        "context": "Task decomposition failed"
                    }
                ]
            }
            logging.info(f"OpenAI API fallback response: {fallback_result}")
            return fallback_result
