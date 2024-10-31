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
                        "complexity": {
                            "type": "string",
                            "enum": ["1", "2", "3", "4", "5"],
                            "description": "Estimated complexity of the sub-task (1: simple task: solution is known and easy to apply, 2: complex task: requires adaptation of known solutions, 3: very complex task: requires combining several approaches, 4: task with high level of innovation: requires creation of a new solution within the current paradigm, 5: task with the highest level of innovation: requires creation of a fundamentally new solution, possibly changing the paradigm)"
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
                        }
                    },
                    "required": ["task", "context", "complexity", "short_description", "contribution_to_parent_task"]
                },
                "description": "List of sub-tasks derived from the main task"
            }
        },
        "required": ["sub_tasks"]
    }
}]


def get_decompose_task_prompt(task: Task, context: str, complexity: int) -> str:
    return f"""
        Decompose the following complex task into smaller, manageable sub-tasks:
        Task: {task.task}
        Ideal Final Result: {task.analysis.get('ideal_final_result', 'N/A')}
        Context: {context}
        Analysis: {json.dumps(task.analysis, ensure_ascii=False)}
        Original Task Complexity: {complexity}
        Task Typification: {json.dumps(task.typification, ensure_ascii=False)}
        Task Approaches: {json.dumps(task.approaches, ensure_ascii=False)}

        Provide a list of sub-tasks, each with its own description, context, and complexity that helps to achieve the ideal final result.
        Ensure that each sub-task has a lower complexity than the original task complexity.
        Those sub-tasks should be as independent as possible and match context and analysis.
        There is typification and approaches for the task, so use them to create sub-tasks.
        ---
        The complexity levels are:
        1 - Level 1 (simple task: solution is known and easy to apply)
        2 - Level 2 (complex task: requires adaptation of known solutions)
        3 - Level 3 (very complex task: requires combining several approaches)
        4 - Level 4 (task with high level of innovation: requires creation of a new solution within the current paradigm)
        5 - Level 5 (task with the highest level of innovation: requires creation of a fundamentally new solution, possibly changing the paradigm)
        """