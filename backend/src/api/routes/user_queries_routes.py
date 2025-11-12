from typing import List
import json
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, Request

from src.api.deps import get_file_storage_service, get_openai_service
from src.api.utils import api_error_handler
from src.model.task import Task
from src.schemas.user_query import UserQuery, UserQueryDB, UserQueryCreate, QueryStatus
from src.services.file_storage_service import FileStorageService
from src.services.openai_service import OpenAIService
from src.utils.project_utils import generate_project_name
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
async def create_user_query(
    user_query: UserQuery,
    request: Request,
    openai_service: OpenAIService = Depends(get_openai_service),
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """Create a new user query associated with a task"""
    try:
        # 1. Generate project name via AI
        project_name = await generate_project_name(
            user_query.query,
            openai_service,
            storage.base_dir
        )

        # 2. Create task with project_name as ID
        task = Task.create_new(
            task=user_query.query,
            project_id=project_name
        )
        task.short_description = user_query.query

        # 3. Create project structure and save
        metadata = storage.create_project(project_name, user_query.query)
        storage.save_task(project_name, task)

        # 4. Return response
        return UserQueryCreate(
            id=project_name,  # Now string instead of int
            task_id=project_name,
            query=user_query.query,
            status=metadata["status"],
            created_at=metadata["created_at"],
            progress=metadata["progress"]
        )

    except Exception as e:
        raise


@router.get("/", response_model=List[UserQueryCreate])
@api_error_handler(OP_GET_QUERIES)
async def get_user_queries(
    request: Request,
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """Get all user queries"""
    try:
        projects = storage.list_projects()
        # Map project metadata to UserQueryCreate format, ensuring task_id is set
        user_queries = []
        for project in projects:
            user_query = UserQueryCreate(
                id=project["id"],
                task_id=project["id"],  # task_id should be the same as project id
                query=project["query"],
                status=project["status"],
                created_at=datetime.fromisoformat(project["created_at"]),
                progress=project["progress"]
            )
            user_queries.append(user_query)
        return user_queries

    except Exception as e:
        raise


@router.delete("/", response_model=dict)
@api_error_handler(OP_DELETE_QUERIES)
async def delete_all_user_queries(request: Request, storage: FileStorageService = Depends(get_file_storage_service)):
    """Delete all user queries"""
    try:
        # Get all projects and delete them
        projects = storage.list_projects()
        deleted_count = 0
        for project in projects:
            success = storage.delete_project(project["id"])
            if success:
                deleted_count += 1

        return {"message": SUCCESS_ALL_QUERIES_DELETED}

    except Exception as e:
        raise


@router.get("/{query_id}", response_model=UserQueryDB)
@api_error_handler(OP_GET_QUERIES)
async def get_user_query(
    query_id: str,  # Changed from int to str
    request: Request,
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """Get a specific user query by ID"""
    try:
        task = storage.load_task(query_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Query {query_id} not found")

        metadata = storage._read_json(storage.base_dir / query_id / "metadata.json")

        return UserQueryDB(
            id=query_id,
            task_id=task.id,
            query=metadata["query"],
            status=metadata["status"],
            created_at=metadata["created_at"],
            progress=metadata["progress"]
        )

    except Exception as e:
        raise




@router.delete("/{query_id}", response_model=dict)
@api_error_handler(OP_DELETE_QUERIES)
async def delete_user_query(
    query_id: str,
    request: Request,
    storage: FileStorageService = Depends(get_file_storage_service)
):
    """Delete a specific user query by ID"""
    try:
        success = storage.delete_project(query_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Query {query_id} not found")

        return {"message": f"Query {query_id} deleted successfully"}

    except Exception as e:
        raise
