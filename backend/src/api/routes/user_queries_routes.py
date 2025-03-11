from typing import List
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import get_db_service
from src.model.task import Task
from src.schemas.user_query import UserQuery, UserQueryDB, UserQueryCreate, QueryStatus
from src.services.database_service import DatabaseService

router = APIRouter()


# POST /user-queries
# {
#     "query": "What is the status of my order?"
# }
@router.post("/", response_model=UserQueryCreate)
async def create_user_query(user_query: UserQuery, db: DatabaseService = Depends(get_db_service)):
    """Create a new user query associated with a task"""
    task = Task.create_new()
    task.short_description = user_query.query
    try:
        inserted_task_id = db.insert_task(task)
        created_at = datetime.utcnow().isoformat()
        created_query = db.insert_user_query(
            inserted_task_id,
            user_query.query,
            status=QueryStatus.PENDING,
            created_at=created_at,
            progress=0.0
        )
        return UserQueryCreate(**created_query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user query: {str(e)}")


# url: http://localhost:8000/user-queries/
@router.get("/", response_model=List[UserQueryCreate])
async def get_user_queries(db: DatabaseService = Depends(get_db_service)):
    """Get all user queries"""
    raw_queries = db.fetch_user_queries()
    return [UserQueryCreate(**query) for query in raw_queries]

@router.delete("/", response_model=dict)
async def delete_all_user_queries(db: DatabaseService = Depends(get_db_service)):
    """Delete all user queries"""
    db.delete_all_user_queries()
    return {"message": "All user queries deleted successfully"}

@router.get("/{query_id}", response_model=UserQueryDB)
async def get_user_query(query_id: int, db: DatabaseService = Depends(get_db_service)):
    """Get a specific user query by ID"""
    query = db.fetch_user_query_by_id(query_id)
    if query is None:
        raise HTTPException(status_code=404, detail="User query not found")
    return UserQueryDB(**query)


@router.get("/tasks/{task_id}", response_model=List[UserQueryDB])
async def get_task_user_queries(task_id: str, db: DatabaseService = Depends(get_db_service)):
    """Get all user queries associated with a specific task"""
    queries = db.fetch_user_queries_by_task_id(task_id)
    if not queries:
        raise HTTPException(status_code=404, detail=f"No queries found for task ID: {task_id}")
    return [UserQueryDB(**query) for query in queries]
