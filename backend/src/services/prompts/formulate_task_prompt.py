from src.model.task import Task
FORMULATE_TASK_FUNCTIONS = [{
    "name": "formulate_task",
    "description": "Formulate a clear task definition based on context and interactions",
    "parameters": {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "Clear and comprehensive task definition"
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
        "required": ["task", "is_context_sufficient", "follow_up_question"]
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