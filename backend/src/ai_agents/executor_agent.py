import logging
import time
from src.model.task import Task
from src.model.subtask import Subtask
from src.model.status import StatusEnum
from datetime import datetime
from src.services.database_service import DatabaseService
from src.utils import context_utils
logger = logging.getLogger(__name__)

# Import Pydantic for type handling
from pydantic import BaseModel, ConfigDict
from typing import Any, Dict, Optional

# Try to import the OpenAI Agents SDK
try:
    from agents import Agent, function_tool # type: ignore
    AGENTS_SDK_AVAILABLE = True
    
    # Create a wrapper for function_tool that allows arbitrary types
    def adk_function_tool(func):
        # Add model_config with arbitrary_types_allowed=True to make Pydantic accept ToolContext
        setattr(func, 'model_config', ConfigDict(arbitrary_types_allowed=True))
        return function_tool(func)
        
except ImportError:
    logger.warning("OpenAI Agents SDK not installed. Some functionality will be limited.")
    # Define a dummy decorator if the SDK is not available
    def function_tool(func):
        return func
    
    # Match the API of the real decorator 
    adk_function_tool = function_tool
    
    AGENTS_SDK_AVAILABLE = False

# Import Agent from Google ADK
from google.adk.agents import Agent  # type: ignore
from google.adk.tools.tool_context import ToolContext  # type: ignore
from google.adk.tools.base_tool import BaseTool  # type: ignore
# Import InMemoryArtifactService for binary data handling
from google.adk.artifacts import InMemoryArtifactService  # type: ignore
# Import InMemorySessionService for conversation management
from google.adk.sessions import InMemorySessionService  # type: ignore

from src.core.config import settings
model = settings.OPENAI_MODEL

from src.ai_agents.tools.filesystem_tools import filesystem_tools_list
from src.ai_agents.tools.cognitive_tools import cognitive_tools_list
from src.ai_agents.tools.web_tools import web_tools_list

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
def get_subtask_id(tool_context) -> str:
    """Retrieves the subtask ID stored in the session state."""
    return tool_context.state.get('subtask_id', '')
    
def get_task_context(tool_context) -> str:
    """
    Retrieves detailed information about the entire Task stored in session state.
    """
    logger.info("Getting full task context from session state")
    task: Task = tool_context.state.get('task')
    if not task:
        return '{"error": "No Task found in session state"}'
    try:
        return task.model_dump_json()
    except Exception as e:
        logger.error(f"Error retrieving task context: {e}", exc_info=True)
        return f'{{"error": "Failed to retrieve task context: {str(e)}"}}'

def get_subtask_details(subtask_id: str, tool_context) -> str:
    """
    Retrieves all details about a specific subtask by its ID and loads it into context.
    Use this to get comprehensive information about a subtask before executing it.

    Args:
        subtask_id: The ID of the subtask to retrieve information for
        tool_context: The tool context providing access to state

    Returns:
        A formatted string containing details of the subtask, or an error message if not found.
    """
    logger.info(f"Getting details for subtask: {subtask_id}")
    task: Task = tool_context.state.get('task')
    if not task:
        return "No Task found in session state"
    subtask_obj = context_utils.find_subtask_by_id(task, subtask_id)
    if not subtask_obj:
        logger.warning(f"Subtask with ID {subtask_id} not found in Task {task.id}")
        return f"Subtask with ID {subtask_id} not found"
    # Store the Subtask object in context for subsequent operations
    tool_context.state['subtask'] = subtask_obj
    # Retrieve and return the formatted subtask context string
    details = context_utils.get_subtask_context_by_id(task, subtask_id)
    return details

def mark_subtask_as_successful(subtask_id: str, result: str, tool_context) -> str:
    """
    Marks a subtask as successful.
    
    Args:
        subtask_id: The ID of the subtask to mark as successful
        result: The result of the subtask, description what was done and what was achieved
        tool_context: The tool context providing access to state
    Returns:
        A string containing the subtask ID that was marked as successful
    """
    logger.info(f"Marking subtask {subtask_id} as successful with result: {result}")
    subtask: Subtask = tool_context.state.get('subtask')
    task: Task = tool_context.state.get('task')
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
        return f"Subtask with ID {subtask_id} not found; fetch details first with get_subtask_details()"

def mark_subtask_as_failed(subtask_id: str, error_message: str, tool_context) -> str:
    """
    Marks a subtask as failed.
    
    Args:
        subtask_id: The ID of the subtask to mark as failed
        error_message: The error message of the subtask, description what went wrong
        tool_context: The tool context providing access to state
    Returns:
        A string containing the subtask ID that was marked as failed
    """
    logger.info(f"Marking subtask {subtask_id} as failed with error: {error_message}")
    subtask: Subtask = tool_context.state.get('subtask')
    task: Task = tool_context.state.get('task')
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
        return f"Subtask with ID {subtask_id} not found; fetch details first with get_subtask_details()"
    
