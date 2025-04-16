from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional, cast, AsyncGenerator
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
from src.services.database_service import DatabaseService

# API utils imports
from src.api.deps import get_problem_analyzer, get_db_service
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

logger = logging.getLogger(__name__)

router = APIRouter()

# Define the request body model for editing context
class EditContextRequest(BaseModel):
    feedback: str

@router.delete("/", response_model=dict)
@api_error_handler(OP_TASK_DELETION)
async def delete_all_tasks(db: DatabaseService = Depends(get_db_service)):
    """Delete all tasks"""
    try:
        db.delete_all_tasks()
        return {"message": SUCCESS_ALL_TASKS_DELETED}
    except Exception as e:
        logger.error(f"Failed to delete all tasks: {e}")
        raise ServerException("Failed to delete all tasks")
 
@router.delete("/{task_id}")
@api_error_handler(OP_TASK_DELETION)
async def delete_task(
    task_id: str,
    db: DatabaseService = Depends(get_db_service)
):
    # We first check if the task exists by trying to deserialize it
    task_data = db.fetch_task_by_id(task_id)
    deserialize_task(task_data, task_id)  # This will raise an appropriate exception if the task doesn't exist
    
    # If we get here, the task exists, so we can delete it
    success = db.delete_task_by_id(task_id)
    if not success:
        # This should rarely happen since we already confirmed the task exists
        from src.exceptions import ServerException
        raise ServerException(f"Failed to delete task {task_id}")
    
    return {"message": SUCCESS_TASK_DELETED.format(task_id=task_id)}

@router.get("/{task_id}", response_model=Task)
@api_error_handler(OP_GET_TASK)
async def get_task(task_id: str, db: DatabaseService = Depends(get_db_service)):
    task_data = db.fetch_task_by_id(task_id)
    return deserialize_task(task_data, task_id)


@router.post("/{task_id}/context-questions", response_model=ContextSufficiencyResult)
@api_error_handler(OP_UPDATE_TASK)
async def update_task_context(
    task_id: str, 
    context_answers: Optional[UserAnswers] = None, 
    force: bool = False,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer), 
    db: DatabaseService = Depends(get_db_service)
):
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
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
        db.updated_task(task)
        return await analyzer.clarify_context(task)
    
@router.get("/{task_id}/formulate/{group}", response_model=List[ScopeFormulationGroup])
@api_error_handler(OP_FORMULATE_TASK)
async def formulate_task(
    task_id: str,
    group: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
):
    """Endpoint to explicitly trigger task formulation"""
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
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
    db: DatabaseService = Depends(get_db_service)
):
    """Submit formulation answers for a specific group"""
    logger.info(f"Submitting formulation answers for task {task_id} and group {group}")
    logger.info(f"Answers: {answers.json()}")
    
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
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
    db.updated_task(task)
    
    return {"message": "Formulation answers submitted successfully"}

@router.get("/{task_id}/draft-scope", response_model=DraftScope)
@api_error_handler(OP_SCOPE_VALIDATION)
async def get_draft_scope(
    task_id: str, 
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer), 
    db: DatabaseService = Depends(get_db_service)
):
    """Get the draft scope for a specific task"""
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
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
    db.updated_task(task)
    
    return draft_scope

@router.post("/{task_id}/validate-scope", response_model=ValidationScopeResult)
@api_error_handler(OP_SCOPE_VALIDATION)
async def validate_scope(
    task_id: str,
    request: ScopeValidationRequest,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
):
    """Validate the scope for a specific task"""
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
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
            
        db.updated_task(task)
        return validation_result
    
    # If scope is approved, update DB
    if task.scope and task.scope.scope:
        task.scope.status = "approved"
        db.updated_task(task)
        return ValidationScopeResult(updatedScope=task.scope.scope, changes=[])

@router.post("/{task_id}/ifr", response_model=IFR)
@api_error_handler(OP_IFR_GENERATION)
async def generate_ifr(
    task_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
):
    """Generate an ideal final result for a specific task"""
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    if not is_task_in_states(task, [TaskState.TASK_FORMATION, TaskState.IFR_GENERATED]):
        error_message = f"Task must be in TASK_FORMATION or IFR_GENERATED state. Current state: {task.state}"
        logger.error(error_message)
        raise InvalidStateException(error_message)
    
    ifr = await analyzer.generate_IFR(task)
    task.ifr = ifr
    task.state = TaskState.IFR_GENERATED
    db.updated_task(task)
    return ifr

