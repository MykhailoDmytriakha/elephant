import logging
from typing import List, Dict, Optional, Any
from src.core.config import settings
from src.model.task import Task
from src.model.context import ClarifiedTask
from src.ai_agents.utils import detect_language, get_language_instruction

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
    
    # Detect language from task description
    task_description = task.short_description or ""
    user_language = detect_language(task_description)
    logger.info(f"Detected language: {user_language}")
    
    # Get language-specific instruction
    language_instruction = get_language_instruction(user_language)
    
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
    INITIAL USER INPUT: {task.short_description}
    ---
    TASK: {task.task}
    ---
    CONTEXT ANSWERS: {context_answers_text}
    ---
    {language_instruction}

    OUTPUT REQUIREMENTS:
    1. Task clarification (What needs to be built):
       - Begin with a single concise sentence stating the core objective
       - Include only essential requirements in order of priority
       - Define clear, measurable outcomes or deliverables
       - Use active voice and direct language
       - Limit to 3-5 lines maximum
       - Avoid parenthetical expressions and nested clauses

    2. Context summary (How it should be implemented):
       - Organize information into these clear sections:
         * Core Functionality (essential features)
         * User Experience (user-facing considerations)
         * Technical Requirements (implementation details)
         * Open Questions (items needing further clarification)
       - For each section:
         * Use concise bullet points (1 line each)
         * Prioritize requirements within sections
         * Highlight dependencies between requirements
         * Reference source information from Q&A where relevant
       - Focus on synthesizing insights, not listing answers
       - Separate confirmed requirements from tentative ones
       - Ensure no contradictions with the task statement

    3. Quality criteria:
       - Task: Specific, Measurable, Actionable, Relevant, Time-bound
       - Context: Comprehensive, Structured, Prioritized, Unambiguous
       - Alignment: Context details must support and reference task objectives
       - Clarity: Both outputs must be understandable without additional explanation

    The output must be formatted as a JSON object with 'task' and 'context' fields.
    """
    
    logger.info(f"Summarizing context for the task")
    logger.info(f"Summarization instructions: {instructions}")
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
    logger.info(f"Clarified task: {clarified_task.model_dump_json(indent=2)}")
    return clarified_task
