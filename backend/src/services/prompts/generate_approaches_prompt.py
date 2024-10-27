import json
from src.model.task import Task

GENERATE_APPROACHES_FUNCTIONS = [
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

def get_generate_approaches_prompt(task: Task, context: str) -> str:
    return f"""
        Generate approaches to solve the following task:
        Task: {task.task}
        Ideal Final Result: {task.analysis.get('ideal_final_result', 'N/A')}
        Short Description: {task.short_description}
        Context: {context}
        Analysis: {json.dumps(task.analysis, ensure_ascii=False)}
        Typification: {json.dumps(task.typification, ensure_ascii=False)}
        Clarification: {json.dumps(task.clarification_data, ensure_ascii=False)}

        Provide a list of approaches that could potentially solve the problem.
        Include a description of how each approach helps solve the parent task.
        """