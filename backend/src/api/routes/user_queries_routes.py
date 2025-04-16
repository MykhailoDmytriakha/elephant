from typing import List
import json
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import get_db_service
from src.api.utils import api_error_handler
from src.model.task import Task
from src.schemas.user_query import UserQuery, UserQueryDB, UserQueryCreate, QueryStatus
from src.services.database_service import DatabaseService
from src.constants import (
    ERROR_QUERY_NOT_FOUND, 
    ERROR_NO_QUERIES_FOR_TASK,
    ERROR_CREATE_QUERY,
    SUCCESS_ALL_QUERIES_DELETED,
    OP_CREATE_QUERY,
    OP_GET_QUERIES,
    OP_DELETE_QUERIES
)

router = APIRouter()


@router.post("/", response_model=UserQueryCreate)
@api_error_handler(OP_CREATE_QUERY)
async def create_user_query(user_query: UserQuery, db: DatabaseService = Depends(get_db_service)):
    """Create a new user query associated with a task"""
    task = Task.create_new()
    task.short_description = user_query.query
    
    inserted_task_id = db.insert_task(task)
    created_at = datetime.now(UTC).isoformat()
    created_query = db.insert_user_query(
        inserted_task_id,
        user_query.query,
        status=QueryStatus.PENDING,
        created_at=created_at,
        progress=0.0
    )
    return UserQueryCreate(**created_query)

@router.get("/", response_model=List[UserQueryCreate])
@api_error_handler(OP_GET_QUERIES)
async def get_user_queries(db: DatabaseService = Depends(get_db_service)):
    """Get all user queries"""
    raw_queries = db.fetch_user_queries()
    return [UserQueryCreate(**query) for query in raw_queries]

@router.delete("/", response_model=dict)
@api_error_handler(OP_DELETE_QUERIES)
async def delete_all_user_queries(db: DatabaseService = Depends(get_db_service)):
    """Delete all user queries"""
    db.delete_all_user_queries()
    return {"message": SUCCESS_ALL_QUERIES_DELETED}

@router.get("/{query_id}", response_model=UserQueryDB)
@api_error_handler(OP_GET_QUERIES)
async def get_user_query(query_id: int, db: DatabaseService = Depends(get_db_service)):
    """Get a specific user query by ID"""
    query = db.fetch_user_query_by_id(query_id)
    if query is None:
        raise ValueError(ERROR_QUERY_NOT_FOUND.format(query_id=query_id))
    return UserQueryDB(**query)


@router.get("/tasks/{task_id}", response_model=List[UserQueryDB])
@api_error_handler(OP_GET_QUERIES)
async def get_task_user_queries(task_id: str, db: DatabaseService = Depends(get_db_service)):
    """Get all user queries associated with a specific task"""
    queries = db.fetch_user_queries_by_task_id(task_id)
    if not queries:
        from src.exceptions import QueryNotFoundException
        raise QueryNotFoundException(ERROR_NO_QUERIES_FOR_TASK.format(task_id=task_id))
    return [UserQueryDB(**query) for query in queries]
