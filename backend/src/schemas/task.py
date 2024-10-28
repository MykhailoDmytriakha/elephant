from typing import List, Optional, Dict, Union

from pydantic import BaseModel, Field
from src.model.task import Task
        
class Typification(BaseModel):
    typification: Dict = Field({}, description="Typification results for the task")

class AnalysisResult(BaseModel):
    analysis: Dict = Field({}, description="Analysis results for the task")


class DecompositionResult(BaseModel):
    sub_tasks: List[Task] = Field(..., description="List of sub-tasks derived from the main task")

class MethodSelectionResult(BaseModel):
    method: str = Field(..., description="Selected method for the task")

Task.model_rebuild()
