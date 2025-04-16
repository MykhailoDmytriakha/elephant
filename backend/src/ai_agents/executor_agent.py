import logging
from src.model.task import Task
from src.model.subtask import Subtask
from src.model.status import StatusEnum
from datetime import datetime
from src.services.database_service import DatabaseService
from src.utils import context_utils
logger = logging.getLogger(__name__)

# Try to import the OpenAI Agents SDK
try:
    from agents import Agent, function_tool # type: ignore
    from agents.run_context import RunContextWrapper # type: ignore
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI Agents SDK not installed. Some functionality will be limited.")
    AGENTS_SDK_AVAILABLE = False

if not AGENTS_SDK_AVAILABLE:
    logger.error("OpenAI Agents SDK not installed.")
    raise ImportError("OpenAI Agents SDK not installed. Please install with `pip install openai-agents`")

from src.core.config import settings
model = settings.OPENAI_MODEL

from src.ai_agents.tools.filesystem_tools import filesystem_tools_list
from src.ai_agents.tools.cognitive_tools import cognitive_tools_list

# Helper function to update task in database with subtask changes
def _update_subtask_in_database(task: Task, subtask_id: str, operation: str) -> tuple[bool, str]:
    """
    Updates the task in the database after a subtask has been modified.
    
    Args:
        task: The Task object containing the modified subtask
        subtask_id: The ID of the subtask that was modified
        operation: Description of the operation performed (for logging)
        
    Returns:
        A tuple of (success, message) where success is a boolean indicating if the database update was successful,
        and message is an error message if unsuccessful
    """
    try:
        db_service = DatabaseService()
        db_service.updated_task(task)
        logger.info(f"Task with ID {task.id} updated in the database with {operation} subtask {subtask_id}")
        return True, ""
    except Exception as e:
        error_msg = f"Error saving task to database: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg

# --- Executor Agent Tools ---
@function_tool
def get_subtask_id(wrapper: RunContextWrapper[Task]) -> str:
    """Retrieves the subtask ID from the context."""
    return wrapper.context['subtask_id']
    
@function_tool
def get_task_context(wrapper: RunContextWrapper[Task]) -> str:
    """
    Retrieves detailed information about the entire task, including scope, requirements, plan, and subtasks.
    """
    logger.info("Getting full task context")
    try:
        # Return full Task JSON
        return wrapper.context['task'].model_dump_json()
    except Exception as e:
        logger.error(f"Error retrieving task context: {e}", exc_info=True)
        return f'{{"error": "Failed to retrieve task context: {str(e)}"}}'

@function_tool
def get_subtask_details(wrapper: RunContextWrapper[Task], subtask_id: str) -> str:
    """
    Retrieves all details about a specific subtask by its ID and loads it into context.
    Use this to get comprehensive information about a subtask before executing it.

    Args:
        subtask_id: The ID of the subtask to retrieve information for

    Returns:
        A formatted string containing details of the subtask, or an error message if not found.
    """
    logger.info(f"Getting details for subtask: {subtask_id}")
    # Locate the Subtask model instance in the Task
    subtask_obj = context_utils.find_subtask_by_id(wrapper.context['task'], subtask_id)
    if not subtask_obj:
        logger.warning(f"Subtask with ID {subtask_id} not found in Task {wrapper.context['task'].id}")
        return f"Subtask with ID {subtask_id} not found"
    # Store the Subtask object in context for subsequent operations
    wrapper.context['subtask'] = subtask_obj
    # Retrieve and return the formatted subtask context string
    details = context_utils.get_subtask_context_by_id(wrapper.context['task'], subtask_id)
    return details

@function_tool
def mark_subtask_as_successful(wrapper: RunContextWrapper[Task], subtask_id: str, result: str) -> str:
    """
    Marks a subtask as successful.
    
    Args:
        subtask_id: The ID of the subtask to mark as successful
        result: The result of the subtask, description what was done and what was achieved
    Returns:
        A string containing the subtask ID that was marked as successful
    """
    logger.info(f"Marking subtask {subtask_id} as successful with result: {result}")
    subtask = wrapper.context['subtask']
    task = wrapper.context['task']
    if subtask is not None and isinstance(subtask, Subtask):
        subtask.status = StatusEnum.COMPLETED
        subtask.result = result
        subtask.completed_at = datetime.now().isoformat()
        
        # Save subtask to the database
        success, error_msg = _update_subtask_in_database(task, subtask_id, "completed")
        if not success:
            return f"Subtask {subtask_id} marked as successful, but failed to save to database: {error_msg}"
        
        return f"Subtask {subtask_id} marked as successful with result: {result}"
    else:
        return f"Subtask with ID {subtask_id} not found, get subtask details first using get_subtask_details()"

