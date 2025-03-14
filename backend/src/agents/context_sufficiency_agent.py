import logging
from typing import List, Dict, Optional
from pydantic import BaseModel
from agents import Agent, Runner

from src.model.context import ContextSufficiencyResult, ContextQuestion
from src.model.task import Task

logger = logging.getLogger(__name__)

try:
    from openai.agents import Agent, Runner
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI Agents SDK not installed. Some functionality will be limited.")
    AGENTS_SDK_AVAILABLE = False


class ContextSufficiencyOutput(BaseModel):
    """Output schema for the ContextSufficiencyAgent"""
    is_context_sufficient: bool
    questions: List[Dict[str, object]] = []


def analyze_context_sufficiency(
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
    Analyze the following task and context information to determine if there's sufficient context to proceed.
    
    TASK: {task_description}
    
    CONTEXT: {context_info}
    
    CONTEXT ANSWERS: {context_answers_text}
    
    If the context is insufficient, provide 1-3 questions to gather more information.
    Each question should be specific and focused on resolving ambiguities or filling gaps.
    For each question, provide 3-5 possible options if appropriate.
    """
    
    # Create the agent
    agent = Agent(
        name="ContextSufficiencyAgent",
        instructions=instructions,
        output_type=ContextSufficiencyOutput,
    )
    
    # Run the agent
    result = Runner.run_sync(agent, "Analyze context sufficiency for the task")
    
    # Process the response
    agent_output = result.final_output
    
    # Convert agent output to ContextSufficiencyResult
    questions = []
    for q in agent_output.questions:
        questions.append(ContextQuestion(
            question=q.get("question", ""),
            options=q.get("options", [])
        ))
    
    return ContextSufficiencyResult(
        is_context_sufficient=agent_output.is_context_sufficient,
        questions=questions
    )


def get_fallback_result() -> ContextSufficiencyResult:
    """
    Provides a fallback result when the agent cannot be used.
    
    Returns:
        ContextSufficiencyResult: Default fallback result
    """
    return ContextSufficiencyResult(
        is_context_sufficient=False,
        questions=[
            ContextQuestion(
                question="Could you provide more details about your requirements?",
                options=["Specific goals", "Technical constraints", "Timeline expectations"]
            ),
            ContextQuestion(
                question="What is the most important outcome you're looking for?",
                options=["Performance", "Usability", "Cost efficiency", "Long-term maintainability"]
            )
        ]
    )
