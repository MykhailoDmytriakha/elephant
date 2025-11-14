import logging
from src.core.config import settings
from src.model.context import ContextSufficiencyResult 
from src.model.task import Task
from src.ai_agents.utils import detect_language, get_language_instruction

logger = logging.getLogger(__name__)
try:
    from agents import Agent, Runner  # type: ignore # noqa
    model = settings.OPENAI_MODEL
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI Agents SDK not installed. Some functionality will be limited.")
    AGENTS_SDK_AVAILABLE = False

async def analyze_context_sufficiency(
    task: Task,
    iteration_count: int = 0
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
    
    # Detect language from task description
    task_description = task.short_description or ""
    user_language = detect_language(task_description)
    
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
    This is an initial interaction with the user, so treat it as user has:
     - a problem that should be converted into a task or
     - idea/task that should be clarified, like more "crystallized".
    The main goal is to understand the user intent, and missing information that should be clarified.
    Analyze the provided task and context information to determine if there's sufficient context to proceed.

    ADAPTATION PRINCIPLE: Evaluate the complexity level of the user's request and adapt question depth accordingly.
    - SIMPLE REQUESTS (casual ideas, basic tasks): Ask 1-3 basic questions, focus on core intent
    - MODERATE REQUESTS (technical ideas, business tasks): Ask 3-5 focused questions
    - COMPLEX REQUESTS (multi-disciplinary, regulatory, high-stakes): Ask 5-7 detailed questions

    ITERATION LIMIT: Current iteration count is {iteration_count}.
    - If iteration count >= 3: Be very conservative, ask at most 2 questions, prioritize only critical gaps
    - If iteration count >= 5: Consider context sufficient unless there are critical missing elements
    - Do not ask more than {max(1, 5 - iteration_count)} questions in this iteration.

    If the context is insufficient, provide questions to gather more information.
    Each question should be specific and focused on resolving ambiguities or filling gaps.
    For each question, provide 3-5 possible options if appropriate.
    Do not include options like "both", "all", "none", etc.

    IMPORTANT: Do NOT ask follow-up questions about topics where the user has indicated they will address it later
    (responses like "we'll determine this later", "we'll figure this out later", "this will be decided later", etc.).
    These topics should be deferred to the scope formulation phase instead of being asked again.

    IMPORTANT: If the user has repeatedly answered "не знаю" (I don't know) or provided very limited information,
    consider the context sufficient with what we have and DO NOT ask more questions on those topics.

    FOCUS ON ESSENTIALS: Prioritize questions that directly impact the core task execution. Avoid over-engineering
    with excessive detail unless the request clearly requires deep technical/regulatory analysis.
    """

    # Construct the message with dynamic data
    message_content = f"""
    Analyze the following task and context information:

    INITITAL USER INPUT (TASK): {task.short_description}
    ---
    CONTEXT ANSWERS: {context_answers_text}
    ---
    {language_instruction}
    ---
    """
    
    logger.info(f"Analyzing context sufficiency for the task {task.id}")
    # logger.info(f"Analysis instructions: {instructions}")
    logger.info(f"---> REQUEST OPENAI **ContextSufficiencyAgent** ({user_language}) with message: {message_content}")
    # Create the agent
    agent = Agent(
        name="ContextSufficiencyAgent",
        instructions=instructions,
        output_type=ContextSufficiencyResult,
        model=model
    )
    
    # Run the agent
    result = await Runner.run(agent, message_content)
    
    # Process the response
    result = result.final_output
    logger.info(f"Context sufficiency result: {result.model_dump_json(indent=2)}")
    return result
