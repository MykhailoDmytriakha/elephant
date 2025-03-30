import logging
from typing import Callable, Any, TypeVar, ParamSpec, Awaitable, Optional, Dict, cast, Type, Union, List
from functools import wraps

from fastapi import HTTPException
import json

from src.constants import (
    ERROR_TASK_NOT_FOUND,
    ERROR_TASK_STATE_INVALID,
    ERROR_TASK_NO_NETWORK_PLAN,
    ERROR_STAGE_NOT_FOUND,
    ERROR_WORK_NOT_FOUND,
    ERROR_EXECUTABLE_TASK_NOT_FOUND,
    ERROR_STAGE_NO_WORK,
    ERROR_WORK_NO_TASKS,
    ERROR_TASK_DESERIALIZE,
    ERROR_TASK_GROUP_NOT_FOUND,
    ERROR_DATABASE_OPERATION,
    ERROR_BATCH_OPERATION,
    ERROR_EMPTY_LIST,
    ERROR_TASK_NO_SCOPE,
    ERROR_TASK_NO_SCOPE_GROUP,
    HTTP_NOT_FOUND,
    HTTP_BAD_REQUEST,
    HTTP_SERVER_ERROR,
    HTTP_NOT_IMPLEMENTED
)

from src.exceptions import (
    TaskNotFoundException,
    StageNotFoundException,
    WorkNotFoundException,
    ExecutableTaskNotFoundException,
    InvalidStateException,
    MissingComponentException,
    DeserializationException,
    QueryNotFoundException,
    GroupNotFoundException,
    ValidationException
)

# Forward references for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.model.task import Task, TaskState
    from src.model.planning import Stage, NetworkPlan
    from src.model.work import Work
    from src.model.executable_task import ExecutableTask

logger = logging.getLogger(__name__)

P = ParamSpec('P')
T = TypeVar('T')

def api_error_handler(operation_name: str) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """
    Decorator for API endpoint functions to standardize error handling.
    
    Args:
        operation_name: A descriptive name for the operation being performed
        
    Returns:
        Decorated function with standardized error handling
    
    Example:
        @router.post("/some-endpoint")
        @api_error_handler("some operation")
        async def some_endpoint(request_data: SomeType):
            # Function implementation that may raise errors
            return result
    """
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except TaskNotFoundException as e:
                logger.error(f"Task not found during {operation_name}: {e}")
                raise HTTPException(status_code=HTTP_NOT_FOUND, detail=str(e))
            except StageNotFoundException as e:
                logger.error(f"Stage not found during {operation_name}: {e}")
                raise HTTPException(status_code=HTTP_NOT_FOUND, detail=str(e))
            except WorkNotFoundException as e:
                logger.error(f"Work not found during {operation_name}: {e}")
                raise HTTPException(status_code=HTTP_NOT_FOUND, detail=str(e))
            except ExecutableTaskNotFoundException as e:
                logger.error(f"ExecutableTask not found during {operation_name}: {e}")
                raise HTTPException(status_code=HTTP_NOT_FOUND, detail=str(e))
            except QueryNotFoundException as e:
                logger.error(f"Query not found during {operation_name}: {e}")
                raise HTTPException(status_code=HTTP_NOT_FOUND, detail=str(e))
            except GroupNotFoundException as e:
                logger.error(f"Group not found during {operation_name}: {e}")
                raise HTTPException(status_code=HTTP_NOT_FOUND, detail=str(e))
            except InvalidStateException as e:
                logger.error(f"Invalid state error during {operation_name}: {e}")
                raise HTTPException(status_code=HTTP_BAD_REQUEST, detail=str(e))
            except MissingComponentException as e:
                logger.error(f"Missing component error during {operation_name}: {e}")
                raise HTTPException(status_code=HTTP_BAD_REQUEST, detail=str(e))
            except ValidationException as e:
                logger.error(f"Validation error during {operation_name}: {e}")
                raise HTTPException(status_code=HTTP_BAD_REQUEST, detail=str(e))
            except DeserializationException as e:
                logger.error(f"Deserialization error during {operation_name}: {e}")
                raise HTTPException(status_code=HTTP_SERVER_ERROR, detail=str(e))
            except ImportError as ie:
                logger.error(f"Import error during {operation_name}: {ie}")
                raise HTTPException(status_code=HTTP_NOT_IMPLEMENTED, detail=f"{operation_name} feature requires additional dependencies.")
            except Exception as e:
                logger.error(f"Unexpected error during {operation_name}: {e}", exc_info=True)
                raise HTTPException(status_code=HTTP_SERVER_ERROR, detail=f"An internal error occurred during {operation_name}.")
        return wrapper
    return decorator

