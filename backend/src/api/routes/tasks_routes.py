from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Tuple, Optional
from src.model.context import ContextSufficiencyResult, UserAnswers, UserAnswer
from src.api.deps import get_problem_analyzer, get_db_service
from src.model.task import Task, TaskState
from src.schemas.task import AnalysisResult, DecompositionResult, MethodSelectionResult, Typification
from src.services.problem_analyzer import ProblemAnalyzer
from src.services.database_service import DatabaseService
from src.model.scope import TaskScope, DraftScope, ValidationScopeResult
import logging
from pydantic import BaseModel
from typing import List
from src.model.scope import ScopeFormulationGroup

logger = logging.getLogger(__name__)

import json

router = APIRouter()

class ClarificationRequest(BaseModel):
    message: Optional[str] = None

class SelectedTools(BaseModel):
    analytical_tools: List[str]
    practical_methods: List[str]
    frameworks: List[str]
    
    class Config:
        extra = "allow"

class ScopeValidationRequest(BaseModel):
    isApproved: bool
    feedback: Optional[str] = None

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



@router.post("/{task_id}/analyze", response_model=AnalysisResult)
async def analyze_task(
    task_id: str, 
    reAnalyze: bool = False, 
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
):
    """Analyze a task to determine its type and complexity"""
    task_data = db.fetch_task_by_id(task_id)
    if task_data is None:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    # Convert task_data to Task object
    task_dict = json.loads(task_data['task_json'])
    task = Task(**task_dict)
    
    if task.state == TaskState.NEW or reAnalyze:
        try:
            # Analyze the task
            analyzer.analyze(task, reAnalyze)
            task.state = TaskState.ANALYSIS
            db.updated_task(task)
            # Update progress to 25% after analysis
            db.update_user_query_progress(task_id, 25.0)
            # Create and return the AnalysisResult
            analysis_result = AnalysisResult(analysis=task.analysis)
            return analysis_result
        except Exception as e:
            logger.error(f"Error analyzing task: {e}")
            raise HTTPException(status_code=500, detail=f"Error analyzing task: {str(e)}")
    else:
        return AnalysisResult(analysis=task.analysis)

@router.post("/{task_id}/typify", response_model=Typification)
async def typify_task(task_id: str, reTypify: bool = False, analyzer: ProblemAnalyzer = Depends(get_problem_analyzer), db: DatabaseService = Depends(get_db_service)):
    """Typify a task to determine its type and complexity"""
    task_data = db.fetch_task_by_id(task_id)
    if task_data is None:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    # Convert task_data to Task object
    task_dict = json.loads(task_data['task_json'])
    task = Task(**task_dict)
    
    if task.state == TaskState.ANALYSIS or reTypify:
        try:
            # Typify the task
            analyzer.typify(task)
            task.state = TaskState.TYPIFY
            db.updated_task(task)
            # Update progress to 50% after typification
            db.update_user_query_progress(task_id, 50.0)
            return Typification(typification=task.typification)
        except Exception as e:
            logger.error(f"Error typifying task: {e}")
            raise HTTPException(status_code=500, detail=f"Error typifying task: {str(e)}")
    else:
        return Typification(typification=task.typification)

@router.post("/{task_id}/clarify", response_model=dict)
async def clarify_for_approaches(task_id: str, request: ClarificationRequest, analyzer: ProblemAnalyzer = Depends(get_problem_analyzer), db: DatabaseService = Depends(get_db_service)):
    """
    Handle the clarification dialogue before approaches generation.
    If message is None, generate initial questions.
    If message is provided, process the answer and return next question.
    """
    task_data = db.fetch_task_by_id(task_id)
    if task_data is None:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    task_dict = json.loads(task_data['task_json'])
    task = Task(**task_dict)
    
    # Check if task is in appropriate state
    if task.state not in [TaskState.TYPIFY, TaskState.CLARIFYING]:
        raise HTTPException(
            status_code=400, 
            detail=f"Task must be in TYPIFY or CLARIFYING state. Current state: {task.state}"
        )
    
    # Start or continue clarification dialogue
    clarification_result = analyzer.clarify_for_approaches(task, request.message)
    
    return clarification_result 

@router.post("/{task_id}/approaches", response_model=dict)
async def generate_approaches(task_id: str, analyzer: ProblemAnalyzer = Depends(get_problem_analyzer), db: DatabaseService = Depends(get_db_service)):
    """Generate approaches for a specific task"""
    task_data = db.fetch_task_by_id(task_id)
    if task_data is None:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    task_dict = json.loads(task_data['task_json'])
    task = Task(**task_dict)
    analyzer.generate_approaches(task)
    return task.approaches

    
@router.post("/{task_id}/decompose")
async def decompose_task(
    task_id: str,
    selected_tools: SelectedTools,
    redecompose: bool = False,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
):
    """Decompose a task into subtasks"""
    task_data = db.fetch_task_by_id(task_id)
    if task_data is None:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    # Convert task_data to Task object
    task_dict = json.loads(task_data['task_json'])
    task = Task(**task_dict)
    
    if task.state == TaskState.METHOD_SELECTION or redecompose:
        try:
            task.approaches['selected_approaches'] = selected_tools.dict()
            # Decompose the task
            analyzer.decompose(task, redecompose)
            task.state = TaskState.DECOMPOSITION
            db.updated_task(task)
            # Update progress to 100% after decomposition
            db.update_user_query_progress(task_id, 100.0)
            return task.sub_tasks
        except Exception as e:
            logger.error(f"Error decomposing task: {e}")
            raise HTTPException(status_code=500, detail=f"Error decomposing task: {str(e)}")
    else:
        return task.sub_tasks
    


@router.get("/{task_id}/tree", response_model=Task)
async def get_task_tree(task_id: str, analyzer: ProblemAnalyzer = Depends(get_problem_analyzer)):
    """Get the task tree for a specific task"""
    # Implementation here
