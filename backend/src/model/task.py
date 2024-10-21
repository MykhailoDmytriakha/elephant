import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict
from src.model.user_interaction import UserInteraction
from pydantic import BaseModel, Field
import json

class TaskState(Enum):
    NEW = "1.1. new"
    CONTEXT = "1.2. context"
    ANALYSIS = "2.1. analysis"
    ANALYZED = "2.2. analyzed"
    DECOMPOSED = "3. decomposed"
    CONCEPTS = "4. concept"
    METHOD_SELECTION = "method_selection"
    METHOD_APPLICATION = "method_application"
    SOLUTION = "solution"
    EVALUATION = "evaluation"
    INTEGRATION = "integration"
    OUTPUT = "output"


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sub_level: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    state: TaskState = Field(default=TaskState.NEW)
    context: Optional[str] = None
    is_context_sufficient: bool = False
    task: Optional[str] = None
    short_description: Optional[str] = ''
    user_interaction: List[UserInteraction] = Field(default_factory=list)
    analysis: Dict = Field(default_factory=dict)
    concepts: Dict = Field(default_factory=dict)
    sub_tasks: List['Task'] = Field(default_factory=list)
    parent_task: Optional['Task'] = None
    
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
            task=task,
            context=context,
            sub_level=0,
            is_context_sufficient=False,
            short_description='',
            user_interaction=[],
            analysis={},
            concepts={},
        )

    def add_user_interaction(self, user_interaction: UserInteraction):
        self.user_interaction.append(user_interaction)

    @property
    def formatted_user_interaction(self) -> str:
            return "\n".join([f"Q: {user_interaction.query}\nA: {user_interaction.answer}" for user_interaction in self.user_interaction])

    def update_state(self, new_state: TaskState):
        self.state = new_state
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return json.loads(self.json(by_alias=True))
