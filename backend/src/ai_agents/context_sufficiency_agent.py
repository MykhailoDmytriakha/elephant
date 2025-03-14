import logging
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from src.core.config import settings
from src.model.context import ContextSufficiencyResult, ContextQuestion
from src.model.task import Task

logger = logging.getLogger(__name__)
try:
    from agents import Agent, Runner
    model = settings.OPENAI_MODEL
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI Agents SDK not installed. Some functionality will be limited.")
    AGENTS_SDK_AVAILABLE = False

async def analyze_context_sufficiency(
    task: Task,
) -> ContextSufficiencyResult:
    """
    Uses OpenAI Agent SDK to determine if the gathered context is sufficient.
    
    Args:
        task: The task containing the context information
        
    Returns:
        ContextSufficiencyResult: Result indicating if context is sufficient and any follow-up questions
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
    Analyze the following task and context information to determine if there's sufficient context to proceed.
    
    TASK: {task_description}    
    CONTEXT ANSWERS: {context_answers_text}
    
    If the context is insufficient, provide questions to gather more information.
    Each question should be specific and focused on resolving ambiguities or filling gaps.
    For each question, provide 3-5 possible options if appropriate.
    Do not include options like "both", "all", "none", etc.
    Your analysis should be thorough and comprehensive. Ask as many clarifying questions as needed to ensure all aspects of the task are fully understood and all potential ambiguities are resolved. The questions should systematically cover all dimensions of the task context to leave no significant gaps in understanding.
    """
    
    # Create the agent
    agent = Agent(
        name="ContextSufficiencyAgent",
        instructions=instructions,
        output_type=ContextSufficiencyResult,
        model=model
    )
    
    # Run the agent
    result = await Runner.run(agent, "Analyze context sufficiency for the task")
    
    # Process the response
    result = result.final_output
    logger.info(f"Context sufficiency result: {result}")
    return result
