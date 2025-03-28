from fastapi import APIRouter, Depends, HTTPException
import json

from src.api.deps import get_db_service
from src.api.utils import api_error_handler, deserialize_task, validate_task_scope_group
from src.model.task import Task, TaskState
from src.services.database_service import DatabaseService
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
    db: DatabaseService = Depends(get_db_service)
):
    """Clear the scope of a specific task"""
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    # Clear the scope
    task.scope = None
    
    # Update the task in the database
    db.updated_task(task)
    
    return {"message": SUCCESS_SCOPE_CLEARED.format(task_id=task_id)} 

# cleanup specific group
@router.delete("/tasks/{task_id}/clear-group/{group}", response_model=dict)
@api_error_handler(OP_GROUP_CLEARING)
async def clear_task_group(
    task_id: str,
    group: str,
    db: DatabaseService = Depends(get_db_service)
):
    """Clear a specific group from the task"""
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    # Validate that the group exists in the task scope
    validate_task_scope_group(task, group, task_id)
    
    # Clear the specific group
    setattr(task.scope, group, None)
    
    db.updated_task(task)
    
    return {"message": SUCCESS_GROUP_CLEARED.format(group=group, task_id=task_id)}

@router.delete("/tasks/{task_id}/draft", response_model=dict)
@api_error_handler(OP_DRAFT_CLEARING)
async def clear_task_draft(
    task_id: str,
    db: DatabaseService = Depends(get_db_service)
):
    """Clear the draft scope of a specific task"""
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    if task.scope:
        task.scope.scope = None
        task.scope.status = None
        task.scope.validation_criteria = None
        task.scope.feedback = None
    
    db.updated_task(task)
    
    return {"message": SUCCESS_DRAFT_CLEARED.format(task_id=task_id)} 

@router.delete("/tasks/{task_id}/clear-requirements", response_model=dict)
@api_error_handler(OP_REQUIREMENTS_CLEARING)
async def clear_task_requirements(
    task_id: str,
    db: DatabaseService = Depends(get_db_service)
):
    """Clear the requirements of a specific task"""
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    task.requirements = None
    task.state = TaskState.IFR_GENERATED
    
    db.updated_task(task)
    
    return {"message": SUCCESS_REQUIREMENTS_CLEARED.format(task_id=task_id)}
