from fastapi import APIRouter, Depends, HTTPException
from typing import Tuple, Optional
from src.model.context import ContextSufficiencyResult
from src.api.deps import get_problem_analyzer, get_db_service
from src.model.task import Task, TaskState
from src.schemas.task import AnalysisResult, DecompositionResult, ConceptFormationResult
from src.schemas.user_query import UserQuery
from src.services.problem_analyzer import ProblemAnalyzer
from src.services.database_service import DatabaseService
from src.model.user_interaction import UserInteraction
import logging

logger = logging.getLogger(__name__)

import json

router = APIRouter()


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
    
    task = Task(**task_dict)
    task.state = TaskState.CONTEXT
    
    if not user_interaction:
        logger.info("No user interaction provided. Clarifying context.")
        return analyzer.clarify_context(task)
    else:
        logger.info(f"User interaction provided: {user_interaction}")
        task.add_user_interaction(user_interaction)
        return analyzer.clarify_context(task)
 


@router.post("/{task_id}/analyze", response_model=AnalysisResult)
async def analyze_task(task_id: str, analyzer: ProblemAnalyzer = Depends(get_problem_analyzer), db: DatabaseService = Depends(get_db_service)):
    """Analyze a specific task"""
    # Fetch the task from the database
    task_data = db.fetch_task_by_id(task_id)
    
    if task_data is None:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    # Convert the JSON string to a dictionary and create a Task object
    task_dict = json.loads(task_data['task_json'])
    task = Task(**task_dict)
    
    # Check if the task is in the correct state for analysis
    if task.state != TaskState.NEW:
        raise HTTPException(status_code=400, detail=f"Task is not in the correct state for analysis. Current state: {task.state}")
    
    if task.state != TaskState.CONTEXT and task.is_context_sufficient == False:
        raise HTTPException(status_code=400, detail=f"Task is not in the correct state for analysis. Required more context. Current state: {task.state}")
    
    # Perform the analysis
    analyzer.analyze(task)
    
    # Create and return the AnalysisResult
    analysis_result = AnalysisResult(
        parameters_constraints=task.analysis.get('parameters_constraints', ''),
        available_resources=task.analysis.get('available_resources', []),
        required_resources=task.analysis.get('required_resources', []),
        ideal_final_result=task.analysis.get('ideal_final_result', ''),
        missing_information=task.analysis.get('missing_information', []),
        complexity=task.analysis.get('complexity', '')
    )
    
    return analysis_result

@router.post("/{task_id}/generate-concepts", response_model=ConceptFormationResult)
async def generate_concepts(task_id: str, analyzer: ProblemAnalyzer = Depends(get_problem_analyzer)):
    """Generate concepts for a specific task"""
    # Implementation here
    
    
@router.post("/{task_id}/decompose", response_model=DecompositionResult)
async def decompose_task(task_id: str, analyzer: ProblemAnalyzer = Depends(get_problem_analyzer)):
    """Decompose a specific task into sub-tasks"""
    # Implementation here


@router.get("/{task_id}/tree", response_model=Task)
async def get_task_tree(task_id: str, analyzer: ProblemAnalyzer = Depends(get_problem_analyzer)):
    """Get the task tree for a specific task"""
    # Implementation here
