import logging
from typing import AsyncGenerator, List, Any, Optional
import json 
import time

from src.model.task import Task
from src.ai_agents.utils import detect_language, get_language_instruction
from src.ai_agents.tools.filesystem_tools import google_adk_filesystem_tools, create_tracked_filesystem_tools
from src.ai_agents.tools.cognitive_tools import google_adk_cognitive_tools, create_tracked_cognitive_tools
from src.ai_agents.tools.web_tools import google_adk_web_tools, create_tracked_web_tools
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

**Guidelines**:
1. Be proactive - don't wait for permission to use tools
2. Create organized file structures in your workspace
3. Document your work process
4. If you need to delegate to specialized agents, use the appropriate handoff tools
5. Always explain what you're doing and why
6. Handle errors gracefully and try alternative approaches
7. Save important results and maintain session state

**Available Tools**: You have access to filesystem tools, web search, cognitive tools, and can hand off to specialized agents when needed.

Please respond naturally and use your tools as needed to accomplish the user's goals."""

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
    agent_response_accumulator = ""
    
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
        tracker = get_tracker(str(task.id), session_id)
        
        # Add filesystem tools (for working in the agent's workspace) with tracking
        all_tools.extend(create_tracked_filesystem_tools(str(task.id), session_id))
        
        # Add cognitive tools (for analysis and planning) with tracking
        all_tools.extend(create_tracked_cognitive_tools(str(task.id), session_id))
        
        # Add web tools (for research and information gathering) with tracking
        all_tools.extend(create_tracked_web_tools(str(task.id), session_id))
        
        # Create executor agent tools for delegation
        executor_tools = create_tracked_executor_tools(str(task.id), session_id)
        
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
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
            if event.is_final_response():
                text = event.content.parts[0].text if event.content and event.content.parts else ""
                agent_response_accumulator += text
                yield text
                return
                
        # If no final response was received, yield an empty response
        if not agent_response_accumulator:
            yield "I apologize, but I couldn't generate a response. Please try again."

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