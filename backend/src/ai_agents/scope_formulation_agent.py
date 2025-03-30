import logging
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from src.core.config import settings
from src.model.task import Task
from src.model.scope import ScopeQuestion, ValidationCriteria, DraftScope, ValidationScopeResult
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

async def formulate_scope_questions(
    task: Task,
    group: str,
) -> List[ScopeQuestion]:
    """
    Uses OpenAI Agent SDK to formulate scope questions for a given group.
    
    Args:
        task: The task containing the context information
        group: The group of scope questions to formulate (what, why, who, where, when, how)
        
    Returns:
        List[ScopeQuestion]: List of scope questions for the specified group
    """
    if not AGENTS_SDK_AVAILABLE:
        logger.error("OpenAI Agents SDK not installed.")
        raise ImportError("OpenAI Agents SDK not installed. Please install with `pip install openai-agents`")

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
    
    # Detect language from task description
    user_language = detect_language(task_description)
    logger.info(f"Detected language: {user_language}")
    
    # Get language-specific instruction
    language_instruction = get_language_instruction(user_language)
    
    # Create the instruction for the agent
    instructions = f"""
    You are a Scope Formulation Agent designed to create SPECIFIC, CONCRETE questions that precisely define the scope boundaries of a task by clarifying existing details and uncovering ambiguities. Your goal is to act like a helpful partner, asking natural-sounding questions to refine the understanding based on the provided context.
    
    Think of this as a conversation to narrow down the specifics. We've gathered initial context, now we need to zoom in further.
    
    FIRST STEP - ANALYZE USER REQUEST COMPLEXITY AND AMBIGUITY:
    1. Carefully assess the complexity level AND clarity of the user's initial input, task description, and existing context/answers.
    2. Classify the request complexity as: Simple, Moderate, Advanced.
    3. Assess the ambiguity level: High (many unclear points), Medium (some details missing), Low (mostly clear).
    4. Adapt your questions to match this complexity and ambiguity level. More ambiguity requires more questions to clarify.
    5. For simple requests: Use straightforward language, limit technical specifications, focus on basic boundaries.
    6. For advanced requests: Include more technical parameters, specialized terminology, and detailed specifications.
    7. It's better to ask slightly more complex/detailed questions than overly simple ones if unsure. Aim for depth.
    
    MINIMUM NUMBER OF QUESTIONS & ADAPTATION:
    - Generate AT LEAST 5 questions for each dimension.
    - If the context for the dimension is ambiguous or lacks detail (Medium/High ambiguity), generate MORE questions (potentially 6-8 or even more for highly complex/ambiguous tasks) to ensure full clarity.
    - The number of questions should directly reflect the need for clarification based on the input. Do not stick to a fixed number; adapt dynamically.
    - Include AT LEAST 1-2 exclusion questions defining what's OUT of scope for the dimension.
    
    QUESTION STYLE - AIM FOR NATURAL CLARIFICATION:
    - Frame questions conversationally, as if clarifying points in a discussion.
    - Ensure questions sound natural and idiomatic in the user's detected language ({user_language}). Avoid overly robotic or formulaic phrasing.
    - Use the context provided not just as input, but as a starting point for deeper clarification. "Based on X, should we clarify Y?"
    - Match question style to request complexity:
        - Simple requests: Everyday language, minimal technical terms, straightforward options.
        - Moderate requests: Balance technical terms with clear explanations, moderate detail in options.
        - Advanced requests: Specialized terminology, detailed technical specifications, precise parameters.
    
    Your questions must establish EXACT LIMITS and CLEAR CRITERIA for the "{group}" dimension of the task scope.
    
    Analyze the following information to generate highly specific, clarifying questions for the "{group}" dimension:
    
    ---
    SCOPE DIMENSION: `{group}`
    ---
    INITITAL USER INPUT: {task_description}
    ---
    TASK: {clarified_task}
    ---
    CONTEXT: {task_context}
    ---
    CONTEXT ANSWERS: {context_answers_text}
    ---
    SCOPE ANSWERS FROM PREVIOUS DIMENSIONS: {previous_scope_answers}
    ---
    
    {language_instruction}
    
    For each question you generate:
    1. Create a clear, specific question about the "{group}" dimension that CLARIFIES an ambiguous point or ESTABLISHES CONCRETE BOUNDARIES with MEASURABLE CRITERIA based on the existing context.
    2. Extract options directly suggested by the context (if any), presenting them as potential clarifications.
    3. Generate additional options representing SPECIFIC CHOICES with technical parameters, not just general categories.
    4. Assign a priority level (Critical, High, Medium, Low) indicating importance for scope definition.
    
    DIMENSION-SPECIFIC GUIDELINES (Focus on measurable specifics):
    - "what": EXACT deliverables, features, quantifiable criteria (e.g., "Should the report include exactly 5 interactive diagrams with drill-down capability, building on the mentioned reporting requirement?")
    - "why": SPECIFIC objectives, measurable outcomes (e.g., "Regarding the goal of increasing sales, should we target a 10% increase within 3 months specifically?")
    - "who": PRECISE audience definitions, roles, demographics (e.g., "For the target college students, should we focus only on those using iOS 14.5+ devices?")
    - "where": EXPLICIT platforms, environments, technical boundaries (e.g., "Confirming platform support: iOS 14.5+ and Android 10+ only, correct?")
    - "when": EXACT dates, timeframes, milestones (e.g., "Is the MVP deadline precisely April 15th, 2023, or is there flexibility?")
    - "how": SPECIFIC implementation approaches, technical standards (e.g., "Regarding implementation, should we proceed with NextJS 13.4 and server-side rendering as discussed?")
    
    SPECIAL GUIDELINES FOR UNIVERSAL METHODOLOGY:
    - When creating a universal methodology/approach, focus questions on defining UNIVERSAL BOUNDARIES and PRINCIPLES, not specific implementations.
    - Frame questions around roles, concepts, applicability domains, process phases, approach categories.
    - AVOID questions tied to specific individuals, organizations, technologies, platforms, or deadlines unless they define a boundary of the *methodology itself*.
    - The goal is to define a METHODOLOGY applicable across contexts.
    
    CROSS-DIMENSIONAL BOUNDARIES & CONTEXT AWARENESS:
    - Ensure questions refine the specific dimension ({group}) without straying into others (e.g., 'What' questions focus on features, not 'When' timelines).
    - Analyze if the request is for a METHODOLOGY vs. a SPECIFIC IMPLEMENTATION and tailor questions accordingly.
    - For methodologies, focus on generic roles, principles, and conceptual boundaries.
    
    TECHNICAL DETAIL REQUIREMENTS (Ensure specificity):
    - Security: Specify standards (e.g., AES-256 encryption for data at rest).
    - Performance: Include metrics (e.g., 1000 concurrent users, response < 200ms).
    - AI Capabilities: Define limits (e.g., response within 500ms, 95% accuracy on classification).
    - UX: Specify criteria (e.g., Material Design 3.0 standards, dark mode support).
    
    Each question MUST establish clear boundaries (BINARY or MULTIPLE-CHOICE). Frame them for scope decisions, not general info gathering.
    
    IMPORTANT: EVERY question must help establish a clear BOUNDARY or LIMIT with SPECIFIC, MEASURABLE CRITERIA, building upon or clarifying the existing context.
    
    CROSS-REFERENCE REQUIREMENT:
    Before finalizing, cross-reference questions with ALL previous dimension answers to:
    1. Ensure NO overlap or contradiction.
    2. Eliminate redundancy.
    3. Build upon established boundaries.
    4. Address gaps.
    
    CRITICALLY IMPORTANT: The entire question, including structure and format, MUST be in the user's detected language ({user_language}). Ensure it sounds natural and conversational in that language.
    
    QUESTION FORMATTING (in user's language):
    - Use a mix of formats naturally fitting the clarification needed. Examples:
        - "Should [specific element with parameters] be included...?"
        - "To clarify [aspect], which specific option is correct: Option A [details], Option B [details], ...?"
        - "Regarding [context point], does this mean [specific boundary]?"
    - Ensure natural phrasing, simple structures, and common expressions in the target language.
    
    EXCLUSION QUESTIONS (ALWAYS INCLUDE 1-2):
    - Ask explicitly what should be EXCLUDED from the scope for this dimension to prevent scope creep.
    - Format like: "To keep the project focused, which of these should be explicitly EXCLUDED from the '{group}' scope for now?" (Adapt to user's language).
    - Options should be specific features/capabilities with brief technical/business rationales for exclusion.
    - Provide 3-5 concrete, reasonable exclusion options directly related to the task.
    - Mark these with "Приоритет: Critical" (adapt to user's language).
    
    IMPORTANT RULES FOR AVOIDING REDUNDANCY:
    1. DO NOT ask about aspects ALREADY CLEARLY DEFINED in context/answers. Focus on gaps and ambiguities.
    2. If context states "registration via email and phone", don't ask IF email/phone should be included. Ask about *limits* (e.g., "Should phone registration support international numbers?").
    3. Each question MUST add NEW clarification or define a boundary not already present.
    4. NEVER ask redundant questions covering the same point. Check for overlap before finalizing.
    5. If context mentions a capability (e.g., "AI analyzes problems"), ask about its *boundaries* (e.g., "What specific types of problems should the AI analyze?").
    6. MOST IMPORTANTLY: Tailor question complexity and *detail level* to the user's request complexity and the existing context's clarity.
    """
    
    # Create the agent
    class ScopeQuestionsList(BaseModel):
        questions: List[ScopeQuestion]
    
    logger.info(f"Formulating scope questions for {group} dimension, task {task.id}")
    # logger.info(f"Formulation instructions: {instructions}")
    agent = Agent(
        name="ScopeFormulationAgent",
        instructions=instructions,
        output_type=ScopeQuestionsList,
        model=model
    )
    
    # Run the agent
    result = await Runner.run(agent, f"Formulate specific, boundary-defining '{group}' scope questions for the task")
    
    # Process the response
    scope_questions = result.final_output
    logger.info(f"Generated {len(scope_questions.questions)} scope questions for '{group}' dimension")
    logger.info(f"Scope questions: {scope_questions.model_dump_json(indent=2)}")
    return scope_questions.questions

