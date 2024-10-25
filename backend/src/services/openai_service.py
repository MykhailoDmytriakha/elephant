import json
import logging
from typing import TypedDict
from src.model.context import ContextSufficiencyResult
from openai import OpenAI

from src.core.config import settings
from src.model.task import Task

logger = logging.getLogger(__name__)

TRIZ_SYSTEM_PROMPT = """You are an AI assistant trained to help solve problems using TRIZ principles. Here are the 40 TRIZ principles:

1. Segmentation - Divide objects or systems into independent parts
2. Taking Out - Extract disturbing parts or properties
3. Local Quality - Transition from homogeneous to heterogeneous structures
4. Asymmetry - Replace symmetrical forms with asymmetrical ones
5. Merging - Combine identical or similar objects, make operations parallel
6. Universality - Make parts perform multiple functions
7. Nested Doll - Place objects inside each other
8. Anti-Weight - Compensate object's weight with lift or buoyancy
9. Preliminary Anti-Action - Preempt negative effects with opposing action
10. Preliminary Action - Perform required changes before needed
11. Beforehand Cushioning - Prepare emergency means beforehand
12. Equipotentiality - Eliminate need to raise or lower objects
13. The Other Way Round - Invert the action or process
14. Spheroidality - Use curves instead of straight lines
15. Dynamics - Allow characteristics to change for optimal operation
16. Partial or Excessive Actions - Use slightly more or less than required
17. Another Dimension - Move into additional dimensions
18. Mechanical Vibration - Oscillate or vibrate object
19. Periodic Action - Use periodic or pulsating actions
20. Continuity of Useful Action - Work continuously without idle phases
21. Skipping - Conduct process at high speed
22. "Blessing in Disguise" - Turn harmful factors into benefits
23. Feedback - Introduce feedback to improve process
24. Intermediary - Use intermediary carrier or process
25. Self-Service - Make object serve itself and perform auxiliary functions
26. Copying - Use simple copies instead of expensive objects
27. Cheap Short-Living Objects - Replace expensive with cheap disposables
28. Mechanics Substitution - Replace mechanical with other means
29. Pneumatics and Hydraulics - Use gas and liquid parts
30. Flexible Shells and Thin Films - Use flexible structures
31. Porous Materials - Make objects porous or add porous elements
32. Color Changes - Change color or transparency
33. Homogeneity - Make interacting objects from same material
34. Discarding and Recovering - Make parts disappear after use
35. Parameter Changes - Change physical state, concentration, flexibility
36. Phase Transitions - Use phase transitions
37. Thermal Expansion - Use thermal expansion or contraction
38. Strong Oxidants - Use enriched atmospheres
39. Inert Atmosphere - Replace normal environment with inert one
40. Composite Materials - Use multiple materials instead of uniform ones"""


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
        if not context and not formatted_user_interaction:
            logger.info("Context is empty. Skipping summarization.")
            return ""
        prompt = f"Summarize the following context: \n- {context}\n- {formatted_user_interaction}"
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
        current_task = task
        while current_task:
            if current_task.context:
                contexts.append(current_task.context)
            current_task = current_task.parent_task
        return "\n".join(contexts) if contexts else ""
    
    def is_context_sufficient(self, task: Task) -> ContextSufficiencyResult:
        logger.info("Called is_context_sufficient method")
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
        functions = [
            {
                "name": "analyze_task",
                "description": "Analyze the given task and context, providing a structured analysis.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "A refined and comprehensive task definition based on the original query and context, including clear objectives, scope, and any relevant constraints or requirements"
                        },
                        "analysis": {
                            "type": "object",
                            "properties": {
                                "ideal_final_result": {
                                    "type": "string",
                                    "description": "Ideal Final Result - The specific goals or results expected from solving the task"
                                },
                                "parameters": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Key parameters that affect the task"
                                },
                                "constraints": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Key constraints that affect the task"
                                },
                                "current_limitations": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Current limitations or drawbacks in the system"
                                },
                                "contradictions": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "improving_parameter": {
                                                "type": "string",
                                                "description": "Parameter we want to improve"
                                            },
                                            "worsening_parameter": {
                                                "type": "string",
                                                "description": "Parameter that worsens as a result"
                                            }
                                        },
                                        "required": ["improving_parameter", "worsening_parameter"]
                                    },
                                    "description": "Technical and physical contradictions identified in the system"
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
                                "missing_information": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Information that is missing and required to solve the task"
                                },
                                "complexity": {
                                    "type": "string",
                                    "enum": ["1", "2", "3", "4", "5"],
                                    "description": "Level of complexity of the task (1: simple, 2: low, 3: medium, 4: high, 5: very high)"
                                },
                                "eta": {
                                    "type": "object",
                                    "properties": {
                                        "time": {
                                            "type": "string",
                                            "description": "Estimated time to complete the task"
                                        },
                                        "reasoning": {
                                            "type": "string",
                                            "description": "Reasoning about the estimated time to complete the task"
                                        }
                                    },
                                    "required": ["time", "reasoning"]
                                }
                            },
                            "required": ["ideal_final_result", "parameters", "constraints", "current_limitations", "contradictions", 
                                         "available_resources", "required_resources",
                                         "missing_information", "complexity", "eta"]
                        }
                    },
                    "required": ["task", "analysis"]
                }
            }
        ]

        context = self._gather_context(task)
        prompt = f"""
        Analyze the following task and context:
        Task: {task.task or task.short_description}
        Context: {context}

        Provide a detailed analysis of the task, including task formulation, key parameters, resources, ideal final result, missing information, and complexity level.
        """
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
                    "missing_information": ["Unable to determine missing information"],
                    "complexity": "0"
                }
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
        Concepts: {json.dumps(task.concepts, ensure_ascii=False)}
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

    def generate_approaches(self, task: Task) -> dict:
        logger.info("Called generate_approaches method")
        functions = [
            {
                "name": "generate_approaches",
                "description": "Generate approaches to solve the task following TOP-TRIZ methodology",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "approaches": {
                            "type": "object",
                            "properties": {
                                "principles": {
                                    "type": "array",
                                    "items": { "type": "string" },
                                    "description": "TRIZ, ARIZ, TOP-TRIZ principles that should be applied to generate innovative solutions. Format: {principle_number} {principle_name}: {principle_description}"
                                },
                                "solution_by_principles": {
                                    "type": "array",
                                    "items": { "type": "string" },
                                    "description": "Different solutions that could potentially solve the problem in format: {principle_number} {principle_name}: {solution description}"
                                },
                                "approach_list": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "approach_id": {
                                                "type": "string",
                                                "description": "Unique identifier for the approach (e.g., 'A1', 'A2')."
                                            },
                                            "approach_name": {
                                                "type": "string",
                                                "description": "Name of the approach"
                                            },
                                            "description": {
                                                "type": "string",
                                                "description": "Detailed description of the approach"
                                            },
                                            "contribution_to_parent_task": {
                                                "type": "string",
                                                "description": "How this approach helps solve the parent task"
                                            },
                                            "applied_principles": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "principle_name": {
                                                            "type": "string",
                                                            "description": "Name of the TOP-TRIZ, TRIZ or ARIZ principle applied. Format: {principle_number}: {principle_name}"
                                                        },
                                                        "application_description": {
                                                            "type": "string",
                                                            "description": "How the principle is applied in this approach"
                                                        }
                                                    },
                                                    "required": ["principle_name", "application_description"]
                                                }
                                            },
                                            "resources": {
                                                "type": "array",
                                                "items": {
                                                    "type": "string",
                                                    "description": "Analysis of resources required for this approach"
                                                }
                                            }
                                        },
                                        "required": [
                                            "approach_id", 
                                            "approach_name",
                                            "description", 
                                            "contribution_to_parent_task", 
                                            "applied_principles",
                                            "resources"
                                        ]
                                    },
                                    "description": "List of generated approaches. Minimum 2, maximum 5"
                                },
                                "evaluation_criteria": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "approach_id": {
                                                "type": "string",
                                                "description": "Reference to the approach"
                                            },
                                            "ideality_score": {
                                                "type": "object",
                                                "properties": {
                                                    "score": {
                                                        "type": "number",
                                                        "description": "Score based on the Ideal Final Result (IFR) principle"
                                                    },
                                                    "reasoning": {
                                                        "type": "string",
                                                        "description": "Reasoning about the ideality score"
                                                    }
                                                },
                                                "required": ["score", "reasoning"]
                                            },
                                            "feasibility": {
                                                "type": "object",
                                                "properties": {
                                                    "score": {
                                                        "type": "number",
                                                        "minimum": 0,
                                                        "maximum": 1,
                                                        "description": "Technical feasibility score (0-1)"
                                                    },
                                                    "reasoning": {
                                                        "type": "string",
                                                        "description": "Reasoning about the feasibility score"
                                                    }
                                                },
                                                "required": ["score", "reasoning"]
                                            },
                                            "resource_efficiency": {
                                                "type": "object",
                                                "properties": {
                                                    "score": {
                                                        "type": "number",
                                                        "minimum": 0,
                                                        "maximum": 1,
                                                        "description": "Score for efficient use of available resources (0-1)"
                                                    },
                                                    "reasoning": {
                                                        "type": "string",
                                                        "description": "Reasoning about the resource efficiency score"
                                                    }
                                                },
                                                "required": ["score", "reasoning"]
                                            }
                                        },
                                        "required": [
                                            "approach_id", 
                                            "ideality_score", 
                                            "feasibility", 
                                            "resource_efficiency", 
                                        ]
                                    },
                                    "description": "Evaluation criteria for each approach"
                                }
                            },
                            "required": [
                                "principles",
                                "solution_by_principles",
                                "approach_list",
                                "evaluation_criteria"
                            ]
                        }
                    },
                    "required": ["approaches"]
                }
            }
        ]

        context = self._gather_context(task)
        prompt = f"""
        Generate approaches to solve the following task:
        Task: {task.task}
        Ideal Final Result: {task.analysis.get('ideal_final_result', 'N/A')}
        Short Description: {task.short_description}
        Context: {context}
        Analysis: {json.dumps(task.analysis, ensure_ascii=False)}

        Provide a list of approaches that could potentially solve the problem.
        Include a description of how each approach helps solve the parent task.
        """
        logger.debug(f"OpenAI API prompt: {prompt}")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": TRIZ_SYSTEM_PROMPT},
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
                "approaches": {
                    "principles": ["Approach generation failed"],
                    "solution_by_principles": ["Approach generation failed"],
                    "approach_list": ["Approach generation failed"],
                    "evaluation_criteria": ["Approach generation failed"],
                }
            }
            logger.warning(f"OpenAI API fallback response: {fallback_result}")
            return fallback_result