def deserialize_task(task_data: Optional[Dict[str, Any]], task_id: str) -> 'Task':
    """
    Deserialize task data from JSON string to Task object.
    
    Args:
        task_data: The task data from the database
        task_id: The ID of the task
    
    Returns:
        Deserialized Task object
    
    Raises:
        TaskNotFoundException: If task is not found
        DeserializationException: If deserialization fails
        HTTPException: When converted from custom exceptions
    """
    from src.model.task import Task
    
    if task_data is None:
        logger.error(f"Task {task_id} not found.")
        raise TaskNotFoundException(ERROR_TASK_NOT_FOUND.format(task_id=task_id))
    
    try:
        return Task(**json.loads(task_data['task_json']))
    except Exception as e:
        logger.error(f"Failed to deserialize task {task_id}: {e}")
        raise DeserializationException(ERROR_TASK_DESERIALIZE)

def validate_task_state(task: 'Task', required_state: 'TaskState', task_id: Optional[str] = None) -> bool:
    """
    Validate that a task is in the required state.
    
    Args:
        task: The task object to validate
        required_state: The required state for the task
        task_id: Optional ID for better error messages
    
    Returns:
        True if the task is in the required state
    
    Raises:
        InvalidStateException: If the task is not in the required state
    """
    id_str = f" {task_id}" if task_id else ""
    
    if not is_task_in_states(task, [required_state]):
        # For error message, ensure we get the string value safely
        current_state = task.state.value if hasattr(task.state, 'value') else str(task.state)
        required_state_value = required_state.value if hasattr(required_state, 'value') else str(required_state)
        
        error_message = ERROR_TASK_STATE_INVALID.format(
            id_str=id_str,
            required_state=required_state_value,
            current_state=current_state
        )
        logger.error(f"Task state validation failed: {error_message}")
        raise InvalidStateException(error_message)
    
    return True

def has_network_plan(task: 'Task') -> bool:
    """
    Type guard to check if task has a network plan.
    
    Args:
        task: The task object to check
    
    Returns:
        True if the task has a network plan, False otherwise
    """
    return task.network_plan is not None

def has_stages(network_plan: 'NetworkPlan') -> bool:
    """
    Type guard to check if network plan has stages.
    
    Args:
        network_plan: The network plan to check
    
    Returns:
        True if the network plan has stages, False otherwise
    """
    return network_plan.stages is not None and len(network_plan.stages) > 0

def has_work_packages(stage: 'Stage') -> bool:
    """
    Type guard to check if stage has work packages.
    
    Args:
        stage: The stage to check
    
    Returns:
        True if the stage has work packages, False otherwise
    """
    return stage.work_packages is not None and len(stage.work_packages) > 0

def has_tasks(work: 'Work') -> bool:
    """
    Type guard to check if work has tasks.
    
    Args:
        work: The work to check
    
    Returns:
        True if the work has tasks, False otherwise
    """
    return work.tasks is not None and len(work.tasks) > 0

def validate_task_network_plan(task: 'Task', task_id: Optional[str] = None) -> bool:
    """
    Validate that a task has a network plan.
    
    Args:
        task: The task object to validate
        task_id: Optional ID for better error messages
    
    Returns:
        True if the task has a network plan
    
    Raises:
        MissingComponentException: If the task does not have a network plan
    """
    id_str = f" {task_id}" if task_id else ""
    
    if not has_network_plan(task):
        error_message = ERROR_TASK_NO_NETWORK_PLAN.format(id_str=id_str)
        logger.error(error_message)
        raise MissingComponentException(error_message)
    
    return True

