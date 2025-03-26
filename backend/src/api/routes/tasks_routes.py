from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from src.model.context import ContextSufficiencyResult, UserAnswers
from src.api.deps import get_problem_analyzer, get_db_service
from src.model.task import Task, TaskState
from src.services.problem_analyzer import ProblemAnalyzer
from src.services.database_service import DatabaseService
from src.model.scope import TaskScope, DraftScope, ValidationScopeResult, ScopeValidationRequest
import logging
from typing import List
from src.model.scope import ScopeFormulationGroup
from src.model.ifr import IFR, Requirements
from src.model.planning import NetworkPlan, Stage
from src.model.work import Work
from src.model.executable_task import ExecutableTask
logger = logging.getLogger(__name__)

import json

router = APIRouter()

# @router.post("/", response_model=Task)
# # task creaeted manually by user
# async def create_task(user_query: UserQuery, analyzer: ProblemAnalyzer = Depends(get_problem_analyzer)):
#     """Create a new task based on user query"""
#     # TODO: do not implemet yet. Keeping it for future, maybe it make sense to create task manualy by user
@router.delete("/", response_model=dict)
async def delete_all_tasks(db: DatabaseService = Depends(get_db_service)):
    """Delete all tasks"""
    db.delete_all_tasks()
    return {"message": "All tasks deleted successfully"}
 
@router.delete("/{task_id}", response_model=dict)
async def delete_task(task_id: str, db: DatabaseService = Depends(get_db_service)):
    """Delete a specific task by ID"""
    task_data = db.fetch_task_by_id(task_id)
    if task_data is None:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    # Delete the task from the database
    success = db.delete_task_by_id(task_id)
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to delete task with ID {task_id}")
    
    return {"message": f"Task with ID {task_id} has been successfully deleted"}

@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str, db: DatabaseService = Depends(get_db_service)):
    """Get a specific task by ID"""
    task_data = db.fetch_task_by_id(task_id)
    if task_data is None:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    task_dict = json.loads(task_data['task_json'])
    task = Task(**task_dict)
    
    return task


@router.post("/{task_id}/context-questions", response_model=ContextSufficiencyResult)
async def update_task_context(
    task_id: str, 
    context_answers: Optional[UserAnswers] = None, 
    force: bool = False,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer), 
    db: DatabaseService = Depends(get_db_service)
):
    task_data = db.fetch_task_by_id(task_id)
    if task_data is None:
        logger.error(f"Task with ID {task_id} not found")
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    task_dict = json.loads(task_data['task_json'])
    
    # Only check state if force is False
    if not force and task_dict['state'] == TaskState.CONTEXT_GATHERED:
        logger.error(f"Task is already in the context gathered state. Current state: {task_dict['state']}")
        raise HTTPException(status_code=400, detail=f"Task is already in the context gathered state. Current state: {task_dict['state']}")
    
    task = Task(**task_dict)
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
async def formulate_task(
    task_id: str,
    group: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
):
    """Endpoint to explicitly trigger task formulation"""
    task_data = db.fetch_task_by_id(task_id)
    if task_data is None:
        logger.error(f"Task with ID {task_id} not found")
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    task = Task(**json.loads(task_data['task_json']))
    
    if task.state != TaskState.CONTEXT_GATHERED and task.state != TaskState.TASK_FORMATION:
        logger.error(f"Task must be in CONTEXT_GATHERED or TASK_FORMATION state. Current state: {task.state}")
        raise HTTPException(
            status_code=400,
            detail=f"Task must be in CONTEXT_GATHERED or TASK_FORMATION state. Current state: {task.state}"
        )
        
    if task.scope:
        if group in task.scope.__dict__.keys():
            exist_group = getattr(task.scope, group)
            if exist_group:
                logger.info(f"Group {group} found in task scope")
                raise HTTPException(status_code=400, detail=f"Group {group} already exists in task scope")
    
    result = await analyzer.define_scope_question(task, group)
    return result