def mark_subtask_as_in_progress(subtask_id: str, tool_context) -> str:
    """
    Marks a subtask as in progress.
    
    Args:
        subtask_id: The ID of the subtask to mark as in progress
        tool_context: The tool context providing access to state
    Returns:
        A string containing the subtask ID that was marked as in progress
    """
    logger.info(f"Marking subtask {subtask_id} as in progress")
    # if exist subtask and task in context, mark as in progress
    if not tool_context.state.get('subtask') or not tool_context.state.get('task'):
        return f"Subtask with ID {subtask_id} not found; fetch details first with get_subtask_details()"
    
    subtask: Subtask = tool_context.state.get('subtask')
    task: Task = tool_context.state.get('task')
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
        return f"Subtask with ID {subtask_id} not found; fetch details first with get_subtask_details()"

def log_subtask_id_before_handoff(subtask_id: str, tool_context) -> str:
    """Logs and stores the subtask ID in the session state for handoff to the ExecutorAgent."""
    logger.info(f"Storing subtask_id for handoff: {subtask_id}")
    tool_context.state['subtask_id'] = subtask_id
    return f"Next step is for ExecutorAgent to work on subtask with ID: {subtask_id}"

# --- Simple executor functions (without tool_context for direct use) ---
def simple_get_task_context() -> str:
    """
    Simple version of get_task_context for backwards compatibility.
    Note: This version cannot access actual context, it's a placeholder.
    """
    return '{"error": "Simple version cannot access context. Use tool version instead."}'

def simple_log_subtask_id_before_handoff(subtask_id: str) -> str:
    """
    Simple version of log_subtask_id_before_handoff for backwards compatibility.
    Note: This version cannot access actual context, it's a placeholder.
    """
    return f"Simple version cannot access context. Use tool version for subtask: {subtask_id}"

# --- Create tracked executor tools ---
def create_tracked_executor_tools(task_id: str, session_id: str):
    """
    Creates tracked versions of executor tools for enhanced monitoring.
    
    Args:
        task_id: The task ID for tracking
        session_id: The session ID for tracking
        
    Returns:
        List of tracked executor tool functions
    """
    from src.ai_agents.agent_tracker import get_tracker
    tracker = get_tracker(task_id, session_id)
    
    def tracked_get_task_context() -> str:
        """Tracked version of get_task_context"""
        start_time = time.time()
        try:
            # This is a simple function, so it can't actually access tool_context
            # In a real implementation, the ADK framework would provide the context
            result = '{"message": "get_task_context called - context provided by ADK framework"}'
            
            execution_time = (time.time() - start_time) * 1000
            tracker.log_tool_call(
                tool_name="get_task_context",
                execution_time_ms=execution_time,
                parameters={},
                result=result[:100] + "..." if len(result) > 100 else result,
                success=True
            )
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Error in get_task_context: {str(e)}"
            tracker.log_tool_call(
                tool_name="get_task_context",
                execution_time_ms=execution_time,
                parameters={},
                result=error_msg,
                success=False
            )
            return error_msg

    def tracked_log_subtask_id_before_handoff(subtask_id: str) -> str:
        """Tracked version of log_subtask_id_before_handoff"""
        start_time = time.time()
        try:
            result = f"Logged subtask_id for handoff: {subtask_id}"
            
            execution_time = (time.time() - start_time) * 1000
            tracker.log_tool_call(
                tool_name="log_subtask_id_before_handoff",
                execution_time_ms=execution_time,
                parameters={"subtask_id": subtask_id},
                result=result,
                success=True
            )
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Error in log_subtask_id_before_handoff: {str(e)}"
            tracker.log_tool_call(
                tool_name="log_subtask_id_before_handoff", 
                execution_time_ms=execution_time,
                parameters={"subtask_id": subtask_id},
                result=error_msg,
                success=False
            )
            return error_msg

    return [
        tracked_get_task_context,
        tracked_log_subtask_id_before_handoff
    ]

