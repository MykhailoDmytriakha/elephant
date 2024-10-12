import openai
import json
import os
from typing import Optional
from .task import Task, TaskState

class OpenAiService:
    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.model = self._get_openai_model()

    def _get_openai_model(self) -> str:
        model = os.getenv('OPENAI_MODEL')
        if not model:
            raise ValueError("OPENAI_MODEL environment variable is not set")
        return model
    
    def summarize_context(self, context: str) -> str:
        """
        Summarizes the given context using the OpenAI model.
        """
        prompt = f"Summarize the following context:\n{context}"
        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    
    def analyze_problem(self, origin_query: str, context: str) -> dict:
        """
        should return Json object 
        {
            "task": origin_query with context converted to a task
            "analysis": "Analysis of the problem"
            {
                "parameters_constraints": key parameters and constraints that affect the problem
                "available_resources": [stings: Details of the resources available for solving the problem.]
                "required_resources": [strings: Details of the resources required for solving the problem.]
                "ifr": IFR (ideal final result) The specific goals or results that are expected from solving the problem.
                "missing_information": [strings: Information that is missing and required to solve the problem or Details of any missing data or knowledge gaps that need to be addressed]
                complexity: Possible values: '1 is low', '2 is medium', '3 is high' - Represents the level of complexity of the problem.
            }
        }
        """
        functions = [
            {
                "name": "analyze_problem",
                "description": "Analyze the given problem and context, providing a structured analysis.",
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
                                    "description": "Key parameters and constraints that affect the problem"
                                },
                                "available_resources": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Details of the resources available for solving the problem"
                                },
                                "required_resources": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Details of the resources required for solving the problem"
                                },
                                "ifr": {
                                    "type": "string",
                                    "description": "Ideal Final Result - The specific goals or results expected from solving the problem"
                                },
                                "missing_information": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Information that is missing and required to solve the problem"
                                },
                                "complexity": {
                                    "type": "string",
                                    "enum": ["1", "2", "3"],
                                    "description": "Level of complexity of the problem (1: low, 2: medium, 3: high)"
                                }
                            },
                            "required": ["parameters_constraints", "available_resources", "required_resources", "ifr", "missing_information", "complexity"]
                        }
                    },
                    "required": ["task", "analysis"]
                }
            }
        ]

        prompt = f"""
        Analyze the following problem and context:
        Problem: {origin_query}
        Context: {context}

        Provide a detailed analysis of the problem, including task formulation, key parameters, resources, ideal final result, missing information, and complexity level.
        """
        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            functions=functions,
            function_call={"name": "analyze_problem"}
        )
        function_call = response.choices[0].message.function_call
        if function_call:
            return json.loads(function_call.arguments)
        else:
            # Fallback in case function calling doesn't work as expected
            return {
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

    def is_context_sufficient(self, task: Task) -> dict:
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
                            "description": "A question to ask the user if more context is needed"
                        }
                    },
                    "required": ["is_context_sufficient"] #TODO: sometimes is_context_sufficient = true and follow_up_question is not provided
                }
            }
        ]

        summarized_context = self.summarize_context(task.formatted_context) if task.context else ""
        prompt = f"""
        Given the following problem and context, determine if the context is sufficient for analysis:
        Problem: {task.origin_query}
        Context: {summarized_context}

        If the context is not sufficient, provide a follow-up question to gather more information.
        """
        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            functions=functions,
            function_call={"name": "context_analysis"}
        )
        function_call = response.choices[0].message.function_call
        if function_call:
            return json.loads(function_call.arguments)
        else:
            # Fallback in case function calling doesn't work as expected
            return {
                "is_context_sufficient": False,
                "follow_up_question": "Can you provide more details about the problem?"
            }

