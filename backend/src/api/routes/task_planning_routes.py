"""
Task Planning Routes Module

Handles all API endpoints related to task planning phase.
Includes IFR generation, requirements definition, and network plan creation.
"""

from fastapi import APIRouter, Depends
import logging

# Model imports
from src.model.task import Task, TaskState
from src.model.ifr import IFR, Requirements
from src.model.planning import NetworkPlan

# Service imports
from src.services.problem_analyzer import ProblemAnalyzer
from src.services.file_storage_service import FileStorageService

# API utils imports
from src.api.deps import get_problem_analyzer, get_file_storage_service
from src.api.utils import api_error_handler, deserialize_task
from src.api.validators import TaskValidator

# Exception imports
from src.exceptions import InvalidStateException

# Constants
from src.constants import (
    OP_IFR_GENERATION,
    OP_REQUIREMENTS_GENERATION,
    OP_NETWORK_PLAN_GENERATION
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{task_id}/ifr", response_model=IFR)
@api_error_handler(OP_IFR_GENERATION)
async def generate_ifr(
    task_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    storage: FileStorageService = Depends(get_file_storage_service)
) -> IFR:
    """
    Generate Initial Functional Requirements (IFR) for a task.
    
    Args:
        task_id: Unique identifier of the task
        analyzer: Problem analyzer service
        db: Database service
        
    Returns:
        Generated IFR object
        
    Raises:
        TaskNotFoundException: If task does not exist
    """
    logger.info(f"Generating IFR for task {task_id}")

    task = storage.load_task(task_id)
    if not task:
        from fastapi import HTTPException
        raise HTTPException(404, detail=f"Task {task_id} not found")
    
    # Generate IFR using the problem analyzer
    ifr = await analyzer.generate_ifr(task)
    
    # Update task with the generated IFR
    task.ifr = ifr
    task.state = TaskState.IFR_GENERATED
    storage.save_task(task_id, task)
    
    logger.info(f"IFR generated and saved for task {task_id}")
    return ifr


@router.post("/{task_id}/requirements", response_model=Requirements)
@api_error_handler(OP_REQUIREMENTS_GENERATION)
async def generate_requirements(
    task_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    storage: FileStorageService = Depends(get_file_storage_service)
) -> Requirements:
    """
    Generate detailed requirements based on the task's IFR.
    
    Args:
        task_id: Unique identifier of the task
        analyzer: Problem analyzer service
        db: Database service
        
    Returns:
        Generated requirements object
        
    Raises:
        TaskNotFoundException: If task does not exist
    """
    logger.info(f"Generating requirements for task {task_id}")

    task = storage.load_task(task_id)
    if not task:
        from fastapi import HTTPException
        raise HTTPException(404, detail=f"Task {task_id} not found")
    
    # Generate requirements using the problem analyzer
    requirements = await analyzer.define_requirements(task)
    
    # Update task with the generated requirements
    task.requirements = requirements
    task.state = TaskState.REQUIREMENTS_DEFINED
    storage.save_task(task_id, task)
    
    logger.info(f"Requirements generated and saved for task {task_id}")
    return requirements


@router.post("/{task_id}/network-plan", response_model=NetworkPlan)
@api_error_handler(OP_NETWORK_PLAN_GENERATION)
async def generate_network_plan(
    task_id: str,
    force: bool = False,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    storage: FileStorageService = Depends(get_file_storage_service)
) -> NetworkPlan:
    """
    Generate a network plan for the task based on its requirements.
    
    Args:
        task_id: Unique identifier of the task
        force: Force regeneration even if network plan already exists
        analyzer: Problem analyzer service
        db: Database service
        
    Returns:
        Generated network plan
        
    Raises:
        InvalidStateException: If task already has network plan and force is False
        TaskNotFoundException: If task does not exist
    """
    logger.info(f"Generating network plan for task {task_id}, force={force}")

    task = storage.load_task(task_id)
    if not task:
        from fastapi import HTTPException
        raise HTTPException(404, detail=f"Task {task_id} not found")
    
    # Check if network plan already exists (unless force is True)
    if not force and TaskValidator.has_network_plan(task):
        error_message = f"Task {task_id} already has a network plan. Use force=true to regenerate."
        logger.error(error_message)
        raise InvalidStateException(error_message)
    
    # Generate network plan using the problem analyzer
    network_plan = await analyzer.generate_network_plan(task)
    
    # Update task with the generated network plan
    task.network_plan = network_plan
    task.state = TaskState.NETWORK_PLAN_GENERATED
    storage.save_task(task_id, task)

    # Save each stage individually
    if task.network_plan and task.network_plan.stages:
        for stage in task.network_plan.stages:
            storage.save_stage(task_id, stage)

    logger.info(f"Network plan generated and saved for task {task_id}")
    return network_plan 