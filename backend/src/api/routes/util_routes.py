from fastapi import APIRouter, Depends, HTTPException
import json

from src.api.deps import get_file_storage_service
from src.api.utils import api_error_handler, deserialize_task, validate_task_scope_group
from src.model.task import Task, TaskState
from src.services.file_storage_service import FileStorageService
from src.constants import (
    ERROR_TASK_NOT_FOUND,
    ERROR_TASK_GROUP_NOT_FOUND,
    SUCCESS_SCOPE_CLEARED,
    SUCCESS_GROUP_CLEARED,
    SUCCESS_DRAFT_CLEARED,
    SUCCESS_REQUIREMENTS_CLEARED,
    OP_SCOPE_CLEARING,
    OP_GROUP_CLEARING,
    OP_DRAFT_CLEARING,
    OP_REQUIREMENTS_CLEARING
)

router = APIRouter()

@router.delete("/tasks/{task_id}/clear-scope", response_model=dict)
@api_error_handler(OP_SCOPE_CLEARING)
async def clear_task_scope(
    task_id: str,
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """Clear the scope of a specific task"""
    task = storage.load_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # Clear the scope
    task.scope = None

    # Update the task in storage
    storage.save_task(task_id, task)

    return {"message": SUCCESS_SCOPE_CLEARED.format(task_id=task_id)} 

@router.delete("/tasks/{task_id}/clear-group/{group}", response_model=dict)
@api_error_handler(OP_GROUP_CLEARING)
async def clear_task_group(
    task_id: str,
    group: str,
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """Clear a specific group from the task"""
    task = storage.load_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # Validate that the group exists in the task scope
    validate_task_scope_group(task, group, task_id)

    # Clear the specific group
    setattr(task.scope, group, None)

    storage.save_task(task_id, task)

    return {"message": SUCCESS_GROUP_CLEARED.format(group=group, task_id=task_id)}

@router.delete("/tasks/{task_id}/draft", response_model=dict)
@api_error_handler(OP_DRAFT_CLEARING)
async def clear_task_draft(
    task_id: str,
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """Clear the draft scope of a specific task"""
    task = storage.load_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    if task.scope:
        task.scope.scope = None
        task.scope.status = None
        task.scope.validation_criteria = None
        task.scope.feedback = None

    storage.save_task(task_id, task)

    return {"message": SUCCESS_DRAFT_CLEARED.format(task_id=task_id)} 

@router.delete("/tasks/{task_id}/clear-requirements", response_model=dict)
@api_error_handler(OP_REQUIREMENTS_CLEARING)
async def clear_task_requirements(
    task_id: str,
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """Clear the requirements of a specific task"""
    task = storage.load_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    task.requirements = None
    task.state = TaskState.IFR_GENERATED

    storage.save_task(task_id, task)

    return {"message": SUCCESS_REQUIREMENTS_CLEARED.format(task_id=task_id)}
