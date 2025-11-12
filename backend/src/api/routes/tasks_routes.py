from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List, Optional, cast, AsyncGenerator, Dict, Any
import logging
import json
import asyncio
from pydantic import BaseModel

# Model imports
from src.model.task import Task, TaskState
from src.model.context import ContextSufficiencyResult, UserAnswers
from src.model.scope import TaskScope, DraftScope, ValidationScopeResult, ScopeValidationRequest, ScopeFormulationGroup
from src.model.ifr import IFR, Requirements
from src.model.planning import NetworkPlan, Stage
from src.model.work import Work
from src.model.executable_task import ExecutableTask
from src.model.subtask import Subtask
from src.schemas.chat import ChatRequest, ChatResponse

# Service imports
from src.services.problem_analyzer import ProblemAnalyzer
from src.services.file_storage_service import FileStorageService

# API utils imports
from src.api.deps import get_problem_analyzer, get_file_storage_service
from src.api.utils import api_error_handler, deserialize_task, validate_task_state, validate_task_network_plan, find_stage_by_id, find_work_package_by_id, find_executable_task_by_id, is_task_in_states

# Exception imports
from src.exceptions import (
    TaskNotFoundException,
    StageNotFoundException,
    WorkNotFoundException,
    ExecutableTaskNotFoundException,
    InvalidStateException,
    MissingComponentException,
    DeserializationException,
    ValidationException,
    ServerException
)

# Constants
from src.constants import (
    OP_SUBTASK_GENERATION,
    OP_TASK_GENERATION,
    OP_BATCH_TASK_GENERATION,
    OP_WORK_GENERATION,
    OP_BATCH_WORK_GENERATION,
    OP_BATCH_SUBTASK_GENERATION,
    OP_TASK_DELETION,
    SUCCESS_TASK_DELETED,
    OP_GET_QUERIES,
    OP_GET_TASK,
    OP_FORMULATE_TASK,
    OP_UPDATE_TASK,
    OP_SCOPE_VALIDATION,
    OP_IFR_GENERATION,
    OP_REQUIREMENTS_GENERATION,
    OP_NETWORK_PLAN_GENERATION,
    SUCCESS_ALL_TASKS_DELETED,
    ERROR_EMPTY_LIST,
    ERROR_PARTIAL_SUCCESS,
    ERROR_CONCURRENT_OPERATION,
    OP_CHAT,
)

# Import the chat agent
from src.ai_agents import stream_chat_response
from src.ai_agents.agent_tracker import get_tracker, _trackers

logger = logging.getLogger(__name__)

router = APIRouter()

# Define the request body model for editing context
class EditContextRequest(BaseModel):
    feedback: str

@router.delete("/", response_model=dict)
@api_error_handler(OP_TASK_DELETION)
async def delete_all_tasks(storage: FileStorageService = Depends(get_file_storage_service)):
    """Delete all tasks"""
    try:
        # Get all projects and delete them
        projects = storage.list_projects()
        deleted_count = 0
        for project in projects:
            success = storage.delete_project(project["id"])
            if success:
                deleted_count += 1

        logger.info(f"Deleted {deleted_count} out of {len(projects)} projects")
        return {"message": SUCCESS_ALL_TASKS_DELETED}
    except Exception as e:
        logger.error(f"Failed to delete all tasks: {e}")
        raise ServerException("Failed to delete all tasks")
 
@router.delete("/{task_id}")
@api_error_handler(OP_TASK_DELETION)
async def delete_task(
    task_id: str,
    storage: FileStorageService = Depends(get_file_storage_service)
):
    # Check if the project exists in file system
    project_dir = storage.base_dir / task_id
    if not project_dir.exists():
        from src.exceptions import TaskNotFoundException
        raise TaskNotFoundException(f"Task {task_id} not found")

    # Delete the entire project folder
    success = storage.delete_project(task_id)
    if not success:
        from src.exceptions import ServerException
        raise ServerException(f"Failed to delete task {task_id}")

    return {"message": SUCCESS_TASK_DELETED.format(task_id=task_id)}

@router.get("/{task_id}", response_model=Task)
@api_error_handler(OP_GET_TASK)
async def get_task(task_id: str, storage: FileStorageService = Depends(get_file_storage_service)):
    task = storage.load_task(task_id)
    if not task:
        from src.exceptions import TaskNotFoundException
        raise TaskNotFoundException(f"Task {task_id} not found")
    return task


@router.post("/{task_id}/context-questions", response_model=ContextSufficiencyResult)
@api_error_handler(OP_UPDATE_TASK)
async def update_task_context(
    task_id: str,
    context_answers: Optional[UserAnswers] = None,
    force: bool = False,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    storage: FileStorageService = Depends(get_file_storage_service)
):
    task = storage.load_task(task_id)
    if not task:
        raise HTTPException(404, detail=f"Task {task_id} not found")
    
    # Only check state if force is False
    if not force and is_task_in_states(task, [TaskState.CONTEXT_GATHERED]):
        error_message = f"Task is already in the context gathered state. Current state: {task.state}"
        logger.error(error_message)
        raise InvalidStateException(error_message)
    
    task.state = TaskState.CONTEXT_GATHERING
    
    # Handle the case where UserInteraction is provided but both query and answer are empty
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
    
