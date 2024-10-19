import uuid
from datetime import datetime
from enum import Enum
from typing import List, Tuple
from user_interaction import UserInteraction


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


class Task:
    def __init__(self, task: str = '', context: str = ''):
        # metadata
        self.id = str(uuid.uuid4())
        self.sub_level = 0
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.state = TaskState.NEW
        self.sub_tasks: List[Task] = []
        self.parent_task = None
        # core
        self.context = context
        self.is_context_sufficient = False
        self.task = task
        self.short_description = None
        # user interaction
        self.user_interaction: List[UserInteraction] = []
        # problem analysis
        self.analysis = {}
        # concept formation
        self.concepts = {}

    def add_user_interaction(self, user_interaction: UserInteraction):
        self.user_interaction.append(user_interaction)

    @property
    def formatted_user_interaction(self) -> str:
            return "\n".join([f"Q: {user_interaction.query}\nA: {user_interaction.answer}" for user_interaction in self.user_interaction])

    def update_state(self, new_state: TaskState):
        self.state = new_state
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sub_level": self.sub_level,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "state": self.state.value,
            "context": self.context,
            "is_context_sufficient": self.is_context_sufficient,
            "task": self.task,
            "short_description": self.short_description,
            "user_interaction": self.user_interaction,
            "analysis": self.analysis,
            "concepts": self.concepts,
            "sub_tasks": [sub_task.to_dict() for sub_task in self.sub_tasks],
            "parent_task": self.parent_task.id if self.parent_task else None
        }
