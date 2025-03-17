from src.model.context import UserAnswer
from pydantic import BaseModel
from typing import List, Optional

class ValidationScopeResult(BaseModel):
        updatedScope: str
        changes: List[str]

class ValidationCriteria(BaseModel):
        question: str
        answer: str
    
class DraftScope(BaseModel):
    validation_criteria: List[ValidationCriteria]
    scope: str

    
class ScopeQuestion(BaseModel):
    question: str
    options: List[str]
    
class ScopeFormulationGroup(ScopeQuestion):
    group: str

class TaskScope(BaseModel):
    what: Optional[List[UserAnswer]] = None
    why: Optional[List[UserAnswer]] = None
    who: Optional[List[UserAnswer]] = None
    where: Optional[List[UserAnswer]] = None
    when: Optional[List[UserAnswer]] = None
    how: Optional[List[UserAnswer]] = None
    validation_criteria: Optional[List[ValidationCriteria]] = None
    scope: Optional[str] = None
    status: Optional[str] = None
    feedback: Optional[List[str]] = None