async def generate_draft_scope(task: Task) -> DraftScope:
    """
    Uses OpenAI Agent SDK to generate a draft scope for a given task.
    
    Args:
        task: The task containing the context information

    Returns:
        str: Draft scope for the task
    """
    if not AGENTS_SDK_AVAILABLE:
        logger.error("OpenAI Agents SDK not installed.")
        raise ImportError("OpenAI Agents SDK not installed. Please install with `pip install openai-agents`")
    
    # Detect language from task description
    user_language = detect_language(task.short_description or "")
    logger.info(f"Detected language: {user_language}")
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
      
    instructions = f"""
    You are a Scope Formulation Agent designed to create a draft scope for a given task.
    
    Your task is to analyze the following information and generate a draft scope for the task:
    
    INITITAL USER INPUT: {task_description}
    ---
    TASK: {clarified_task}
    ---
    CONTEXT: {task_context}
    ---
    CONTEXT ANSWERS: {context_answers_text}
    ---
    SCOPE ANSWERS FROM PREVIOUS DIMENSIONS: {previous_scope_answers}
    ---
    {language_instruction}
    
    You must generate a draft scope for the task based on the following validation criteria (according to language instruction):
    1. Are the objectives (what) clear?
    2. Does it align with the purpose (why)?
    3. Are stakeholders (who) accounted for?
    4. Is the location (where) finalized?
    5. Are timelines (when) reasonable?
    6. Are the processes/tools (how) defined?
    """
    
    logger.info("Generating draft scope")
    logger.info(f"Draft scope instructions: {instructions}")
    agent = Agent(
        name="DraftScopeGenerator",
        instructions=instructions,
        output_type=DraftScope,
        model=model
    )
    
    # Run the agent
    result = await Runner.run(agent, f"Generate a draft scope for the task")
    
    # Process the response
    draft_scope = result.final_output
    logger.info(f"Generated draft scope: {draft_scope.model_dump_json(indent=2)}")
    return draft_scope

