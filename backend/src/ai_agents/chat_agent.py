import logging
from typing import AsyncGenerator, List, Any, Optional
import json 
import time

from src.model.task import Task
from src.ai_agents.utils import detect_language, get_language_instruction
from src.ai_agents.tools.filesystem_tools import google_adk_filesystem_tools, create_tracked_filesystem_tools
from src.ai_agents.tools.cognitive_tools import google_adk_cognitive_tools, create_tracked_cognitive_tools
from src.ai_agents.tools.web_tools import google_adk_web_tools, create_tracked_web_tools
from src.ai_agents.tools.task_management_tools import create_tracked_task_management_tools
from src.ai_agents.executor_agent import create_executor_agent
from src.core.config import settings
from src.ai_agents.agent_tracker import get_tracker

# Google ADK imports
from google.adk.agents import Agent  # type: ignore
from google.adk.sessions import InMemorySessionService  # type: ignore
from google.adk.runners import Runner  # type: ignore
from google.genai import types  # type: ignore
from google.adk.memory import InMemoryMemoryService  # type: ignore
from google.adk.tools import load_memory  # type: ignore
from google.adk.tools import FunctionTool  # type: ignore
from google.adk.tools.base_tool import BaseTool  # type: ignore
from google.adk.models.lite_llm import LiteLlm

# ExecutorAgent tools
from src.ai_agents.executor_agent import (  # type: ignore
    create_tracked_executor_tools,
)

# Persistent workspace management
from src.ai_agents.workspace_manager import get_workspace_manager
from src.ai_agents.workspace_tools import create_workspace_management_tools
from src.ai_agents.tools.database_tools import create_tracked_database_tools

# NEW: Add workspace-aware tools
from src.ai_agents.workspace_aware_tools import create_workspace_aware_tools

# NEW: Add intent understanding tools for better user interaction
from src.ai_agents.intent_understanding_tools import create_intent_understanding_tools

# NEW: Add task execution tools for comprehensive task management
from src.ai_agents.task_execution_tools import create_task_execution_tools

# Add new imports for workspace management
import os
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

# Create a shared session service that persists across requests
# This will allow us to maintain conversation state
_session_service = InMemorySessionService()
_memory_service = InMemoryMemoryService()

def create_workspace_for_task(task_id: str) -> str:
    """
    Creates or returns persistent workspace directory for the task.
    NO MORE RANDOM SUFFIXES! One workspace per task, persistent across sessions.
    
    This is a major improvement inspired by Manus AI and Cursor AI patterns.
    """
    workspace_manager = get_workspace_manager()
    workspace_path = workspace_manager.create_or_get_workspace(task_id)
    
    # Load existing context if available
    context = workspace_manager.load_context(task_id)
    if context:
        logger.info(f"Loaded existing context for task {task_id}: {len(context)} components")
    
    logger.info(f"Using persistent workspace for task {task_id}: {workspace_path}")
    return workspace_path