@router.post("/{task_id}/requirements", response_model=Requirements)
@api_error_handler(OP_REQUIREMENTS_GENERATION)
async def define_requirements(
    task_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
):
    """Define requirements for a specific task"""
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    if not is_task_in_states(task, [TaskState.IFR_GENERATED]):
        error_message = f"Task must be in IFR_GENERATED state. Current state: {task.state}"
        logger.error(error_message)
        raise InvalidStateException(error_message)
    
    requirements = await analyzer.define_requirements(task)
    task.requirements = requirements
    task.state = TaskState.REQUIREMENTS_GENERATED
    db.updated_task(task)
    return requirements

@router.post("/{task_id}/network-plan", response_model=NetworkPlan)
@api_error_handler(OP_NETWORK_PLAN_GENERATION)
async def generate_network_plan(
    task_id: str,
    force: bool = False,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
):
    """Generate a network plan for a specific task"""
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
    if not is_task_in_states(task, [TaskState.REQUIREMENTS_GENERATED]) and not force:
        error_message = f"Task must be in REQUIREMENTS_GENERATED state. Current state: {task.state}"
        logger.error(error_message)
        raise InvalidStateException(error_message)
    
    network_plan = await analyzer.generate_network_plan(task)
    task.network_plan = network_plan
    task.state = TaskState.NETWORK_PLAN_GENERATED
    db.updated_task(task)
    return network_plan
    
@router.post("/{task_id}/stages/{stage_id}/generate-work", response_model=List[Work])
@api_error_handler(OP_WORK_GENERATION)
async def generate_work_for_stage_endpoint(
    task_id: str,
    stage_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
):
    """
    Generates a list of Work packages for a specific Stage within a Task.
    The Task must have a Network Plan generated (state NETWORK_PLAN_GENERATED).
    """
    logger.info(f"Received request to generate work for Task {task_id}, Stage {stage_id}")
    
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)

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
    db: DatabaseService = Depends(get_db_service)
):
    """
    Generates a list of Work packages for all stages within a Task.
    The Task must have a Network Plan generated (state NETWORK_PLAN_GENERATED).
    """
    logger.info(f"Received request to generate work for Task {task_id}")
    
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
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
    db: DatabaseService = Depends(get_db_service) # Analyzer already depends on DB
):
    """
    Generates a list of ExecutableTask units for a specific Work package within a Stage.
    The Task must have Work packages generated for the specified Stage.
    """
    logger.info(f"API endpoint called: Generate ExecutableTasks for Task {task_id}, Stage {stage_id}, Work {work_id}")

    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
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
    db: DatabaseService = Depends(get_db_service)
):
    """
    Generates a list of atomic Subtask units for a specific ExecutableTask.
    The Task must have the parent ExecutableTask generated.
    """
    logger.info(f"API endpoint called: Generate Subtasks for Task {task_id}, Stage {stage_id}, Work {work_id}, ExecutableTask {executable_task_id}")

    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
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
    db: DatabaseService = Depends(get_db_service)
):
    """
    Generates a list of atomic Subtask units for all ExecutableTasks in a Work package.
    The Task must have the parent ExecutableTask generated.
    """
    logger.info(f"API endpoint called: Generate Subtasks for all Tasks in Work {work_id} of Stage {stage_id} of Task {task_id}")
    
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
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
    db: DatabaseService = Depends(get_db_service)
):
    """
    Generates a list of ExecutableTask units for all Work packages within a Stage.
    The Task must have Work packages generated for the specified Stage.
    """
    logger.info(f"API endpoint called: Generate ExecutableTasks for all Works in Stage {stage_id} of Task {task_id}")

    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
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
    db: DatabaseService = Depends(get_db_service)
):
    """
    Generates ExecutableTask units for ALL Work packages across ALL Stages within a Task.
    Processes stages sequentially, but work packages within each stage concurrently.
    The Task must have Work packages generated for all relevant Stages.
    """
    logger.info(f"API endpoint called: Generate ExecutableTasks for ALL Works in ALL Stages of Task {task_id}")

    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
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
    db: DatabaseService = Depends(get_db_service)
):
    """Endpoint to edit the context summary based on user feedback."""
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
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
    db: DatabaseService = Depends(get_db_service)
):
    """
    Chat with an AI assistant about the task (non-streaming version)
    """
    # Get the task data
    task_data = db.fetch_task_by_id(task_id)
    task = deserialize_task(task_data, task_id)
    
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
    db: DatabaseService = Depends(get_db_service)
):
    """
    Chat with an AI assistant about the task (streaming version)
    """
    async def event_generator():
        """Generate events for server-sent events (SSE)"""
        try:
            # Get the task data
            task_data = db.fetch_task_by_id(task_id)
            task = deserialize_task(task_data, task_id)
            
            async for chunk in stream_chat_response(task, chat_request.message, chat_request.message_history):
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
