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
    if task.complexity == 1 or (task.level and "LEVEL_1" in task.level):
        return f"""
            Based on the task's characteristics, suggest specific, practical tools, methods, and frameworks
            that will help achieve the final result effectively. Focus on real-world, proven approaches.
            
            Task: {task.task}
            Short Description: {task.short_description}
            Context: {context}
            Level: {task.level}
            Complexity: {task.complexity}
            Contribution to Parent Task: {task.contribution_to_parent_task}
            Scope: {task.scope}
            Analysis: {task.analysis}

            APPROACHES RULES:
            1. Stay strictly within defined scope boundaries
            2. Do not approach aspects listed in "Explicitly Excludes"
            3. Consider only available resources and realistic constraints
            4. Focus on concrete, measurable deliverables
            5. Suggest only proven tools with demonstrated success
            6. Prioritize tools that directly contribute to the final result
            
            Requirements:
            1. First, provide exactly 3 tools for each category:
            - Analytical tools (T1-T3): Focus on specific software, techniques, or methodologies that are currently available
            - Practical methods (M1-M3): Include step-by-step processes that have been proven in similar contexts
            - Frameworks (F1-F3): Suggest established frameworks with documented success cases

            2. Then, create exactly 3 effective combinations where:
            - Each combination must include one tool from each category
            - Provide concrete examples of successful implementation
            - Include specific metrics or indicators of success
            - Explain exactly how this combination leads to the desired result

            Make sure all tools and combinations are:
            - Currently available and accessible
            - Have documented success cases
            - Include specific implementation steps
            - Provide measurable outcomes
            - Consider resource constraints

            Important: You must provide both tool categories AND tool combinations in your response.
            The tool combinations should reference the tools you defined using their IDs (T1-T3, M1-M3, F1-F3).
            For each tool, include at least one real-world example of successful implementation.
            """
    else:
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
            1. First, provide exactly 3 tools for each category:
            - Analytical tools (T1-T3)
            - Practical methods (M1-M3)
            - Frameworks (F1-F3)

            2. Then, create exactly 3 effective combinations where:
            - Each combination must include one tool from each category
            - Explain how they work together (synergy)
            - Provide a specific use case for the combination

            Make sure all tools and combinations are:
            - Specific to the task and domain
            - Matched to user's experience level
            - Practical and immediately applicable
            - Well-integrated with each other

            Important: You must provide both tool categories AND tool combinations in your response.
            The tool combinations should reference the tools you defined using their IDs (T1-T3, M1-M3, F1-F3).
            """