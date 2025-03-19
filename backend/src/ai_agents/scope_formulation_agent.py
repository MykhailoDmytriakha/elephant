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
    You are a Scope Formulation Agent designed to create SPECIFIC, CONCRETE questions that precisely define the scope boundaries of a task.
    
    FIRST STEP - ANALYZE USER REQUEST COMPLEXITY:
    1. Carefully assess the complexity level of the user's initial input and overall task description
    2. Classify the request complexity as:
       - Simple: Basic tasks with clear definitions and minimal technical requirements
       - Moderate: Tasks with some technical complexity but familiar concepts
       - Advanced: Tasks with high technical complexity, specialized domain knowledge or innovations
    3. Adapt your questions to match this complexity level - don't overwhelm simple requests with overly technical questions
    4. For simple requests: Use straightforward language, limit technical specifications, focus on basic boundaries
    5. For advanced requests: Include more technical parameters, specialized terminology, and detailed specifications
    6. It's better to ask on 20% complex questions, than to ask on 20% less complex questions. I mean better a little bit more complex questions, than a little bit less complex questions.
    
    RECOMMENDED NUMBER OF QUESTIONS:
    - Simple requests: 2-3 focused questions plus 1 exclusion question
    - Moderate requests: 3-5 focused questions plus 1 exclusion question
    - Advanced requests: 5-7 focused questions plus 1 exclusion question
    
    MATCHING QUESTION STYLE TO REQUEST COMPLEXITY:
    - For simple requests: Use everyday language, minimal technical terms, and straightforward options 
    - For moderate requests: Balance technical terminology with clear explanations, provide moderate detail in options
    - For advanced requests: Include specialized terminology, detailed technical specifications in options, and precise parameters
    
    Your questions must establish EXACT LIMITS and CLEAR CRITERIA for the "{group}" dimension of the task scope.
    
    To define scope we use approach 5W+H: What, Why, Who, Where, When, How.
    Your task is to analyze the following information and generate highly specific questions for the "{group}" dimension:
    
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
    1. Create a clear, specific question about the "{group}" dimension that ESTABLISHES CONCRETE BOUNDARIES with MEASURABLE CRITERIA
    2. Extract options directly suggested by the context (if any)
    3. Generate additional options that represent SPECIFIC CHOICES with technical parameters, not general categories
    4. Assign a priority level (Critical, High, Medium, Low) to each question to indicate its importance for scope definition
    
    DIMENSION-SPECIFIC GUIDELINES:
    - For "what" dimension: Focus on EXACT deliverables with quantifiable criteria (e.g., "Should the report include exactly 5 interactive diagrams with drill-down capability?" not "What should the report include?")
    - For "why" dimension: Focus on SPECIFIC objectives with numeric, measurable outcomes (e.g., "Is the goal to increase sales by 10% within 3 months?" not "What are the goals?")
    - For "who" dimension: Focus on PRECISE audience definitions with demographic data or specific roles (e.g., "Should the content target 18-25 year old college students with iOS devices?" not "Who is the audience?")
    - For "where" dimension: Focus on EXPLICIT platforms with version numbers and technical boundaries (e.g., "Should the app support iOS 14.5+ and Android 10+ only?" not "Which platforms?")
    - For "when" dimension: Focus on EXACT dates, timeframes and milestones with specific deadlines (e.g., "Is the MVP deadline April 15th, 2023?" not "When is it due?")
    - For "how" dimension: Focus on SPECIFIC implementation approaches with technical standards (e.g., "Should we use NextJS 13.4 with server-side rendering for the frontend?" not "How should we implement it?")
    
    SPECIAL GUIDELINES FOR UNIVERSAL METHODOLOGY:
    - When creating a universal methodology or approach (as opposed to a specific implementation), focus questions on defining UNIVERSAL BOUNDARIES rather than specific implementations
    - For methodology/framework questions: Ask about the types of roles that would interact with the methodology, not about specific individuals or rigid requirements
    - Structure questions to establish boundaries for a METHODOLOGY that can be applied across contexts, not just in one specific use case
    - Focus on principles and approach definitions rather than specific implementation details when developing a universal framework
    
    UNIVERSAL METHODOLOGY DIMENSION FRAMEWORK:
    - For ALL dimensions in universal methodologies: AVOID questions about specific implementations, technologies, or platforms
    - For ALL dimensions in universal methodologies: Focus on PRINCIPLES, CONCEPTS, and BOUNDARIES, not implementation details
    - For "what" in methodologies: Focus on CONCEPTUAL DELIVERABLES and PRINCIPLES, not specific features or technical implementations
    - For "why" in methodologies: Focus on PURPOSE CATEGORIES and GOAL TYPES, not specific business metrics
    - For "who" in methodologies: Focus on ROLE CATEGORIES and RESPONSIBILITY TYPES, not specific people or certifications
    - For "where" in methodologies: Focus on DOMAIN APPLICABILITY and CONTEXTUAL BOUNDARIES, not specific platforms or environments
    - For "when" in methodologies: Focus on PROCESS PHASES and METHODOLOGY LIFECYCLE, not specific dates or deadlines
    - For "how" in methodologies: Focus on APPROACH CATEGORIES and PRINCIPLE TYPES, not specific technologies or tools
    - For ALL dimensions in methodologies: Ask questions that establish CONCEPTUAL BOUNDARIES, not implementation specifications
    - REMEMBER: The purpose is to define a METHODOLOGY that can work across different contexts, not a specific implementation
    
    CROSS-DIMENSIONAL BOUNDARIES:
    - "What" questions should focus on features and deliverables, NOT on timelines (When) or platforms (Where)
    - "Why" questions should focus on business objectives and metrics, NOT on implementation methods (How)
    - "Who" questions should focus on users, stakeholders and roles, NOT on where users are located (Where)
    - "Where" questions should focus on platforms, locations and environments, NOT on implementation methods (How)
    - "When" questions should focus on timelines, deadlines and scheduling, NOT on who is responsible (Who)
    - "How" questions should focus on implementation methods, standards and approaches, NOT on what features to implement (What)
    
    CONTEXT AWARENESS GUIDELINES:
    - Carefully analyze if the user is requesting a METHODOLOGY/APPROACH vs a SPECIFIC IMPLEMENTATION
    - For methodologies and frameworks, ensure questions focus on universal principles, not specific implementation details
    - When user wants a "universal approach" or "methodology", avoid questions about specific individuals, organizations, or implementation contexts
    - For "who" dimension in methodologies, focus on generic role definitions and responsibilities, not specific experience levels or certifications
    - Recognize that methodology development requires different question types than specific implementation projects
    
    TECHNICAL DETAIL REQUIREMENTS:
    - Security questions must specify exact standards (e.g., "Should AES-256 encryption be used for data at rest?" instead of "Should we use encryption?")
    - Performance questions must include specific metrics (e.g., "Should the app support 1000 concurrent users with response times under 200ms?" not "What performance is needed?")
    - AI capability questions must define concrete limits (e.g., "Should the AI agent respond within 500ms with 95% accuracy on problem classification?" not "How fast should the AI be?")
    - UX questions must specify measurable criteria (e.g., "Should the UI follow Material Design 3.0 standards with dark mode support?" not "What design should we use?")
    
    Each question MUST establish clear boundaries through BINARY or MULTIPLE-CHOICE structures.
    Frame questions to make exact scope decisions, not to gather general information.
    
    IMPORTANT: EVERY question must help establish a clear BOUNDARY or LIMIT with SPECIFIC, MEASURABLE CRITERIA. 
    Generate as many highly specific, boundary-defining questions as necessary to precisely define the scope. Focus on quality and precision rather than limiting to a specific number of questions.
    
    CROSS-REFERENCE REQUIREMENT:
    Before finalizing your questions, cross-reference them with ALL previous dimension answers to:
    1. Ensure NO overlap or contradiction with questions already answered in other dimensions
    2. Eliminate any redundancy across dimensions
    3. Build upon established boundaries rather than redefining them
    4. Address gaps left by other dimensions
    
    CRITICALLY IMPORTANT: The entire question, including the question structure and format, MUST be in the same language as the user's original request. Do not mix languages.
    
    For half of your questions, use a format equivalent to: "Should [specific element with technical parameters] be included in the scope?" in the user's language.
    For the other half, use a format equivalent to: "Which specific [aspect with measurable criteria] should be included: Option A with [specific parameters], Option B with [specific parameters], or Option C with [specific parameters]?" in the user's language.
    
    Follow these additional guidelines:
    1. Simplify technical terminology and use common everyday expressions in the target language
    2. Make questions conversational and easy to understand at first reading
    3. Avoid literal translations from English that sound awkward or unnatural
    4. Use simple sentence structures that are idiomatic to the target language 
    5. Ensure questions flow naturally when read aloud in the target language
    6. Rephrase overly formal or complex questions to sound more natural
    7. Use the most common grammatical patterns from the target language
    
    As the last questions, ALWAYS include comprehensive boundary-defining questions that explicitly lists what should be EXCLUDED from scope for this dimension, with technical rationales for each exclusion.
    
    IMPORTANT RULES:
    1. DO NOT ask questions about aspects that are ALREADY CLEARLY DEFINED in the context or context answers.
    2. Focus ONLY on uncertain or ambiguous aspects that need boundary clarification.
    3. If something is explicitly stated (e.g., "registration via social media accounts, email, and phone"), do not ask whether these should be included.
    4. Look for the gaps and undefined boundaries in the requirements, not what's already established.
    5. Each question must add new clarification that doesn't exist in the context.
    6. NEVER ask redundant questions - each question MUST address a UNIQUE aspect of the scope dimension.
    7. Do not ask about the same feature in both binary and multiple-choice format - choose only one format for each feature.
    8. Before finalizing your questions, check each against the others to ensure they don't overlap in content or intent.
    9. If context mentions a feature has certain capabilities (e.g., "AI agent analyzes problems"), don't ask IF this feature should exist - instead, ask about specific boundaries or limitations of that feature not defined in context.
    10. For features explicitly mentioned in context, focus questions on their scope limitations, constraints, or specific implementation details that are still ambiguous.
    11. MOST IMPORTANTLY: Tailor the complexity of your questions to match the complexity of the user's initial request. Don't create overly sophisticated questions for simple requests or simplistic questions for highly technical requests.
    
    For the final exclusion questions:
    - Format the question explicitly as: "Какие функции должны быть ИСКЛЮЧЕНЫ из реализации [dimension] для предотвращения расширения проекта:" (adapt to user's language)
    - Format each option as: "Option A – [specific feature to exclude], обоснование: [precise technical justification];"
    - Ensure the answer options directly state what will NOT be included (not what could be excluded)
    - The user's answer will explicitly select which features to exclude from the project
    - Provide 3-5 concrete options that would be reasonable to include but should be excluded for scope control
    - Each option must have a specific technical or business rationale after "обоснование:" (or equivalent in user's language)
    - The options must be realistic and directly connected to the task context
    - Each exclusion option should be something that could reasonably be considered as part of scope
    - Do not propose excluding fundamental features that are clearly core to the task
    - Focus on practical boundaries like specific feature limitations, data restrictions, or implementation constraints
    - Ensure options are concrete and meaningful to the user's actual task requirements
    - Mark this exclusion question with "Приоритет: Critical" (adapt to user's language)
    """
    
    # Create the agent
    class ScopeQuestionsList(BaseModel):
        questions: List[ScopeQuestion]
    
    logger.info(f"Formulating scope questions for {group} dimension")
    logger.info(f"Formulation instructions: {instructions}")
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
