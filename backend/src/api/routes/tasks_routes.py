from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, cast
import logging
import json
import asyncio

# Model imports
from src.model.task import Task, TaskState
from src.model.context import ContextSufficiencyResult, UserAnswers
from src.model.scope import TaskScope, DraftScope, ValidationScopeResult, ScopeValidationRequest, ScopeFormulationGroup
from src.model.ifr import IFR, Requirements
from src.model.planning import NetworkPlan, Stage
from src.model.work import Work
from src.model.executable_task import ExecutableTask
from src.model.subtask import Subtask

# Service imports
from src.services.problem_analyzer import ProblemAnalyzer
from src.services.database_service import DatabaseService

# API utils imports
from src.api.deps import get_problem_analyzer, get_db_service
from src.api.utils import api_error_handler, deserialize_task, validate_task_state, validate_task_network_plan, find_stage_by_id, find_work_package_by_id, find_executable_task_by_id

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
    ERROR_CONCURRENT_OPERATION
)

logger = logging.getLogger(__name__)

router = APIRouter()

# @router.post("/", response_model=Task)
# # task creaeted manually by user
# async def create_task(user_query: UserQuery, analyzer: ProblemAnalyzer = Depends(get_problem_analyzer)):
#     """Create a new task based on user query"""
#     # TODO: do not implemet yet. Keeping it for future, maybe it make sense to create task manualy by user
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
    if not force and task.state == TaskState.CONTEXT_GATHERED:
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
    
    if task.state != TaskState.CONTEXT_GATHERED and task.state != TaskState.TASK_FORMATION:
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
    
    if task.state != TaskState.CONTEXT_GATHERED and task.state != TaskState.TASK_FORMATION:
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
    
    if task.state != TaskState.TASK_FORMATION:
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
    
    if task.state != TaskState.TASK_FORMATION:
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
    
    if task.state != TaskState.TASK_FORMATION:
        error_message = f"Task must be in TASK_FORMATION state. Current state: {task.state}"
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
    
    if task.state != TaskState.IFR_GENERATED:
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
    
    if task.state != TaskState.REQUIREMENTS_GENERATED and not force:
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
        
        # Check for any exceptions in the results
        failed_tasks = []
        successful_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_tasks.append((target_work.tasks[i].id, str(result)))
            else:
                successful_results.append(result)
        
        if failed_tasks:
            error_message = ERROR_PARTIAL_SUCCESS.format(
                success_count=len(successful_results),
                total_count=len(results)
            )
            logger.error(f"{error_message}. Failed tasks: {failed_tasks}")
            raise ValidationException(error_message)
        
        # Log successful results
        for i, generated_subtasks in enumerate(successful_results):
            executable_task_id = target_work.tasks[i].id
            logger.info(f"Successfully generated {len(generated_subtasks)} subtasks for ExecutableTask {executable_task_id}.")
        
        return target_work.tasks
        
    except Exception as e:
        error_message = ERROR_CONCURRENT_OPERATION.format(operation="subtask generation")
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
        
        # Check for any exceptions in the results
        failed_works = []
        successful_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_works.append((target_stage.work_packages[i].id, str(result)))
            else:
                successful_results.append(result)
        
        if failed_works:
            error_message = ERROR_PARTIAL_SUCCESS.format(
                success_count=len(successful_results),
                total_count=len(results)
            )
            logger.error(f"{error_message}. Failed works: {failed_works}")
            raise ValidationException(error_message)
        
        # Log successful results
        for i, generated_tasks in enumerate(successful_results):
            work_id = target_stage.work_packages[i].id
            logger.info(f"Successfully generated {len(generated_tasks)} tasks for Work {work_id}.")
        
        return target_stage.work_packages
        
    except Exception as e:
        error_message = ERROR_CONCURRENT_OPERATION.format(operation="task generation")
        logger.error(f"{error_message}: {str(e)}")
        raise ValidationException(error_message)
