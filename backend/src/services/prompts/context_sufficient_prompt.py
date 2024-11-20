import json
from src.model.task import Task

CONTEXT_SUFFICIENT_FUNCTIONS = [
    {
        "name": "context_analysis",
        "parameters": {
            "type": "object",
            "properties": {
                "is_context_sufficient": {
                    "type": "boolean"
                },
                "gathered_information": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key points already gathered from previous interactions"
                },
                "follow_up_question": {
                    "type": "string"
                },
                "scope_alignment": {
                    "type": "object",
                    "properties": {
                        "deliverables_readiness": {
                            "type": "object",
                            "description": "Status of each deliverable",
                            "additionalProperties": {
                                "type": "boolean"
                            }
                        },
                        "missing_elements": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Critical elements still missing for deliverables"
                        }
                    },
                    "required": ["deliverables_readiness", "missing_elements"]
                }
            },
            "required": ["is_context_sufficient", "gathered_information", "follow_up_question", "scope_alignment"]
        }
    }
]

CONTEXT_SUFFICIENT_TOOLS = [
    {
        "type": "function",
        "function": CONTEXT_SUFFICIENT_FUNCTIONS[0],
        "strict": True
    }
]

def get_context_sufficient_prompt(task: Task, summarized_context: str) -> str:
    previous_interactions = "\n".join([
        f"Q: {interaction.query}\nA: {interaction.answer}"
        for interaction in task.user_interaction
    ])

    scope_context = ""
    if task.scope:
        scope_context = f"""
        TASK SCOPE BOUNDARIES:
        Must Include:
        {json.dumps(task.scope.get('boundaries', {}).get('includes', []), indent=2)}
        
        Must Exclude:
        {json.dumps(task.scope.get('boundaries', {}).get('excludes', []), indent=2)}
        
        Required Deliverables:
        {json.dumps(task.scope.get('deliverables', []), indent=2)}
        """

    return f"""
        Determine if the current context is sufficient to understand and proceed with the task.
        
        CURRENT TASK: {task.task or task.short_description}
        CURRENT CONTEXT: {summarized_context}

        PREVIOUS INTERACTIONS:
        {previous_interactions}

        {scope_context}

        EVALUATION PROCESS:
        1. Review previous interactions carefully:
           - If you see 3 or more responses indicating "no idea", "don't know", "нет", "не знаю" or similar:
             * Consider this a signal that the user has provided all available information
             * Mark context as sufficient and proceed
           - If you see the same type of questions being asked repeatedly without new information:
             * Consider the current context as the best available
             * Mark as sufficient and move forward
           - If responses are becoming shorter or less informative:
             * Take this as an indication that we've gathered all available information
             * Mark context as sufficient

        2. Assess Context Quality:
           - Is there enough information to understand the basic task requirements?
           - Have we identified at least one clear criterion or preference?
           - Is there a pattern in the user's responses that indicates their priorities?

        3. Consider Language and Communication:
           - Are responses in multiple languages? This is okay.
           - Short or informal responses are acceptable
           - Focus on the meaning rather than the format of responses

        4. Only if truly necessary:
           - Ask ONE final, critical question
           - Make it specific and focused
           - Avoid repeating previously asked topics

        RESPONSE REQUIREMENTS:
        1. First, analyze the pattern of responses
        2. List key information already gathered (even if minimal)
        3. Then decide:
           - If any pattern of "no more information" is detected -> mark as sufficient
           - If we have at least basic requirements -> mark as sufficient
           - Only if critically unclear -> ask one final question
        4. Explain your decision briefly
        """