def get_enhanced_instruction(task: Task, workspace_path: str) -> str:
    """
    Creates an enhanced instruction that gives the agent more autonomy and capabilities.
    Now includes persistent workspace context for continuity across sessions.
    """
    # Load workspace context
    workspace_manager = get_workspace_manager()
    context_summary = workspace_manager.get_context_summary(str(task.id))
    
    base_instruction = f"""You are an advanced AI assistant with autonomous capabilities, similar to Claude Code. You have access to a dedicated PERSISTENT workspace and comprehensive tools to help users with complex tasks.

**PERSISTENT WORKSPACE CONTEXT**:
{context_summary}

**Your Workspace**: {workspace_path}
- You can create, read, modify files **WITHIN YOUR WORKSPACE ONLY**
- Run commands and scripts
- Search the web for information
- Analyze and process data
- Create subdirectories and organize your work
- **IMPORTANT**: This workspace persists across sessions - you can build upon previous work!
- **FILE OPERATIONS**: All file operations are automatically scoped to your workspace directory

**Your Mission**: 
- Understand the user's request deeply
- Review previous work and context from this workspace
- Break down complex tasks into manageable steps
- Use your tools proactively to gather information, create files, and execute solutions
- Provide detailed explanations of your process
- Maintain context and build upon previous work
- Save important findings and progress to workspace files

**Task Context**:
- Task ID: {task.id}"""

    if task.task:
        base_instruction += f"\n- Task: {task.task}"
    if task.short_description:
        base_instruction += f"\n- Description: {task.short_description}"
    if task.state:
        base_instruction += f"\n- State: {task.state.value if hasattr(task.state, 'value') else task.state}"

    base_instruction += """

**INTELLIGENT TASK MANAGEMENT:**
You have special tools to analyze and manage the current task's structure:

1. **get_task_stages_summary(task_id)** - Analyzes current task structure and shows which stages need work packages, which work packages need tasks, etc.
2. **suggest_next_action(task_id)** - Gets intelligent suggestions for the next logical step based on current task state.
3. **generate_work_packages_for_stage(task_id, stage_id)** - Generates work packages for a specific stage.
4. **generate_tasks_for_work_package(task_id, stage_id, work_id)** - Generates executable tasks for a work package.
5. **generate_subtasks_for_executable_task(task_id, stage_id, work_id, executable_task_id)** - Generates subtasks for execution.

**WORK PACKAGE IDENTIFIER RECOGNITION:**
- When user mentions "s1_w1", "S1_W1", or similar patterns, this refers to work package ID "S1_W1" in stage "S1"
- Pattern: "s<stage_number>_w<work_number>" = Stage ID "S<stage_number>", Work ID "S<stage_number>_W<work_number>"
- Examples: "s1_w1" = Stage "S1", Work "S1_W1"; "s2_w3" = Stage "S2", Work "S2_W3"

**SMART WORKFLOW:**
- ALWAYS start with analyzing the current task state using get_task_stages_summary() when user asks to work on stages or tasks
- Use suggest_next_action() to understand what needs to be done next
- When user asks to generate tasks for a specific work package (like "s1_w1"), IMMEDIATELY use generate_tasks_for_work_package()
- When user says "only do this for the s1_w1" or similar, they want you to generate tasks for that specific work package
- Suggest work package generation if stages are missing work packages
- Offer to generate tasks or subtasks when appropriate
- Explain what you're doing and why each step is needed
- NEVER provide manual text descriptions of tasks - ALWAYS use the actual task generation tools

**WORKSPACE PERSISTENCE:**
- Review previous session history and project notes before starting new work
- Update project notes with important findings and decisions
- Save generated files to the generated_files/ directory
- Build upon previous work rather than starting from scratch
- Reference previous findings and context when relevant

**WORKSPACE MANAGEMENT TOOLS:**
You have special tools to actively manage your persistent workspace:

1. **workspace_update_notes(notes)** - Add important findings and decisions to project notes
2. **workspace_update_status(current_focus, completed_tasks, next_actions, files_created)** - Update your current progress
3. **workspace_get_context()** - Get a summary of all workspace context
4. **workspace_get_history(last_n_sessions)** - Review recent conversation history
5. **workspace_save_file(filename, content, subfolder)** - Save files directly to workspace
6. **workspace_list_files()** - List all files in the workspace
7. **workspace_get_info()** - Get workspace path and status information

Use these tools proactively to maintain context and build upon previous work!

**WORKSPACE-SCOPED FILE OPERATIONS:**
You now have workspace-scoped file tools that prevent directory confusion:

1. **create_directory(path)** - Creates directories within YOUR workspace
2. **write_file(path, content)** - Creates files within YOUR workspace
3. **read_file(path)** - Reads files from YOUR workspace
4. **list_directory(path)** - Lists contents within YOUR workspace
5. **get_workspace_info()** - Shows workspace path and scope information

🎯 **KEY FEATURE**: These tools automatically work within your task's workspace directory!
No more confusion about where files are created - everything stays in YOUR workspace.

**DATABASE QUERY TOOLS:**
You now have direct access to database information to compare and sync with workspace:

1. **get_task_from_database(task_id)** - Get complete task data from database
2. **get_task_stages_from_database(task_id)** - Get detailed stage information from database
3. **get_work_package_details_from_database(task_id, stage_id, work_id)** - Get specific work package details
4. **compare_workspace_with_database(task_id)** - Compare workspace state with database state
5. **get_all_tasks_from_database()** - Get summary of all tasks in database
6. **get_user_queries_from_database(task_id)** - Get user queries for this task

Use these tools to ensure your workspace understanding matches the database reality!

**Guidelines**:
1. Be proactive - analyze task state and suggest logical next steps
2. When user mentions working on "этап 1" or "stage 1", analyze what needs to be done for that stage
3. Always explain the task structure and current progress before making suggestions
4. If work packages are missing, offer to generate them and explain the benefits
5. Create organized file structures in your workspace when needed
6. Handle errors gracefully and try alternative approaches
7. Save important results and maintain session state
8. Reference and build upon previous work from this persistent workspace
9. ALL FILE OPERATIONS are automatically scoped to your workspace - no path confusion!

**Available Tools**: You have access to workspace-scoped filesystem tools, web search, cognitive tools, task management tools, and can hand off to specialized agents when needed.

Please respond naturally and use your tools as needed to accomplish the user's goals. When working with tasks and stages, always analyze the current state first and provide intelligent suggestions. Remember that this workspace persists across sessions, so you can build upon previous work!

**INTENT UNDERSTANDING TOOLS:**
You now have advanced tools to better understand user intentions, especially for specific task references:

1. **parse_task_reference(message)** - Parses task IDs like S1_W1_ET1_ST1 from user messages
2. **analyze_intent(message)** - Analyzes user intent (status inquiry, verification, etc.)
3. **check_task_completion_status(task_reference)** - Checks both workspace AND database for task completion
4. **generate_smart_response(message)** - Generates intelligent responses based on intent analysis

🎯 **SMART INTENT DETECTION**: When users ask about specific tasks like "S1_W1_ET1_ST1 выполнена или нет?", 
automatically use these tools to check BOTH workspace files AND database status!

**TASK EXECUTION TOOLS:**
You now have comprehensive task execution capabilities with full lifecycle management:

1. **get_task_details(task_reference, task_type)** - Get detailed task info including validation criteria
2. **execute_task(task_details)** - Execute tasks based on their requirements and description
3. **validate_task_completion(task_details, execution_result)** - Validate against criteria
4. **update_task_status_complete(task_id, validation_result, execution_result)** - Update status and fill result fields
5. **execute_task_flow(task_reference, task_type)** - Complete flow: get details → execute → validate → update
6. **mark_last_checked_task_complete(task_reference)** - 🆕 Simple wrapper to mark a task as complete
7. **update_task_status_from_message(user_message)** - 🆕 Smart wrapper that extracts task reference from message

🎯 **TASK EXECUTION FLOW**: Use execute_task_flow() for complete task processing:
- Gets task details including validation criteria
- Executes the task based on requirements
- Validates completion against criteria
- Updates status (Pending → In Progress → Completed/Failed)
- Fills result fields with artifacts and timestamps

🎯 **SIMPLIFIED UPDATE**: For simple status updates, use:
- **mark_last_checked_task_complete(task_reference)** - Direct completion for specific task
- **update_task_status_from_message(user_message)** - Smart parsing and completion from user intent

**VALIDATION & STATUS MANAGEMENT**: 
- Tasks must pass ALL validation criteria to be marked as Completed
- Failed validation marks task as Failed with detailed error info
- All status changes are tracked with timestamps
- Result fields include execution summary, artifacts created, validation results
"""

    return base_instruction

