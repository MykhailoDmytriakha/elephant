# src/model/subtask.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal, Union
import uuid
from datetime import datetime
from src.model.status import StatusEnum

class Subtask(BaseModel):
    id: str = Field(default_factory=lambda: f"ST-{uuid.uuid4()}", description="Unique identifier for the subtask")
    name: str = Field(..., description="Concise name for the atomic action (e.g., 'Set Motor Angle', 'Call API Endpoint')")
    description: str = Field(..., description="Detailed instruction for this specific subtask.")
    # Parent references
    parent_executable_task_id: str = Field(..., description="ID of the parent ExecutableTask")
    parent_work_id: str = Field(..., description="ID of the parent Work package")
    parent_stage_id: str = Field(..., description="ID of the parent Stage")
    parent_task_id: str = Field(..., description="ID of the top-level Task") # Renamed from top_level_task_id for clarity
    # Execution details
    sequence_order: int = Field(..., description="Execution order within the parent ExecutableTask (0-based index)")
    executor_type: Literal["AI_AGENT", "ROBOT", "HUMAN"] = Field(..., description="Specifies the type of executor needed for this subtask")
    # Status tracking fields
    status: Optional[StatusEnum] = Field(None, description="Status of the subtask execution")
    result: Optional[str] = Field(None, description="Result of the subtask execution as a string")
    error_message: Optional[str] = Field(default=None, description="Error message if execution failed")
    started_at: Optional[str] = Field(None, description="Timestamp when execution started (ISO format)")
    completed_at: Optional[str] = Field(None, description="Timestamp when execution completed (ISO format)")
    

class SubtaskList(BaseModel):
    subtasks: List[Subtask]