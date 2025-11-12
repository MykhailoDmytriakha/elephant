# backend/tests/test_user_queries_routes_files.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from src.main import app
from src.services.file_storage_service import FileStorageService
from src.services.openai_service import OpenAIService
from src.utils.project_utils import generate_project_name


@pytest.fixture
def client():
    """Test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_storage(monkeypatch):
    """Mock FileStorageService."""
    mock = MagicMock(spec=FileStorageService)
    mock.create_project.return_value = {
        "id": "test_project_123",
        "query": "Test query",
        "status": "pending",
        "created_at": "2025-11-12T10:00:00",
        "progress": 0.0
    }
    mock.list_projects.return_value = [
        {
            "id": "test_project_123",
            "query": "Test query",
            "status": "pending",
            "created_at": "2025-11-12T10:00:00",
            "progress": 0.0
        }
    ]
    mock.load_task.return_value = MagicMock(id="test_project_123")
    mock._read_json.return_value = {
        "query": "Test query",
        "status": "pending",
        "created_at": "2025-11-12T10:00:00",
        "progress": 0.0
    }

    # Mock the dependency injection function
    monkeypatch.setattr('src.api.routes.user_queries_routes.get_file_storage_service', lambda: mock)
    return mock


@pytest.fixture
def mock_openai(monkeypatch):
    """Mock OpenAIService."""
    mock = MagicMock(spec=OpenAIService)
    mock.generate_completion = AsyncMock(return_value="test_project_123")

    # Mock the dependency injection function
    monkeypatch.setattr('src.api.routes.user_queries_routes.get_openai_service', lambda: mock)
    # Also mock the generate_project_name function
    monkeypatch.setattr('src.api.routes.user_queries_routes.generate_project_name', AsyncMock(return_value="test_project_123"))
    return mock


class TestUserQueriesRoutesFiles:

    def test_create_user_query(self, client, mock_storage, mock_openai):
        """Test creating a new user query."""
        response = client.post(
            "/api/v1/user-queries/",
            json={"query": "Test query"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test_project_123"
        assert data["query"] == "Test query"
        assert data["status"] == "pending"

        # Verify storage was called
        mock_storage.create_project.assert_called_once_with("test_project_123", "Test query")
        mock_storage.save_task.assert_called_once()

    def test_get_user_queries(self, client, mock_storage):
        """Test getting all user queries."""
        response = client.get("/api/v1/user-queries/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "test_project_123"

        mock_storage.list_projects.assert_called_once()

    def test_get_user_query_by_id(self, client, mock_storage):
        """Test getting a specific user query by ID."""
        response = client.get("/api/v1/user-queries/test_project_123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test_project_123"
        assert data["task_id"] == "test_project_123"

        mock_storage.load_task.assert_called_once_with("test_project_123")

    def test_get_nonexistent_user_query(self, client, mock_storage):
        """Test getting a non-existent user query."""
        mock_storage.load_task.return_value = None

        response = client.get("/api/v1/user-queries/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_delete_user_query(self, client, mock_storage):
        """Test deleting a user query."""
        mock_storage.delete_project.return_value = True

        response = client.delete("/api/v1/user-queries/test_project_123")

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        mock_storage.delete_project.assert_called_once_with("test_project_123")

    def test_delete_nonexistent_user_query(self, client, mock_storage):
        """Test deleting a non-existent user query."""
        mock_storage.delete_project.return_value = False

        response = client.delete("/api/v1/user-queries/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
