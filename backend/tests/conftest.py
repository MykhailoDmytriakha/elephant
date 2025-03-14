import pytest
import os
from unittest.mock import MagicMock
from datetime import datetime, UTC
from fastapi.testclient import TestClient

# Set required environment variables before imports to avoid validation errors
os.environ["OPENAI_API_KEY"] = "dummy-key-for-testing"

from src.main import app
from src.schemas.user_query import QueryStatus
from src.model.task import Task
from src.services.database_service import DatabaseService

# Constants for testing
MOCK_TASK_ID = "task-123"
MOCK_QUERY_TEXT = "Test query"


@pytest.fixture
def client():
    """Create a test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def mock_task():
    """Create a mock Task that will be used in tests"""
    task = MagicMock(spec=Task)
    task.id = MOCK_TASK_ID
    return task


@pytest.fixture
def mock_db_service():
    """Create a mock database service with predefined responses"""
    # Create timestamp for all responses
    created_at = datetime.now(UTC).isoformat()
    
    # Create the mock database service
    mock_db = MagicMock(spec=DatabaseService)
    
    # Mock insert_task
    mock_db.insert_task.return_value = MOCK_TASK_ID
    
    # Mock insert_user_query
    mock_db.insert_user_query.return_value = {
        "id": 1,
        "task_id": MOCK_TASK_ID,
        "query": MOCK_QUERY_TEXT,
        "status": QueryStatus.PENDING,
        "created_at": created_at,
        "progress": 0.0
    }
    
    # Mock fetch_user_queries
    mock_db.fetch_user_queries.return_value = [
        {
            "id": 1,
            "task_id": MOCK_TASK_ID,
            "query": "Test query 1",
            "status": QueryStatus.PENDING,
            "created_at": created_at,
            "progress": 0.0
        },
        {
            "id": 2,
            "task_id": "task-456",
            "query": "Test query 2",
            "status": QueryStatus.COMPLETED,
            "created_at": created_at,
            "progress": 1.0
        }
    ]
    
    # Mock fetch_user_query_by_id
    mock_db.fetch_user_query_by_id.return_value = {
        "id": 1,
        "task_id": MOCK_TASK_ID,
        "query": MOCK_QUERY_TEXT,
        "status": QueryStatus.PENDING,
        "created_at": created_at,
        "progress": 0.0
    }
    
    # Mock fetch_user_queries_by_task_id
    mock_db.fetch_user_queries_by_task_id.return_value = [
        {
            "id": 1,
            "task_id": MOCK_TASK_ID,
            "query": MOCK_QUERY_TEXT,
            "status": QueryStatus.PENDING,
            "created_at": created_at,
            "progress": 0.0
        }
    ]
    
    return mock_db 