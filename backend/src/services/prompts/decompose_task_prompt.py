import json
from src.model.task import Task

DECOMPOSE_TASK_FUNCTIONS = [
{
    "name": "decompose_task",
    "description": "Decompose a complex task into smaller sub-tasks with clear scopes",
    "strict": True,
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
                            "description": "The comprehensive description of the sub-task"
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
                                            "description": "What is included in this sub-task's scope"
                                        },
                                        "excludes": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "description": "What is explicitly excluded from this sub-task's scope"
                                        }
                                    },
                                    "required": ["includes", "excludes"]
                                },
                                "constraints": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Constraints specific to this sub-task"
                                },
                                "dependencies": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Dependencies specific to this sub-task"
                                },
                                "deliverables": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Expected outputs from this sub-task"
                                }
                            },
                            "required": ["boundaries", "constraints", "dependencies", "deliverables"]
                        },
                        "context": {
                            "type": "string",
                            "description": "Technical context specific to this sub-task"
                        },
                        "complexity_level": {
                            "type": "string",
                            "enum": [
                                "LEVEL_1 (simple task: solution is known and easy to apply)",
                                "LEVEL_2 (complex task: requires adaptation of known solutions)",
                                "LEVEL_3 (very complex task: requires combining several approaches)",
                                "LEVEL_4 (task with high level of innovation: requires creation of a new solution within the current paradigm)",
                                "LEVEL_5 (task with the highest level of innovation: requires creation of a fundamentally new solution, possibly changing the paradigm)"
                            ]
                        },
                        "short_description": {
                            "type": "string",
                            "description": "Brief description of the sub-task"
                        },
                        "contribution_to_parent_task": {
                            "type": "string",
                            "description": "How this sub-task contributes to parent task"
                        },
                        "order": {
                            "type": "integer",
                            "description": "Execution order (1-based)"
                        },
                        "eta": {
                            "description": "Estimated time to complete the task",
                            "type": "object",
                            "properties": {"time": {"type": "string"}, "reasoning": {"type": "string"}},
                            "required": ["time", "reasoning"]
                        }
                    },
                    "required": [
                        "task",
                        "scope",
                        "context",
                        "complexity_level",
                        "short_description",
                        "contribution_to_parent_task",
                        "order",
                        "eta"
                    ]
                }
            }
        },
        "required": ["sub_tasks"]
    }
}]

def get_decompose_task_prompt(task: Task, context: str) -> str:
    return f"""
    Your task is to decompose the given task into smaller sub-tasks with clear scopes.

    PARENT TASK:
    {task.task}

    PARENT SCOPE:
    {json.dumps(task.scope, indent=2)}

    SELECTED APPROACHES:
    {json.dumps(task.approaches.get('selected_approaches', {}), indent=2)}

    DECOMPOSITION RULES:
    1. Scope Inheritance:
       - Each sub-task's scope must be a SUBSET of parent task's scope
       - Sub-task boundaries must not overlap with other sub-tasks
       - Explicitly define what's excluded from each sub-task
       - Together, sub-task scopes must cover entire parent scope

    2. Scope Definition:
       - Define clear boundaries (includes/excludes)
       - List specific constraints
       - Identify dependencies
       - Specify deliverables

    3. Responsibility Separation:
       Parent task owns:
       - Overall testing/validation
       - Feedback collection
       - Integration
       - Deployment

       Sub-tasks handle:
       - Specific implementation details
       - Clear deliverables
       - Focused responsibilities

    4. Time Estimation:
       - Provide realistic time estimates for each sub-task
       - Include explanation for the estimates
       - Consider complexity and dependencies

    Create focused sub-tasks that solve specific parts of the parent task.
    Each sub-task must have lower complexity than parent task's level: {task.level}
    """