async def stream_chat_response(task: Task, user_message: str, message_history: Optional[List[Any]] = None, session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
    """
    Streams a chat response for the given task and user message using Agent SDK.
    Now uses intelligent routing to automatically direct requests to appropriate specialist agents.
    Also saves session data to persistent workspace for context continuity.

    Args:
        task: The task to generate a response for
        user_message: The user's message to respond to
        message_history: Optional list of previous messages in the conversation (legacy parameter)
        session_id: Optional session ID for maintaining conversation state between requests

    Yields:
        Chunks of the response as they are generated
    """
    logger.info(f"Starting intelligent chat response for task {task.id} with session_id: {session_id}")

    # Use the task_id as default session_id if none provided
    effective_session_id = session_id or f"session_{task.id}"
    
    # Accumulate response for saving to workspace
    accumulated_response = ""

    # Use intelligent routing system
    try:
        from src.ai_agents.router_agent import stream_intelligent_router_response
        async for content in stream_intelligent_router_response(task, user_message, effective_session_id):
            accumulated_response += content
            yield content
    except ImportError as e:
        logger.warning(f"Router agent not available: {e}. Falling back to basic chat agent.")
        # Fallback to basic chat agent if router is not available
        async for content in stream_chat_with_agent_sdk(task, user_message, message_history, effective_session_id):
            accumulated_response += content
            yield content
    except Exception as e:
        logger.error(f"Error in intelligent routing: {e}. Falling back to basic chat agent.")
        # Fallback to basic chat agent on any error
        async for content in stream_chat_with_agent_sdk(task, user_message, message_history, effective_session_id):
            accumulated_response += content
            yield content
    
    # Save session to persistent workspace
    try:
        workspace_manager = get_workspace_manager()
        workspace_manager.save_session(
            task_id=str(task.id),
            user_message=user_message,
            agent_response=accumulated_response,
            session_id=effective_session_id
        )
        logger.info(f"Saved session to persistent workspace for task {task.id}")
    except Exception as e:
        logger.error(f"Failed to save session to workspace: {e}")
        # Don't fail the entire request if saving fails

async def stream_chat_with_agent_sdk(task: Task, user_message: str, message_history: Optional[List[Any]] = None, session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
    """
    Streams chat response using Google ADK's Agent streaming API.
    This implementation maintains conversation history between requests through session_service.
    """
    user_id = task.id  # Task ID will be used as user ID
    
    # Generate a session ID if one wasn't provided
    if not session_id:
        session_id = f"session_{task.id}"
    
    logger.info(f"Using session_id: {session_id} for chat with task {task.id}")
    
    # Create workspace for this task
    workspace_path = create_workspace_for_task(str(task.id))
    
    # Detect language and create appropriate instruction
    user_language = detect_language(user_message)
    language_instruction = get_language_instruction(user_language)
    
    # Build the enhanced instruction with workspace and capabilities
    full_instruction = get_enhanced_instruction(task, workspace_path)
    
    # Apply language preference
    if language_instruction:
        full_instruction = f"{language_instruction}\n\n{full_instruction}"

    # Create the content for the user message
    content = types.Content(role='user', parts=[types.Part(text=user_message)])
    
    try:
        # Ensure session exists - Fixed approach: handle synchronous session service
        session = None
        try:
            # Try to get the existing session first
            session = _session_service.get_session(
                app_name=settings.PROJECT_NAME,
                user_id=user_id,
                session_id=session_id
            )
            # Check if session is None (no exception thrown, just returns None)
            if session is None:
                raise Exception("Session not found")
            logger.info(f"Found existing session: {session.id}")
        except Exception as e:
            # Session doesn't exist, create it synchronously (no await needed!)
            logger.info(f"Creating new session, error was: {e}")
            # Create session synchronously - this was the key fix!
            session = _session_service.create_session(
                app_name=settings.PROJECT_NAME,
                user_id=user_id,
                session_id=session_id,
                state={"workspace_path": workspace_path, "task_id": str(task.id)}  # Store workspace info in session
            )
            logger.info(f"Created new session: {session.id}")
            # Use the session_id we provided
            session_id = session.id

        # Combine all available tools for the agent
        all_tools = []
        
        # Add tracked tools for enhanced monitoring
        # Ensure session_id is a string
        effective_session_id = session_id or f"session_{task.id}"
        tracker = get_tracker(str(task.id), effective_session_id)
        
        # Add workspace-aware tools for proper directory scoping
        all_tools.extend(create_workspace_aware_tools(str(task.id), effective_session_id))
        
        # Add intent understanding tools for better user interaction
        all_tools.extend(create_intent_understanding_tools(str(task.id), effective_session_id))
        
        # Add task execution tools for comprehensive task management
        all_tools.extend(create_task_execution_tools(str(task.id), effective_session_id))
        
        # Add cognitive tools (for analysis and planning) with tracking
        all_tools.extend(create_tracked_cognitive_tools(str(task.id), effective_session_id))
        
        # Add web tools (for research and information gathering) with tracking
        all_tools.extend(create_tracked_web_tools(str(task.id), effective_session_id))
        
        # Add task management tools - Google ADK auto-wraps functions as FunctionTool
        all_tools.extend(create_tracked_task_management_tools(str(task.id), effective_session_id))
        
        # Add workspace management tools for persistent workspace interaction
        all_tools.extend(create_workspace_management_tools(str(task.id), effective_session_id))
        
        # Add database tools for querying and comparing workspace state with database state
        all_tools.extend(create_tracked_database_tools(str(task.id), effective_session_id))
        
        # Create executor agent tools for delegation
        executor_tools = create_tracked_executor_tools(str(task.id), effective_session_id)
        
        # Add executor functions directly (they should already be simple functions)
        all_tools.extend(executor_tools)

        # Create the ADK agent with OpenAI model via LiteLLM and all tools
        agent = Agent(
            name="autonomous_task_assistant",
            model=LiteLlm(model=f"openai/{settings.OPENAI_MODEL}"),  # Use LiteLlm wrapper for OpenAI
            instruction=full_instruction,
            tools=all_tools  # Provide all available tools
        )
        
        # Create the runner with the agent and session service
        runner = Runner(
            agent=agent,
            app_name=settings.PROJECT_NAME,
            session_service=_session_service
        )
        
        # Run and stream using ADK with the confirmed session ID
        logger.info(f"Starting autonomous agent with session_id: {session_id}, workspace: {workspace_path}")
        
        # Variables for tracking streaming state
        agent_response_accumulator = ""
        tools_displayed = False
        
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
            # Track event details for debugging
            logger.debug(f"ADK Event: author={getattr(event, 'author', 'unknown')}, "
                        f"partial={getattr(event, 'partial', None)}, "
                        f"has_content={bool(event.content)}, "
                        f"is_final={event.is_final_response()}")
            
            # Handle Function Calls (Tool Requests) - Display immediately
            function_calls = event.get_function_calls() if hasattr(event, 'get_function_calls') else []
            if function_calls:
                if not tools_displayed:
                    yield f"\n🛠️ **Tools Used:** (real-time as tools are called ✅)\n"
                    tools_displayed = True
                
                for call in function_calls:
                    tool_name = getattr(call, 'name', 'unknown_tool')
                    yield f"  • 🔄 {tool_name} (executing...)\n"
                    
                    # Log tool call in tracker
                    tracker.log_tool_call(
                        tool_name=tool_name,
                        parameters=getattr(call, 'args', {}),
                        success=True,  # Initial call is successful, will be updated if there's an error
                        execution_time_ms=None
                    )
            
            # Handle Function Responses (Tool Results) - Display results
            function_responses = event.get_function_responses() if hasattr(event, 'get_function_responses') else []
            if function_responses:
                for response in function_responses:
                    tool_name = getattr(response, 'name', 'unknown_tool')
                    success = True  # Assume success if we got a response
                    
                    # Update the tool call status in display
                    yield f"  • ✅ {tool_name} (completed)\n"
                    
                    # Update tracker with results
                    tracker.log_tool_call(
                        tool_name=tool_name,
                        result=str(getattr(response, 'response', 'No response'))[:100],
                        success=success
                    )
            
            # Handle Text Content - Stream as it comes
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_chunk = part.text
                        agent_response_accumulator += text_chunk
                        
                        # Yield the text chunk immediately for real-time streaming
                        yield text_chunk
            
            # Check if this is the final response
            if event.is_final_response():
                logger.debug(f"Final response detected, accumulated text length: {len(agent_response_accumulator)}")
                # Final response reached - end the stream
                if not agent_response_accumulator.strip():
                    yield "\n\n✅ Task completed."
                return

    # Error handling with better session error detection
    except Exception as e:
        logger.error(f"Error in Agent SDK chat streaming: {str(e)}", exc_info=True)
        
        # Handle specific session errors by providing helpful message
        error_message = str(e).lower()
        if "session not found" in error_message:
            yield "⚠️ Error: Your chat session has expired. Please reset the chat to continue."
        elif "timeout" in error_message:
            yield "⚠️ Error: The request timed out. Please try again."
        elif "authentication" in error_message or "unauthorized" in error_message:
            yield "⚠️ Error: Authentication failed. Please check your credentials."
        else:
            yield f"⚠️ Error: {str(e)}"