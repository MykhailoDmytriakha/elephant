"""
Task Scope Routes Module

Handles all API endpoints related to task scope formulation and validation.
Includes scope questions, answers submission, draft generation, and validation.
"""

from fastapi import APIRouter, Depends
from typing import List
import logging

# Model imports
from src.model.task import Task, TaskState
from src.model.context import UserAnswers
from src.model.scope import TaskScope, DraftScope, ValidationScopeResult, ScopeValidationRequest, ScopeFormulationGroup

# Service imports
from src.services.problem_analyzer import ProblemAnalyzer
from src.services.database_service import DatabaseService

# API utils imports
from src.api.deps import get_problem_analyzer, get_db_service
from src.api.utils import api_error_handler, deserialize_task
from src.api.validators import TaskValidator

# Exception imports
from src.exceptions import InvalidStateException, ValidationException

# Constants
from src.constants import OP_FORMULATE_TASK, OP_SCOPE_VALIDATION

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{task_id}/formulate/{group}", response_model=List[ScopeFormulationGroup])
@api_error_handler(OP_FORMULATE_TASK)
async def get_scope_questions(
    task_id: str,
    group: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
) -> List[ScopeFormulationGroup]:
    """
    Get scope formulation questions for a specific group (What, Why, Who, Where, When, How).
    
    Args:
        task_id: Unique identifier of the task
        group: Scope group to get questions for
        analyzer: Problem analyzer service
        db: Database service
        
    Returns:
        List of scope formulation groups with questions
        
    Raises:
        InvalidStateException: If task is not in valid state for scope formulation
        ValidationException: If group already exists in task scope
        TaskNotFoundException: If task does not exist
    """
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    # Validate task state
    if not TaskValidator.is_task_in_states(task, [TaskState.CONTEXT_GATHERED, TaskState.TASK_FORMATION]):
        error_message = f"Task must be in CONTEXT_GATHERED or TASK_FORMATION state. Current state: {task.state}"
        logger.error(error_message)
        raise InvalidStateException(error_message)
    
    # Check if group already exists
    if task.scope and hasattr(task.scope, group):
        existing_group = getattr(task.scope, group)
        if existing_group:
            logger.info(f"Group {group} found in task scope")
            raise ValidationException(f"Group {group} already exists in task scope")
    
    result = await analyzer.define_scope_question(task, group)
    return result


@router.post("/{task_id}/formulate/{group}", response_model=dict)
@api_error_handler(OP_FORMULATE_TASK)
async def submit_scope_answers(
    task_id: str,
    group: str,
    answers: UserAnswers,
    db: DatabaseService = Depends(get_db_service)
) -> dict:
    """
    Submit scope formulation answers for a specific group.
    
    Args:
        task_id: Unique identifier of the task
        group: Scope group to submit answers for
        answers: User answers to scope questions
        db: Database service
        
    Returns:
        Confirmation message
        
    Raises:
        InvalidStateException: If task is not in valid state for scope formulation
        TaskNotFoundException: If task does not exist
    """
    logger.info(f"Submitting formulation answers for task {task_id} and group {group}")
    logger.info(f"Answers: {answers.json()}")
    
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    # Validate task state
    if not TaskValidator.is_task_in_states(task, [TaskState.CONTEXT_GATHERED, TaskState.TASK_FORMATION]):
        error_message = f"Task must be in CONTEXT_GATHERED or TASK_FORMATION state. Current state: {task.state}"
        logger.error(error_message)
        raise InvalidStateException(error_message)
    
    # Initialize scope if it doesn't exist
    if not task.scope:
        task.scope = TaskScope()
    
    # Set the answers directly to the appropriate group
    setattr(task.scope, group, answers.answers)
    
    # Update task state to indicate formulation is in progress
    task.state = TaskState.TASK_FORMATION
    
    # Save the updated task
    db.updated_task(task)
    
    return {"message": f"Formulation answers for group '{group}' saved successfully"}


@router.get("/{task_id}/draft-scope", response_model=DraftScope)
@api_error_handler(OP_SCOPE_VALIDATION)
async def get_draft_scope(
    task_id: str, 
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer), 
    db: DatabaseService = Depends(get_db_service)
) -> DraftScope:
    """
    Generate a draft scope based on all submitted scope formulation answers.
    
    Args:
        task_id: Unique identifier of the task
        analyzer: Problem analyzer service
        db: Database service
        
    Returns:
        Draft scope with generated content
        
    Raises:
        TaskNotFoundException: If task does not exist
    """
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    # Generate draft scope using the problem analyzer
    draft_scope = await analyzer.generate_draft_scope(task)
    
    logger.info(f"Draft scope generated for task {task_id}")
    return draft_scope


@router.post("/{task_id}/validate-scope", response_model=ValidationScopeResult)
@api_error_handler(OP_SCOPE_VALIDATION)
async def validate_scope(
    task_id: str,
    request: ScopeValidationRequest,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
) -> ValidationScopeResult:
    """
    Validate and finalize the task scope based on user approval or feedback.
    
    Args:
        task_id: Unique identifier of the task
        request: Validation request with approval status and optional feedback
        analyzer: Problem analyzer service
        db: Database service
        
    Returns:
        Validation result with final scope or revision requirements
        
    Raises:
        TaskNotFoundException: If task does not exist
    """
    logger.info(f"Validating scope for task {task_id}")
    logger.info(f"Approved: {request.isApproved}, Feedback: {request.feedback}")
    
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    # Validate scope using the problem analyzer
    result = await analyzer.validate_scope(task, request.isApproved, request.feedback)
    
    # Update task state if scope is approved
    if request.isApproved:
        task.state = TaskState.CONTEXT_GATHERED  # Move to next stage
        db.updated_task(task)
        logger.info(f"Scope approved and task state updated for {task_id}")
    
    return result 