@router.post("/{task_id}/formulate/{group}", response_model=dict)
async def submit_formulation_answers(
    task_id: str,
    group: str,
    answers: UserAnswers,
    db: DatabaseService = Depends(get_db_service)
):
    """Submit formulation answers for a specific group"""
    print(f"Submitting formulation answers for task {task_id} and group {group}")
    print(f"Answers: {answers.json()}")
    task_data = db.fetch_task_by_id(task_id)
    if task_data is None:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    task = Task(**json.loads(task_data['task_json']))
    if task.state != TaskState.CONTEXT_GATHERED and task.state != TaskState.TASK_FORMATION:
        raise HTTPException(
            status_code=400,
            detail=f"Task must be in CONTEXT_GATHERED or TASK_FORMATION state. Current state: {task.state}"
        )
    
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
async def get_draft_scope(
    task_id: str, 
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer), 
    db: DatabaseService = Depends(get_db_service)
    ):
    """Get the draft scope for a specific task"""
    task_data = db.fetch_task_by_id(task_id)
    if task_data is None:
        logger.error(f"Task with ID {task_id} not found")
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")    
    
    task = Task(**json.loads(task_data['task_json']))
    if task.state != TaskState.TASK_FORMATION:
        logger.error(f"Task must be in TASK_FORMATION state. Current state: {task.state}")
        raise HTTPException(status_code=400, detail=f"Task must be in TASK_FORMATION state. Current state: {task.state}")
    
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
async def validate_scope(
    task_id: str,
    request: ScopeValidationRequest,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
):
    """Validate the scope for a specific task"""
    task_data = db.fetch_task_by_id(task_id)
    if task_data is None:
        logger.error(f"Task with ID {task_id} not found")
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    task = Task(**json.loads(task_data['task_json']))
    if task.state != TaskState.TASK_FORMATION:
        logger.error(f"Task must be in TASK_FORMATION state. Current state: {task.state}")
        raise HTTPException(status_code=400, detail=f"Task must be in TASK_FORMATION state. Current state: {task.state}")
    
    # Validate the scope
    if not request.isApproved and not request.feedback:
        logger.error("Feedback is required when scope is not approved")
        raise HTTPException(status_code=400, detail="Feedback is required when scope is not approved")
    
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
async def generate_ifr(
    task_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
):
    """Generate an ideal final result for a specific task"""
    task_data = db.fetch_task_by_id(task_id)
    if task_data is None:
        logger.error(f"Task with ID {task_id} not found")
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    task = Task(**json.loads(task_data['task_json']))
    if task.state != TaskState.TASK_FORMATION:
        logger.error(f"Task must be in TASK_FORMATION state. Current state: {task.state}")
        raise HTTPException(status_code=400, detail=f"Task must be in TASK_FORMATION state. Current state: {task.state}")
    
    ifr = await analyzer.generate_IFR(task)
    task.ifr = ifr
    task.state = TaskState.IFR_GENERATED
    db.updated_task(task)
    return ifr

@router.post("/{task_id}/requirements", response_model=Requirements)
async def define_requirements(
    task_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
):
    """Define requirements for a specific task"""
    task_data = db.fetch_task_by_id(task_id)
    if task_data is None:
        logger.error(f"Task with ID {task_id} not found")
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    task = Task(**json.loads(task_data['task_json']))
    if task.state != TaskState.IFR_GENERATED:
        logger.error(f"Task must be in IFR_GENERATED state. Current state: {task.state}")
        raise HTTPException(status_code=400, detail=f"Task must be in IFR_GENERATED state. Current state: {task.state}")
    
    requirements = await analyzer.define_requirements(task)
    task.requirements = requirements
    task.state = TaskState.REQUIREMENTS_GENERATED
    db.updated_task(task)
    return requirements

@router.post("/{task_id}/network-plan", response_model=NetworkPlan)
async def generate_network_plan(
    task_id: str,
    force: bool = False,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
):
    """Generate a network plan for a specific task"""
    task_data = db.fetch_task_by_id(task_id)
    if task_data is None:
        logger.error(f"Task with ID {task_id} not found")
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    task = Task(**json.loads(task_data['task_json']))
    if task.state != TaskState.REQUIREMENTS_GENERATED and not force:
        logger.error(f"Task must be in REQUIREMENTS_GENERATED state. Current state: {task.state}")
        raise HTTPException(status_code=400, detail=f"Task must be in REQUIREMENTS_GENERATED state. Current state: {task.state}")
    
    network_plan = await analyzer.generate_network_plan(task)
    task.network_plan = network_plan
    task.state = TaskState.NETWORK_PLAN_GENERATED
    db.updated_task(task)
    return network_plan
    
