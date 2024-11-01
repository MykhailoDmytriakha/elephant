import json
from src.model.task import Task

ANALYZE_TASK_FUNCTIONS = [
    {
        "name": "analyze_task",
        "description": "Analyze the given task and context within defined scope boundaries.",
        "parameters": {
            "type": "object",
            "properties": {
                "analysis": {
                    "type": "object",
                    "properties": {
                        "ideal_final_result": {
                            "type": "string",
                            "description": "Ideal Final Result - The specific goals or results expected WITHIN the defined scope"
                        },
                        "parameters": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Key parameters that affect the task within its scope"
                        },
                        "constraints": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Key constraints from the defined scope and additional technical constraints"
                        },
                        "current_limitations": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Current limitations within the scope boundaries"
                        },
                        "contradictions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "improving_parameter": {
                                        "type": "string",
                                        "description": "Parameter we want to improve within scope"
                                    },
                                    "worsening_parameter": {
                                        "type": "string",
                                        "description": "Parameter that worsens as a result within scope"
                                    }
                                },
                                "required": ["improving_parameter", "worsening_parameter"]
                            },
                            "description": "Technical and physical contradictions identified within scope"
                        },
                        "available_resources": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Resources available within scope boundaries"
                        },
                        "required_resources": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Resources required within scope boundaries"
                        },
                        "missing_information": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Information missing for this specific scope"
                        }
                    },
                    "required": ["ideal_final_result", "parameters", "constraints", 
                               "current_limitations", "contradictions", 
                               "available_resources", "required_resources",
                               "missing_information"]
                }
            },
            "required": ["analysis"]
        }
    }
]

def get_analyze_task_prompt(task_description: str, context: str, scope: dict) -> str:
    if not task_description:
        raise ValueError("Task description is required")
    
    return f"""
    Analyze the following task strictly within its defined scope:

    TASK DEFINITION:
    {task_description}

    SCOPE BOUNDARIES:
    Includes:
    {json.dumps(scope.get('boundaries', {}).get('includes', []), indent=2)}
    
    Explicitly Excludes:
    {json.dumps(scope.get('boundaries', {}).get('excludes', []), indent=2)}
    
    Constraints:
    {json.dumps(scope.get('constraints', []), indent=2)}
    
    Dependencies:
    {json.dumps(scope.get('dependencies', []), indent=2)}
    
    Expected Deliverables:
    {json.dumps(scope.get('deliverables', []), indent=2)}

    CONTEXT:
    {context}

    ANALYSIS RULES:
    1. Stay strictly within defined scope boundaries
    2. Do not analyze aspects listed in "Explicitly Excludes"
    3. Consider only the resources and constraints relevant to this scope
    4. Focus analysis on delivering specified deliverables
    5. Identify contradictions only within scope boundaries

    Provide a detailed analysis focused ONLY on elements within these scope boundaries.
    If you identify aspects that might be important but are outside the scope,
    list them in "missing_information" but do not include in main analysis.
    """