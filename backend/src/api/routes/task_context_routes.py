"""
Task Context Routes Module

Handles all API endpoints related to task context gathering and management.
Separated from main tasks_routes for better modularity and maintainability.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List
import logging
from pydantic import BaseModel

# Model imports
from src.model.task import Task, TaskState
from src.model.context import ContextSufficiencyResult, UserAnswers

# Service imports
from src.services.problem_analyzer import ProblemAnalyzer
from src.services.file_storage_service import FileStorageService

# API utils imports
from src.api.deps import get_problem_analyzer, get_file_storage_service
from src.api.utils import api_error_handler, deserialize_task
from src.api.validators import TaskValidator

# Exception imports
from src.exceptions import InvalidStateException, TaskNotFoundException

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

    logger.info(f"=== CONTEXT QUESTIONS DEBUG ===")
    logger.info(f"Task ID: {task_id}")
    logger.info(f"Force mode: {force}")
    logger.info(f"Context answers provided: {bool(context_answers)}")
    logger.info(f"Task current state: {task.state}")
    logger.info(f"Task context_answers before: {len(task.context_answers) if task.context_answers else 0} items")

    # Only check state if force is False
    if not force and TaskValidator.is_task_in_states(task, [TaskState.CONTEXT_GATHERED]):
        error_message = f"Task is already in the context gathered state. Current state: {task.state}"
        logger.error(error_message)
        raise InvalidStateException(error_message)

    # Set state to CONTEXT_GATHERING only if we're providing answers or forcing
    # Don't reset state if we're just checking sufficiency without answers
    if context_answers or force:
        task.state = TaskState.CONTEXT_GATHERING

    # Handle the case where no context answers are provided
    if not context_answers:
        # Check for existing pending questions
        pending = task.get_pending_questions()
        logger.info(f"Task has {len(task.context_answers)} total context answers, {len(pending)} pending questions")
        logger.info(f"Pending questions details: {[q.question for q in pending]}")
        if pending and not force:
            logger.info(f"Returning {len(pending)} existing pending questions")
            return ContextSufficiencyResult(is_context_sufficient=False, questions=pending)

        # Generate new questions
        logger.info(f"Generating new questions. Force mode: {force}")
        result = await analyzer.clarify_context(task, force)
        logger.info(f"Context sufficiency result: is_context_sufficient={result.is_context_sufficient}, questions_count={len(result.questions) if result.questions else 0}")

        # Debug: check the result structure
        logger.info(f"Result questions type: {type(result.questions)}")
        if result.questions:
            logger.info(f"First question: {result.questions[0] if result.questions else 'None'}")
            logger.info(f"All questions: {[q.question for q in result.questions]}")

        # Save questions as pending
        logger.info(f"Checking condition: not {result.is_context_sufficient} and {bool(result.questions)} = {not result.is_context_sufficient and bool(result.questions)}")
        if not result.is_context_sufficient and result.questions:
            logger.info(f"Adding {len(result.questions)} pending questions to task")
            task.add_pending_questions(result.questions)
            logger.info(f"Task now has {len(task.context_answers)} context answers total")
            logger.info(f"Context answers after adding: {[{'question': ca.question, 'answer': ca.answer, 'options': len(ca.options) if ca.options else 0} for ca in task.context_answers]}")
            storage.save_task(task_id, task)
            logger.info(f"Task saved with pending questions")

        return result
    else:
        # Update answers for pending questions
        logger.info(f"User context answers provided: {context_answers}")
        task.update_answers(context_answers)

        # Save answers immediately to prevent data loss
        logger.info("Saving task with updated answers before generating new questions")
        storage.save_task(task_id, task)

        # Increment iteration count for adaptation
        task.context_iteration_count += 1
        logger.info(f"Context iteration {task.context_iteration_count} for task {task_id}")

        # Get next result
        result = await analyzer.clarify_context(task)
        logger.info(f"Next context sufficiency result: {result}")

        # Always save task after clarify_context as it may have changed state or context
        storage.save_task(task_id, task)

        # Save new pending questions if any (additional save if needed)
        if not result.is_context_sufficient and result.questions:
            task.add_pending_questions(result.questions)
            # Save again with new questions
            storage.save_task(task_id, task)

        return result


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


@router.delete("/{task_id}/context-answers/{answer_index}", response_model=Task)
@api_error_handler(OP_UPDATE_TASK)
async def delete_context_answer(
    task_id: str,
    answer_index: int,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    storage: FileStorageService = Depends(get_file_storage_service)
) -> Task:
    """
    Delete a specific context answer by index.

    Args:
        task_id: Unique identifier of the task
        answer_index: Index of the context answer to delete
        analyzer: Problem analyzer service
        storage: File storage service

    Returns:
        Updated task after removing the context answer

    Raises:
        TaskNotFoundException: If task does not exist
    """
    logger.info(f"Deleting context answer at index {answer_index} for task {task_id}")

    task = storage.load_task(task_id)
    if not task:
        raise TaskNotFoundException(f"Task {task_id} not found")

    # Remove the context answer
    if not task.remove_context_answer(answer_index):
        error_message = f"Invalid answer index {answer_index}. Task has {len(task.context_answers)} context answers."
        logger.error(error_message)
        raise HTTPException(status_code=400, detail=error_message)

    # Save the updated task
    storage.save_task(task_id, task)

    logger.info(f"Context answer at index {answer_index} deleted for task {task_id}")
    return task


@router.delete("/{task_id}/context-questions", response_model=Task)
@api_error_handler(OP_UPDATE_TASK)
async def delete_context_question(
    task_id: str,
    question: str,
    storage: FileStorageService = Depends(get_file_storage_service)
) -> Task:
    """
    Delete a specific context question by question text.

    Args:
        task_id: Unique identifier of the task
        question: Question text to delete (from query parameter)
        storage: File storage service

    Returns:
        Updated task after removing the context question

    Raises:
        TaskNotFoundException: If task does not exist
        HTTPException: If question not found or already answered
    """
    task = storage.load_task(task_id)
    if not task:
        raise TaskNotFoundException(f"Task {task_id} not found")

    # Find and remove the unanswered question
    question_found = False
    for i, answer in enumerate(task.context_answers):
        if answer.question == question and answer.answer.strip() == "":
            # Only allow deleting unanswered questions
            task.context_answers.pop(i)
            question_found = True
            break

    if not question_found:
        error_message = f"Question '{question}' not found or already answered"
        logger.error(error_message)
        raise HTTPException(status_code=400, detail=error_message)

    # Save the updated task
    storage.save_task(task_id, task)

    logger.info(f"Context question '{question}' deleted for task {task_id}")
    return task