@function_tool
def mark_subtask_as_failed(wrapper: RunContextWrapper[Task], subtask_id: str, error_message: str) -> str:
    """
    Marks a subtask as failed.
    
    Args:
        subtask_id: The ID of the subtask to mark as failed
        error_message: The error message of the subtask, description what went wrong
    Returns:
        A string containing the subtask ID that was marked as failed
    """
    logger.info(f"Marking subtask {subtask_id} as failed with error: {error_message}")
    subtask = wrapper.context['subtask']
    task = wrapper.context['task']
    if subtask is not None and isinstance(subtask, Subtask):
        subtask.status = StatusEnum.FAILED
        subtask.error_message = error_message
        subtask.completed_at = datetime.now().isoformat()
        
        # Save subtask to the database
        success, error_msg = _update_subtask_in_database(task, subtask_id, "failed")
        if not success:
            return f"Subtask {subtask_id} marked as failed, but failed to save to database: {error_msg}"
        
        return f"Subtask {subtask_id} marked as failed with error: {error_message}"
    else:
        return f"Subtask with ID {subtask_id} not found, get subtask details first using get_subtask_details()"
    
@function_tool
def mark_subtask_as_in_progress(wrapper: RunContextWrapper[Task], subtask_id: str) -> str:
    """
    Marks a subtask as in progress.
    
    Args:
        subtask_id: The ID of the subtask to mark as in progress
    Returns:
        A string containing the subtask ID that was marked as in progress
    """
    logger.info(f"Marking subtask {subtask_id} as in progress")
    # if exist subtask and task in context, mark as in progress
    if not wrapper.context.get('subtask') or not wrapper.context.get('task'):
        return f"Subtask with ID {subtask_id} not found, get subtask details first using get_subtask_details()"
    
    subtask = wrapper.context['subtask']
    task = wrapper.context['task']
    if subtask is not None and isinstance(subtask, Subtask):
        subtask.status = StatusEnum.IN_PROGRESS
        subtask.started_at = datetime.now().isoformat()
        subtask.completed_at = None
        subtask.error_message = None
        subtask.result = None
        
        # Save subtask to the database
        success, error_msg = _update_subtask_in_database(task, subtask_id, "in-progress")
        if not success:
            return f"Subtask {subtask_id} marked as in progress, but failed to save to database: {error_msg}"
        
        return f"Subtask {subtask_id} marked as in progress"
    else:
        return f"Subtask with ID {subtask_id} not found, get subtask details first using get_subtask_details()"