async def validate_scope(task: Task, feedback: str) -> ValidationScopeResult:
    """
    Uses OpenAI Agent SDK to validate a draft scope for a given task and feedback.
    
    Args:
        task: The task containing the context information
        feedback: Feedback on the scope

    Returns:
        ValidationScopeResult: Validation result
    """
    
    if not AGENTS_SDK_AVAILABLE:
        logger.error("OpenAI Agents SDK not installed.")
        raise ImportError("OpenAI Agents SDK not installed. Please install with `pip install openai-agents`")
    
    # Detect language from task description
    user_language = detect_language(task.short_description or "")
    logger.info(f"Detected language: {user_language}")
    language_instruction = get_language_instruction(user_language)
    
    # Prepare the task information
    task_description = task.short_description or ""
    clarified_task = task.task
    task_context = task.context
    context_answers_text = "\n".join([
        f"Q: {answer.question}\nA: {answer.answer}" 
        for answer in task.context_answers
    ])
    draft_scope = task.scope.scope if task.scope else ""
    
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
    
    instructions = f"""
    You are a Scope Validation Agent designed to validate a draft scope for a given task and feedback.
    
    Your task is to analyze the user feedback and rewrite the draft scope for the task:
    
    INITITAL USER INPUT: {task_description}
    ---
    TASK: {clarified_task}
    ---
    CONTEXT: {task_context}
    ---
    CONTEXT ANSWERS: {context_answers_text}
    ---
    SCOPE ANSWERS FROM PREVIOUS DIMENSIONS: {previous_scope_answers}
    ---
    USER FEEDBACK: {feedback}
    ---
    SCOPE DRAFT: {draft_scope}
    ---
    {language_instruction}
    
    You must rewrite the draft scope for the task based on the user feedback.
    You response will include the rewritten scope and the list of changes you made to the scope.
    """
    
    logger.info("Validating scope")
    logger.info(f"Validation instructions: {instructions}")
    agent = Agent(
        name="ScopeValidationAgent",
        instructions=instructions,
        output_type=ValidationScopeResult,
        model=model
    )
    
    # Run the agent
    result = await Runner.run(agent, f"Validate the draft scope for the task")
    
    # Process the response
    validation_result = result.final_output
    logger.info(f"Validation result: {validation_result.model_dump_json(indent=2)}")
    return validation_result
