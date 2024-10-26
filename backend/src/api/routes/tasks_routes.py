from fastapi import APIRouter, Depends, HTTPException
from typing import Tuple, Optional
from src.model.context import ContextSufficiencyResult
from src.api.deps import get_problem_analyzer, get_db_service
from src.model.task import Task, TaskState
from src.schemas.task import AnalysisResult, DecompositionResult, ApproachFormationResult, MethodSelectionResult, Typification
from src.schemas.user_query import UserQuery
from src.services.problem_analyzer import ProblemAnalyzer
from src.services.database_service import DatabaseService
from src.model.user_interaction import UserInteraction
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

import json

router = APIRouter()

class ClarificationRequest(BaseModel):
    message: Optional[str] = None


# @router.post("/", response_model=Task)
# # task creaeted manually by user
# async def create_task(user_query: UserQuery, analyzer: ProblemAnalyzer = Depends(get_problem_analyzer)):
#     """Create a new task based on user query"""
#     # TODO: do not implemet yet. Keeping it for future, maybe it make sense to create task manualy by user


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str, db: DatabaseService = Depends(get_db_service)):
    """Get a specific task by ID"""
    task_data = db.fetch_task_by_id(task_id)
    if task_data is None:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    task_dict = json.loads(task_data['task_json'])
    task = Task(**task_dict)
    
    return task


@router.put("/{task_id}/context", response_model=ContextSufficiencyResult)
async def update_task_context(task_id: str, user_interaction: Optional[UserInteraction] = None, analyzer: ProblemAnalyzer = Depends(get_problem_analyzer), db: DatabaseService = Depends(get_db_service)):
    task_data = db.fetch_task_by_id(task_id)
    if task_data is None:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    task_dict = json.loads(task_data['task_json'])
    if task_dict['state'] == TaskState.CONTEXT_GATHERED:
        raise HTTPException(status_code=400, detail=f"Task is already in the context gathered state. Current state: {task_dict['state']}")
    
    task = Task(**task_dict)
    task.state = TaskState.CONTEXT_GATHERING
    
    # Handle the case where UserInteraction is provided but both query and answer are empty
    if not user_interaction:
        logger.info("No user interaction provided. Clarifying context.")
        return analyzer.clarify_context(task)
    if user_interaction and not user_interaction.query and not user_interaction.answer:
        logger.info("Empty user interaction provided. Treating as if no interaction was given.")
        return analyzer.clarify_context(task)
    else:
        logger.info(f"User interaction provided: {user_interaction}")
        task.add_user_interaction(user_interaction)
        db.updated_task(task)
        return analyzer.clarify_context(task)
    
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


@router.post("/{task_id}/analyze", response_model=AnalysisResult)
async def analyze_task(task_id: str, reAnalyze: bool = False, analyzer: ProblemAnalyzer = Depends(get_problem_analyzer), db: DatabaseService = Depends(get_db_service)):
    """Analyze a specific task"""
    # Fetch the task from the database
    task_data = db.fetch_task_by_id(task_id)
    
    if task_data is None:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    # Convert the JSON string to a dictionary and create a Task object
    task_dict = json.loads(task_data['task_json'])
    task = Task(**task_dict)
    
    # Check if the task is in the correct state for analysis, unless force is True
    if not reAnalyze:
        if task.state == TaskState.NEW or task.state == TaskState.CONTEXT_GATHERING:
            raise HTTPException(status_code=400, detail=f"Task is not in the correct state for analysis. Current state: {task.state}")
        
        if task.state != TaskState.CONTEXT_GATHERED or task.is_context_sufficient == False:
            raise HTTPException(status_code=400, detail=f"Task is not in the correct state for analysis. Current state: {task.state}")
    
    # Perform the analysis
    analyzer.analyze(task, reAnalyze)
    
    # Create and return the AnalysisResult
    analysis_result = AnalysisResult(
        parameters_constraints=task.analysis.get('parameters_constraints', ''),
        available_resources=task.analysis.get('available_resources', []),
        required_resources=task.analysis.get('required_resources', []),
        ideal_final_result=task.analysis.get('ideal_final_result', ''),
        missing_information=task.analysis.get('missing_information', [])
    )
    
    return analysis_result

@router.post("/{task_id}/typify", response_model=Typification)
async def typify_task(task_id: str, reTypify: bool = False, analyzer: ProblemAnalyzer = Depends(get_problem_analyzer), db: DatabaseService = Depends(get_db_service)):
    """Typify a specific task"""
    task_data = db.fetch_task_by_id(task_id)
    if task_data is None:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    task_dict = json.loads(task_data['task_json'])
    task = Task(**task_dict)
    
    if not reTypify:
        if task.state != TaskState.ANALYSIS:
            raise HTTPException(status_code=400, detail=f"Task is not in the correct state for typification. Current state: {task.state}")
    
    analyzer.typify(task)
    return Typification(typification=task.typification)

@router.post("/{task_id}/clarify", response_model=dict)
async def clarify_for_approaches(
    task_id: str,
    request: ClarificationRequest,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
):
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

@router.post("/{task_id}/approaches", response_model=ApproachFormationResult)
async def generate_approaches(task_id: str, analyzer: ProblemAnalyzer = Depends(get_problem_analyzer), db: DatabaseService = Depends(get_db_service)):
    """Generate approaches for a specific task"""
    task_data = db.fetch_task_by_id(task_id)
    if task_data is None:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    task_dict = json.loads(task_data['task_json'])
    task = Task(**task_dict)
    approach_definition = analyzer.generate_approaches(task)

    approach_result = ApproachFormationResult(
        principles=approach_definition['principles'],
        solution_by_principles=approach_definition['solution_by_principles'],
        approach_list=approach_definition['approach_list'],
        evaluation_criteria=approach_definition.get('evaluation_criteria', None)
    )
    return approach_result

# TODO: add method selection
@router.post("/{task_id}/method_selection", response_model=MethodSelectionResult)
async def method_selection(task_id: str, analyzer: ProblemAnalyzer = Depends(get_problem_analyzer)):
    """Select a method for a specific task"""
    # Implementation here

    
@router.post("/{task_id}/decompose", response_model=DecompositionResult)
async def decompose_task(task_id: str, analyzer: ProblemAnalyzer = Depends(get_problem_analyzer)):
    """Decompose a specific task into sub-tasks"""
    # Implementation here


@router.get("/{task_id}/tree", response_model=Task)
async def get_task_tree(task_id: str, analyzer: ProblemAnalyzer = Depends(get_problem_analyzer)):
    """Get the task tree for a specific task"""
    # Implementation here
