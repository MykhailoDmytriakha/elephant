# backend/src/utils/task_utils.py
from typing import List, Optional, Any, Dict
import logging
from datetime import datetime, timezone # Added for timestamps

# Model imports - Assuming they are in src.model
from src.model.task import Task
from src.model.planning import Stage
from src.model.work import Work
from src.model.executable_task import ExecutableTask
from src.model.subtask import Subtask
from src.model.status import StatusEnum # Added for status updates
from src.exceptions import StageNotFoundException, WorkNotFoundException, ExecutableTaskNotFoundException, SubtaskNotFoundException, MissingComponentException

logger = logging.getLogger(__name__)

# --- Getters / Finders by Full Path ---

def get_stage(task: Task, stage_id: str) -> Stage:
    """Finds a Stage within a Task by its ID."""
    if not task.network_plan or not task.network_plan.stages:
        logger.warning(f"Task {task.id}: Network plan or stages are missing when trying to find Stage {stage_id}.")
        raise MissingComponentException(f"Task {task.id} has no network plan or stages defined.")
    
    stage = next((s for s in task.network_plan.stages if s.id == stage_id), None)
    if not stage:
        logger.warning(f"Task {task.id}: Stage with ID '{stage_id}' not found.")
        raise StageNotFoundException(f"Stage '{stage_id}' not found in task '{task.id}'.")
    return stage

def get_work(task: Task, stage_id: str, work_id: str) -> Work:
    """Finds a Work package within a specific Stage of a Task by their IDs."""
    stage = get_stage(task, stage_id) # Raises StageNotFoundException if stage not found
    
    if not stage.work_packages:
        logger.warning(f"Task {task.id}, Stage {stage_id}: No work packages found when trying to find Work {work_id}.")
        raise MissingComponentException(f"Stage '{stage_id}' in task '{task.id}' has no work packages.")

    work = next((w for w in stage.work_packages if w.id == work_id), None)
    if not work:
        logger.warning(f"Task {task.id}, Stage {stage_id}: Work package with ID '{work_id}' not found.")
        raise WorkNotFoundException(f"Work package '{work_id}' not found in stage '{stage_id}' of task '{task.id}'.")
    return work

def get_executable_task(task: Task, stage_id: str, work_id: str, executable_task_id: str) -> ExecutableTask:
    """Finds an ExecutableTask within a specific Work package and Stage of a Task."""
    work = get_work(task, stage_id, work_id) # Raises exceptions if stage or work not found
    
    if not work.tasks:
        logger.warning(f"Task {task.id}, Stage {stage_id}, Work {work_id}: No executable tasks found when trying to find ET {executable_task_id}.")
        raise MissingComponentException(f"Work package '{work_id}' in stage '{stage_id}' of task '{task.id}' has no executable tasks.")

    executable_task = next((et for et in work.tasks if et.id == executable_task_id), None)
    if not executable_task:
        logger.warning(f"Task {task.id}, Stage {stage_id}, Work {work_id}: ExecutableTask with ID '{executable_task_id}' not found.")
        raise ExecutableTaskNotFoundException(f"ExecutableTask '{executable_task_id}' not found in work package '{work_id}', stage '{stage_id}' of task '{task.id}'.")
    return executable_task

def get_subtask(task: Task, stage_id: str, work_id: str, executable_task_id: str, subtask_id: str) -> Subtask:
    """Finds a Subtask within a specific ExecutableTask, Work package, and Stage of a Task."""
    executable_task = get_executable_task(task, stage_id, work_id, executable_task_id) # Raises exceptions if parents not found
    
    if not executable_task.subtasks:
        logger.warning(f"Task {task.id}, ..., ET {executable_task_id}: No subtasks found when trying to find Subtask {subtask_id}.")
        raise MissingComponentException(f"ExecutableTask '{executable_task_id}' has no subtasks.")

    subtask = next((st for st in executable_task.subtasks if st.id == subtask_id), None)
    if not subtask:
        logger.warning(f"Task {task.id}, ..., ET {executable_task_id}: Subtask with ID '{subtask_id}' not found.")
        raise SubtaskNotFoundException(f"Subtask '{subtask_id}' not found in executable task '{executable_task_id}'.")
    return subtask

# --- Finders by ID (Searching the hierarchy) ---

def find_stage_by_id(task: Task, stage_id: str) -> Optional[Stage]:
    """Finds a Stage within a Task by its ID. Returns None if not found."""
    if not task.network_plan or not task.network_plan.stages:
        return None
    return next((s for s in task.network_plan.stages if s.id == stage_id), None)

def find_work_by_id(task: Task, work_id: str) -> Optional[Work]:
    """Finds a Work package within any Stage of a Task by its ID. Returns None if not found."""
    if not task.network_plan or not task.network_plan.stages:
        return None
    for stage in task.network_plan.stages:
        if stage.work_packages:
            work = next((w for w in stage.work_packages if w.id == work_id), None)
            if work:
                return work
    return None

