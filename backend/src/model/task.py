# backend/src/model/task.py
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
import logging # Added for logging

logger = logging.getLogger(__name__) # Added logger

class TaskState(Enum):
    NEW = "1. New"
    CONTEXT_GATHERING = "2. Context Gathering"
    CONTEXT_GATHERED = "3. Context Gathered"
    TASK_FORMATION = "3.5. Task Formation" # Keep this intermediate state if used
    IFR_GENERATED = "4. IFR Generated"
    REQUIREMENTS_GENERATED = "5. Requirements Defined"
    NETWORK_PLAN_GENERATED = "6. Network (Stages) Plan Generated"
    HIERARCHICAL_DECOMPOSITION_COMPLETE = "7. Hierarchical Decomposition Complete" # Added decomposition state
    COMPLETED = "8. Completed" # Added completed state


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
        # If state is a string, convert it to the appropriate TaskState enum
        if 'state' in data and isinstance(data['state'], str):
            # Try to find the enum by its value
            for state_enum in TaskState:
                if state_enum.value == data['state']:
                    data['state'] = state_enum
                    break
            # If no match found, try to use the string directly as an enum name
            if isinstance(data['state'], str):
                try:
                    data['state'] = TaskState[data['state']]
                except KeyError:
                    # If conversion fails, set to default NEW state
                    data['state'] = TaskState.NEW
        
        super().__init__(**data)
        # Ensure defaults are set if not provided, handled by Field default_factory mostly
        if not self.updated_at:
            self.updated_at = self.created_at or datetime.now().isoformat()
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
            short_description=task, # Initialize short_description with task query
            scope=TaskScope(), # Initialize scope object
            ifr=None,
            requirements=None,
            network_plan=None,
            context_answers=[]
        )

    def add_context_answers(self, context_answers: UserAnswers):
        for answer in context_answers.answers:
            # Avoid adding duplicate questions if needed (simple check by question text)
            # if not any(existing.question == answer.question for existing in self.context_answers):
            self.context_answers.append(answer)
        self.updated_at = datetime.now().isoformat() # Update timestamp

    def update_state(self, new_state: TaskState):
        # Always allow setting state, log invalid transitions as warnings
        # Logic for strict validation can be added back if required by business rules
        # if self._is_valid_state_transition(new_state):
        if self.state != new_state:
            logger.info(f"Task {self.id}: State changing from {self.state} to {new_state}")
            self.state = new_state
            self.updated_at = datetime.now().isoformat()


    def to_dict(self) -> dict:
        # Ensure enums are represented by their values in the dictionary
        dump = self.model_dump(mode='json')
        # Check if state is already a string or an enum with a value attribute
        if hasattr(self.state, 'value'):
            dump['state'] = self.state.value  # Explicitly set state value for enum
        else:
            dump['state'] = self.state  # State is already a string
        return dump

# Ensure the model is rebuilt if other models were updated
Task.model_rebuild()