"""
Task Context Routes Module

Handles all API endpoints related to task context gathering and management.
Separated from main tasks_routes for better modularity and maintainability.
"""

from fastapi import APIRouter, Depends
from typing import Optional, List
import logging
from pydantic import BaseModel

# Model imports
from src.model.task import Task, TaskState
from src.model.context import ContextSufficiencyResult, UserAnswers

# Service imports
from src.services.problem_analyzer import ProblemAnalyzer

# API utils imports
from src.api.deps import get_problem_analyzer, get_file_storage_service
from src.api.utils import api_error_handler, deserialize_task
from src.api.validators import TaskValidator

# Exception imports
from src.exceptions import InvalidStateException

# Constants
from src.constants import OP_UPDATE_TASK

logger = logging.getLogger(__name__)

router = APIRouter()


class EditContextRequest(BaseModel):
    """Request model for editing context summary"""
    feedback: str


@router.post("/{task_id}/context-questions", response_model=ContextSufficiencyResult)
@api_error_handler(OP_UPDATE_TASK)
async def update_task_context(
    task_id: str,
    context_answers: Optional[UserAnswers] = None,
    force: bool = False,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    storage: FileStorageService = Depends(get_file_storage_service)
) -> ContextSufficiencyResult:
    """
    Update task context with answers or get context clarification questions.
    
    Args:
        task_id: Unique identifier of the task
        context_answers: Optional user answers to context questions
        force: Force context gathering even if already gathered
        analyzer: Problem analyzer service
        db: Database service
        
    Returns:
        Context sufficiency result with questions or confirmation
        
    Raises:
        InvalidStateException: If task is in invalid state for context updates
        TaskNotFoundException: If task does not exist
    """
    task = storage.load_task(task_id)
    if not task:
        raise TaskNotFoundException(f"Task {task_id} not found")
    
    # Only check state if force is False
    if not force and TaskValidator.is_task_in_states(task, [TaskState.CONTEXT_GATHERED]):
        error_message = f"Task is already in the context gathered state. Current state: {task.state}"
        logger.error(error_message)
        raise InvalidStateException(error_message)
    
    task.state = TaskState.CONTEXT_GATHERING
    
    # Handle the case where no context answers are provided
    if not context_answers:
        logger.info(f"No context answers provided. Clarifying context. Force mode: {force}")
        result = await analyzer.clarify_context(task, force)
        logger.info(f"Context sufficiency result: {result}")
        return result
    else:
        logger.info(f"User context answers provided: {context_answers}")
        task.add_context_answers(context_answers)
        storage.save_task(task_id, task)
        return await analyzer.clarify_context(task)


@router.post("/{task_id}/edit-context", response_model=Task)
@api_error_handler(OP_UPDATE_TASK)
async def edit_context_summary(
    task_id: str,
    request: EditContextRequest,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    storage: FileStorageService = Depends(get_file_storage_service)
) -> Task:
    """
    Edit the context summary of a task based on user feedback.
    
    Args:
        task_id: Unique identifier of the task
        request: Request containing feedback for context editing
        analyzer: Problem analyzer service
        db: Database service
        
    Returns:
        Updated task with modified context
        
    Raises:
        TaskNotFoundException: If task does not exist
    """
    logger.info(f"Editing context summary for task {task_id}")
    logger.info(f"Feedback: {request.feedback}")
    
    task = storage.load_task(task_id)
    if not task:
        raise TaskNotFoundException(f"Task {task_id} not found")

    # Edit the context using the problem analyzer
    updated_task = await analyzer.edit_context_summary(task, request.feedback)

    # Save the updated task
    storage.save_task(task_id, updated_task)
    
    logger.info(f"Context summary updated for task {task_id}")
    return updated_task 