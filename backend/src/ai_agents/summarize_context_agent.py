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
    feedback: Optional[str] = None
) -> ClarifiedTask:
    """
    Uses OpenAI Agent SDK to summarize the context of a task, optionally refining
    it based on user feedback.
    
    Args:
        task: The task containing the context information.
        feedback: Optional user feedback to guide the summarization/refinement.
        
    Returns:
        ClarifiedTask: Containing the summarized/refined task description and context.
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
    
    # --- Dynamic Input Data Block ---
    # This block contains the actual data the agent needs to process.
    # It will be passed as part of the message content.
    dynamic_input_data = f"""
    You are a Context Analysis Agent designed to process task information and create structured summaries.

    INPUT:
    INITIAL USER INPUT: {task.short_description}
    ---
    PREVIOUS TASK CLARIFICATION (if available): {task.task}
    ---
    PREVIOUS CONTEXT SUMMARY (if available): {task.context}
    ---
    CONTEXT ANSWERS (from Q&A): {context_answers_text}
    ---
    {language_instruction}
    """

    # --- Static Instructions Block ---
    # These define HOW the agent should perform its task (generation or revision).
    
    # Static instructions for initial generation (no feedback)
    generation_instruction = f"""
    GENERATION TASK:
    Analyze all the provided input (initial request, answers) in the message and produce two distinct outputs:
    1. A clarified task statement ('task')
    2. A comprehensive context summary ('context')

    OUTPUT REQUIREMENTS:
    1. Task clarification (What needs to be built):
       - Begin with a single concise sentence stating the core objective
       - Include only essential requirements in order of priority
       - Define clear, measurable outcomes or deliverables
       - Use active voice and direct language
       - Limit to 3-5 lines maximum
       - Avoid parenthetical expressions and nested clauses

    2. Context summary (How it should be implemented):
       - Organize information into clear sections (e.g., Core Functionality, User Experience, Technical Requirements, Open Questions)
       - Use concise bullet points (1 line each)
       - Prioritize requirements within sections
       - Highlight dependencies between requirements
       - Reference source information from Q&A where relevant
       - Focus on synthesizing insights, not listing answers
       - Ensure no contradictions with the task statement

    3. Quality criteria:
       - Task: Specific, Measurable, Actionable, Relevant, Time-bound
       - Context: Comprehensive, Structured, Prioritized, Unambiguous
       - Alignment: Context details must support and reference task objectives
       - Clarity: Both outputs must be understandable without additional explanation

    The output must be formatted as a JSON object with 'task' and 'context' fields.
    """
    
    # Static instructions for revision (with feedback)
    feedback_instruction = f"""
    REVISION TASK:
    Revise the 'PREVIOUS TASK CLARIFICATION' and 'PREVIOUS CONTEXT SUMMARY' (provided in the message) based *strictly* on the 'USER FEEDBACK FOR REVISION' (also in the message).
    - Incorporate the feedback accurately and concisely.
    - Maintain the overall structure and intent unless the feedback explicitly requests changes.
    - If the feedback contradicts previous information, prioritize the feedback but make a note of the change if significant.
    - Ensure the revised task and context are consistent with each other.
    - Produce the revised output in the specified JSON format with 'task' and 'context' fields.
    """
    
    # Add feedback-specific instructions if feedback is provided
    if feedback:
        static_instructions = feedback_instruction
        message_content = f"{dynamic_input_data}\nUSER FEEDBACK FOR REVISION:\n{feedback}\n---\nRevise the task clarification and context summary based on the provided feedback and input data."
        logger.info(f"Summarizing context for task {task.id} WITH feedback.")
    else:
        static_instructions = generation_instruction
        message_content = f"{dynamic_input_data}\nSummarize the context of the task and clarify the task description based on the input data."
        logger.info(f"Summarizing context for task {task.id} WITHOUT feedback (initial generation)." )
    
    # logger.info(f"Summarization instructions: {instructions}") # Can be verbose
    
    agent = Agent(
        name="ContextSummaryAgent",
        instructions=static_instructions,
        output_type=ClarifiedTask,
        model=model
    )
    
    logger.info(f"---> REQUEST OPENAI **ContextSummaryAgent** ({user_language}) with message: {message_content}")
    # Run the agent
    result = await Runner.run(agent, message_content)
    
    # Process the response
    clarified_task = result.final_output
    logger.info(f"Agent produced ClarifiedTask (feedback: {bool(feedback)}): {clarified_task.model_dump_json(indent=2)}")
    return clarified_task
