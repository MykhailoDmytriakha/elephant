from src.model.task import Task
# src/services/prompts/formulate_task_prompt.py
FORMULATE_TASK_FUNCTIONS = [{
    "name": "formulate_task",
    "description": "Formulate a clear task definition and scope based on context and interactions",
    "strict": True,
    "parameters": {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "Clear and comprehensive task definition"
            },
            "scope": {
                "type": "object",
                "properties": {
                    "boundaries": {
                        "type": "object",
                        "properties": {
                            "includes": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "What is included in this task's scope"
                            },
                            "excludes": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "What is explicitly excluded from this task's scope"
                            }
                        },
                        "required": ["includes", "excludes"]
                    },
                    "constraints": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Key constraints and limitations"
                    },
                    "dependencies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "External dependencies and requirements"
                    },
                    "deliverables": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Expected outputs and deliverables"
                    }
                },
                "required": ["boundaries", "constraints", "dependencies", "deliverables"]
            },
            "is_context_sufficient": {
                "type": "boolean",
                "description": "Whether the context is sufficient for task formulation"
            },
            "follow_up_question": {
                "type": "string",
                "description": "Question to ask if more context is needed"
            }
        },
        "required": ["task", "scope", "is_context_sufficient", "follow_up_question"]
    }
}]

def get_formulate_task_prompt(task: Task) -> str:
    return f"""
        Based on the following information, formulate a clear and comprehensive task definition:
        
        Original Query: {task.short_description}
        Context: {task.context}
        User Interactions: {task.formatted_user_interaction}
        
        Your task is to:
        1. Formulate a clear and comprehensive task definition
        2. Determine if the current context is sufficient
        3. If context is insufficient, provide a specific follow-up question
        
        The task definition should include:
        - Clear objectives
        - Scope
        - Key requirements
        - Known constraints
        """