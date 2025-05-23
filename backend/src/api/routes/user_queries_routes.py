from typing import List
import json
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, Request

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

# Import user activity logging
from src.core.user_activity_logger import (
    user_activity_logger, 
    UserAction, 
    ActionType,
    UserSession
)

router = APIRouter()


def get_user_session_from_request(request: Request) -> UserSession:
    """Extract user session information from request"""
    return UserSession(
        session_id=request.headers.get("X-Request-ID", "unknown"),
        user_id=request.headers.get("X-User-ID"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
        current_page=request.url.path,
        referrer=request.headers.get("Referer")
    )


@router.post("/", response_model=UserQueryCreate)
@api_error_handler(OP_CREATE_QUERY)
async def create_user_query(user_query: UserQuery, request: Request, db: DatabaseService = Depends(get_db_service)):
    """Create a new user query associated with a task"""
    user_session = get_user_session_from_request(request)
    
    # Log the form submission attempt
    user_activity_logger.log_form_submission(
        form_name="Create User Query",
        success=False,  # Will update this after processing
        user_session=user_session
    )
    
    try:
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
        
        # Log successful query creation
        action = UserAction(
            action_type=ActionType.FORM_SUBMISSION,
            description=f"User query created: '{user_query.query[:50]}...'",
            data={"task_id": inserted_task_id, "query_length": len(user_query.query)},
            result="Query created successfully",
            success=True
        )
        user_activity_logger.log_user_action(action, user_session)
        
        return UserQueryCreate(**created_query)
        
    except Exception as e:
        # Log the error
        user_activity_logger.log_error(
            error_type=type(e).__name__,
            error_message=str(e),
            context={"operation": "create_user_query", "query": user_query.query},
            user_session=user_session
        )
        raise


@router.get("/", response_model=List[UserQueryCreate])
@api_error_handler(OP_GET_QUERIES)
async def get_user_queries(request: Request, db: DatabaseService = Depends(get_db_service)):
    """Get all user queries"""
    user_session = get_user_session_from_request(request)
    
    try:
        raw_queries = db.fetch_user_queries()
        query_count = len(raw_queries)
        
        # Log the data retrieval action
        action = UserAction(
            action_type=ActionType.API_CALL,
            description="Retrieved all user queries",
            data={"queries_count": query_count},
            result=f"Found {query_count} queries",
            success=True
        )
        user_activity_logger.log_user_action(action, user_session)
        
        return [UserQueryCreate(**query) for query in raw_queries]
        
    except Exception as e:
        user_activity_logger.log_error(
            error_type=type(e).__name__,
            error_message=str(e),
            context={"operation": "get_user_queries"},
            user_session=user_session
        )
        raise


@router.delete("/", response_model=dict)
@api_error_handler(OP_DELETE_QUERIES)
async def delete_all_user_queries(request: Request, db: DatabaseService = Depends(get_db_service)):
    """Delete all user queries"""
    user_session = get_user_session_from_request(request)
    
    try:
        # Get count before deletion for logging
        queries_before = db.fetch_user_queries()
        count_before = len(queries_before)
        
        db.delete_all_user_queries()
        
        # Log the deletion action
        action = UserAction(
            action_type=ActionType.API_CALL,
            description="Deleted all user queries",
            data={"deleted_count": count_before},
            result=f"Successfully deleted {count_before} queries",
            success=True
        )
        user_activity_logger.log_user_action(action, user_session)
        
        return {"message": SUCCESS_ALL_QUERIES_DELETED}
        
    except Exception as e:
        user_activity_logger.log_error(
            error_type=type(e).__name__,
            error_message=str(e),
            context={"operation": "delete_all_user_queries"},
            user_session=user_session
        )
        raise


@router.get("/{query_id}", response_model=UserQueryDB)
@api_error_handler(OP_GET_QUERIES)
async def get_user_query(query_id: int, request: Request, db: DatabaseService = Depends(get_db_service)):
    """Get a specific user query by ID"""
    user_session = get_user_session_from_request(request)
    
    try:
        query = db.fetch_user_query_by_id(query_id)
        if query is None:
            # Log the not found case
            action = UserAction(
                action_type=ActionType.API_CALL,
                description=f"Attempted to retrieve query ID {query_id}",
                data={"query_id": query_id},
                result="Query not found",
                success=False
            )
            user_activity_logger.log_user_action(action, user_session)
            raise ValueError(ERROR_QUERY_NOT_FOUND.format(query_id=query_id))
        
        # Log successful retrieval
        action = UserAction(
            action_type=ActionType.API_CALL,
            description=f"Retrieved query ID {query_id}",
            data={"query_id": query_id, "query_text": query.get("query", "")[:50]},
            result="Query found successfully",
            success=True
        )
        user_activity_logger.log_user_action(action, user_session)
        
        return UserQueryDB(**query)
        
    except Exception as e:
        if "Query not found" not in str(e):  # Don't double-log the not found error
            user_activity_logger.log_error(
                error_type=type(e).__name__,
                error_message=str(e),
                context={"operation": "get_user_query", "query_id": query_id},
                user_session=user_session
            )
        raise


@router.get("/tasks/{task_id}", response_model=List[UserQueryDB])
@api_error_handler(OP_GET_QUERIES)
async def get_task_user_queries(task_id: str, request: Request, db: DatabaseService = Depends(get_db_service)):
    """Get all user queries associated with a specific task"""
    user_session = get_user_session_from_request(request)
    
    try:
        queries = db.fetch_user_queries_by_task_id(task_id)
        if not queries:
            # Log the not found case
            action = UserAction(
                action_type=ActionType.API_CALL,
                description=f"Attempted to retrieve queries for task {task_id}",
                data={"task_id": task_id},
                result="No queries found for task",
                success=False
            )
            user_activity_logger.log_user_action(action, user_session)
            
            from src.exceptions import QueryNotFoundException
            raise QueryNotFoundException(ERROR_NO_QUERIES_FOR_TASK.format(task_id=task_id))
        
        # Log successful retrieval
        action = UserAction(
            action_type=ActionType.API_CALL,
            description=f"Retrieved queries for task {task_id}",
            data={"task_id": task_id, "queries_count": len(queries)},
            result=f"Found {len(queries)} queries for task",
            success=True
        )
        user_activity_logger.log_user_action(action, user_session)
        
        return [UserQueryDB(**query) for query in queries]
        
    except Exception as e:
        if "no queries" not in str(e).lower():  # Don't double-log the not found error
            user_activity_logger.log_error(
                error_type=type(e).__name__,
                error_message=str(e),
                context={"operation": "get_task_user_queries", "task_id": task_id},
                user_session=user_session
            )
        raise
