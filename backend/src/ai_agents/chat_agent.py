import logging
from typing import AsyncGenerator, List, Any, Optional
import json 

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
    
    # Generate a sessiong ID if one wasn't provided
    if not session_id:
        session_id = f"session_{task.id}"
    
    logger.info(f"Using session_id: {session_id} for chat with task {task.id}")
    
    # Detect language and create appropriate instruction
    user_language = detect_language(user_message)
    language_instruction = get_language_instruction(user_language)
    
    # Variable to collect the complete agent response for logging
    agent_response_accumulator = ""
    
    try:
        # Create task context string from Task model fields
        task_context = f"""
        Task ID: {task.id}
        Task: {task.task or ''}
        Short Description: {task.short_description or ''}
        State: {task.state.value if hasattr(task.state, 'value') else task.state if task.state else 'Unknown'}
        Context: {task.context or ''}
        """
        
        # Add scope information if available
        if task.scope:
            task_context += f"""
            Scope: {task.scope.scope or ''}
            """
        
        # Add IFR information if available
        if task.ifr:
            ifr_criteria = "\n".join([f"- {criterion}" for criterion in (task.ifr.success_criteria or [])])
            ifr_outcomes = "\n".join([f"- {outcome}" for outcome in (task.ifr.expected_outcomes or [])])
            
            task_context += f"""
            Ideal Final Result: {task.ifr.ideal_final_result or ''}
            Success Criteria: 
            {ifr_criteria}
            Expected Outcomes:
            {ifr_outcomes}
            """
        
        # Add Requirements information if available
        if task.requirements:
            requirements = "\n".join([f"- {req}" for req in (task.requirements.requirements or [])])
            constraints = "\n".join([f"- {constraint}" for constraint in (task.requirements.constraints or [])])
            limitations = "\n".join([f"- {limitation}" for limitation in (task.requirements.limitations or [])])
            resources = "\n".join([f"- {resource}" for resource in (task.requirements.resources or [])])
            tools = "\n".join([f"- {tool}" for tool in (task.requirements.tools or [])])
            
            task_context += f"""
            Requirements:
            {requirements}
            
            Constraints:
            {constraints}
            
            Limitations:
            {limitations}
            
            Resources:
            {resources}
            
            Tools:
            {tools}
            """
    
        instructions = f"""
        You are a helpful assistant similar to Claude Code, capable of helping users with complex tasks through conversation and tool usage.
        You can create files, write code, search the web, run commands, and execute various operations to help solve problems.
        
        CAPABILITIES:
        - **File Operations**: Read, write, edit, create, delete, copy, move files and directories
        - **Command Execution**: Run shell commands safely (git, npm, python, etc.)
        - **Web Research**: Search the web and fetch content from URLs
        - **Cognitive Analysis**: Plan, analyze, break down complex tasks
        - **Task Execution**: Execute subtasks through specialized ExecutorAgent
        
        TASK CONTEXT:
        {task_context}
        
        INTERACTION STYLE:
        - Be conversational and helpful like Claude Code
        - Ask clarifying questions when needed
        - Provide step-by-step guidance
        - Use tools proactively to help solve problems
        - Execute commands and operations as needed
        
        LANGUAGE INSTRUCTION:
        {language_instruction}
        """
        
        # Create our agent with tools and instructions
        executor_agent = create_executor_agent()
        
        # Import FunctionTool from Google ADK
        from google.adk.tools import FunctionTool
        
        # Convert tools to proper Google ADK FunctionTool instances
        adk_tools = []
        
        # Add the task management tools as FunctionTool instances
        adk_tools.extend([
            FunctionTool(func=get_task_context),
            FunctionTool(func=log_subtask_id_before_handoff),
            FunctionTool(func=load_memory)
        ])
        
        # Convert filesystem tools
        for tool in filesystem_tools_list:
            if hasattr(tool, '__call__') and hasattr(tool, '__name__'):
                adk_tools.append(FunctionTool(func=tool))
            else:
                logger.warning(f"Skipping filesystem tool {getattr(tool, 'name', 'unknown')} - not compatible with Google ADK")
        
        # Convert cognitive tools
        for tool in cognitive_tools_list:
            if hasattr(tool, '__call__') and hasattr(tool, '__name__'):
                adk_tools.append(FunctionTool(func=tool))
            else:
                logger.warning(f"Skipping cognitive tool {getattr(tool, 'name', 'unknown')} - not compatible with Google ADK")
        
        # Convert web tools
        for tool in web_tools_list:
            if hasattr(tool, '__call__') and hasattr(tool, '__name__'):
                adk_tools.append(FunctionTool(func=tool))
            else:
                logger.warning(f"Skipping web tool {getattr(tool, 'name', 'unknown')} - not compatible with Google ADK")
        
        # Create our agent with the proper tools
        agent = Agent(
            model=settings.OPENAI_MODEL,  
            name='main_assistant_agent',
            instruction=instructions,
            tools=adk_tools
        )

        # Create runner with our persistent session service
        runner = Runner(
            agent=agent, 
            app_name=settings.PROJECT_NAME, 
            session_service=_session_service, 
            memory_service=_memory_service
        )

        # Prepare user message for ADK
        content = types.Content(role="user", parts=[types.Part(text=user_message)])  # type: ignore
        
        # Run and stream using ADK
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
            if event.is_final_response():
                text = event.content.parts[0].text if event.content and event.content.parts else ""
                yield text
                return
        # Fallback empty
        yield ""

    # Error handling
    except Exception as e:
        logger.error(f"Error in Agent SDK chat streaming: {str(e)}", exc_info=True)
        # Yield a JSON error chunk for the frontend to parse
        yield json.dumps({"error": f"Error generating response: {str(e)}"}) + "\n\n"
    finally:
        # Log the complete agent response
        logger.info(f"AGENT RESPONSE for Task {task.id}: {agent_response_accumulator}")
        # pass # logger.debug("Chat stream finished.")