# Create the executor agent
def create_executor_agent() -> Agent:
    """
    Creates and configures the executor agent with all necessary tools.
    
    Returns:
        An Agent instance configured for task execution
    """
    instructions = """
    You are an Executor Agent specialized in executing **specific subtasks**. Your role is more analytical and thoughtful than simply executing commands.

    Your overall workflow starts with information gathering, followed by analysis and planning, and only then proceeding to execution.

    **Mandatory Workflow:**

    1.  **Get Target ID:** Call `get_subtask_id()` to retrieve the specific `subtask_id` from the context that you need to execute.
        *   **Error Handling:** If `get_subtask_id` fails or returns no ID, **stop immediately**, report the error, and do not proceed to any other steps.

    2.  **Get Details:** Using the retrieved `subtask_id`, call `get_subtask_details(subtask_id=RETRIEVED_ID)`. This step is **essential** as it populates the necessary `subtask` object into the context for later steps.
        *   **Error Handling:** If `get_subtask_details` returns an error (e.g., ID belongs to a Stage/Work/Task, ID not found, or any other failure preventing successful retrieval and context population), **stop immediately**, return that specific error message, and **do not attempt any further steps** like marking status or executing.

    3.  **Mark as In Progress:** **Only after successfully completing step 2**, call `mark_subtask_as_in_progress(subtask_id=RETRIEVED_ID)`. If this step fails, report the error and stop.

    4.  **Information Gathering & Analysis:** Before implementing anything, use the cognitive tools to:
        * Analyze the subtask using `break_down_complex_task()` to understand exactly what needs to be done
        * Identify required resources with `identify_required_resources()` to determine what you have and what you're missing
        * Evaluate potential approaches using `compare_alternative_approaches()` if there are multiple ways to accomplish the task
        * Assess risks with `analyze_potential_risks()` before proceeding with implementation
        
        If you identify any missing information, unclear requirements, or potential issues, **DO NOT HESITATE TO ASK THE USER FOR CLARIFICATION**. Examples of when to ask:
        * The requirements are ambiguous
        * You're missing necessary resources
        * You need access to specific files or information
        * You need to confirm your understanding of the task
        * You need to explain trade-offs between different approaches

    5.  **Execute:** Only after thorough analysis, perform the task's implementation. Use filesystem tools and other resources to complete the work.
        * Always explain your reasoning for key decisions
        * Break down complex implementations into steps
        * Use `verify_step_completion()` to validate milestones as you proceed
        * For complex workflows, consider using `synthesize_information()` to organize your findings

    6.  **Update Status:** After execution:
        *   If successful, call `mark_subtask_as_successful(subtask_id=RETRIEVED_ID, result=...)` with a detailed description of what was accomplished
        *   If failed, call `mark_subtask_as_failed(subtask_id=RETRIEVED_ID, error_message=...)` with precise details about what went wrong and any attempted remediation steps

    **Available Tools:**

    *   **Task Context:**
        *   `get_task_context()`: Retrieves detailed information about the entire task, including scope, requirements, plan, and subtasks.

    *   **Subtask Management:**
        *   `get_subtask_id()`: Retrieves the target subtask ID from the context. **Call this first.**
        *   `get_subtask_details(subtask_id)`: Retrieves details for the **specific** subtask ID you were given. **Crucial second step.**
        *   `mark_subtask_as_in_progress(subtask_id)`: Marks the target subtask as started. **Call only after successful `get_subtask_details`.**
        *   `mark_subtask_as_successful(subtask_id, result)`: Marks completion with results. **Call only after successful execution.**
        *   `mark_subtask_as_failed(subtask_id, error_message)`: Marks failure with error details. **Call only after failed execution.**
    *   **Filesystem Tools:** (Operate ONLY within the allowed directory)
        *   `list_allowed_directory()`: Shows the base directory.
        *   `read_file(path)`
        *   `write_file(path, content)`
        *   `edit_file(path, edits, dry_run)`
        *   `create_directory(path)`
        *   `list_directory(path)`
        *   `directory_tree(path)`
        *   `move_file(source, destination)`
        *   `search_files(path, pattern, case_sensitive)`
        *   `get_file_info(path)`
    *   **Cognitive Tools:** (For planning, analysis, and information processing)
        *   `evaluate_plan_feasibility(plan_description, constraints)`: Evaluates if a plan is feasible given constraints.
        *   `identify_required_resources(task_description, current_context)`: Lists resources needed for a task.
        *   `analyze_potential_risks(action_description, context)`: Analyzes risks of an action.
        *   `break_down_complex_task(task_description, max_depth)`: Breaks down complex tasks into sub-tasks.
        *   `verify_step_completion(step_description, evidence)`: Verifies if a step is completed based on evidence.
        *   `compare_alternative_approaches(goal, approaches)`: Compares different approaches to a goal.
        *   `synthesize_information(information_pieces, desired_output_format)`: Combines information into cohesive output.

    **Important Guidelines:**

    *   **Don't rush into implementation.** First understand and analyze using the cognitive tools.
    *   **Always ask the user for clarification** when requirements are unclear or information is missing.
    *   Follow the **Mandatory Workflow** strictly. **Do not skip steps.**
    *   When analyzing or implementing, explain your reasoning clearly.
    *   Be thorough in your analysis but concise in your explanations.
    *   Work within the allowed filesystem directory. Use relative paths.
    """
    
    tools = [
        get_task_context,
        get_subtask_id,
        get_subtask_details,
        mark_subtask_as_successful,
        mark_subtask_as_failed,
        mark_subtask_as_in_progress
    ] + filesystem_tools_list + cognitive_tools_list
    
    return Agent(
        name="ExecutorAgent",
        instructions=instructions,
        model=model,
        tools=tools
    )