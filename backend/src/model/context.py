from typing import TypedDict, List
from pydantic import BaseModel


class ContextQuestion(BaseModel):
    question: str
    options: List[str]
    
class ContextSufficiencyResult(BaseModel):
    is_context_sufficient: bool
    questions: List[ContextQuestion]
    

class ContextAnswer(BaseModel):
    question: str
    answer: str
    

class ContextAnswers(BaseModel):
    answers: List[ContextAnswer]
    
class ClarifiedTask(BaseModel):
    task: str
    context: str