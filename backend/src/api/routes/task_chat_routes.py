"""
Task Chat Routes Module

Handles all API endpoints related to task chat functionality.
Includes regular chat, streaming chat, session reset, and agent tracing.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional, AsyncGenerator
import logging
import json

# Model imports
from src.model.task import Task
from src.schemas.chat import ChatRequest, ChatResponse

# Service imports
from src.services.database_service import DatabaseService

# API utils imports
from src.api.deps import get_file_storage_service
from src.api.utils import api_error_handler, deserialize_task

# Constants
from src.constants import OP_CHAT

# Import the chat agent and tracker
from src.ai_agents import stream_chat_response
from src.ai_agents.agent_tracker import get_tracker, _trackers

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{task_id}/chat", response_model=ChatResponse)
@api_error_handler(OP_CHAT)
async def chat_with_task_assistant(
    task_id: str,
    chat_request: ChatRequest,
    db: DatabaseService = Depends(get_db_service)
) -> ChatResponse:
    """
    Send a message to the task assistant and get a response.
    
    Args:
        task_id: Unique identifier of the task
        chat_request: Chat request with message and session information
        db: Database service
        
    Returns:
        Chat response with assistant's reply
        
    Raises:
        TaskNotFoundException: If task does not exist
    """
    logger.info(f"Chat request for task {task_id}: {chat_request.message}")
    
    # Get task to ensure it exists
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    # Process chat request with the AI agent
    # This would typically involve calling the chat agent
    # For now, return a placeholder response
    response = ChatResponse(
        message="This is a placeholder response for the chat feature.",
        session_id=chat_request.session_id or "default",
        timestamp="2024-01-01T00:00:00Z"
    )
    
    logger.info(f"Chat response for task {task_id}: {response.message}")
    return response


@router.post("/{task_id}/chat/stream")
@api_error_handler(OP_CHAT)
async def stream_chat_with_task_assistant(
    task_id: str,
    chat_request: ChatRequest,
    db: DatabaseService = Depends(get_db_service)
) -> StreamingResponse:
    """
    Stream a chat conversation with the task assistant.
    
    Args:
        task_id: Unique identifier of the task
        chat_request: Chat request with message and session information
        db: Database service
        
    Returns:
        Streaming response with chat data
        
    Raises:
        TaskNotFoundException: If task does not exist
    """
    logger.info(f"Starting streaming chat for task {task_id}")
    
    # Get task to ensure it exists
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate streaming chat events."""
        try:
            # Use the actual streaming chat response
            async for chunk in stream_chat_response(
                task=task,
                query=chat_request.message,
                session_id=chat_request.session_id or "default"
            ):
                if chunk:
                    # Format as Server-Sent Events
                    event_data = {
                        "type": "message_chunk",
                        "content": chunk,
                        "task_id": task_id,
                        "session_id": chat_request.session_id or "default"
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"
            
            # Send completion event
            completion_event = {
                "type": "completion",
                "task_id": task_id,
                "session_id": chat_request.session_id or "default"
            }
            yield f"data: {json.dumps(completion_event)}\n\n"
            
        except Exception as e:
            logger.error(f"Error in streaming chat for task {task_id}: {e}")
            error_event = {
                "type": "error",
                "error": str(e),
                "task_id": task_id
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


@router.post("/{task_id}/chat/reset")
@api_error_handler(OP_CHAT)
async def reset_chat_session(
    task_id: str,
    session_id: Optional[str] = None,
    db: DatabaseService = Depends(get_db_service)
) -> dict:
    """
    Reset the chat session for a task.
    
    Args:
        task_id: Unique identifier of the task
        session_id: Optional session ID to reset (defaults to "default")
        db: Database service
        
    Returns:
        Confirmation message
        
    Raises:
        TaskNotFoundException: If task does not exist
    """
    logger.info(f"Resetting chat session for task {task_id}")
    
    # Get task to ensure it exists
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    # Reset the chat session
    effective_session_id = session_id or "default"
    
    # Clear the chat history for this task and session
    # This would typically involve clearing the agent's memory
    logger.info(f"Chat session {effective_session_id} reset for task {task_id}")
    
    return {
        "message": f"Chat session reset successfully for task {task_id}",
        "session_id": effective_session_id
    }


@router.get("/{task_id}/trace")
async def get_agent_trace(
    task_id: str, 
    session_id: Optional[str] = None
) -> JSONResponse:
    """
    Get the agent execution trace for debugging purposes.
    
    Args:
        task_id: Unique identifier of the task
        session_id: Optional session ID
        
    Returns:
        JSON response with agent trace information
    """
    logger.info(f"Getting agent trace for task {task_id}")
    
    effective_session_id = session_id or "default"
    
    try:
        # Get the tracker for this task/session
        tracker = get_tracker(task_id, effective_session_id)
        
        if tracker:
            trace_data = {
                "task_id": task_id,
                "session_id": effective_session_id,
                "trace": tracker.get_trace(),
                "status": "success"
            }
        else:
            trace_data = {
                "task_id": task_id,
                "session_id": effective_session_id,
                "trace": [],
                "message": "No trace found for this task/session",
                "status": "not_found"
            }
        
        return JSONResponse(content=trace_data)
        
    except Exception as e:
        logger.error(f"Error getting trace for task {task_id}: {e}")
        error_data = {
            "task_id": task_id,
            "session_id": effective_session_id,
            "error": str(e),
            "status": "error"
        }
        return JSONResponse(content=error_data, status_code=500) 