"""
Task Execution Routes Module

Handles all API endpoints related to task execution and subtask management.
Includes subtask status updates, completion, failure handling, and status queries.
"""

from fastapi import APIRouter, Depends
from typing import Optional
import logging
from pydantic import BaseModel

# Model imports
from src.model.task import Task
from src.model.subtask import Subtask, SubtaskStatus

# Service imports
from src.services.database_service import DatabaseService

# API utils imports
from src.api.deps import get_db_service
from src.api.utils import api_error_handler, deserialize_task

logger = logging.getLogger(__name__)

router = APIRouter()


class SubtaskStatusUpdateRequest(BaseModel):
    """Request model for updating subtask status"""
    status: str
    result: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@router.put("/{task_id}/subtasks/{subtask_reference}/status")
@api_error_handler("OP_UPDATE_SUBTASK_STATUS")
async def update_subtask_status(
    task_id: str,
    subtask_reference: str,
    request: SubtaskStatusUpdateRequest,
    db: DatabaseService = Depends(get_db_service)
) -> dict:
    """
    Update the status of a specific subtask.
    
    Args:
        task_id: Unique identifier of the task
        subtask_reference: Reference identifier of the subtask
        request: Status update request with new status and optional details
        db: Database service
        
    Returns:
        Confirmation message with updated status
        
    Raises:
        TaskNotFoundException: If task does not exist
        ValueError: If subtask reference is not found
    """
    logger.info(f"Updating subtask {subtask_reference} status for task {task_id}")
    logger.info(f"New status: {request.status}")
    
    # Get task to ensure it exists
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    # Find the subtask by reference
    subtask = _find_subtask_by_reference(task, subtask_reference)
    if not subtask:
        raise ValueError(f"Subtask with reference '{subtask_reference}' not found in task {task_id}")
    
    # Update subtask status
    old_status = subtask.status
    subtask.status = SubtaskStatus(request.status)
    
    # Update optional fields if provided
    if request.result is not None:
        subtask.result = request.result
    if request.error_message is not None:
        subtask.error_message = request.error_message
    if request.started_at is not None:
        subtask.started_at = request.started_at
    if request.completed_at is not None:
        subtask.completed_at = request.completed_at
    
    # Save the updated task
    db.updated_task(task)
    
    logger.info(f"Subtask {subtask_reference} status updated from {old_status} to {request.status}")
    
    return {
        "message": f"Subtask {subtask_reference} status updated successfully",
        "old_status": old_status.value if hasattr(old_status, 'value') else str(old_status),
        "new_status": request.status,
        "task_id": task_id,
        "subtask_reference": subtask_reference
    }


@router.get("/{task_id}/subtasks/{subtask_reference}/status")
@api_error_handler("OP_GET_SUBTASK_STATUS")
async def get_subtask_status(
    task_id: str,
    subtask_reference: str,
    db: DatabaseService = Depends(get_db_service)
) -> dict:
    """
    Get the current status of a specific subtask.
    
    Args:
        task_id: Unique identifier of the task
        subtask_reference: Reference identifier of the subtask
        db: Database service
        
    Returns:
        Current subtask status and details
        
    Raises:
        TaskNotFoundException: If task does not exist
        ValueError: If subtask reference is not found
    """
    logger.info(f"Getting status for subtask {subtask_reference} in task {task_id}")
    
    # Get task to ensure it exists
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    # Find the subtask by reference
    subtask = _find_subtask_by_reference(task, subtask_reference)
    if not subtask:
        raise ValueError(f"Subtask with reference '{subtask_reference}' not found in task {task_id}")
    
    status_info = {
        "task_id": task_id,
        "subtask_reference": subtask_reference,
        "subtask_id": subtask.id,
        "title": subtask.title,
        "status": subtask.status.value if hasattr(subtask.status, 'value') else str(subtask.status),
        "result": subtask.result,
        "error_message": subtask.error_message,
        "started_at": subtask.started_at,
        "completed_at": subtask.completed_at,
        "created_at": subtask.created_at if hasattr(subtask, 'created_at') else None
    }
    
    logger.info(f"Retrieved status for subtask {subtask_reference}: {status_info['status']}")
    return status_info