@router.get("/{task_id}/formulate/{group}", response_model=List[ScopeFormulationGroup])
@api_error_handler(OP_FORMULATE_TASK)
async def formulate_task(
    task_id: str,
    group: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """Endpoint to explicitly trigger task formulation"""
    task = storage.load_task(task_id)
    if not task:
        raise TaskNotFoundException(f"Task {task_id} not found")
    
    if not is_task_in_states(task, [TaskState.CONTEXT_GATHERED, TaskState.TASK_FORMATION]):
        error_message = f"Task must be in CONTEXT_GATHERED or TASK_FORMATION state. Current state: {task.state}"
        logger.error(error_message)
        raise InvalidStateException(error_message)
        
    if task.scope:
        if group in task.scope.__dict__.keys():
            exist_group = getattr(task.scope, group)
            if exist_group:
                logger.info(f"Group {group} found in task scope")
                raise ValidationException(f"Group {group} already exists in task scope")
    
    result = await analyzer.define_scope_question(task, group)
    return result

@router.post("/{task_id}/formulate/{group}", response_model=dict)
@api_error_handler(OP_FORMULATE_TASK)
async def submit_formulation_answers(
    task_id: str,
    group: str,
    answers: UserAnswers,
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """Submit formulation answers for a specific group"""
    logger.info(f"Submitting formulation answers for task {task_id} and group {group}")
    logger.info(f"Answers: {answers.json()}")

    task = storage.load_task(task_id)
    if not task:
        raise HTTPException(404, detail=f"Task {task_id} not found")
    
    if not is_task_in_states(task, [TaskState.CONTEXT_GATHERED, TaskState.TASK_FORMATION]):
        error_message = f"Task must be in CONTEXT_GATHERED or TASK_FORMATION state. Current state: {task.state}"
        logger.error(error_message)
        raise InvalidStateException(error_message)
    
    # Update the task scope with formulation answers
    if not task.scope:
        task.scope = TaskScope()
    
    # Set the answers directly to the appropriate group as a list of UserAnswer objects
    setattr(task.scope, group, answers.answers)
    
    # Update task state
    task.state = TaskState.TASK_FORMATION
    
    # Save the updated task to the database
    storage.save_task(task_id, task)
    
    return {"message": "Formulation answers submitted successfully"}

@router.get("/{task_id}/draft-scope", response_model=DraftScope)
@api_error_handler(OP_SCOPE_VALIDATION)
async def get_draft_scope(
    task_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """Get the draft scope for a specific task"""
    task = storage.load_task(task_id)
    if not task:
        raise HTTPException(404, detail=f"Task {task_id} not found")
    
    if not is_task_in_states(task, [TaskState.TASK_FORMATION]):
        error_message = f"Task must be in TASK_FORMATION state. Current state: {task.state}"
        logger.error(error_message)
        raise InvalidStateException(error_message)
    
    # Generate the draft scope
    draft_scope = await analyzer.generate_draft_scope(task)
    
    # Save the draft scope to the database
    if not task.scope:
        task.scope = TaskScope()
        
    task.scope.validation_criteria = draft_scope.validation_criteria
    task.scope.scope = draft_scope.scope
    task.scope.status = "draft"
    storage.save_task(task_id, task)
    
    return draft_scope

@router.post("/{task_id}/validate-scope", response_model=ValidationScopeResult)
@api_error_handler(OP_SCOPE_VALIDATION)
async def validate_scope(
    task_id: str,
    request: ScopeValidationRequest,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """Validate the scope for a specific task"""
    task = storage.load_task(task_id)
    if not task:
        raise HTTPException(404, detail=f"Task {task_id} not found")
    
    if not is_task_in_states(task, [TaskState.TASK_FORMATION]):
        error_message = f"Task must be in TASK_FORMATION state. Current state: {task.state}"
        logger.error(error_message)
        raise InvalidStateException(error_message)
    
    # Validate the scope
    if not request.isApproved and not request.feedback:
        error_message = "Feedback is required when scope is not approved"
        logger.error(error_message)
        raise ValidationException(error_message)
    
    if not request.isApproved and request.feedback:
        validation_result = await analyzer.validate_scope(task, request.feedback)
        if task.scope and task.scope.scope:
            task.scope.scope = validation_result.updatedScope
            if task.scope.feedback:
                task.scope.feedback.append(request.feedback)
            else:
                task.scope.feedback = [request.feedback]

        storage.save_task(task_id, task)
        return validation_result
    
    # If scope is approved, update DB
    if task.scope and task.scope.scope:
        task.scope.status = "approved"
        storage.save_task(task_id, task)
        return ValidationScopeResult(updatedScope=task.scope.scope, changes=[])

@router.post("/{task_id}/ifr", response_model=IFR)
@api_error_handler(OP_IFR_GENERATION)
async def generate_ifr(
    task_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """Generate an ideal final result for a specific task"""
    task = storage.load_task(task_id)
    if not task:
        raise HTTPException(404, detail=f"Task {task_id} not found")
    
    if not is_task_in_states(task, [TaskState.TASK_FORMATION, TaskState.IFR_GENERATED]):
        error_message = f"Task must be in TASK_FORMATION or IFR_GENERATED state. Current state: {task.state}"
        logger.error(error_message)
        raise InvalidStateException(error_message)
    
    ifr = await analyzer.generate_IFR(task)
    task.ifr = ifr
    task.state = TaskState.IFR_GENERATED
    storage.save_task(task_id, task)
    return ifr

@router.post("/{task_id}/requirements", response_model=Requirements)
@api_error_handler(OP_REQUIREMENTS_GENERATION)
async def define_requirements(
    task_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """Define requirements for a specific task"""
    task = storage.load_task(task_id)
    if not task:
        raise HTTPException(404, detail=f"Task {task_id} not found")
    
    if not is_task_in_states(task, [TaskState.IFR_GENERATED]):
        error_message = f"Task must be in IFR_GENERATED state. Current state: {task.state}"
        logger.error(error_message)
        raise InvalidStateException(error_message)
    
    requirements = await analyzer.define_requirements(task)
    task.requirements = requirements
    task.state = TaskState.REQUIREMENTS_GENERATED
    storage.save_task(task_id, task)
    return requirements

@router.post("/{task_id}/network-plan", response_model=NetworkPlan)
@api_error_handler(OP_NETWORK_PLAN_GENERATION)
async def generate_network_plan(
    task_id: str,
    force: bool = False,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """Generate a network plan for a specific task"""
    task = storage.load_task(task_id)
    if not task:
        raise HTTPException(404, detail=f"Task {task_id} not found")
    
    if not is_task_in_states(task, [TaskState.REQUIREMENTS_GENERATED]) and not force:
        error_message = f"Task must be in REQUIREMENTS_GENERATED state. Current state: {task.state}"
        logger.error(error_message)
        raise InvalidStateException(error_message)
    
    network_plan = await analyzer.generate_network_plan(task)
    task.network_plan = network_plan
    task.state = TaskState.NETWORK_PLAN_GENERATED
    storage.save_task(task_id, task)

    # Save each stage individually
    if task.network_plan and task.network_plan.stages:
        for stage in task.network_plan.stages:
            storage.save_stage(task_id, stage)

    return network_plan
    
@router.post("/{task_id}/stages/{stage_id}/generate-work", response_model=List[Work])
@api_error_handler(OP_WORK_GENERATION)
async def generate_work_for_stage_endpoint(
    task_id: str,
    stage_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """
    Generates a list of Work packages for a specific Stage within a Task.
    The Task must have a Network Plan generated (state NETWORK_PLAN_GENERATED).
    """
    logger.info(f"Received request to generate work for Task {task_id}, Stage {stage_id}")

    task = storage.load_task(task_id)
    if not task:
        raise TaskNotFoundException(f"Task {task_id} not found")

    # Validate task state
    validate_task_state(task, TaskState.NETWORK_PLAN_GENERATED, task_id)
    validate_task_network_plan(task, task_id)

    # Call the analyzer method which handles finding the stage, calling AI, and updating DB
    generated_work = await analyzer.generate_stage_work(task, stage_id)
    return generated_work

@router.post("/{task_id}/stages/generate-work", response_model=NetworkPlan)
@api_error_handler(OP_BATCH_WORK_GENERATION)
async def generate_work_packages_for_all_stages(
    task_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """
    Generates a list of Work packages for all stages within a Task.
    The Task must have a Network Plan generated (state NETWORK_PLAN_GENERATED).
    """
    logger.info(f"Received request to generate work for Task {task_id}")

    task = storage.load_task(task_id)
    if not task:
        raise TaskNotFoundException(f"Task {task_id} not found")
    
    # Validate task state
    validate_task_state(task, TaskState.NETWORK_PLAN_GENERATED, task_id)
    validate_task_network_plan(task, task_id)
    
    # At this point we know network_plan is not None
    network_plan = cast('NetworkPlan', task.network_plan)
    
    # Generate work packages for all stages concurrently
    if not network_plan.stages:
        error_message = ERROR_EMPTY_LIST.format(list_name="stages")
        logger.error(error_message)
        raise ValidationException(error_message)
    
    # Create a list of coroutines, one for each stage
    stage_coroutines = [
        analyzer.generate_stage_work(task, stage.id)
        for stage in network_plan.stages
    ]
    
    try:
        # Execute all coroutines concurrently and wait for all to complete
        results = await asyncio.gather(*stage_coroutines, return_exceptions=True)
        
        # Check for any exceptions in the results
        failed_stages = []
        successful_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_stages.append((network_plan.stages[i].id, str(result)))
            else:
                successful_results.append(result)
        
        if failed_stages:
            error_message = ERROR_PARTIAL_SUCCESS.format(
                success_count=len(successful_results),
                total_count=len(results)
            )
            logger.error(f"{error_message}. Failed stages: {failed_stages}")
            raise ValidationException(error_message)
        
        # Log successful results
        for i, generated_work in enumerate(successful_results):
            stage_id = network_plan.stages[i].id
            logger.info(f"Generated work for Stage {stage_id}: {generated_work}")
        
        return network_plan
        
    except Exception as e:
        error_message = ERROR_CONCURRENT_OPERATION.format(operation="work generation")
        logger.error(f"{error_message}: {str(e)}")
        raise ValidationException(error_message)

@router.post("/{task_id}/stages/{stage_id}/work/{work_id}/generate-tasks", response_model=List[ExecutableTask])
@api_error_handler(OP_TASK_GENERATION)
async def generate_tasks_for_work_endpoint(
    task_id: str,
    stage_id: str,
    work_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """
    Generates a list of ExecutableTask units for a specific Work package within a Stage.
    The Task must have Work packages generated for the specified Stage.
    """
    logger.info(f"API endpoint called: Generate ExecutableTasks for Task {task_id}, Stage {stage_id}, Work {work_id}")

    task = storage.load_task(task_id)
    if not task:
        raise TaskNotFoundException(f"Task {task_id} not found")
    
    # Validate task state
    validate_task_state(task, TaskState.NETWORK_PLAN_GENERATED, task_id)
    validate_task_network_plan(task, task_id)

    generated_tasks = await analyzer.generate_tasks_for_work(task, stage_id, work_id)
    logger.info(f"Successfully generated {len(generated_tasks)} tasks for Work {work_id}.")
    return generated_tasks

@router.post("/{task_id}/stages/{stage_id}/work/{work_id}/tasks/{executable_task_id}/generate-subtasks", response_model=List[Subtask])
@api_error_handler(OP_SUBTASK_GENERATION)
async def generate_subtasks_for_task_endpoint(
    task_id: str,
    stage_id: str,
    work_id: str,
    executable_task_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """
    Generates a list of atomic Subtask units for a specific ExecutableTask.
    The Task must have the parent ExecutableTask generated.
    """
    logger.info(f"API endpoint called: Generate Subtasks for Task {task_id}, Stage {stage_id}, Work {work_id}, ExecutableTask {executable_task_id}")

    task = storage.load_task(task_id)
    if not task:
        raise TaskNotFoundException(f"Task {task_id} not found")
    
    # Validate task state and requirements
    validate_task_state(task, TaskState.NETWORK_PLAN_GENERATED, task_id)
    validate_task_network_plan(task, task_id)
    
    # Find the stage, work, and executable task using utility functions
    stage = find_stage_by_id(task, stage_id)
    work = find_work_package_by_id(stage, work_id)
    executable_task = find_executable_task_by_id(work, executable_task_id)

    generated_subtasks = await analyzer.generate_subtasks_for_executable_task(task, stage_id, work_id, executable_task_id)
    logger.info(f"Successfully generated {len(generated_subtasks)} subtasks for ExecutableTask {executable_task_id}.")
    return generated_subtasks

@router.post("/{task_id}/stages/{stage_id}/work/{work_id}/tasks/generate-subtasks", response_model=List[ExecutableTask])
@api_error_handler(OP_BATCH_SUBTASK_GENERATION)
async def generate_subtasks_for_all_tasks_endpoint(
    task_id: str,
    stage_id: str,
    work_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """
    Generates a list of atomic Subtask units for all ExecutableTasks in a Work package.
    The Task must have the parent ExecutableTask generated.
    """
    logger.info(f"API endpoint called: Generate Subtasks for all Tasks in Work {work_id} of Stage {stage_id} of Task {task_id}")

    task = storage.load_task(task_id)
    if not task:
        raise TaskNotFoundException(f"Task {task_id} not found")
    
    validate_task_state(task, TaskState.NETWORK_PLAN_GENERATED, task_id)
    validate_task_network_plan(task, task_id)
    
    # Find Stage and Work package using the utility functions
    stage = find_stage_by_id(task, stage_id)
    target_work = find_work_package_by_id(stage, work_id)
    
    # Validate that work has tasks
    if not target_work.tasks:
        error_message = ERROR_EMPTY_LIST.format(list_name="tasks")
        logger.error(error_message)
        raise ValidationException(error_message)
    
    try:
        # Create a list of coroutines, one for each executable task
        subtask_coroutines = [
            analyzer.generate_subtasks_for_executable_task(task, stage_id, work_id, executable_task.id)
            for executable_task in target_work.tasks
        ]
        
        # Execute all coroutines concurrently and wait for all to complete
        results = await asyncio.gather(*subtask_coroutines, return_exceptions=True)
        
        # Process results and check for errors
        failed_tasks_info = []
        successful_tasks_count = 0
        for i, result in enumerate(results):
            executable_task_id = target_work.tasks[i].id
            if isinstance(result, Exception):
                failed_tasks_info.append((executable_task_id, str(result)))
                logger.error(f"Subtask generation failed for Task {executable_task_id}: {str(result)}")
            else:
                # LINTER FIX: Use cast to assert the type before calling len()
                # We know it's List[Subtask] here because it's not an Exception
                logger.info(f"Successfully generated {len(cast(List[Subtask], result))} subtasks for ExecutableTask {executable_task_id}.")
                successful_tasks_count += 1

        if failed_tasks_info:
             error_message = ERROR_PARTIAL_SUCCESS.format(
                 success_count=successful_tasks_count,
                 total_count=len(results)
             )
             logger.error(f"{error_message}. Failed tasks: {failed_tasks_info}")
             raise ValidationException(f"{error_message}. Failed task IDs: {[item[0] for item in failed_tasks_info]}")

        # On success (even partial if not raising), the underlying task object is updated.
        # Return the tasks list from the work package which should reflect the updates.
        return target_work.tasks 
        
    except Exception as e:
        # Catch potential errors from asyncio.gather itself or ValidationException
        if isinstance(e, ValidationException):
             raise e # Re-raise validation exceptions from partial failure check
        error_message = ERROR_CONCURRENT_OPERATION.format(operation="batch subtask generation")
        logger.error(f"{error_message}: {str(e)}")
        raise ValidationException(error_message)

@router.post("/{task_id}/stages/{stage_id}/works/generate-tasks", response_model=List[Work])
@api_error_handler(OP_BATCH_TASK_GENERATION)
async def generate_tasks_for_all_works_endpoint(
    task_id: str,
    stage_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """
    Generates a list of ExecutableTask units for all Work packages within a Stage.
    The Task must have Work packages generated for the specified Stage.
    """
    logger.info(f"API endpoint called: Generate ExecutableTasks for all Works in Stage {stage_id} of Task {task_id}")

    task = storage.load_task(task_id)
    if not task:
        raise TaskNotFoundException(f"Task {task_id} not found")
    
    # Validate task state and requirements
    validate_task_state(task, TaskState.NETWORK_PLAN_GENERATED, task_id)
    validate_task_network_plan(task, task_id)
    
    # Find the Stage using the utility function
    target_stage = find_stage_by_id(task, stage_id)
    
    # Validate that stage has work packages
    if not target_stage.work_packages:
        error_message = ERROR_EMPTY_LIST.format(list_name="work packages")
        logger.error(error_message)
        raise ValidationException(error_message)
    
    try:
        # Create a list of coroutines, one for each work package
        work_coroutines = [
            analyzer.generate_tasks_for_work(task, stage_id, work.id)
            for work in target_stage.work_packages
        ]
        
        # Execute all coroutines concurrently and wait for all to complete
        results = await asyncio.gather(*work_coroutines, return_exceptions=True)
        
        # Process results and check for errors
        failed_works_info = []
        successful_works_count = 0
        for i, result in enumerate(results):
             work_id = target_stage.work_packages[i].id
             if isinstance(result, Exception):
                 failed_works_info.append((work_id, str(result)))
                 logger.error(f"Task generation failed for Work {work_id}: {str(result)}")
             else:
                 # LINTER FIX: Use cast to assert the type before calling len()
                 # We know it's List[ExecutableTask] here
                 logger.info(f"Successfully generated {len(cast(List[ExecutableTask], result))} tasks for Work {work_id}.")
                 successful_works_count += 1

        if failed_works_info:
             error_message = ERROR_PARTIAL_SUCCESS.format(
                 success_count=successful_works_count,
                 total_count=len(results)
             )
             logger.error(f"{error_message}. Failed works: {failed_works_info}")
             raise ValidationException(f"{error_message}. Failed work IDs: {[item[0] for item in failed_works_info]}")

        # On success, the underlying stage object in task is updated.
        # Return the work packages list from the stage.
        return target_stage.work_packages
        
    except Exception as e:
         # Catch potential errors from asyncio.gather itself or ValidationException
        if isinstance(e, ValidationException):
            raise e # Re-raise validation exceptions from partial failure check
        error_message = ERROR_CONCURRENT_OPERATION.format(operation="batch task generation for stage")
        logger.error(f"{error_message}: {str(e)}")
        raise ValidationException(error_message)

@router.post("/{task_id}/stages/generate-all-tasks", response_model=NetworkPlan)
@api_error_handler(OP_BATCH_TASK_GENERATION)
async def generate_tasks_for_all_stages_endpoint(
    task_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """
    Generates ExecutableTask units for ALL Work packages across ALL Stages within a Task.
    Processes stages sequentially, but work packages within each stage concurrently.
    The Task must have Work packages generated for all relevant Stages.
    """
    logger.info(f"API endpoint called: Generate ExecutableTasks for ALL Works in ALL Stages of Task {task_id}")

    task = storage.load_task(task_id)
    if not task:
        raise TaskNotFoundException(f"Task {task_id} not found")
    
    # Validate task state and requirements
    validate_task_state(task, TaskState.NETWORK_PLAN_GENERATED, task_id)
    validate_task_network_plan(task, task_id)
    network_plan = cast('NetworkPlan', task.network_plan) # Safe cast after validation

    if not network_plan.stages:
        logger.warning(f"Task {task_id}: No stages found. Nothing to generate.")
        return network_plan

    overall_failures = [] # Collect failures across all stages: list of (stage_id, work_id, error_str)

    # Iterate through stages sequentially
    for stage in network_plan.stages:
        stage_id = stage.id
        logger.info(f"Task {task_id}, Stage {stage_id}: Starting task generation for its work packages.")

        if not stage.work_packages:
            logger.warning(f"Task {task_id}, Stage {stage_id}: No work packages found, skipping task generation.")
            continue # Move to the next stage

        # Prepare coroutines for work packages within the current stage
        stage_work_coroutines = []
        stage_work_package_refs = [] # Keep track of work_id for error reporting within this stage
        for work in stage.work_packages:
            # Ensure work package has an ID
            if not work.id:
                 logger.error(f"Task {task_id}, Stage {stage_id}: Found work package without ID, skipping.")
                 overall_failures.append((stage_id, "<missing_id>", "Work package missing ID"))
                 continue
            stage_work_coroutines.append(analyzer.generate_tasks_for_work(task, stage_id, work.id))
            stage_work_package_refs.append(work.id)
        
        if not stage_work_coroutines:
            # This might happen if all work packages in a stage lacked IDs
            logger.warning(f"Task {task_id}, Stage {stage_id}: No valid work package coroutines generated.")
            continue

        try:
            # Execute task generation concurrently for work packages *within this stage*
            results = await asyncio.gather(*stage_work_coroutines, return_exceptions=True)
            
            # Process results for the current stage
            stage_successful_count = 0
            for i, result in enumerate(results):
                # Use the ref list which only contains valid work IDs
                work_id = stage_work_package_refs[i] 
                if isinstance(result, Exception):
                    error_str = str(result)
                    overall_failures.append((stage_id, work_id, error_str))
                    logger.error(f"Task {task_id}, Stage {stage_id}, Work {work_id}: Failed task generation - {error_str}")
                else:
                    # LINTER FIX: Use cast to assert the type before calling len()
                    # We know it's List[ExecutableTask] here
                    stage_successful_count += 1
                    logger.info(f"Task {task_id}, Stage {stage_id}, Work {work_id}: Successfully generated {len(cast(List[ExecutableTask], result))} tasks.")
            
            logger.info(f"Task {task_id}, Stage {stage_id}: Finished processing. {stage_successful_count}/{len(stage_work_coroutines)} work packages succeeded.")

        except Exception as e:
            # Catch errors from asyncio.gather itself or other unexpected issues during stage processing
            error_str = f"Unexpected error during task generation for stage {stage_id}: {str(e)}"
            logger.error(f"Task {task_id}: {error_str}")
            # Add a general failure marker for the stage if gather fails unexpectedly
            overall_failures.append((stage_id, "<stage-error>", error_str))
            # Continue to the next stage despite the error in this one

    # After processing all stages, check if any failures occurred
    if overall_failures:
        error_message = f"Task {task_id}: Task generation completed with errors. {len(overall_failures)} work packages/stages failed."
        logger.error(f"{error_message} Details: {overall_failures}")
        # Raise an exception summarizing the failures
        raise ValidationException(f"{error_message} See logs for details on failed stage/work packages.")

    logger.info(f"Task {task_id}: Successfully generated tasks for all applicable work packages across all stages.")
    # The task object has been updated by the analyzer calls during the loops
    return task.network_plan

@router.post("/{task_id}/edit-context", response_model=Task)
@api_error_handler(OP_UPDATE_TASK)
async def edit_context_summary_endpoint(
    task_id: str,
    request: EditContextRequest,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """Endpoint to edit the context summary based on user feedback."""
    task = storage.load_task(task_id)
    if not task:
        raise TaskNotFoundException(f"Task {task_id} not found")
    
    # Check if the task is in a state where context editing is allowed
    # Typically after context is gathered or potentially after subsequent steps like scope definition
    # Adjust these states as needed for your specific workflow
    if not is_task_in_states(task, [TaskState.CONTEXT_GATHERED, TaskState.TASK_FORMATION]):
        error_message = f"Context editing is not allowed in the current task state: {task.state}"
        logger.error(error_message)
        raise InvalidStateException(error_message)
        
    logger.info(f"Editing context for task {task_id} with feedback: {request.feedback[:100]}...")
    
    # Call the new method in ProblemAnalyzer
    updated_task = await analyzer.edit_context_summary(task, request.feedback)
    
    # The updated_task should already be saved in the DB by the analyzer service
    # but we return it to the frontend
    return updated_task

# =============== Chat Endpoints ===============

@router.post("/{task_id}/chat", response_model=ChatResponse)
@api_error_handler(OP_CHAT)
async def chat_with_task_assistant(
    task_id: str,
    chat_request: ChatRequest,
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """
    Chat with an AI assistant about the task (non-streaming version)
    """
    # Get the task data
    task = storage.load_task(task_id)
    if not task:
        raise TaskNotFoundException(f"Task {task_id} not found")
    
    # Collect the full response
    full_response = ""
    async for chunk in stream_chat_response(task, chat_request.message, chat_request.message_history):
        full_response += chunk
    
    return ChatResponse(response=full_response, task_id=task_id)

@router.post("/{task_id}/chat/stream")
@api_error_handler(OP_CHAT)
async def stream_chat_with_task_assistant(
    task_id: str,
    chat_request: ChatRequest,
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """
    Chat with an AI assistant about the task (streaming version)
    """
    async def event_generator():
        """Generate events for server-sent events (SSE)"""
        try:
            # Get the task data
            task = storage.load_task(task_id)
            if not task:
                raise TaskNotFoundException(f"Task {task_id} not found")
            
            # Pass the session_id from the request to stream_chat_response
            session_id = chat_request.session_id
            logger.info(f"Using session_id: {session_id} for chat with task {task_id}")
            
            async for chunk in stream_chat_response(
                task, 
                chat_request.message, 
                chat_request.message_history,
                session_id=session_id
            ):
                if chunk:
                    # Ensure chunk is a string before JSON serialization
                    chunk_str = str(chunk)
                    # Format as SSE
                    yield f"data: {json.dumps({'chunk': chunk_str})}\n\n"
            
            # Send completion event
            yield f"data: {json.dumps({'done': True})}\n\n"
        
        except TaskNotFoundException as e:
            logger.error(f"Task not found: {str(e)}")
            yield f"data: {json.dumps({'error': f'Task not found: {task_id}'})}\n\n"
        except DeserializationException as e:
            logger.error(f"Error deserializing task: {str(e)}")
            yield f"data: {json.dumps({'error': f'Error loading task data: {str(e)}'})}\n\n"
        except Exception as e:
            logger.error(f"Error in streaming chat: {str(e)}")
            yield f"data: {json.dumps({'error': f'Error: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering for nginx
        }
    )

@router.post("/{task_id}/chat/reset")
@api_error_handler(OP_CHAT)
async def reset_chat_session(
    task_id: str
):
    """
    Reset the chat session for a specific task
    """
    try:
        # Import the session service from chat_agent
        from src.ai_agents.chat_agent import _session_service
        from src.core.config import settings
        
        # Generate the session ID that would be used for this task
        session_id = f"session_{task_id}"
        user_id = task_id
        
        # Try to delete the existing session properly
        try:
            # First check if session exists
            existing_session = _session_service.get_session(
                app_name=settings.PROJECT_NAME,
                user_id=user_id,
                session_id=session_id
            )
            
            # If session exists, delete it properly
            if existing_session:
                # Session service methods are synchronous, not async
                _session_service.delete_session(
                    app_name=settings.PROJECT_NAME,
                    user_id=user_id,
                    session_id=session_id
                )
                logger.info(f"Successfully deleted session: {session_id}")
            
        except Exception as e:
            # Session doesn't exist or error getting it, which is fine for reset
            logger.info(f"Session {session_id} doesn't exist or error getting it: {e}")
        
        # Create a fresh session using synchronous method
        try:
            new_session = _session_service.create_session(
                app_name=settings.PROJECT_NAME,
                user_id=user_id,
                session_id=session_id,
                state={}
            )
            logger.info(f"Created fresh session: {new_session.id}")
            
            return {
                "success": True,
                "message": "Chat session has been reset successfully",
                "session_id": session_id
            }
            
        except Exception as create_error:
            logger.error(f"Failed to create new session after reset: {create_error}")
            return {
                "success": False,
                "message": "Failed to create new session after reset. Please try again."
            }
            
    except Exception as e:
        logger.error(f"Error resetting chat session for task {task_id}: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to reset chat session: {str(e)}"
        }

# ========================================
# Status Update Endpoints
# ========================================

class SubtaskStatusUpdateRequest(BaseModel):
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
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """
    Update the status of a specific subtask.
    
    Args:
        task_id: The task ID containing the subtask
        subtask_reference: Subtask reference like "S1_W1_ET1_ST1" or subtask ID
        request: Status update details
        
    Returns:
        Updated status information
    """
    logger.info(f"API call to update subtask {subtask_reference} status to {request.status} in task {task_id}")
    
    # Validate status value
    valid_statuses = ["Pending", "In Progress", "Completed", "Failed", "Cancelled", "Waiting"]
    if request.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{request.status}'. Must be one of: {valid_statuses}"
        )
    
    # Load the task
    task = storage.load_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # Convert task to dict for manipulation
    task_dict = task.to_dict()

    # Find and update the subtask (simplified version of database logic)
    update_result = _find_and_update_subtask_in_dict(
        task_dict, subtask_reference, request.status,
        request.result, request.error_message, request.started_at, request.completed_at
    )

    if not update_result["found"]:
        raise HTTPException(status_code=404, detail=f"Subtask {subtask_reference} not found in task {task_id}")

    # Update the task's updated_at timestamp
    from datetime import datetime
    task_dict['updated_at'] = datetime.now().isoformat()

    # Create updated task object
    updated_task = Task(**task_dict)

    # Save back to storage
    storage.save_task(task_id, updated_task)

    result = {
        "success": True,
        "task_id": task_id,
        "subtask_reference": subtask_reference,
        "old_status": update_result["old_status"],
        "new_status": request.status,
        "updated_fields": update_result["updated_fields"],
        "message": f"Subtask {subtask_reference} status updated from {update_result['old_status']} to {request.status}"
    }
    
    if not result["success"]:
        if "not found" in result.get("error", "").lower():
            raise HTTPException(status_code=404, detail=result["error"])
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.get("/{task_id}/subtasks/{subtask_reference}/status")
@api_error_handler("OP_GET_SUBTASK_STATUS")
async def get_subtask_status(
    task_id: str,
    subtask_reference: str,
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """
    Get the current status and details of a specific subtask.

    Args:
        task_id: The task ID containing the subtask
        subtask_reference: Subtask reference like "S1_W1_ET1_ST1" or subtask ID

    Returns:
        Subtask status and details
    """
    logger.info(f"API call to get subtask {subtask_reference} status in task {task_id}")

    # Load the task
    task = storage.load_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # Convert task to dict for searching
    task_dict = task.to_dict()

    # Find the subtask
    subtask_info = _find_subtask_in_dict(task_dict, subtask_reference)

    if not subtask_info["found"]:
        raise HTTPException(status_code=404, detail=f"Subtask {subtask_reference} not found in task {task_id}")

    return {
        "success": True,
        "task_id": task_id,
        "subtask": subtask_info["subtask"]
    }

@router.post("/{task_id}/subtasks/{subtask_reference}/complete")
@api_error_handler("OP_COMPLETE_SUBTASK")
async def complete_subtask(
    task_id: str,
    subtask_reference: str,
    result_text: str = "Task completed successfully",
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """
    Mark a subtask as completed with a result.
    Convenience endpoint that sets status to "Completed" with proper timestamps.
    """
    logger.info(f"API call to complete subtask {subtask_reference} in task {task_id}")

    # Load the task
    task = storage.load_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # Convert task to dict for manipulation
    task_dict = task.to_dict()

    from datetime import datetime
    current_time = datetime.now().isoformat()

    # Find and update the subtask
    update_result = _find_and_update_subtask_in_dict(
        task_dict, subtask_reference, "Completed",
        result_text, None, None, current_time
    )

    if not update_result["found"]:
        raise HTTPException(status_code=404, detail=f"Subtask {subtask_reference} not found in task {task_id}")

    # Update the task's updated_at timestamp
    task_dict['updated_at'] = current_time

    # Create updated task object
    updated_task = Task(**task_dict)

    # Save back to storage
    storage.save_task(task_id, updated_task)

    update_result = {
        "success": True,
        "task_id": task_id,
        "subtask_reference": subtask_reference,
        "old_status": update_result["old_status"],
        "new_status": "Completed",
        "updated_fields": update_result["updated_fields"],
        "message": f"Subtask {subtask_reference} status updated from {update_result['old_status']} to Completed"
    }
    
    if not update_result["success"]:
        if "not found" in update_result.get("error", "").lower():
            raise HTTPException(status_code=404, detail=update_result["error"])
        else:
            raise HTTPException(status_code=500, detail=update_result["error"])
    
    return update_result

@router.post("/{task_id}/subtasks/{subtask_reference}/fail")
@api_error_handler("OP_FAIL_SUBTASK")
async def fail_subtask(
    task_id: str,
    subtask_reference: str,
    error_message: str = "Task failed",
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """
    Mark a subtask as failed with an error message.
    Convenience endpoint that sets status to "Failed" with proper timestamps.
    """
    logger.info(f"API call to fail subtask {subtask_reference} in task {task_id}")

    # Load the task
    task = storage.load_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # Convert task to dict for manipulation
    task_dict = task.to_dict()

    from datetime import datetime
    current_time = datetime.now().isoformat()

    # Find and update the subtask
    update_result = _find_and_update_subtask_in_dict(
        task_dict, subtask_reference, "Failed",
        None, error_message, None, current_time
    )

    if not update_result["found"]:
        raise HTTPException(status_code=404, detail=f"Subtask {subtask_reference} not found in task {task_id}")

    # Update the task's updated_at timestamp
    task_dict['updated_at'] = current_time

    # Create updated task object
    updated_task = Task(**task_dict)

    # Save back to storage
    storage.save_task(task_id, updated_task)

    update_result = {
        "success": True,
        "task_id": task_id,
        "subtask_reference": subtask_reference,
        "old_status": update_result["old_status"],
        "new_status": "Failed",
        "updated_fields": update_result["updated_fields"],
        "message": f"Subtask {subtask_reference} status updated from {update_result['old_status']} to Failed"
    }
    
    if not update_result["success"]:
        if "not found" in update_result.get("error", "").lower():
            raise HTTPException(status_code=404, detail=update_result["error"])
        else:
            raise HTTPException(status_code=500, detail=update_result["error"])
    
    return update_result

@router.get("/{task_id}/trace")
async def get_agent_trace(task_id: str, session_id: Optional[str] = None) -> JSONResponse:
    """
    Get detailed agent execution trace for a task.
    Shows what agents were used, what tools were called, and execution flow.
    """
    try:
        # Find the tracker
        tracker = None
        search_session_id = session_id or f"session_{task_id}"
        
        # Try to find exact match first
        key = f"{task_id}_{search_session_id}"
        if key in _trackers:
            tracker = _trackers[key]
        else:
            # Try to find any tracker for this task
            for tracker_key in _trackers:
                if tracker_key.startswith(f"{task_id}_"):
                    tracker = _trackers[tracker_key]
                    break
        
        if not tracker:
            return JSONResponse(
                status_code=404,
                content={
                    "error": "No execution trace found for this task",
                    "task_id": task_id,
                    "session_id": search_session_id,
                    "available_trackers": list(_trackers.keys())
                }
            )
        
        # Return detailed trace information
        trace_data = {
            "task_id": task_id,
            "session_id": search_session_id,
            "summary": tracker.get_summary(),
            "formatted_trace": tracker.format_trace(),
            "agent_transfers": [
                {
                    "timestamp": transfer.timestamp,
                    "from_agent": transfer.from_agent,
                    "to_agent": transfer.to_agent,
                    "reason": transfer.reason,
                    "confidence_score": transfer.confidence_score,
                    "context": transfer.context
                }
                for transfer in tracker.agent_transfers
            ],
            "tool_calls": [
                {
                    "timestamp": call.timestamp,
                    "tool_name": call.tool_name,
                    "parameters": call.parameters,
                    "success": call.success,
                    "error_message": call.error_message,
                    "execution_time_ms": call.execution_time_ms,
                    "result_preview": call.result[:100] + "..." if call.result and len(call.result) > 100 else call.result
                }
                for call in tracker.tool_calls
            ],
            "activities": [
                {
                    "timestamp": activity.timestamp,
                    "agent_name": activity.agent_name,
                    "action_type": activity.action_type,
                    "description": activity.description,
                    "success": activity.success,
                    "error_message": activity.error_message,
                    "details": activity.details
                }
                for activity in tracker.activities
            ]
        }
        
        return JSONResponse(content=trace_data)
        
    except Exception as e:
        logger.error(f"Error getting agent trace: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get agent trace: {str(e)}"}
        )


# Helper functions for subtask management
def _find_and_update_subtask_in_dict(task_json: Dict[str, Any], subtask_reference: str,
                                    status: str, result: Optional[str] = None, error_message: Optional[str] = None,
                                    started_at: Optional[str] = None, completed_at: Optional[str] = None) -> Dict[str, Any]:
    """
    Find and update a subtask within the task JSON structure.
    Handles both subtask IDs and references like "S1_W1_ET1_ST1".
    """
    from datetime import datetime

    network_plan = task_json.get('network_plan', {})
    stages = network_plan.get('stages', [])

    for stage in stages:
        work_packages = stage.get('work_packages', [])
        for work in work_packages:
            executable_tasks = work.get('tasks', [])
            for exec_task in executable_tasks:
                subtasks = exec_task.get('subtasks', [])
                for subtask in subtasks:
                    # Check if this is the target subtask (by ID or reference)
                    subtask_id = subtask.get('id', '')
                    subtask_matches = (
                        subtask_id == subtask_reference or
                        subtask_reference in subtask_id or
                        _matches_subtask_reference_in_dict(stage, work, exec_task, subtask, subtask_reference)
                    )

                    if subtask_matches:
                        old_status = subtask.get('status', 'Pending')
                        updated_fields = []

                        # Update status
                        subtask['status'] = status
                        updated_fields.append('status')

                        # Update timestamps and fields based on status
                        current_time = datetime.now().isoformat()

                        if status == "In Progress":
                            if not subtask.get('started_at') or started_at:
                                subtask['started_at'] = started_at or current_time
                                updated_fields.append('started_at')
                            # Clear completion fields
                            subtask.pop('completed_at', None)
                            subtask.pop('result', None)
                            subtask.pop('error_message', None)

                        elif status in ["Completed", "Failed", "Cancelled"]:
                            if not subtask.get('completed_at') or completed_at:
                                subtask['completed_at'] = completed_at or current_time
                                updated_fields.append('completed_at')

                            if status == "Completed" and result is not None:
                                subtask['result'] = result
                                updated_fields.append('result')
                                subtask.pop('error_message', None)  # Clear error on success

                            elif status == "Failed" and error_message is not None:
                                subtask['error_message'] = error_message
                                updated_fields.append('error_message')
                                subtask.pop('result', None)  # Clear result on failure

                        # Update started_at if provided
                        if started_at and status != "In Progress":
                            subtask['started_at'] = started_at
                            updated_fields.append('started_at')

                        return {
                            "found": True,
                            "old_status": old_status,
                            "updated_fields": updated_fields,
                            "subtask_id": subtask_id
                        }

    return {"found": False}


def _find_subtask_in_dict(task_json: Dict[str, Any], subtask_reference: str) -> Dict[str, Any]:
    """Find and return complete subtask information."""
    network_plan = task_json.get('network_plan', {})
    stages = network_plan.get('stages', [])

    for stage in stages:
        work_packages = stage.get('work_packages', [])
        for work in work_packages:
            executable_tasks = work.get('tasks', [])
            for exec_task in executable_tasks:
                subtasks = exec_task.get('subtasks', [])
                for subtask in subtasks:
                    subtask_id = subtask.get('id', '')
                    if (subtask_id == subtask_reference or
                        subtask_reference in subtask_id or
                        _matches_subtask_reference_in_dict(stage, work, exec_task, subtask, subtask_reference)):

                        return {
                            "found": True,
                            "subtask": subtask,
                            "stage_id": stage.get('id'),
                            "work_id": work.get('id'),
                            "exec_task_id": exec_task.get('id')
                        }

    return {"found": False}


def _matches_subtask_reference_in_dict(stage: Dict, work: Dict, exec_task: Dict, subtask: Dict, reference: str) -> bool:
    """
    Check if a subtask matches a reference pattern like "S1_W1_ET1_ST1".
    """
    if '_' not in reference:
        return False

    try:
        parts = reference.split('_')
        if len(parts) != 4:
            return False

        stage_ref, work_ref, exec_ref, subtask_ref = parts

        # Extract numbers from IDs
        stage_match = stage.get('id', '').replace('S', '') == stage_ref.replace('S', '')
        work_match = work.get('id', '').endswith(work_ref) or work_ref in work.get('id', '')
        exec_match = exec_ref in exec_task.get('id', '') or exec_task.get('id', '').endswith(exec_ref)

        # For subtasks, check both position-based and ID-based matching
        subtask_sequence = subtask.get('sequence_order', -1)
        subtask_num = subtask_ref.replace('ST', '')

        # Try to match by sequence (ST1 = sequence 0, ST2 = sequence 1, etc.)
        try:
            expected_sequence = int(subtask_num) - 1
            sequence_match = subtask_sequence == expected_sequence
        except:
            sequence_match = False

        id_match = subtask_ref in subtask.get('id', '')

        return stage_match and work_match and exec_match and (sequence_match or id_match)
    except:
        return False
