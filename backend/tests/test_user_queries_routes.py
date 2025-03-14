import pytest
from datetime import datetime, UTC
import uuid
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.main import app
from src.schemas.user_query import QueryStatus
from src.model.task import Task
from src.api.deps import get_db_service
from tests.conftest import MOCK_TASK_ID, MOCK_QUERY_TEXT

client = TestClient(app)

# Mock task ID for consistent testing
MOCK_TASK_ID = "task-123"
MOCK_QUERY_TEXT = "Test query"


@pytest.fixture
def mock_task():
    """Create a mock Task that will be used in tests"""
    task = MagicMock()
    task.id = MOCK_TASK_ID
    return task


@pytest.fixture
def mock_db_responses():
    """Create mock database responses that will be used in tests"""
    created_at = datetime.now(UTC).isoformat()
    return {
        "user_query": {
            "id": 1,
            "task_id": MOCK_TASK_ID,
            "query": MOCK_QUERY_TEXT,
            "status": QueryStatus.PENDING,
            "created_at": created_at,
            "progress": 0.0
        },
        "user_queries": [
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
        ],
        "task_queries": [
            {
                "id": 1,
                "task_id": MOCK_TASK_ID,
                "query": MOCK_QUERY_TEXT,
                "status": QueryStatus.PENDING,
                "created_at": created_at,
                "progress": 0.0
            }
        ]
    }


@pytest.fixture
def mock_db():
    """Create a mock database service"""
    mock = MagicMock()
    return mock


# This test file demonstrates how to test FastAPI routes with dependency injection
# The key approach is:
# 1. Create a test app with dependency overrides to mock the database service
# 2. Import the router and include it in the test app
# 3. Create a TestClient using the test app
# 4. Use pytest fixtures to manage dependencies
# 5. Use patch decorators for external dependencies like Task.create_new


# The key is to patch the dependency correctly - we need to modify the app
@pytest.fixture
def test_app(mock_db_service, mock_task):
    """
    Create a test FastAPI app with mocked dependencies.
    
    This approach overrides the get_db_service dependency with our mock_db_service,
    which allows us to control the behavior of the database in our tests.
    """
    # Create a copy of the app for testing
    test_app = FastAPI()
    test_app.dependency_overrides = {
        get_db_service: lambda: mock_db_service
    }
    
    # Import the router after we've set up the dependency override
    from src.api.routes.user_queries_routes import router
    test_app.include_router(router, prefix="/user-queries", tags=["User Queries"])
    
    return test_app


@pytest.fixture
def test_client(test_app):
    """Create a test client for the test FastAPI app."""
    return TestClient(test_app)


@patch.object(Task, 'create_new')
def test_create_user_query(mock_create_new, test_client, mock_task, mock_db_service):
    """Test creating a user query"""
    # Setup Task.create_new mock
    mock_create_new.return_value = mock_task
    
    # Make the request
    response = test_client.post("/user-queries/", json={"query": MOCK_QUERY_TEXT})
    
    # Assert response is correct
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == MOCK_QUERY_TEXT
    assert data["task_id"] == MOCK_TASK_ID
    assert data["status"] == QueryStatus.PENDING
    assert "created_at" in data
    assert data["progress"] == 0.0
    
    # Verify the mocks were called correctly
    mock_db_service.insert_task.assert_called_once()
    mock_db_service.insert_user_query.assert_called_once()


@patch.object(Task, 'create_new')
def test_create_user_query_error(mock_create_new, test_client, mock_task, mock_db_service):
    """Test handling error when creating a user query"""
    # Setup Task.create_new mock
    mock_create_new.return_value = mock_task
    
    # Setup database mock to raise exception
    mock_db_service.insert_task.side_effect = Exception("Database error")
    
    # Make the request
    response = test_client.post("/user-queries/", json={"query": MOCK_QUERY_TEXT})
    
    # Assert response is correct
    assert response.status_code == 500
    data = response.json()
    assert "Failed to create user query" in data["detail"]


def test_get_user_queries(test_client, mock_db_service):
    """Test getting all user queries"""
    # Make the request
    response = test_client.get("/user-queries/")
    
    # Assert response is correct
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["query"] == "Test query 1"
    assert data[1]["query"] == "Test query 2"
    
    # Verify the mock was called correctly
    mock_db_service.fetch_user_queries.assert_called_once()


def test_delete_all_user_queries(test_client, mock_db_service):
    """Test deleting all user queries"""
    # Make the request
    response = test_client.delete("/user-queries/")
    
    # Assert response is correct
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "All user queries deleted successfully"
    
    # Verify the mock was called correctly
    mock_db_service.delete_all_user_queries.assert_called_once()


def test_get_user_query(test_client, mock_db_service):
    """Test getting a specific user query by ID"""
    # Make the request
    response = test_client.get("/user-queries/1")
    
    # Assert response is correct
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["query"] == MOCK_QUERY_TEXT
    
    # Verify the mock was called correctly
    mock_db_service.fetch_user_query_by_id.assert_called_once_with(1)


def test_get_user_query_not_found(test_client, mock_db_service):
    """Test getting a user query that doesn't exist"""
    # Reset the mock and set the return value to None
    mock_db_service.fetch_user_query_by_id.reset_mock()
    mock_db_service.fetch_user_query_by_id.return_value = None
    
    # Make the request
    response = test_client.get("/user-queries/999")
    
    # Assert response is correct
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "User query not found"


def test_get_task_user_queries(test_client, mock_db_service):
    """Test getting all user queries for a specific task"""
    # Make the request
    response = test_client.get(f"/user-queries/tasks/{MOCK_TASK_ID}")
    
    # Assert response is correct
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["task_id"] == MOCK_TASK_ID
    
    # Verify the mock was called correctly
    mock_db_service.fetch_user_queries_by_task_id.assert_called_once_with(MOCK_TASK_ID)


def test_get_task_user_queries_not_found(test_client, mock_db_service):
    """Test getting user queries for a task that doesn't exist"""
    # Reset the mock and set the return value to an empty list
    mock_db_service.fetch_user_queries_by_task_id.reset_mock()
    mock_db_service.fetch_user_queries_by_task_id.return_value = []
    
    # Make the request
    response = test_client.get("/user-queries/tasks/nonexistent-task")
    
    # Assert response is correct
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "No queries found for task ID: nonexistent-task" 