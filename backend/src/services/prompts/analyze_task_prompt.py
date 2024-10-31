ANALYZE_TASK_FUNCTIONS = [
            {
                "name": "analyze_task",
                "description": "Analyze the given task and context, providing a structured analysis.",
                "parameters": {
                    "type": "object",
                    "properties": {
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
                                }
                            },
                            "required": ["ideal_final_result", "parameters", "constraints", "current_limitations", "contradictions", 
                                         "available_resources", "required_resources",
                                         "missing_information"]
                        }
                    },
                    "required": ["analysis"]
                }
            }
        ]

def get_analyze_task_prompt(task_description: str, context: str) -> str:
    if not task_description:
        raise ValueError("Task description is required")
    return f"""
        Analyze the following task and context:
        Task: {task_description}
        Context: {context}

        Provide a detailed analysis of the task, including task formulation, key parameters, resources, ideal final result, missing information, and complexity level.
        """
