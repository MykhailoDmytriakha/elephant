import uuid
from datetime import datetime
from enum import Enum
from typing import List, Tuple

class TaskState(Enum):
    NEW = "1. new"
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
    def __init__(self, origin_query: str, context: str = None):
        self.uuid = str(uuid.uuid4())
        self.sub_level = 0
        self.id = self.uuid + "---" + str(self.sub_level)
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.state = TaskState.NEW
        self.origin_query = origin_query
        self.context: List[Tuple[str, str]] = []
        self.analysis = {}
        
    def add_context(self, question: str, answer: str):
        self.context.append((question, answer))
        
    @property
    def formatted_context(self) -> str:
        return "\n".join([f"Q: {q}\nA: {a}" for q, a in self.context])

    def update_state(self, new_state: str):
        self.state = new_state
        self.updated_at = datetime.now().isoformat()
