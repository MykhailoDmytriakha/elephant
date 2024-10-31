import json
from src.model.task import Task

GENERATE_APPROACHES_FUNCTIONS = [
{
    "name": "generate_approaches",
    "description": "Generate practical tools and methods based on task typification and suggest effective combinations",
    "parameters": {
        "type": "object",
        "properties": {
            "tool_categories": {
                "type": "object",
                "properties": {
                    "analytical_tools": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "tool_id": {"type": "string", "description": "Unique identifier for the tool: T1, T2, T3, etc."},
                                "name": {"type": "string"},
                                "purpose": {"type": "string"},
                                "when_to_use": {"type": "string"},
                                "contribution_to_task": {"type": "string", "description": "How this tool could help to solve the task"},
                                "ease_of_use": {
                                    "type": "string",
                                    "enum": ["BEGINNER", "INTERMEDIATE", "ADVANCED"]
                                },
                                "examples": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "required": ["tool_id", "name", "purpose", "when_to_use", "contribution_to_task", "ease_of_use", "examples"]
                        },
                        "description": "Tools for analysis and understanding, exactly 3 tools required",
                        "minItems": 3,
                        "maxItems": 5
                    },
                    "practical_methods": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "method_id": {"type": "string", "description": "Unique identifier for the method: M1, M2, M3, etc."},
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "best_for": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "difficulty_level": {
                                    "type": "string",
                                    "enum": ["EASY", "MODERATE", "COMPLEX"]
                                }
                            },
                            "required": ["method_id", "name", "description", "best_for", "difficulty_level"]
                        },
                        "description": "Practical methods and techniques, exactly 3 methods required",
                        "minItems": 3,
                        "maxItems": 5
                    },
                    "frameworks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "framework_id": {"type": "string", "description": "Unique identifier for the framework: F1, F2, F3, etc."},
                                "name": {"type": "string"},
                                "structure": {"type": "string"},
                                "how_to_use": {"type": "string", "description": "How this framework can be used to solve the task"},
                                "benefits": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "adaptation_tips": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "required": ["framework_id", "name", "structure", "how_to_use", "benefits", "adaptation_tips"]
                        },
                        "description": "Structured approaches and frameworks, exactly 3 frameworks required",
                        "minItems": 3,
                        "maxItems": 5
                    }
                },
                "required": ["analytical_tools", "practical_methods", "frameworks"]
            },
            "tool_combinations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "combination_name": {"type": "string"},
                        "tools": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of tool IDs in sequence: analytical tool (T1-T3), practical method (M1-M3), framework (F1-F3)",
                            "minItems": 3,
                            "maxItems": 3
                        },
                        "synergy_description": {"type": "string"},
                        "use_case": {"type": "string"}
                    },
                    "required": ["combination_name", "tools", "synergy_description", "use_case"]
                },
                "description": "Recommended combinations of tools, methods, and frameworks, at least 3 combinations required",
                "minItems": 3,
                "maxItems": 5
            }
        },
        "required": ["tool_categories", "tool_combinations"]
    }
}]

def get_generate_approaches_prompt(task: Task, context: str) -> str:
    return f"""
        Based on the task's characteristics and user preferences, suggest practical tools, methods, and frameworks
        that will help solve the task effectively. Then create effective combinations of these tools.
        
        Task: {task.task}
        Context: {context}
        Analysis: {task.analysis}
        Typification: {task.typification}

        Task Nature (from typification):
        - Primary: {task.typification['classification']['nature']['primary']}
        - Domain: {task.typification['classification']['domain']['primary']}
        - Complexity Level: {task.typification['classification']['complexity_level']['level']}

        User Context and Preferences:
        {json.dumps(task.clarification_data.get('answers', {}), ensure_ascii=False)}

        Requirements:
        1. Provide analytical tools (T1-T3)
        2. Provide practical methods (M1-M3)
        3. Provide frameworks (F1-F3)
        4. Create at least 3 effective combinations using these tools
        
        For each combination:
        - Include exactly one tool from each category (1 analytical tool, 1 method, 1 framework)
        - Explain how they work together (synergy)
        - Provide a specific use case

        Make sure all tools are:
        - Specific to the task and domain
        - Matched to user's experience level
        - Practical and immediately applicable
        - Well-integrated with each other
        """