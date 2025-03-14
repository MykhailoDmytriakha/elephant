import logging
from typing import List, Dict, Optional, Any
from src.core.config import settings
from src.model.task import Task
from src.model.context import ClarifiedTask
logger = logging.getLogger(__name__)

# Try to import the OpenAI Agents SDK
# Note: these imports might show linter errors if the SDK is not installed
# but they are handled gracefully at runtime
try:
    from agents import Agent, Runner  # type: ignore # noqa
    model = settings.OPENAI_MODEL
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI Agents SDK not installed. Some functionality will be limited.")
    AGENTS_SDK_AVAILABLE = False

async def summarize_context(
    task: Task,
) -> ClarifiedTask:
    """
    Uses OpenAI Agent SDK to summarize the context of a task.
    
    Args:
        task: The task containing the context information
        
    Returns:
        str: A concise summary of the context
    """
    if not AGENTS_SDK_AVAILABLE:
        logger.error("OpenAI Agents SDK not installed.")
        raise ImportError("OpenAI Agents SDK not installed. Please install with `pip install openai-agents`")

    # Prepare the task information
    task_description = task.task or task.short_description or ""
    
    # Format the context answers if available
    context_answers_text = ""
    if task.context_answers:
        context_answers_text = "\n".join([
            f"Q: {answer.question}\nA: {answer.answer}" 
            for answer in task.context_answers
        ])
    
    # Create the instruction for the agent
    instructions = f"""
    You are a Context Analysis Agent designed to process task information and create structured summaries.

    Your task is to analyze the following information and produce two distinct outputs:
    1. A clarified task statement
    2. A comprehensive context summary

    INPUT:
    - TASK: {task_description}
    - CONTEXT ANSWERS: {context_answers_text}

    OUTPUT REQUIREMENTS:
    1. Task clarification:
       - Start with the core objective in one clear sentence
       - List primary requirements in order of priority
       - Include specific measurable outcomes or deliverables
       - Use active voice and direct language
       - Limit to 2-3 sentences maximum
       - Avoid parenthetical expressions and nested clauses

    2. Context summary:
       - Analyze and synthesize the context answers to identify:
         * Core user requirements and preferences
         * Any evolution or refinement of requirements through Q&A
         * Conflicts in answers and their resolutions
       - Structure the summary into these key aspects:
         * Main objectives (from initial task and refined through Q&A)
         * User preferences and constraints
         * Technical requirements
         * Important clarifications or changes from the Q&A process
       - Keep focus on information actually provided in answers
       - Highlight dependencies between different requirements
       - Note any gaps or ambiguities that might need further clarification

    3. Quality checks:
       - Verify that task statement is actionable and measurable
       - Ensure context captures all decision points from Q&A
       - Confirm no loss of critical details in summarization
       - Check for clarity and readability

    The output must be formatted as a JSON object with 'task' and 'context' fields.
    """
    
    # Create the agent
    agent = Agent(
        name="ContextSummaryAgent",
        instructions=instructions,
        output_type=ClarifiedTask,
        model=model
    )
    
    # Run the agent
    result = await Runner.run(agent, "Summarize the context of the task and clarify the task")
    
    # Process the response
    clarified_task = result.final_output
    logger.info(f"Clarified task: {clarified_task}")
    return clarified_task