@router.post("/{task_id}/subtasks/{subtask_reference}/complete")
@api_error_handler("OP_COMPLETE_SUBTASK")
async def complete_subtask(
    task_id: str,
    subtask_reference: str,
    result_text: str = "Task completed successfully",
    db: DatabaseService = Depends(get_db_service)
) -> dict:
    """
    Mark a subtask as completed with a result.
    
    Args:
        task_id: Unique identifier of the task
        subtask_reference: Reference identifier of the subtask
        result_text: Result description for the completed subtask
        db: Database service
        
    Returns:
        Confirmation message
        
    Raises:
        TaskNotFoundException: If task does not exist
        ValueError: If subtask reference is not found
    """
    logger.info(f"Completing subtask {subtask_reference} for task {task_id}")
    logger.info(f"Result: {result_text}")
    
    # Get task to ensure it exists
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    # Find the subtask by reference
    subtask = _find_subtask_by_reference(task, subtask_reference)
    if not subtask:
        raise ValueError(f"Subtask with reference '{subtask_reference}' not found in task {task_id}")
    
    # Update subtask to completed status
    subtask.status = SubtaskStatus.COMPLETED
    subtask.result = result_text
    subtask.completed_at = None  # Would set current timestamp in real implementation
    
    # Save the updated task
    db.updated_task(task)
    
    logger.info(f"Subtask {subtask_reference} marked as completed")
    
    return {
        "message": f"Subtask {subtask_reference} completed successfully",
        "task_id": task_id,
        "subtask_reference": subtask_reference,
        "result": result_text,
        "status": SubtaskStatus.COMPLETED.value
    }


@router.post("/{task_id}/subtasks/{subtask_reference}/fail")
@api_error_handler("OP_FAIL_SUBTASK")
async def fail_subtask(
    task_id: str,
    subtask_reference: str,
    error_message: str = "Task failed",
    db: DatabaseService = Depends(get_db_service)
) -> dict:
    """
    Mark a subtask as failed with an error message.
    
    Args:
        task_id: Unique identifier of the task
        subtask_reference: Reference identifier of the subtask
        error_message: Error description for the failed subtask
        db: Database service
        
    Returns:
        Confirmation message
        
    Raises:
        TaskNotFoundException: If task does not exist
        ValueError: If subtask reference is not found
    """
    logger.info(f"Failing subtask {subtask_reference} for task {task_id}")
    logger.info(f"Error: {error_message}")
    
    # Get task to ensure it exists
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    # Find the subtask by reference
    subtask = _find_subtask_by_reference(task, subtask_reference)
    if not subtask:
        raise ValueError(f"Subtask with reference '{subtask_reference}' not found in task {task_id}")
    
    # Update subtask to failed status
    subtask.status = SubtaskStatus.FAILED
    subtask.error_message = error_message
    subtask.completed_at = None  # Would set current timestamp in real implementation
    
    # Save the updated task
    db.updated_task(task)
    
    logger.info(f"Subtask {subtask_reference} marked as failed")
    
    return {
        "message": f"Subtask {subtask_reference} marked as failed",
        "task_id": task_id,
        "subtask_reference": subtask_reference,
        "error_message": error_message,
        "status": SubtaskStatus.FAILED.value
    }


def _find_subtask_by_reference(task: Task, subtask_reference: str) -> Optional[Subtask]:
    """
    Find a subtask by its reference in the task hierarchy.
    
    Args:
        task: The task to search in
        subtask_reference: The reference identifier to find
        
    Returns:
        The found subtask or None if not found
    """
    if not task.network_plan or not task.network_plan.stages:
        return None
    
    # Search through all stages, work packages, executable tasks, and subtasks
    for stage in task.network_plan.stages:
        if not stage.work_packages:
            continue
            
        for work_package in stage.work_packages:
            if not work_package.tasks:
                continue
                
            for executable_task in work_package.tasks:
                if not executable_task.subtasks:
                    continue
                    
                for subtask in executable_task.subtasks:
                    # Check if this subtask matches the reference
                    if (hasattr(subtask, 'reference') and subtask.reference == subtask_reference) or \
                       subtask.id == subtask_reference:
                        return subtask
    
    return None 