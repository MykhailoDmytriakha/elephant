from src.model.task import Task

CONTEXT_SUFFICIENT_FUNCTIONS = [
            {
                "name": "context_analysis",
                "description": "Analyze if the given context is sufficient for the problem and suggest a question if more information is needed.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "is_context_sufficient": {
                            "type": "boolean",
                            "description": "Whether the given context is sufficient for analysis"
                        },
                        "follow_up_question": {
                            "type": "string",
                            "description": "A question to ask the user if more context is needed. In addition to follow-up questions, suggest possible context to add or variations of relevant context or scopes. If context is sufficient, provide a summary instead."
                        }
                    },
                    "required": ["is_context_sufficient", "follow_up_question"]
                }
            }
        ]

def get_context_sufficient_prompt(task: Task, summarized_context: str) -> str:
    return f"""
        Given the following problem and context, determine if the context is sufficient for analysis:
        Problem: {task.task or task.short_description}
        Context: {summarized_context}

        If the context is not sufficient, provide a follow-up question to gather more information.
        If the context is sufficient, provide a brief summary of the context instead.
        """