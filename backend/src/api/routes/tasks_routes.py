from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Tuple, Optional
from src.model.context import ContextSufficiencyResult, ContextAnswers
from src.api.deps import get_problem_analyzer, get_db_service
from src.model.task import Task, TaskState
from src.schemas.task import AnalysisResult, DecompositionResult, MethodSelectionResult, Typification
from src.schemas.user_query import UserQuery
from src.services.problem_analyzer import ProblemAnalyzer
from src.services.database_service import DatabaseService
from src.model.user_interaction import UserInteraction
import logging
from pydantic import BaseModel
from typing import List

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
async def update_task_context(task_id: str, context_answers: Optional[ContextAnswers] = None, analyzer: ProblemAnalyzer = Depends(get_problem_analyzer), db: DatabaseService = Depends(get_db_service)):
    task_data = db.fetch_task_by_id(task_id)
    if task_data is None:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    task_dict = json.loads(task_data['task_json'])
    if task_dict['state'] == TaskState.CONTEXT_GATHERED:
        raise HTTPException(status_code=400, detail=f"Task is already in the context gathered state. Current state: {task_dict['state']}")
    
    task = Task(**task_dict)
    task.state = TaskState.CONTEXT_GATHERING
    
    # Handle the case where UserInteraction is provided but both query and answer are empty
    if not context_answers:
        logger.info("No context answers provided. Clarifying context.")
        result = await analyzer.clarify_context(task)
        logger.info(f"Context sufficiency result: {result}")
        return result
    else:
        logger.info(f"User context answers provided: {context_answers}")
        task.add_context_answers(context_answers)
        db.updated_task(task)
        return await analyzer.clarify_context(task)
    
@router.post("/{task_id}/formulate", response_model=ContextSufficiencyResult)
async def formulate_task(
    task_id: str,
    analyzer: ProblemAnalyzer = Depends(get_problem_analyzer),
    db: DatabaseService = Depends(get_db_service)
):
    """Endpoint to explicitly trigger task formulation"""
    task_data = db.fetch_task_by_id(task_id)
    if task_data is None:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    task = Task(**json.loads(task_data['task_json']))
    
    if task.state != TaskState.CONTEXT_GATHERED:
        raise HTTPException(
            status_code=400,
            detail=f"Task must be in CONTEXT_GATHERED state. Current state: {task.state}"
        )
    
    result = analyzer.process_context(task)
    return result


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