def find_executable_task_by_id(task: Task, executable_task_id: str) -> Optional[ExecutableTask]:
    """Finds an ExecutableTask within any Work package/Stage by its ID. Returns None if not found."""
    if not task.network_plan or not task.network_plan.stages:
        return None
    for stage in task.network_plan.stages:
        if stage.work_packages:
            for work in stage.work_packages:
                if work.tasks:
                    executable_task = next((et for et in work.tasks if et.id == executable_task_id), None)
                    if executable_task:
                        return executable_task
    return None

def find_subtask_by_id(task: Task, subtask_id: str) -> Optional[Subtask]:
    """Finds a Subtask within any ExecutableTask/Work/Stage by its ID. Returns None if not found."""
    if not task.network_plan or not task.network_plan.stages:
        return None
    for stage in task.network_plan.stages:
        if stage.work_packages:
            for work in stage.work_packages:
                if work.tasks:
                    for executable_task in work.tasks:
                        if executable_task.subtasks:
                            subtask = next((st for st in executable_task.subtasks if st.id == subtask_id), None)
                            if subtask:
                                return subtask
    return None

# --- Updaters ---

def _update_object(obj: Any, update_data: Dict[str, Any]):
    """Helper function to update object attributes from a dictionary."""
    for key, value in update_data.items():
        if hasattr(obj, key):
            setattr(obj, key, value)
            logger.debug(f"Updated attribute '{key}' of object {getattr(obj, 'id', obj)}.")
        else:
            logger.warning(f"Attempted to update non-existent attribute '{key}' on object {getattr(obj, 'id', obj)}.")

def update_stage(task: Task, stage_id: str, update_data: Dict[str, Any]) -> Stage:
    """Finds and updates a Stage within a Task."""
    stage = get_stage(task, stage_id) # Raises StageNotFoundException if stage not found
    _update_object(stage, update_data)
    logger.info(f"Updated Stage '{stage_id}' in task '{task.id}'.")
    return stage

def update_work(task: Task, stage_id: str, work_id: str, update_data: Dict[str, Any]) -> Work:
    """Finds and updates a Work package within a specific Stage of a Task."""
    work = get_work(task, stage_id, work_id) # Raises exceptions if stage or work not found
    _update_object(work, update_data)
    logger.info(f"Updated Work '{work_id}' in Stage '{stage_id}', task '{task.id}'.")
    return work

def update_executable_task(task: Task, stage_id: str, work_id: str, executable_task_id: str, update_data: Dict[str, Any]) -> ExecutableTask:
    """Finds and updates an ExecutableTask within a specific Work package and Stage."""
    executable_task = get_executable_task(task, stage_id, work_id, executable_task_id) # Raises exceptions if parents not found
    _update_object(executable_task, update_data)
    logger.info(f"Updated ExecutableTask '{executable_task_id}' in Work '{work_id}', Stage '{stage_id}', task '{task.id}'.")
    return executable_task

def update_subtask(task: Task, stage_id: str, work_id: str, executable_task_id: str, subtask_id: str, update_data: Dict[str, Any]) -> Subtask:
    """Finds and updates a Subtask within a specific ExecutableTask, Work package, and Stage."""
    subtask = get_subtask(task, stage_id, work_id, executable_task_id, subtask_id) # Raises exceptions if parents not found
    _update_object(subtask, update_data)
    logger.info(f"Updated Subtask '{subtask_id}' in ExecutableTask '{executable_task_id}', ..., task '{task.id}'.")
    return subtask

# --- Specific Status Updaters ---

def _get_iso_timestamp() -> str:
    """Returns the current time in ISO 8601 format with UTC timezone."""
    return datetime.now(timezone.utc).isoformat()

# Stage Status Updaters
def start_stage(task: Task, stage_id: str) -> Stage:
    stage = get_stage(task, stage_id)
    stage.status = StatusEnum.IN_PROGRESS
    stage.started_at = _get_iso_timestamp()
    stage.completed_at = None # Ensure completed_at is reset if restarting
    stage.error_message = None
    logger.info(f"Started Stage '{stage_id}' in task '{task.id}'.")
    return stage

def complete_stage(task: Task, stage_id: str, result_data: Optional[str] = None) -> Stage:
    stage = get_stage(task, stage_id)
    stage.status = StatusEnum.COMPLETED
    stage.completed_at = _get_iso_timestamp()
    stage.result_data = result_data # Storing result data on completion
    stage.error_message = None
    logger.info(f"Completed Stage '{stage_id}' in task '{task.id}'.")
    return stage

