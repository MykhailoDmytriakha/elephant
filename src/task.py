import uuid
from datetime import datetime
from enum import Enum
from typing import List, Tuple

class TaskState(Enum):
    NEW = "1.1. new"
    CONSTEXT = "1.2. context"
    ANALYSIS = "2.1. analysis"
    ANALYZED = "2.2. analyzed"
    CONCEPTS = "concepts"
    METHOD_SELECTION = "method_selection"
    METHOD_APPLICATION = "method_application"
    SOLUTION = "solution"
    EVALUATION = "evaluation"
    INTEGRATION = "integration"
    OUTPUT = "output"

class Task:
    def __init__(self, origin_query: str, task: str = None, context: str = None):
        self.uuid = str(uuid.uuid4())
        self.sub_level = 0
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.state = TaskState.NEW
        self.origin_query = origin_query
        self.task = task
        self.user_interaction: List[Tuple[str, str]] = []
        self.context = context
        self.is_context_sufficient = False
        self.analysis = {}
        self.sub_tasks: List[Task] = []
        self.parent_task = None
        
    def add_user_interaction(self, question: str, answer: str):
        self.user_interaction.append((question, answer))
        
    @property
    def formatted_user_interaction(self) -> str:
        return "\n".join([f"Q: {q}\nA: {a}" for q, a in self.user_interaction])

    def update_state(self, new_state: TaskState):
        self.state = new_state
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "uuid": self.uuid,
            "sub_level": self.sub_level,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "state": self.state.value,
            "origin_query": self.origin_query,
            "task": self.task,
            "user_interaction": self.user_interaction,
            "context": self.context,
            "is_context_sufficient": self.is_context_sufficient,
            "analysis": self.analysis,
            "sub_tasks": [sub_task.to_dict() for sub_task in self.sub_tasks],
            "parent_task": self.parent_task.uuid if self.parent_task else None
        }