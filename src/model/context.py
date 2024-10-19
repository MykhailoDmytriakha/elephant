from typing import TypedDict
from dataclasses import dataclass

@dataclass
class ContextSufficiencyResult(TypedDict):
    is_context_sufficient: bool
    follow_up_question: str