import json
from src.model.task import Task

DECOMPOSE_TASK_FUNCTIONS = [
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
                        "complexity_level": {
                            "description": "Classification of the task according to its complexity level",
                            "type": "string",
                            "enum": [
                                "LEVEL_1 (simple task: solution is known and easy to apply)",
                                "LEVEL_2 (complex task: requires adaptation of known solutions)",
                                "LEVEL_3 (very complex task: requires combining several approaches)",
                                "LEVEL_4 (task with high level of innovation: requires creation of a new solution within the current paradigm)",
                                "LEVEL_5 (task with the highest level of innovation: requires creation of a fundamentally new solution, possibly changing the paradigm)"
                            ]
                        },
                        "eta_to_complete": {
                            "type": "string",
                            "description": "Estimated time to complete the sub-task"
                        },
                        "short_description": {
                            "type": "string",
                            "description": "Short description of the sub-task"
                        },
                        "contribution_to_parent_task": {
                            "type": "string",
                            "description": "Explanation of how this sub-task contributes to achieving the overall goal of the parent task"
                        },
                        "order": {
                            "type": "integer",
                            "description": "The execution order of this sub-task (1-based indexing)"
                        }
                    },
                    "required": ["task", "context", "complexity", "short_description", "contribution_to_parent_task", "order"]
                }
            }
        }
    }
}]


def get_decompose_task_prompt(task: Task, context: str) -> str:
    return f"""
        Decompose the following complex task into smaller, manageable sub-tasks:
        Task: {task.task}
        Ideal Final Result: {task.analysis.get('ideal_final_result', 'N/A')}
        Context: {context}
        Analysis: {json.dumps(task.analysis, ensure_ascii=False)}
        Original Task Complexity: {task.level}
        Task Typification: {json.dumps(task.typification, ensure_ascii=False)}
        Task Approaches: {json.dumps(task.approaches, ensure_ascii=False)}

        Provide an ordered list of sub-tasks, each with its own description, context, and complexity that helps to achieve the ideal final result.
        Requirements:
        1. Each sub-task must have a lower complexity than the original task complexity
        2. Sub-tasks should be as independent as possible and match context and analysis
        3. Assign an order number to each sub-task indicating its execution sequence
        4. Use the provided typification and approaches to create appropriate sub-tasks
        ---
        The complexity levels are:
        1 - Level 1 (simple task: solution is known and easy to apply)
        2 - Level 2 (complex task: requires adaptation of known solutions)
        3 - Level 3 (very complex task: requires combining several approaches)
        4 - Level 4 (task with high level of innovation: requires creation of a new solution within the current paradigm)
        5 - Level 5 (task with the highest level of innovation: requires creation of a fundamentally new solution, possibly changing the paradigm)
        """