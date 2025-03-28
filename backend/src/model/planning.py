from pydantic import BaseModel, Field
from typing import List, Optional
from src.model.work import Work
from src.model.artifact import Artifact

class Checkpoint(BaseModel):
    """
    Checkpoint of a stage.
    """
    checkpoint: str = Field(..., description="Checkpoint of the stage")
    description: str = Field(..., description="Description of the checkpoint")
    artifact: Artifact = Field(..., description="Artifact that proves that the result is achieved")
    validations: List[str] = Field(default_factory=list, description="Validations that were performed to proofe that the checkpoint is achieved")

class Stage(BaseModel):
    """
    Stages represent major project milestones and are visualized as nodes in network diagrams.
    """
    id: str = Field(..., description="Number of the stage (e.g. S1, S2, S3, etc.)")
    name: str = Field(..., description="Name of the stage")
    description: str = Field(..., description="Description of the stage")
    result: List[str] = Field(default_factory=list, description="Shaping the result of the stage")
    what_should_be_delivered: List[str] | None = Field(default=None, description="What should be delivered after the stage is completed")
    checkpoints: List[Checkpoint] = Field(default_factory=list)
    work_packages: Optional[List[Work]] = Field(default_factory=list, description="List of work packages decomposing this stage")

class Connection(BaseModel):
    """
    A connection between two stages.
    """
    stage1: str = Field(..., description="ID of the first stage")
    stage2: str = Field(..., description="ID of the second stage")

class NetworkPlan(BaseModel):
    """
    This represents the entire project.
    """
    stages: List[Stage] = Field(default_factory=list)
    connections: List[Connection] = Field(default_factory=list)