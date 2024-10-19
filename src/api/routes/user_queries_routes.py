from typing import List

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import get_db_service
from src.model.task import Task
from src.schemas.user_query import UserQuery, UserQueryDB
from src.services.database_service import DatabaseService

router = APIRouter()


# POST /user-queries
# {
#     "query": "What is the status of my order?"
# }
@router.post("/", response_model=UserQueryDB)
async def create_user_query(user_query: UserQuery, db: DatabaseService = Depends(get_db_service)):
    """Create a new user query associated with a task"""
    task = Task()
    task.short_description = user_query.query
    try:
        db.insert_task(task)
        created_query = db.insert_user_query(task.id, user_query.query)
        return UserQueryDB(**created_query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user query: {str(e)}")


# url: http://localhost:8000/user-queries/
@router.get("/", response_model=List[UserQueryDB])
async def get_user_queries(db: DatabaseService = Depends(get_db_service)):
    """Get all user queries"""
    raw_queries = db.fetch_user_queries()
    response = [UserQueryDB(**query) for query in raw_queries]
    # [UserQueryDB(
    #     id=query['id'],
    #     task_id=query['task_id'],
    #     origin_query=query['origin_query'].strip()  # Example: strip whitespace
    # ) for query in raw_queries]
    return response


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
