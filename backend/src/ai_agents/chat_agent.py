import logging
from typing import AsyncGenerator, List, Any, Optional
import json 
import time

from src.model.task import Task
from src.ai_agents.utils import detect_language, get_language_instruction
from src.ai_agents.tools.filesystem_tools import filesystem_tools_list
from src.ai_agents.tools.cognitive_tools import cognitive_tools_list
from src.ai_agents.tools.web_tools import web_tools_list
from src.ai_agents.executor_agent import create_executor_agent
from src.core.config import settings

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
    get_task_context,
    log_subtask_id_before_handoff,
)

logger = logging.getLogger(__name__)

# Create a shared session service that persists across requests
# This will allow us to maintain conversation state
_session_service = InMemorySessionService()
_memory_service = InMemoryMemoryService()

async def stream_chat_response(task: Task, user_message: str, message_history: Optional[List[Any]] = None, session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
    """
    Streams a chat response for the given task and user message using Agent SDK.
    Includes filesystem tools if available.

    Args:
        task: The task to generate a response for
        user_message: The user's message to respond to
        message_history: Optional list of previous messages in the conversation (legacy parameter)
        session_id: Optional session ID for maintaining conversation state between requests

    Yields:
        Chunks of the response as they are generated
    """
    logger.info(f"Starting stream_chat_response for task {task.id} with session_id: {session_id}")

    # Use the task_id as default session_id if none provided
    effective_session_id = session_id or f"session_{task.id}"

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
    
    # Detect language and create appropriate instruction
    user_language = detect_language(user_message)
    language_instruction = get_language_instruction(user_language)
    
    # Build the instruction with task context and language preference
    task_context = f"Task ID: {task.id}"
    if task.task:
        task_context += f"\nTask: {task.task}"
    if task.short_description:
        task_context += f"\nDescription: {task.short_description}"
    if task.state:
        task_context += f"\nState: {task.state.value if hasattr(task.state, 'value') else task.state}"
    
    full_instruction = f"""{language_instruction}

You are a helpful AI assistant that can help with various tasks. Here's the current task context:

{task_context}

Please provide helpful, accurate responses and use available tools when appropriate."""

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
                state={}
            )
            logger.info(f"Created new session: {session.id}")
            # Use the session_id we provided
            session_id = session.id

        # Create the ADK agent with OpenAI model via LiteLLM
        agent = Agent(
            name="task_assistant",
            model=LiteLlm(model=f"openai/{settings.OPENAI_MODEL}"),  # Use LiteLlm wrapper for OpenAI
            instruction=full_instruction
        )
        
        # Create the runner with the agent and session service
        runner = Runner(
            agent=agent,
            app_name=settings.PROJECT_NAME,
            session_service=_session_service
        )
        
        # Run and stream using ADK with the confirmed session ID
        logger.info(f"Starting runner with session_id: {session_id}")
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