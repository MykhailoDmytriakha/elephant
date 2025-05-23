from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

class ChatMessage(BaseModel):
    """A message in a chat conversation"""
    role: str = Field(..., description="The role of the message sender (user or assistant)")
    content: str = Field(..., description="The content of the message")

class ChatRequest(BaseModel):
    """Request body for chat endpoint"""
    message: str = Field(..., description="The message to send to the chat agent")
    message_history: Optional[List[ChatMessage]] = Field(
        default=None, 
        description="Previous messages in the conversation, if any"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="ID for the conversation session to maintain state between requests"
    )

class ChatResponse(BaseModel):
    """Response from chat endpoint (non-streaming)"""
    response: str = Field(..., description="The response from the assistant")
    task_id: str = Field(..., description="The ID of the task the chat is about") 