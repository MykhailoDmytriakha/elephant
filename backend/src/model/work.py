from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Any
from enum import Enum
import uuid
from datetime import datetime
from src.model.executable_task import ExecutableTask
from src.model.artifact import Artifact
from src.model.status import StatusEnum

class Work(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the work package.")
    name: str = Field(..., description="Concise name summarizing the work (min 5 chars)")
    description: str = Field(..., description="Detailed description of the work package's objective and scope within the stage (min 20 chars)")
    stage_id: str = Field(..., description="Identifier of the parent Stage")
    sequence_order: int = Field(..., description="Intended execution order within the stage (0-based index)")
    dependencies: List[str] = Field(default_factory=list, description="List of Work IDs (within the same stage) that must be completed first")
    required_inputs: List[Artifact] = Field(default_factory=list, description="Specific artifacts needed to start this work")
    expected_outcome: str = Field(..., description="Description of the state or capability achieved upon completion (min 10 chars)")
    generated_artifacts: List[Artifact] = Field(default_factory=list, description="Tangible artifacts produced by this work")
    validation_criteria: List[str] = Field(default_factory=list, description="At least one automatable criterion to verify successful completion")
    tasks: Optional[List[ExecutableTask]] = Field(default_factory=lambda: [], description="List of executable tasks decomposing this work package")
    # Status tracking fields
    status: Optional[StatusEnum] = Field(None, description="Status of the work execution")
    result: Optional[str] = Field(None, description="Result of the work execution as a string")
    error_message: Optional[str] = Field(default=None, description="Error message if execution failed")
    started_at: Optional[str] = Field(None, description="Timestamp when execution started (ISO format)")
    completed_at: Optional[str] = Field(None, description="Timestamp when execution completed (ISO format)")

class WorkList(BaseModel):
    work_packages: List[Work]