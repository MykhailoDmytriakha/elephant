from .database_service import DatabaseService
from src.services.openai_service import OpenAIService
from src.model.context import ContextSufficiencyResult
from src.model.task import Task, TaskState
from src.model.scope import ScopeFormulationGroup, ScopeQuestion, DraftScope, ValidationScopeResult
from src.model.ifr import IFR
import logging
from typing import List
logger = logging.getLogger(__name__)

class ProblemAnalyzer:

    def __init__(self, openai_service: OpenAIService, db_service: DatabaseService):
        self.openai_service = openai_service
        self.db_service = db_service

    async def clarify_context(self, task: Task, force: bool = False) -> ContextSufficiencyResult:
        """Initial context gathering method"""
        
        if task.is_context_sufficient and not force:
            logger.info(f"Task is already in the context gathered state. Current state: {task.state}")
            task.update_state(TaskState.CONTEXT_GATHERED)
            return ContextSufficiencyResult(
                is_context_sufficient=True,
                questions=[]
            )
        
        if not force:
            task.update_state(TaskState.CONTEXT_GATHERING)
            result = await self.openai_service.is_context_sufficient(task)

            if not result.is_context_sufficient:
                return result
        else:
            result = ContextSufficiencyResult(is_context_sufficient=True, questions=[])
        
        # If context is sufficient
        task.is_context_sufficient = True
        

        clarified_task = await self.openai_service.summarize_context(task)
        task.context = clarified_task.context
        task.task = clarified_task.task
        
        task.update_state(TaskState.CONTEXT_GATHERED)
        self.db_service.updated_task(task)
        
        # After context is gathered, process it to formulate the task
        return result

    async def define_scope_question(self, task: Task, group: str) -> List[ScopeFormulationGroup]:
        # define scope based on gathered context
        # Use OpenAI service to get suggestions based on the context
        result_ai: List[ScopeQuestion] = await self.openai_service.formulate_scope_questions(task, group)
        
        # Convert questions to ScopeFormulationGroup using list comprehension
        result = [ScopeFormulationGroup(**question.__dict__, group=group) for question in result_ai]
        return result
    
    async def generate_draft_scope(self, task: Task) -> DraftScope:
        draft_scope = await self.openai_service.generate_draft_scope(task)
        return draft_scope
    
    async def validate_scope(self, task: Task, feedback: str) -> ValidationScopeResult:
        validation_result = await self.openai_service.validate_scope(task, feedback)
        return validation_result

    async def generate_IFR(self, task: Task) -> IFR:
        ifr = await self.openai_service.generate_IFR(task)
        return ifr