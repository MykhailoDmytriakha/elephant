from typing import TypedDict, List
from pydantic import BaseModel


class ContextQuestion(BaseModel):
    question: str
    options: List[str]
    
class ContextSufficiencyResult(BaseModel):
    is_context_sufficient: bool
    questions: List[ContextQuestion]
    

class UserAnswer(BaseModel):
    question: str
    answer: str
    

class UserAnswers(BaseModel):
    answers: List[UserAnswer]
    
class ClarifiedTask(BaseModel):
    task: str
    context: str