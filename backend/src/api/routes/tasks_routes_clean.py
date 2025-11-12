# backend/src/api/routes/tasks_routes_clean.py
"""
Clean Task Routes Module

Main routing module for tasks that delegates to specialized sub-modules.
This file remains focused on core task operations while specific functionality
is handled by dedicated route modules.
"""

from fastapi import APIRouter, Depends
from typing import List
import logging

# Model imports
from src.model.task import Task
from src.model.planning import NetworkPlan
from src.model.work import Work
from src.model.executable_task import ExecutableTask
from src.model.subtask import Subtask

# Service imports
from src.services.problem_analyzer import ProblemAnalyzer
from src.services.database_service import DatabaseService
from src.services.task_generation_service import TaskGenerationService

# API utils imports
from src.api.deps import get_problem_analyzer, get_file_storage_service
from src.api.utils import api_error_handler, deserialize_task

# Exception imports
from src.exceptions import ServerException

# Constants
from src.constants import (
    OP_TASK_DELETION,
    OP_GET_TASK,
    OP_WORK_GENERATION,
    OP_BATCH_WORK_GENERATION,
    OP_TASK_GENERATION,
    OP_BATCH_TASK_GENERATION,
    OP_SUBTASK_GENERATION,
    OP_BATCH_SUBTASK_GENERATION,
    SUCCESS_TASK_DELETED,
    SUCCESS_ALL_TASKS_DELETED
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# CORE TASK OPERATIONS
# ============================================================================

@router.get("/{task_id}", response_model=Task)
@api_error_handler(OP_GET_TASK)
async def get_task(
    task_id: str, 
    db: DatabaseService = Depends(get_db_service)
) -> Task:
    """
    Get a task by its ID.
    
    Args:
        task_id: Unique identifier of the task
        db: Database service
        
    Returns:
        The requested task
        
    Raises:
        TaskNotFoundException: If task does not exist
    """
    logger.info(f"Retrieving task {task_id}")
    
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    logger.info(f"Successfully retrieved task {task_id}")
    return task


@router.delete("/{task_id}")
@api_error_handler(OP_TASK_DELETION)
async def delete_task(
    task_id: str,
    db: DatabaseService = Depends(get_db_service)
) -> dict:
    """
    Delete a specific task.
    
    Args:
        task_id: Unique identifier of the task to delete
        db: Database service
        
    Returns:
        Confirmation message
        
    Raises:
        TaskNotFoundException: If task does not exist
        ServerException: If deletion fails
    """
    logger.info(f"Deleting task {task_id}")
    
    # Verify task exists before attempting deletion
    task_data = db.fetch_task_by_id(task_id)
    deserialize_task(task_data, task_id)
    
    # Perform deletion
    success = db.delete_task_by_id(task_id)
    if not success:
        raise ServerException(f"Failed to delete task {task_id}")
    
    logger.info(f"Successfully deleted task {task_id}")
    return {"message": SUCCESS_TASK_DELETED.format(task_id=task_id)}


@router.delete("/", response_model=dict)
@api_error_handler(OP_TASK_DELETION)
async def delete_all_tasks(
    db: DatabaseService = Depends(get_db_service)
) -> dict:
    """
    Delete all tasks in the system.
    
    Args:
        db: Database service
        
    Returns:
        Confirmation message
        
    Raises:
        ServerException: If deletion fails
    """
    logger.info("Deleting all tasks")
    
    try:
        db.delete_all_tasks()
        logger.info("Successfully deleted all tasks")
        return {"message": SUCCESS_ALL_TASKS_DELETED}
    except Exception as e:
        logger.error(f"Failed to delete all tasks: {e}")
        raise ServerException("Failed to delete all tasks")


# ============================================================================
# WORK PACKAGE GENERATION
# ============================================================================

@router.post("/{task_id}/stages/{stage_id}/generate-work", response_model=List[Work])
@api_error_handler(OP_WORK_GENERATION)
async def generate_work_for_stage(
    task_id: str,
    stage_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
) -> List[Work]:
    """
    Generate work packages for a specific stage.
    
    Args:
        task_id: Unique identifier of the task
        stage_id: Unique identifier of the stage
        analyzer: Problem analyzer service
        db: Database service
        
    Returns:
        List of generated work packages
    """
    logger.info(f"Generating work packages for stage {stage_id} in task {task_id}")
    
    # Get task and initialize generation service
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    generation_service = TaskGenerationService(analyzer, db)
    
    # Generate work packages
    work_packages = await generation_service.generate_work_for_stage(task, stage_id)
    
    logger.info(f"Generated {len(work_packages)} work packages for stage {stage_id}")
    return work_packages


@router.post("/{task_id}/stages/generate-work", response_model=NetworkPlan)
@api_error_handler(OP_BATCH_WORK_GENERATION)
async def generate_work_for_all_stages(
    task_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
) -> NetworkPlan:
    """
    Generate work packages for all stages in the task.
    
    Args:
        task_id: Unique identifier of the task
        analyzer: Problem analyzer service
        db: Database service
        
    Returns:
        Updated network plan with generated work packages
    """
    logger.info(f"Generating work packages for all stages in task {task_id}")
    
    # Get task and initialize generation service
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    generation_service = TaskGenerationService(analyzer, db)
    
    # Generate work packages for all stages
    network_plan = await generation_service.generate_work_for_all_stages(task)
    
    logger.info(f"Generated work packages for all stages in task {task_id}")
    return network_plan


# ============================================================================
# EXECUTABLE TASK GENERATION
# ============================================================================

@router.post("/{task_id}/stages/{stage_id}/work/{work_id}/generate-tasks", response_model=List[ExecutableTask])
@api_error_handler(OP_TASK_GENERATION)
async def generate_tasks_for_work(
    task_id: str,
    stage_id: str,
    work_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
) -> List[ExecutableTask]:
    """
    Generate executable tasks for a specific work package.
    
    Args:
        task_id: Unique identifier of the task
        stage_id: Unique identifier of the stage
        work_id: Unique identifier of the work package
        analyzer: Problem analyzer service
        db: Database service
        
    Returns:
        List of generated executable tasks
    """
    logger.info(f"Generating tasks for work {work_id} in stage {stage_id} of task {task_id}")
    
    # Get task and initialize generation service
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    generation_service = TaskGenerationService(analyzer, db)
    
    # Generate executable tasks
    executable_tasks = await generation_service.generate_tasks_for_work(task, stage_id, work_id)
    
    logger.info(f"Generated {len(executable_tasks)} tasks for work {work_id}")
    return executable_tasks


@router.post("/{task_id}/stages/{stage_id}/works/generate-tasks", response_model=List[Work])
@api_error_handler(OP_BATCH_TASK_GENERATION)
async def generate_tasks_for_all_works_in_stage(
    task_id: str,
    stage_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
) -> List[Work]:
    """
    Generate executable tasks for all work packages in a stage.
    
    Args:
        task_id: Unique identifier of the task
        stage_id: Unique identifier of the stage
        analyzer: Problem analyzer service
        db: Database service
        
    Returns:
        List of updated work packages with generated tasks
    """
    logger.info(f"Generating tasks for all work packages in stage {stage_id} of task {task_id}")
    
    # Get task and initialize generation service
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    generation_service = TaskGenerationService(analyzer, db)
    
    # Generate tasks for all work packages in the stage
    work_packages = await generation_service.generate_tasks_for_all_works_in_stage(task, stage_id)
    
    logger.info(f"Generated tasks for all work packages in stage {stage_id}")
    return work_packages


@router.post("/{task_id}/stages/generate-all-tasks", response_model=NetworkPlan)
@api_error_handler(OP_BATCH_TASK_GENERATION)
async def generate_tasks_for_all_stages(
    task_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
) -> NetworkPlan:
    """
    Generate executable tasks for all work packages in all stages.
    
    Args:
        task_id: Unique identifier of the task
        analyzer: Problem analyzer service
        db: Database service
        
    Returns:
        Updated network plan with generated tasks
    """
    logger.info(f"Generating tasks for all stages in task {task_id}")
    
    # Get task and initialize generation service
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    generation_service = TaskGenerationService(analyzer, db)
    
    # Generate tasks for all stages
    network_plan = await generation_service.generate_tasks_for_all_stages(task)
    
    logger.info(f"Generated tasks for all stages in task {task_id}")
    return network_plan


# ============================================================================
# SUBTASK GENERATION
# ============================================================================

@router.post("/{task_id}/stages/{stage_id}/work/{work_id}/tasks/{executable_task_id}/generate-subtasks", response_model=List[Subtask])
@api_error_handler(OP_SUBTASK_GENERATION)
async def generate_subtasks_for_task(
    task_id: str,
    stage_id: str,
    work_id: str,
    executable_task_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
) -> List[Subtask]:
    """
    Generate subtasks for a specific executable task.
    
    Args:
        task_id: Unique identifier of the task
        stage_id: Unique identifier of the stage
        work_id: Unique identifier of the work package
        executable_task_id: Unique identifier of the executable task
        analyzer: Problem analyzer service
        db: Database service
        
    Returns:
        List of generated subtasks
    """
    logger.info(f"Generating subtasks for executable task {executable_task_id}")
    
    # Get task and initialize generation service
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    generation_service = TaskGenerationService(analyzer, db)
    
    # Generate subtasks
    subtasks = await generation_service.generate_subtasks_for_task(
        task, stage_id, work_id, executable_task_id
    )
    
    logger.info(f"Generated {len(subtasks)} subtasks for executable task {executable_task_id}")
    return subtasks


@router.post("/{task_id}/stages/{stage_id}/work/{work_id}/tasks/generate-subtasks", response_model=List[ExecutableTask])
@api_error_handler(OP_BATCH_SUBTASK_GENERATION)
async def generate_subtasks_for_all_tasks_in_work(
    task_id: str,
    stage_id: str,
    work_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
) -> List[ExecutableTask]:
    """
    Generate subtasks for all executable tasks in a work package.
    
    Args:
        task_id: Unique identifier of the task
        stage_id: Unique identifier of the stage
        work_id: Unique identifier of the work package
        analyzer: Problem analyzer service
        db: Database service
        
    Returns:
        List of updated executable tasks with generated subtasks
    """
    logger.info(f"Generating subtasks for all tasks in work package {work_id}")
    
    # Get task and initialize generation service
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    generation_service = TaskGenerationService(analyzer, db)
    
    # Generate subtasks for all tasks in the work package
    executable_tasks = await generation_service.generate_subtasks_for_all_tasks_in_work(
        task, stage_id, work_id
    )
    
    logger.info(f"Generated subtasks for all tasks in work package {work_id}")
    return executable_tasks 