def find_stage_by_id(task: 'Task', stage_id: str) -> 'Stage':
    """
    Find a stage in a task's network plan by its ID.
    
    Args:
        task: The task object
        stage_id: The stage ID to find
    
    Returns:
        The stage object if found
    
    Raises:
        MissingComponentException: If the task does not have a network plan with stages
        StageNotFoundException: If the stage is not found
    """
    if not has_network_plan(task):
        raise MissingComponentException(ERROR_TASK_NO_NETWORK_PLAN.format(id_str=""))
    
    # Since we've verified network_plan is not None, we can safely cast it
    network_plan = cast('NetworkPlan', task.network_plan)
    
    if not has_stages(network_plan):
        raise MissingComponentException(ERROR_TASK_NO_NETWORK_PLAN.format(id_str=""))
    
    # At this point we know stages is not None and not empty
    stages = cast(List['Stage'], network_plan.stages)
    stage = next((s for s in stages if s.id == stage_id), None)
    if not stage:
        raise StageNotFoundException(ERROR_STAGE_NOT_FOUND.format(stage_id=stage_id))
    
    return stage

def find_work_package_by_id(stage: 'Stage', work_id: str) -> 'Work':
    """
    Find a work package in a stage by its ID.
    
    Args:
        stage: The stage object
        work_id: The work package ID to find
    
    Returns:
        The work package object if found
    
    Raises:
        MissingComponentException: If the stage does not have work packages
        WorkNotFoundException: If the work package is not found
    """
    if not has_work_packages(stage):
        raise MissingComponentException(ERROR_STAGE_NO_WORK.format(stage_id=stage.id))
    
    # At this point we know work_packages is not None and not empty
    work_packages = cast(List['Work'], stage.work_packages)
    work = next((w for w in work_packages if w.id == work_id), None)
    if not work:
        raise WorkNotFoundException(ERROR_WORK_NOT_FOUND.format(work_id=work_id))
    
    return work

def find_executable_task_by_id(work: 'Work', task_id: str) -> 'ExecutableTask':
    """
    Find an executable task in a work package by its ID.
    
    Args:
        work: The work package
        task_id: The executable task ID to find
    
    Returns:
        The executable task if found
    
    Raises:
        ExecutableTaskNotFoundException: If the task is not found
    """
    if not has_tasks(work):
        raise MissingComponentException(ERROR_WORK_NO_TASKS.format(work_id=work.id))
    
    # Since we've verified tasks is not None and not empty, we can safely cast it
    tasks = cast(List['ExecutableTask'], work.tasks)
    task = next((t for t in tasks if t.id == task_id), None)
    if not task:
        raise ExecutableTaskNotFoundException(ERROR_TASK_NOT_FOUND.format(task_id=task_id))
    
    return task

def is_task_in_states(task: 'Task', states: List['TaskState']) -> bool:
    """
    Checks if a task's state matches any of the provided states, handling both enum and string comparisons.
    
    This function handles the case where task.state might be a string or an enum, 
    by comparing both the enum instance and its string value.
    
    Args:
        task: The task to check
        states: List of valid states to check against
        
    Returns:
        True if task state matches any of the provided states, False otherwise
    """
    from src.model.task import TaskState
    
    # Check if task.state is directly one of the provided enum states
    if any(task.state == state for state in states):
        return True
        
    # If task.state is a string, compare with string values of the enum states
    if isinstance(task.state, str):
        return any(task.state == state.value for state in states)
        
    # If task.state is an enum, compare with string values
    if hasattr(task.state, 'value'):
        return any(task.state.value == state.value for state in states)
    
    return False

def validate_task_scope_group(task: 'Task', group: str, task_id: Optional[str] = None) -> bool:
    """
    Validate that a task scope has the given group.
    
    Args:
        task: The task object to validate
        group: The group to check for
        task_id: Optional ID for better error messages
    
    Returns:
        True if the task scope has the given group
    
    Raises:
        MissingComponentException: If the task does not have the group
    """
    id_str = f" {task_id}" if task_id else ""
    
    if not task.scope:
        error_message = ERROR_TASK_NO_SCOPE.format(id_str=id_str)
        logger.error(error_message)
        raise MissingComponentException(error_message)
    
    scope_dict = task.scope.model_dump()
    if group not in scope_dict:
        error_message = ERROR_TASK_NO_SCOPE_GROUP.format(id_str=id_str, group=group)
        logger.error(error_message)
        raise GroupNotFoundException(error_message)
    
    return True 