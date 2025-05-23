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
    Creates an isolated workspace directory for the task.
    This allows the agent to have its own sandbox environment.
    """
    workspace_base = Path(settings.ALLOWED_BASE_DIR_RESOLVED or Path.cwd()) / "agent_workspaces"
    workspace_path = workspace_base / f"task_{task_id}_{uuid.uuid4().hex[:8]}"
    
    # Create workspace directory
    workspace_path.mkdir(parents=True, exist_ok=True)
    
    # Create standard subdirectories
    (workspace_path / "data").mkdir(exist_ok=True)
    (workspace_path / "output").mkdir(exist_ok=True)
    (workspace_path / "temp").mkdir(exist_ok=True)
    
    logger.info(f"Created workspace for task {task_id}: {workspace_path}")
    return str(workspace_path)

def get_enhanced_instruction(task: Task, workspace_path: str) -> str:
    """
    Creates an enhanced instruction that gives the agent more autonomy and capabilities.
    """
    base_instruction = f"""You are an advanced AI assistant with autonomous capabilities, similar to Claude Code. You have access to a dedicated workspace and comprehensive tools to help users with complex tasks.

**Your Workspace**: {workspace_path}
- You can create, read, modify files
- Run commands and scripts
- Search the web for information
- Analyze and process data
- Create subdirectories and organize your work

**Your Mission**: 
- Understand the user's request deeply
- Break down complex tasks into manageable steps
- Use your tools proactively to gather information, create files, and execute solutions
- Provide detailed explanations of your process
- Maintain context and build upon previous work

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

**Guidelines**:
1. Be proactive - analyze task state and suggest logical next steps
2. When user mentions working on "этап 1" or "stage 1", analyze what needs to be done for that stage
3. Always explain the task structure and current progress before making suggestions
4. If work packages are missing, offer to generate them and explain the benefits
5. Create organized file structures in your workspace when needed
6. Handle errors gracefully and try alternative approaches
7. Save important results and maintain session state

**Available Tools**: You have access to filesystem tools, web search, cognitive tools, task management tools, and can hand off to specialized agents when needed.

Please respond naturally and use your tools as needed to accomplish the user's goals. When working with tasks and stages, always analyze the current state first and provide intelligent suggestions."""

    return base_instruction

async def stream_chat_response(task: Task, user_message: str, message_history: Optional[List[Any]] = None, session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
    """
    Streams a chat response for the given task and user message using Agent SDK.
    Now uses intelligent routing to automatically direct requests to appropriate specialist agents.

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

    # Use intelligent routing system
    try:
        from src.ai_agents.router_agent import stream_intelligent_router_response
        async for content in stream_intelligent_router_response(task, user_message, effective_session_id):
            yield content
    except ImportError as e:
        logger.warning(f"Router agent not available: {e}. Falling back to basic chat agent.")
        # Fallback to basic chat agent if router is not available
        async for content in stream_chat_with_agent_sdk(task, user_message, message_history, effective_session_id):
            yield content
    except Exception as e:
        logger.error(f"Error in intelligent routing: {e}. Falling back to basic chat agent.")
        # Fallback to basic chat agent on any error
        async for content in stream_chat_with_agent_sdk(task, user_message, message_history, effective_session_id):
            yield content

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
        
        # Add filesystem tools (for working in the agent's workspace) with tracking
        # Google ADK will automatically wrap Python functions as FunctionTool instances
        all_tools.extend(create_tracked_filesystem_tools(str(task.id), effective_session_id))
        
        # Add cognitive tools (for analysis and planning) with tracking
        all_tools.extend(create_tracked_cognitive_tools(str(task.id), effective_session_id))
        
        # Add web tools (for research and information gathering) with tracking
        all_tools.extend(create_tracked_web_tools(str(task.id), effective_session_id))
        
        # Add task management tools - Google ADK auto-wraps functions as FunctionTool
        all_tools.extend(create_tracked_task_management_tools(str(task.id), effective_session_id))
        
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