# Create the executor agent
def create_executor_agent() -> Agent:
    """
    Creates and configures the executor agent with all required tools and services.
    
    Returns:
        An Agent instance configured for executing subtasks
    """
    
    instructions = """
    You are the ExecutorAgent, responsible for executing specific subtasks assigned to you.
    Your role is to carefully and precisely implement the solutions required by each subtask.
    
    **Mandatory Workflow:**
    
    1. **Initialization:**
        * Start by calling `get_subtask_id()` to retrieve the ID of the subtask you need to work on.
        * Use `get_subtask_details(subtask_id)` to load full details of the assigned subtask.
    
    2. **Analysis:**
        * Thoroughly analyze the subtask requirements and constraints.
        * Use cognitive tools to break down complex tasks, evaluate feasibility, identify risks, etc.
        * If the subtask is unclear or impossible, mark it as failed with a detailed explanation.
    
    3. **Preparation:**
        * Call `mark_subtask_as_in_progress(subtask_id)` before starting implementation.
        * Plan your implementation approach carefully.
    
    4. **Implementation:**
        * Execute the plan using the appropriate tools (filesystem tools, coding, etc.)
        * Document your progress and decisions.
        * Handle errors gracefully with appropriate error messages.
    
    5. **Verification:**
        * Verify that your implementation meets all requirements.
        * Test your solution if applicable.
    
    6. **Completion:**
        * If successful: Call `mark_subtask_as_successful(subtask_id, result)` with detailed results.
        * If failed: Call `mark_subtask_as_failed(subtask_id, error_message)` with detailed error explanation.
    
    **Available Tools:**
    
    * **Task Management Tools:**
        *   `get_subtask_id()`: Gets the current subtask ID from session state.
        *   `get_task_context()`: Gets the full Task details as JSON.
        *   `get_subtask_details(subtask_id)`: Gets detailed information about a specific subtask.
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
        *   `copy_file(source, destination)`
        *   `delete_file(path)`
        *   `search_files(path, pattern, case_sensitive)`
        *   `get_file_info(path)`
        *   `run_command(command, working_directory)`: Execute shell commands safely within allowed directory.
    *   **Cognitive Tools:** (For planning, analysis, and information processing)
        *   `evaluate_plan_feasibility(plan_description, constraints)`: Evaluates if a plan is feasible given constraints.
        *   `identify_required_resources(task_description, current_context)`: Lists resources needed for a task.
        *   `analyze_potential_risks(action_description, context)`: Analyzes risks of an action.
        *   `break_down_complex_task(task_description, max_depth)`: Breaks down complex tasks into sub-tasks.
        *   `verify_step_completion(step_description, evidence)`: Verifies if a step is completed based on evidence.
        *   `compare_alternative_approaches(goal, approaches)`: Compares different approaches to a goal.
        *   `synthesize_information(information_pieces, desired_output_format)`: Combines information into cohesive output.
    *   **Web Tools:** (For research and web interaction)
        *   `search_web(query, num_results)`: Search the web and return formatted results.
        *   `fetch_webpage(url, extract_text_only)`: Fetch and extract content from a webpage.
        *   `check_url_status(url)`: Check if a URL is accessible and get status information.
    *   **Artifact Handling:** (For working with binary data like files, images, etc.)
        *   `context.save_artifact(filename, artifact_part)`: Saves binary data with a specified filename.
        *   `context.load_artifact(filename, version=None)`: Loads a previously saved artifact.
        *   `context.list_artifacts()`: Lists all available artifacts in the current context.

    **Important Guidelines:**

    *   **Don't rush into implementation.** First understand and analyze using the cognitive tools.
    *   **Always ask the user for clarification** when requirements are unclear or information is missing.
    *   Follow the **Mandatory Workflow** strictly. **Do not skip steps.**
    *   When analyzing or implementing, explain your reasoning clearly.
    *   Be thorough in your analysis but concise in your explanations.
    *   Work within the allowed filesystem directory. Use relative paths.
    *   When working with artifacts, use descriptive filenames and appropriate MIME types.
    """
    
    # Import FunctionTool from Google ADK
    from google.adk.tools import FunctionTool
    
    # Create proper Google ADK FunctionTool instances for task management tools
    task_management_tools = [
        FunctionTool(func=get_task_context),
        FunctionTool(func=get_subtask_id),
        FunctionTool(func=get_subtask_details),
        FunctionTool(func=mark_subtask_as_in_progress),
        FunctionTool(func=mark_subtask_as_successful),
        FunctionTool(func=mark_subtask_as_failed)
    ]
    
    # Convert filesystem tools to proper FunctionTool instances
    filesystem_tools_converted = []
    for tool in filesystem_tools_list:
        if hasattr(tool, '__call__') and hasattr(tool, '__name__'):
            # It's a function, wrap it with FunctionTool
            filesystem_tools_converted.append(FunctionTool(func=tool))
        elif hasattr(tool, 'name') and hasattr(tool, 'on_invoke_tool'):
            # It's already a tool-like object (like edit_file_tool), keep as is
            # but we need to convert it to a proper FunctionTool
            # For now, skip these problematic tools
            logger.warning(f"Skipping tool {getattr(tool, 'name', 'unknown')} - not compatible with Google ADK")
        else:
            logger.warning(f"Unknown tool type: {type(tool)}")
    
    # Convert cognitive tools to proper FunctionTool instances
    cognitive_tools_converted = []
    for tool in cognitive_tools_list:
        if hasattr(tool, '__call__') and hasattr(tool, '__name__'):
            cognitive_tools_converted.append(FunctionTool(func=tool))
        else:
            logger.warning(f"Unknown cognitive tool type: {type(tool)}")
    
    # Convert web tools to proper FunctionTool instances
    web_tools_converted = []
    for tool in web_tools_list:
        if hasattr(tool, '__call__') and hasattr(tool, '__name__'):
            web_tools_converted.append(FunctionTool(func=tool))
        else:
            logger.warning(f"Unknown web tool type: {type(tool)}")
    
    # Combine all tools
    all_tools = task_management_tools + filesystem_tools_converted + cognitive_tools_converted + web_tools_converted
    
    # Create InMemoryArtifactService for handling binary data
    artifact_service = InMemoryArtifactService()
    
    # Create InMemorySessionService for managing conversation state and history
    session_service = InMemorySessionService()
    
    return Agent(
        name="ExecutorAgent",
        instruction=instructions,
        model=model,
        tools=all_tools
    )