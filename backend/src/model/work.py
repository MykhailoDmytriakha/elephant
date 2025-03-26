from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum
import uuid

# Reusing Artifact from planning.py - need proper import structure later
# Assuming Artifact is defined elsewhere or define it here temporarily if needed
class Artifact(BaseModel):
    type: str = Field(..., description="Type of the artifact (e.g., document, dataset, code_module, physical_component)")
    name: str = Field(..., description="Name of the artifact")
    description: str = Field(..., description="Description of the artifact")
    location: str = Field(..., description="Standardized location identifier (e.g., S3_BUCKET_RAW_DATA, GIT_REPO_MAIN, ROBOT_STATION_1_BIN_A)")

class Work(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the work package")
    name: str = Field(..., description="Concise name summarizing the work (min 5 chars)")
    description: str = Field(..., description="Detailed description of the work package's objective and scope within the stage (min 20 chars)")
    stage_id: str = Field(..., description="Identifier of the parent Stage")
    sequence_order: int = Field(..., description="Intended execution order within the stage (0-based index)")
    dependencies: List[str] = Field(default_factory=list, description="List of Work IDs (within the same stage) that must be completed first")
    required_inputs: List[Artifact] = Field(default_factory=list, description="Specific artifacts needed to start this work")
    expected_outcome: str = Field(..., description="Description of the state or capability achieved upon completion (min 10 chars)")
    generated_artifacts: List[Artifact] = Field(default_factory=list, description="Tangible artifacts produced by this work")
    validation_criteria: List[str] = Field(default_factory=list, description="At least one automatable criterion to verify successful completion")

class WorkList(BaseModel):
    work_packages: List[Work]