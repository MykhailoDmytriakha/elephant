# src/model/executable_task.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from enum import Enum
import uuid
from src.model.artifact import Artifact
from src.model.subtask import Subtask
class ExecutableTask(BaseModel):
    id: str = Field(default_factory=lambda: f"ET-{uuid.uuid4()}", description="Unique identifier for the executable task")
    name: str = Field(..., description="Concise name for the executable task (e.g., 'Call Analysis API', 'Move Gripper to Position X')")
    description: str = Field(..., description="Detailed description of the specific action to be performed.")
    work_id: str = Field(..., description="ID of the parent Work package")
    stage_id: str = Field(..., description="ID of the parent Stage")
    task_id: str = Field(..., description="ID of the top-level Task") # Added for easier querying/context
    sequence_order: int = Field(..., description="Execution order within the parent Work package (0-based index)")
    dependencies: List[str] = Field(default_factory=lambda: [], description="List of ExecutableTask IDs (within the same Work package) that must be completed first")
    required_inputs: List[Artifact] = Field(default_factory=lambda: [], description="Specific artifacts needed to start this executable task")
    # Make generated_artifacts optional
    generated_artifacts: Optional[List[Artifact]] = Field(default_factory=lambda: [], description="Specific artifacts produced by completing this executable task (if any)")
    validation_criteria: List[str] = Field(default_factory=lambda: [], description="Specific, automatable criteria to verify successful completion of *this* task. Min 1 item.")
    subtasks: Optional[List[Subtask]] = Field(default_factory=list, description="List of atomic subtasks decomposing this executable task")

class ExecutableTaskList(BaseModel):
    tasks: List[ExecutableTask]