def fail_stage(task: Task, stage_id: str, error_message: str) -> Stage:
    stage = get_stage(task, stage_id)
    stage.status = StatusEnum.FAILED
    stage.completed_at = _get_iso_timestamp() # Mark completion time even on failure
    stage.error_message = error_message
    logger.error(f"Failed Stage '{stage_id}' in task '{task.id}': {error_message}")
    return stage

# Work Status Updaters
def start_work(task: Task, stage_id: str, work_id: str) -> Work:
    work = get_work(task, stage_id, work_id)
    work.status = StatusEnum.IN_PROGRESS
    work.started_at = _get_iso_timestamp()
    work.completed_at = None
    work.error_message = None
    logger.info(f"Started Work '{work_id}' in Stage '{stage_id}', task '{task.id}'.")
    return work

def complete_work(task: Task, stage_id: str, work_id: str, result: Optional[str] = None) -> Work:
    work = get_work(task, stage_id, work_id)
    work.status = StatusEnum.COMPLETED
    work.completed_at = _get_iso_timestamp()
    work.result = result
    work.error_message = None
    logger.info(f"Completed Work '{work_id}' in Stage '{stage_id}', task '{task.id}'.")
    return work

def fail_work(task: Task, stage_id: str, work_id: str, error_message: str) -> Work:
    work = get_work(task, stage_id, work_id)
    work.status = StatusEnum.FAILED
    work.completed_at = _get_iso_timestamp()
    work.error_message = error_message
    logger.error(f"Failed Work '{work_id}' in Stage '{stage_id}', task '{task.id}': {error_message}")
    return work

# ExecutableTask Status Updaters
def start_executable_task(task: Task, stage_id: str, work_id: str, executable_task_id: str) -> ExecutableTask:
    executable_task = get_executable_task(task, stage_id, work_id, executable_task_id)
    executable_task.status = StatusEnum.IN_PROGRESS
    executable_task.started_at = _get_iso_timestamp()
    executable_task.completed_at = None
    executable_task.error_message = None
    logger.info(f"Started ExecutableTask '{executable_task_id}' in Work '{work_id}', task '{task.id}'.")
    return executable_task

def complete_executable_task(task: Task, stage_id: str, work_id: str, executable_task_id: str, result: Optional[str] = None) -> ExecutableTask:
    executable_task = get_executable_task(task, stage_id, work_id, executable_task_id)
    executable_task.status = StatusEnum.COMPLETED
    executable_task.completed_at = _get_iso_timestamp()
    executable_task.result = result
    executable_task.error_message = None
    logger.info(f"Completed ExecutableTask '{executable_task_id}' in Work '{work_id}', task '{task.id}'.")
    return executable_task

def fail_executable_task(task: Task, stage_id: str, work_id: str, executable_task_id: str, error_message: str) -> ExecutableTask:
    executable_task = get_executable_task(task, stage_id, work_id, executable_task_id)
    executable_task.status = StatusEnum.FAILED
    executable_task.completed_at = _get_iso_timestamp()
    executable_task.error_message = error_message
    logger.error(f"Failed ExecutableTask '{executable_task_id}' in Work '{work_id}', task '{task.id}': {error_message}")
    return executable_task

# Subtask Status Updaters
def start_subtask(task: Task, stage_id: str, work_id: str, executable_task_id: str, subtask_id: str) -> Subtask:
    subtask = get_subtask(task, stage_id, work_id, executable_task_id, subtask_id)
    subtask.status = StatusEnum.IN_PROGRESS
    subtask.started_at = _get_iso_timestamp()
    subtask.completed_at = None
    subtask.error_message = None
    logger.info(f"Started Subtask '{subtask_id}' in ET '{executable_task_id}', task '{task.id}'.")
    return subtask

def complete_subtask(task: Task, stage_id: str, work_id: str, executable_task_id: str, subtask_id: str, result: Optional[str] = None) -> Subtask:
    subtask = get_subtask(task, stage_id, work_id, executable_task_id, subtask_id)
    subtask.status = StatusEnum.COMPLETED
    subtask.completed_at = _get_iso_timestamp()
    subtask.result = result
    subtask.error_message = None
    logger.info(f"Completed Subtask '{subtask_id}' in ET '{executable_task_id}', task '{task.id}'.")
    return subtask

def fail_subtask(task: Task, stage_id: str, work_id: str, executable_task_id: str, subtask_id: str, error_message: str) -> Subtask:
    subtask = get_subtask(task, stage_id, work_id, executable_task_id, subtask_id)
    subtask.status = StatusEnum.FAILED
    subtask.completed_at = _get_iso_timestamp()
    subtask.error_message = error_message
    logger.error(f"Failed Subtask '{subtask_id}' in ET '{executable_task_id}', task '{task.id}': {error_message}")
    return subtask 