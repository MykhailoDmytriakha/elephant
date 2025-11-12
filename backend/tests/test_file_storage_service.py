# backend/tests/test_file_storage_service.py
import pytest
import tempfile
import shutil
from pathlib import Path
from src.services.file_storage_service import FileStorageService
from src.model.task import Task


@pytest.fixture
def temp_base_dir():
    """Create a temporary directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def storage_service(temp_base_dir):
    """Create FileStorageService with temporary directory."""
    return FileStorageService(temp_base_dir)


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return Task.create_new(task="Test task", context="Test context", project_id="test_project")


class TestFileStorageService:

    def test_create_project(self, storage_service, temp_base_dir):
        """Test project creation creates correct folder structure."""
        metadata = storage_service.create_project("test_project", "Test query")

        # Check metadata structure
        assert metadata["id"] == "test_project"
        assert metadata["query"] == "Test query"
        assert metadata["status"] == "pending"
        assert "created_at" in metadata
        assert metadata["progress"] == 0.0

        # Check folder structure
        project_dir = temp_base_dir / "test_project"
        assert project_dir.exists()
        assert (project_dir / "metadata.json").exists()  # project.json created only on save_task
        assert (project_dir / "network_plan").exists()
        assert (project_dir / "docs").exists()

    def test_save_and_load_task(self, storage_service):
        """Test saving and loading a task."""
        # Create project first
        storage_service.create_project("test_project", "Test query")

        task = Task.create_new(task="Test task", project_id="test_project")

        # Save task
        storage_service.save_task("test_project", task)

        # Load task
        loaded_task = storage_service.load_task("test_project")

        assert loaded_task is not None
        assert loaded_task.id == "test_project"
        assert loaded_task.task == "Test task"
        assert loaded_task.state.value == "1. New"

    def test_load_nonexistent_task(self, storage_service):
        """Test loading a non-existent task returns None."""
        task = storage_service.load_task("nonexistent")
        assert task is None

    def test_update_metadata(self, storage_service, temp_base_dir):
        """Test metadata updates."""
        # Create project first
        storage_service.create_project("test_project", "Test query")

        # Update metadata
        storage_service.update_metadata("test_project", status="completed", progress=100.0)

        # Load and verify
        metadata = storage_service._read_json(temp_base_dir / "test_project" / "metadata.json")
        assert metadata["status"] == "completed"
        assert metadata["progress"] == 100.0
        assert "updated_at" in metadata

    def test_list_projects(self, storage_service):
        """Test listing all projects."""
        # Create multiple projects
        storage_service.create_project("project1", "Query 1")
        storage_service.create_project("project2", "Query 2")

        projects = storage_service.list_projects()

        assert len(projects) == 2
        # Should be sorted by created_at desc (newest first)
        assert projects[0]["id"] == "project2"
        assert projects[1]["id"] == "project1"

    def test_delete_project(self, storage_service, temp_base_dir):
        """Test project deletion."""
        # Create project
        storage_service.create_project("test_project", "Test query")

        # Verify it exists
        project_dir = temp_base_dir / "test_project"
        assert project_dir.exists()

        # Delete project
        success = storage_service.delete_project("test_project")
        assert success is True

        # Verify it's gone
        assert not project_dir.exists()

        # Try to delete non-existent project
        success = storage_service.delete_project("nonexistent")
        assert success is False

    def test_save_and_load_stages(self, storage_service):
        """Test saving and loading stages."""
        from src.model.planning import Stage

        # Create project first
        storage_service.create_project("test_project", "Test query")

        # Create a stage
        stage = Stage(
            id="S1",
            name="Stage 1",
            description="First stage",
            result=["Result 1"],
            checkpoints=[]
        )

        # Save stage
        storage_service.save_stage("test_project", stage)

        # Load stages
        stages = storage_service.load_stages("test_project")

        assert len(stages) == 1
        assert stages[0].id == "S1"
        assert stages[0].name == "Stage 1"
