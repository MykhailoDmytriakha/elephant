import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict
from src.model.context import UserAnswers, UserAnswer
from src.model.scope import TaskScope
from src.model.ifr import IFR, Requirements
from src.model.planning import NetworkPlan
from pydantic import BaseModel, Field   
import json

class TaskState(Enum):
    NEW = "1. New"
    CONTEXT_GATHERING = "2. Context Gathering"
    CONTEXT_GATHERED = "3. Context Gathered"
    TASK_FORMATION = "3.5. Task Formation"
    IFR_GENERATED = "4. IFR Generated"
    REQUIREMENTS_GENERATED = "5. Requirements Defined"
    NETWORK_PLAN_GENERATED = "6. Network (Stages) Plan Generated"


class Task(BaseModel):
    # core fields
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sub_level: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    level: Optional[str] = None
    complexity: Optional[int] = None
    eta_to_complete: Optional[str] = None
    contribution_to_parent_task: Optional[str] = None
    # task fields
    task: Optional[str] = None
    short_description: Optional[str] = ''
    state: TaskState = Field(default=TaskState.NEW)
    is_context_sufficient: bool = False
    context_answers: List[UserAnswer] = Field(default_factory=list)
    context: Optional[str] = None
    scope: Optional[TaskScope] = None
    ifr: Optional[IFR] = None
    requirements: Optional[Requirements] = None
    network_plan: Optional[NetworkPlan] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if not self.state:
            self.state = TaskState.NEW
        
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        
    @classmethod
    def create_new(cls, task: str = '', context: str = ''):
        return cls(
            state=TaskState.NEW,
            task=task,
            context=context,
            sub_level=0,
            is_context_sufficient=False,
            short_description='',
            analysis={},
            approaches={},
        )
        
    def add_context_answers(self, context_answers: UserAnswers):
        for answer in context_answers.answers:
            self.context_answers.append(answer)

    def update_state(self, new_state: TaskState):
        if self._is_valid_state_transition(new_state):
            self.state = new_state
            self.updated_at = datetime.now().isoformat()
        else:
            raise ValueError(f"Invalid state transition from {self.state} to {new_state}")

    def _is_valid_state_transition(self, new_state: TaskState) -> bool:
        # Allow transition to the same state
        if self.state == new_state:
            return True

        # Define valid state transitions
        valid_transitions = {
            TaskState.NEW: [TaskState.CONTEXT_GATHERING, TaskState.CONTEXT_GATHERED],
            TaskState.CONTEXT_GATHERING: [TaskState.CONTEXT_GATHERED],
            TaskState.CONTEXT_GATHERED: [TaskState.IFR_GENERATED],
            TaskState.IFR_GENERATED: [TaskState.REQUIREMENTS_GENERATED],
            TaskState.REQUIREMENTS_GENERATED: [TaskState.NETWORK_PLAN_GENERATED],
            TaskState.NETWORK_PLAN_GENERATED: [TaskState.COMPLETED],
            TaskState.COMPLETED: []
        }
        return new_state in valid_transitions.get(self.state, [])

    def to_dict(self) -> dict:
        return json.loads(self.model_dump_json(by_alias=True))
