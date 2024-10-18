from typing import List, Optional, Dict

from pydantic import BaseModel, Field


class Task(BaseModel):
    id: str = Field(..., description="Unique identifier for the task")
    sub_level: int = Field(0, description="Level in the problem hierarchy (0 for root, 1 for first level, etc.)")
    state: str = Field(..., description="Current state of the task")
    context: Optional[str] = Field(None, description="Additional context for the task")
    task: Optional[str] = Field(None, description="Description of the task")
    short_description: Optional[str] = Field(None, description="Brief description of the task")
    analysis: Dict = Field({}, description="Analysis results for the task")
    concepts: Dict = Field({}, description="Concepts generated for the task")
    sub_tasks: List['Task'] = Field([], description="List of sub-tasks")

    class Config:
        from_attributes = True


class AnalysisResult(BaseModel):
    parameters_constraints: str = Field(..., description="Key parameters and constraints that affect the task")
    available_resources: List[str] = Field(..., description="Details of the resources available for solving the task")
    required_resources: List[str] = Field(..., description="Details of the resources required for solving the task")
    ideal_final_result: str = Field(..., description="The specific goals or results expected from solving the task")
    missing_information: List[str] = Field(..., description="Information that is missing and required to solve the task")
    complexity: str = Field(..., description="Level of complexity of the task (1: simple, 2: low, 3: medium, 4: high, 5: very high)")


class DecompositionResult(BaseModel):
    sub_tasks: List[Task] = Field(..., description="List of sub-tasks derived from the main task")


class ConceptFormationResult(BaseModel):
    contribution_to_parent_task: Optional[str] = Field(None, description="Description of how the concept contributes to solving the parent task")
    ideas: List[str] = Field(..., description="List of ideas generated to solve the problem")
    TOP_TRIZ_principles: List[str] = Field(..., description="TRIZ, ARIZ, TOP-TRIZ principles that should be applied to generate innovative solutions")
    solution_approaches: List[str] = Field(..., description="Different approaches that could potentially solve the problem")
    resources_per_concept: List[Dict[str, str]] = Field(..., description="Analysis of resources required for each potential solution concept")


class TaskCreate(BaseModel):
    context: Optional[str] = Field(None, description="Additional context for the task")
    task: str = Field(..., description="Description of the task")
    short_description: Optional[str] = Field(None, description="Brief description of the task")


class TaskUpdate(BaseModel):
    context: Optional[str] = Field(None, description="Updated context for the task")
    task: Optional[str] = Field(None, description="Updated description of the task")
    short_description: Optional[str] = Field(None, description="Updated brief description of the task")
    state: Optional[str] = Field(None, description="Updated state of the task")


Task.update_forward_refs()