@router.post("/{task_id}/stages/{stage_id}/generate-work", response_model=List[Work])
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
    if task_data is None:
        logger.error(f"Task {task_id} not found.")
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")

    try:
        task = Task(**json.loads(task_data['task_json']))
    except Exception as e:
        logger.error(f"Failed to deserialize task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load task data.")

    # Ensure the task is in the correct state
    if task.state != TaskState.NETWORK_PLAN_GENERATED:
        logger.error(f"Task {task_id} is not in the required state ({TaskState.NETWORK_PLAN_GENERATED}). Current state: {task.state}")
        raise HTTPException(
            status_code=400,
            detail=f"Task must be in state '{TaskState.NETWORK_PLAN_GENERATED.value}' to generate work packages. Current state: '{task.state.value}'"
        )

    try:
        # Call the analyzer method which handles finding the stage, calling AI, and updating DB
        generated_work = await analyzer.generate_stage_work(task, stage_id)
        return generated_work
    except ValueError as ve: # Catch errors like stage not found
        logger.error(f"Value error during work generation for Task {task_id}, Stage {stage_id}: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except ImportError as ie: # Catch SDK import errors
         logger.error(f"Import error during work generation: {ie}")
         raise HTTPException(status_code=501, detail="Work generation feature requires additional dependencies.")
    except Exception as e:
        logger.error(f"Unexpected error generating work for Task {task_id}, Stage {stage_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while generating work packages.")

@router.post("/{task_id}/stages/generate-work", response_model=NetworkPlan)
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
    if task_data is None:
        logger.error(f"Task {task_id} not found.")
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    try:
        task = Task(**json.loads(task_data['task_json']))
    except Exception as e:
        logger.error(f"Failed to deserialize task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load task data.")
    
    if task.state != TaskState.NETWORK_PLAN_GENERATED:
        logger.error(f"Task {task_id} is not in the required state ({TaskState.NETWORK_PLAN_GENERATED}). Current state: {task.state}")
        raise HTTPException(
            status_code=400,
            detail=f"Task must be in state '{TaskState.NETWORK_PLAN_GENERATED.value}' to generate work packages. Current state: '{task.state.value}'"
        )
    
    # Ensure the network plan is not None
    if not task.network_plan:
        logger.error(f"Task {task_id} does not have a network plan.")
        raise HTTPException(status_code=400, detail="Task does not have a network plan.")
    
    # Generate work packages for all stages
    for stage in task.network_plan.stages:
        generated_work = await analyzer.generate_stage_work(task, stage.id)
        logger.info(f"Generated work for Stage {stage.id}: {generated_work}")
        
    return task.network_plan

@router.post("/{task_id}/stages/{stage_id}/work/{work_id}/generate-tasks", response_model=List[ExecutableTask])
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
    if task_data is None:
        logger.error(f"Task {task_id} not found.")
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    try:
        task = Task(**json.loads(task_data['task_json']))
    except Exception as e:
        logger.error(f"Failed to deserialize task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load task data.")
    
    if task.state != TaskState.NETWORK_PLAN_GENERATED:
        logger.error(f"Task {task_id} is not in the required state ({TaskState.NETWORK_PLAN_GENERATED}). Current state: {task.state}")
        raise HTTPException(
            status_code=400,
            detail=f"Task must be in state '{TaskState.NETWORK_PLAN_GENERATED.value}' to generate tasks. Current state: '{task.state.value}'"
        )
    
    # Ensure the network plan is not None
    if not task.network_plan:
        logger.error(f"Task {task_id} does not have a network plan.")
        raise HTTPException(status_code=400, detail="Task does not have a network plan.")

    try:
        generated_tasks = await analyzer.generate_tasks_for_work(task, stage_id, work_id)
        logger.info(f"Successfully generated {len(generated_tasks)} tasks for Work {work_id}.")
        return generated_tasks
    except ValueError as ve:
        # Handle cases where Task, Stage, or Work is not found, or state is invalid
        logger.error(f"Value error generating tasks: {ve}")
        if "not found" in str(ve).lower():
            raise HTTPException(status_code=404, detail=str(ve))
        else:
            # Treat other ValueErrors (like wrong state) as Bad Request
            raise HTTPException(status_code=400, detail=str(ve))
    except ImportError as ie:
         logger.error(f"Import error during task generation: {ie}")
         raise HTTPException(status_code=501, detail="Task generation feature requires additional dependencies.")
    except Exception as e:
        logger.error(f"Unexpected error generating executable tasks for Work {work_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while generating executable tasks.")
    
@router.post("/{task_id}/stages/{stage_id}/works/generate-tasks", response_model=List[Work])
async def generate_tasks_for_all_works_endpoint(
    task_id: str,
    stage_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service) # Analyzer already depends on DB
):
    """
    Generates a list of ExecutableTask units for all Work packages within a Stage.
    The Task must have Work packages generated for the specified Stage.
    """
    logger.info(f"API endpoint called: Generate ExecutableTasks for all Works in Stage {stage_id} of Task {task_id}")

    task_data = db.fetch_task_by_id(task_id)
    if task_data is None:
        logger.error(f"Task {task_id} not found.")
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")

    try:
        task = Task(**json.loads(task_data['task_json']))
    except Exception as e:
        logger.error(f"Failed to deserialize task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load task data.")
    
    if task.state != TaskState.NETWORK_PLAN_GENERATED:
        logger.error(f"Task {task_id} is not in the required state ({TaskState.NETWORK_PLAN_GENERATED}). Current state: {task.state}")
        raise HTTPException(
            status_code=400,
            detail=f"Task must be in state '{TaskState.NETWORK_PLAN_GENERATED.value}' to generate tasks. Current state: '{task.state.value}'"
        )
        
    # Ensure the network plan is not None
    if not task.network_plan:
        logger.error(f"Task {task_id} does not have a network plan.")
        raise HTTPException(status_code=400, detail="Task does not have a network plan.")
    
    # Find Stage
    target_stage: Optional[Stage] = next((s for s in task.network_plan.stages if s.id == stage_id), None)
    if not target_stage:
        logger.error(f"Stage {stage_id} not found in Task {task_id}.")
        raise ValueError(f"Stage ID {stage_id} not found.")
    
    # Generate tasks for all works in the stage
    if target_stage.work_packages:
        for work in target_stage.work_packages:
            generated_tasks = await analyzer.generate_tasks_for_work(task, stage_id, work.id)
            logger.info(f"Successfully generated {len(generated_tasks)} tasks for Work {work.id}.")
        
    return target_stage.work_packages

        
