import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from src.model.user_interaction import UserInteraction
from pydantic import BaseModel, Field
import json

class TaskState(Enum):
    NEW = "1. New"
    CONTEXT_GATHERING = "2. Context Gathering"
    CONTEXT_GATHERED = "3. Context Gathered"
    TASK_FORMATION = "3.5. Task Formation"
    ANALYSIS = "4. Analysis"
    TYPIFY = "5. Typify"
    CLARIFYING = "6. Clarifying"
    CLARIFICATION_COMPLETE = "7. Clarification Complete"    
    APPROACH_FORMATION = "8. Approach Formation"
    METHOD_SELECTION = "9. Method Selection"
    DECOMPOSITION = "10. Decomposition"
    METHOD_APPLICATION = "11. Method Application"
    SOLUTION_DEVELOPMENT = "12. Solution Development"
    EVALUATION = "13. Evaluation"
    INTEGRATION = "14. Integration"
    OUTPUT_GENERATION = "15. Output Generation"
    COMPLETED = "16. Completed"


class Task(BaseModel):
    # core fields
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sub_level: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    # task fields
    task: Optional[str] = None
    short_description: Optional[str] = ''
    state: TaskState = Field(default=TaskState.NEW)
    is_context_sufficient: bool = False
    context: Optional[str] = None
    complexity: Optional[int] = None
    contribution_to_parent_task: Optional[str] = None
    # analysis fields
    user_interaction: List[UserInteraction] = Field(default_factory=list)
    analysis: Dict = Field(default_factory=dict)
    typification: Dict = Field(default_factory=dict)
    clarification_data: Dict = Field(default_factory=dict)
    approaches: Dict = Field(default_factory=dict)
    # decomposition fields
    sub_tasks: List[str] = Field(default_factory=list)
    parent_task: Optional[str] = None
    
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
            approaches={},
        )

    def add_user_interaction(self, user_interaction: UserInteraction):
        self.user_interaction.append(user_interaction)

    @property
    def formatted_user_interaction(self) -> str:
            return "\n".join([f"Q: {user_interaction.query}\nA: {user_interaction.answer}" for user_interaction in self.user_interaction])

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
            TaskState.NEW: [TaskState.CONTEXT_GATHERING],
            TaskState.CONTEXT_GATHERING: [TaskState.CONTEXT_GATHERED],
            TaskState.CONTEXT_GATHERED: [TaskState.TASK_FORMATION],
            TaskState.TASK_FORMATION: [TaskState.ANALYSIS],  # Changed this
            TaskState.ANALYSIS: [TaskState.TYPIFY],
            TaskState.TYPIFY: [TaskState.CLARIFYING],
            TaskState.CLARIFYING: [TaskState.CLARIFICATION_COMPLETE],
            TaskState.CLARIFICATION_COMPLETE: [TaskState.APPROACH_FORMATION],
            TaskState.APPROACH_FORMATION: [TaskState.METHOD_SELECTION],
            TaskState.METHOD_SELECTION: [TaskState.DECOMPOSITION],
            TaskState.DECOMPOSITION: [TaskState.METHOD_APPLICATION, TaskState.METHOD_SELECTION, TaskState.APPROACH_FORMATION],
            TaskState.METHOD_APPLICATION: [TaskState.SOLUTION_DEVELOPMENT],
            TaskState.SOLUTION_DEVELOPMENT: [TaskState.EVALUATION],
            TaskState.EVALUATION: [TaskState.INTEGRATION],
            TaskState.INTEGRATION: [TaskState.OUTPUT_GENERATION],
            TaskState.OUTPUT_GENERATION: [TaskState.COMPLETED],
            TaskState.COMPLETED: []
        }
        return new_state in valid_transitions.get(self.state, [])

    def to_dict(self) -> dict:
        return json.loads(self.model_dump_json(by_alias=True))
