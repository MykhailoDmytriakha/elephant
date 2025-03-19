import logging
from src.core.config import settings
from src.model.task import Task
from src.model.ifr import IFR, Metric, ValidationItem
from src.ai_agents.utils import detect_language, get_language_instruction

logger = logging.getLogger(__name__)
try:
    from agents import Agent, Runner  # type: ignore # noqa
    model = settings.OPENAI_MODEL
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI Agents SDK not installed. Some functionality will be limited.")
    AGENTS_SDK_AVAILABLE = False

async def generate_IFR(
    task: Task,
) -> IFR:
    """
    Generate an ideal final result for a given task
    
    Args:
        task: The task containing the context information
        
    Returns:
        IFR: An Ideal Final Result with success criteria, expected outcomes, 
             quality metrics, validation checklist, and the IFR statement
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
    
    # Prepare the task information
    task_description = task.short_description or ""
    clarified_task = task.task
    task_context = task.context
    context_answers_text = "\n".join([
        f"Q: {answer.question}\nA: {answer.answer}" 
        for answer in task.context_answers
    ])
    
    # for each group in scope, get the answers
    previous_scope_answers = ""
    if task.scope:
        scope_answers = []
        for g in ["what", "why", "who", "where", "when", "how"]:
            answers = getattr(task.scope, g, None)
            if answers:
                scope_answers.append(f"` - DIMENSION: {g}`")
                for answer in answers:
                    scope_answers.append(f"Q: {answer.question}\nA: {answer.answer}")
        previous_scope_answers = "\n".join(scope_answers)
    
    # Create the instruction for the agent
    instructions = f"""
    Generate an Ideal Final Result (IFR) for the following task based on the provided context.
    
    INITITAL USER INPUT: {task_description}
    TASK: {clarified_task}
    CONTEXT ANSWERS: {context_answers_text}
    CONTEXT: {task_context}
    SCOPE ANSWERS: {previous_scope_answers}
    SCOPE: {task.scope.scope if task.scope else ""}
    
    {language_instruction}
    
    An Ideal Final Result (IFR) is a concise description of the optimal outcome of a task or project.
    It should represent the perfect solution that meets all requirements without any compromises.
    
    INSTRUCTIONS FOR EACH SECTION (strictly follow each format):
    
    1. IDEAL FINAL RESULT STATEMENT:
       - Write exactly 5 concrete (that will cover whole idea "end-to-end" of user's request, on high level), specific sentences without any "watery" filler words
       - Focus solely on the "destination" - what the finished solution will achieve
       - Format: precise, direct statements that clearly define the end goal
       - Absolutely no vague adjectives like "effective," "quality," "advanced," "optimal," etc.
    
    2. SUCCESS CRITERIA:
       - List 10-12 concrete, measurable functional requirements (not metrics)
       - Focus on WHAT the system does, not HOW WELL it does it
       - Format: "[System component] [enables/performs] [specific capability]"
       - Each criterion must address a different core capability, avoiding overlap with quality metrics
       - DO NOT include specific performance thresholds here (those belong in quality metrics)
    
    3. EXPECTED OUTCOMES:
       - List 10-12 direct answers to "What did the user want to achieve with this project?"
       - Format: "[Specific problem] is solved by [concrete solution approach]"
       - Example: "Vehicle owners' wait time for assistance is reduced by enabling direct mechanic communication"
       - Each outcome must directly relate to the user's original request and primary goals
       - Focus on practical benefits that the stakeholders will receive
       
    4. QUALITY METRICS:
       - List 10-12 precise measurements with exact numerical values and units
       - Must span multiple categories: performance, reliability, security, usability, data
       - Format: "[Precise metric name]: [exact value with unit]"
       - This is where ALL specific performance thresholds should appear
       
    5. VALIDATION CHECKLIST:
       - List 10-12 test procedures with specific pass/fail criteria
       - Format: "[Test procedure]: [verification word] [specific element] [meets exact requirement]"
         where [verification word] should be:
         * English: "Verify"
         * Russian: "Проверить"
         * Spanish: "Verificar"
         * French: "Vérifier"
         * German: "Überprüfen"
         * Or appropriate term in the user's language
       - Each validation item must include both what to test and how to determine success
    
    CRITICAL REQUIREMENTS:
    1. Each section MUST contain completely different information
    2. NO duplication across sections - success criteria describe WHAT functions exist, metrics describe HOW WELL they perform
    3. Expected outcomes must directly answer "What did the user initially want to achieve?"
    4. The ideal final result statement must be extremely concrete and specific with zero filler words
    5. Use direct, clear language throughout without buzzwords or marketing language
    
    The IFR should be ambitious yet achievable, focusing on what/why/who/where/when/how will be delivered and achieved.
    """
    
    logger.info(f"Generating IFR for task: {task.id}")
    logger.info(f"Generation instructions: {instructions}")
    
    # Create the agent
    agent = Agent(
        name="IFRGenerationAgent",
        instructions=instructions,
        output_type=IFR,
        model=model
    )
    
    # Run the agent
    result = await Runner.run(agent, "Generate Ideal Final Result for the task")
    
    # Process the response
    ifr_result = result.final_output
    logger.info(f"Generated IFR: {ifr_result.model_dump_json(indent=2)}")
    return ifr_result
