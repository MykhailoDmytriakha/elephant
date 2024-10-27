from typing import List, Optional, Dict, Union

from pydantic import BaseModel, Field


class Task(BaseModel):
    id: str = Field(..., description="Unique identifier for the task")
    sub_level: int = Field(0, description="Level in the problem hierarchy (0 for root, 1 for first level, etc.)")
    state: str = Field(..., description="Current state of the task")
    context: Optional[str] = Field(None, description="Additional context for the task")
    task: Optional[str] = Field(None, description="Description of the task")
    short_description: Optional[str] = Field(None, description="Brief description of the task")
    analysis: Dict = Field({}, description="Analysis results for the task")
    typification: Dict = Field({}, description="Typification results for the task")
    concepts: Dict = Field({}, description="Concepts generated for the task")
    sub_tasks: List['Task'] = Field([], description="List of sub-tasks")

    class Config:
        from_attributes = True
        
class Typification(BaseModel):
    typification: Dict = Field({}, description="Typification results for the task")

class ScoreWithReasoning(BaseModel):
    score: Union[int, float]
    reasoning: str

class ApproachEvaluation(BaseModel):
    approach_id: str
    ideality_score: ScoreWithReasoning
    feasibility: ScoreWithReasoning
    resource_efficiency: ScoreWithReasoning

class AnalysisResult(BaseModel):
    analysis: Dict = Field({}, description="Analysis results for the task")


class DecompositionResult(BaseModel):
    sub_tasks: List[Task] = Field(..., description="List of sub-tasks derived from the main task")


class ConceptFormationResult(BaseModel):
    contribution_to_parent_task: Optional[str] = Field(None, description="Description of how the concept contributes to solving the parent task")
    ideas: List[str] = Field(..., description="List of ideas generated to solve the problem")
    TOP_TRIZ_principles: List[str] = Field(..., description="TRIZ, ARIZ, TOP-TRIZ principles that should be applied to generate innovative solutions")
    solution_approaches: List[str] = Field(..., description="Different approaches that could potentially solve the problem")
    resources_per_concept: List[Dict[str, str]] = Field(..., description="Analysis of resources required for each potential solution concept")
    
class AppliedPrinciple(BaseModel):
    principle_name: str
    application_description: str

class Approach(BaseModel):
    approach_id: str
    approach_name: str
    description: str
    contribution_to_parent_task: str
    applied_principles: List[AppliedPrinciple]
    resources: List[str]

class ApproachFormationResult(BaseModel):
    principles: List[str] = Field(..., description="TRIZ, ARIZ, TOP-TRIZ principles that should be applied to generate innovative solutions")
    solution_by_principles: List[str] = Field(..., description="Different solutions that could potentially solve the problem")
    approach_list: List[Approach] = Field(..., description="Different approaches that could potentially solve the problem")
    evaluation_criteria: List[ApproachEvaluation] | None = Field(None, description="Evaluation criteria for the approaches")


class TaskCreate(BaseModel):
    context: Optional[str] = Field(None, description="Additional context for the task")
    task: str = Field(..., description="Description of the task")
    short_description: Optional[str] = Field(None, description="Brief description of the task")


class TaskUpdate(BaseModel):
    context: Optional[str] = Field(None, description="Updated context for the task")
    task: Optional[str] = Field(None, description="Updated description of the task")
    short_description: Optional[str] = Field(None, description="Updated brief description of the task")
    state: Optional[str] = Field(None, description="Updated state of the task")

class MethodSelectionResult(BaseModel):
    method: str = Field(..., description="Selected method for the task")

Task.model_rebuild()
