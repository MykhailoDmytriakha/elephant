import json
from src.model.task import Task

GENERATE_APPROACHES_FUNCTIONS = [
{
    "name": "generate_approaches",
    "description": "Generate practical tools and methods based on task typification",
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
                                "tool_id": {"type": "string", "description": "Unique identifier for the tool: A1, A2, A3, etc."},
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
                        "description": "Tools for analysis and understanding, at least 3"
                    },
                    "practical_methods": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "method_id": {"type": "string", "description": "Unique identifier for the method: P1, P2, P3, etc."},
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
                        "description": "Practical methods and techniques, at least 3"
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
                        "description": "Structured approaches and frameworks, at least 3"
                    }
                }
            },
            "user_preferences_matching": {
                "type": "object",
                "properties": {
                    "recommended_tools": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "tool_id": {"type": "string"},
                                "match_reason": {"type": "string"},
                                "alignment_with_preferences": {"type": "string"}
                            },
                            "required": ["tool_id", "match_reason", "alignment_with_preferences"]
                        }
                    },
                    "alternative_options": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "tool_id": {"type": "string"},
                                "trade_offs": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "required": ["tool_id", "trade_offs"]
                        }
                    }
                }
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
                            "description": "Array of tool IDs in sequence: analytical tool (A1-A3), practical method (P1-P3), framework (F1-F3). Example: [A1, P1, F1]"
                        },
                        "synergy_description": {"type": "string"},
                        "use_case": {"type": "string"}
                    },
                    "required": ["combination_name", "tools", "synergy_description", "use_case"]
                }
            }
        },
        "required": ["tool_categories", "user_preferences_matching", "tool_combinations"]
    }
}
]

def get_generate_approaches_prompt(task: Task, context: str) -> str:
    # todo: implement this
    return f"""
        Based on the task's characteristics and user preferences, suggest practical tools and methods
        that will help solve the task effectively - think of these as equipment for the journey.
        
        Task: {task.task}
        Context: {context}
        Analysis: {task.analysis}
        Typification: {task.typification}

        Task Nature (from typification):
        - Primary: {task.typification['classification']['nature']['primary']}
        - Domain: {task.typification['classification']['domain']['primary']}
        - Complexity Level: {task.typification['classification']['complexity_level']['level']}

        User Context and Preferences:
        {json.dumps(task.clarification_data['answers'], ensure_ascii=False)}

        Suggest three categories of tools:

        1. Analytical Tools
           - What tools will help understand and analyze the problem?
           - Include both simple and advanced options
           - Specify when each tool is most useful
           - Provide real examples of usage

        2. Practical Methods
           - What concrete techniques can be applied?
           - Include methods for different skill levels
           - Explain how each method helps
           - Highlight when to use each method

        3. Frameworks
           - What structured approaches can guide the work?
           - How can they be adapted to this specific case?
           - What benefits does each framework provide?
           - Include tips for effective use
           
        Consider user preferences:
        - Match tools to user's experience level
        - Consider available resources
        - Account for time constraints
        - Provide alternatives for different scenarios

        For each tool/method:
        - Be specific about its purpose and value
        - Explain why it's suitable for this task
        - Indicate difficulty level and learning curve
        - Suggest how it can be combined with others

        The goal is to give the user a practical toolset they can choose from,
        like selecting the right equipment for a journey. Each tool should have
        a clear purpose and be immediately applicable.
        """