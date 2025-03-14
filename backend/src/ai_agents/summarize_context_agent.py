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
    context_info = task.context or ""
    
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
    - CONTEXT: {context_info}
    - CONTEXT ANSWERS: {context_answers_text}

    OUTPUT REQUIREMENTS:
    1. Task clarification:
       - Based on all provided information, create a clear, concise task statement
       - Incorporate all essential requirements from the context and answers
       - Be specific and actionable
       - Format as a single paragraph with no bullet points

    2. Context summary:
       - Provide a comprehensive yet concise summary of all context information
       - Include all key requirements, constraints, and dependencies
       - Highlight important details and omit redundant information
       - Organize logically with appropriate structure

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
