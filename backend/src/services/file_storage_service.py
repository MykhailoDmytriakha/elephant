# backend/src/services/file_storage_service.py
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
from src.model.task import Task
from src.model.planning import Stage
from src.core.config import settings

logger = logging.getLogger(__name__)


class FileStorageService:
    """
    Service for managing project data stored in file system.
    Each project is stored in a separate folder under data/{project_name}/
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or settings.PROJECTS_BASE_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_project(self, project_name: str, query: str) -> dict:
        """
        Create project folder structure and initialize metadata.

        Args:
            project_name: Unique project name (used as folder name and ID)
            query: Original user query

        Returns:
            Metadata dictionary
        """
        project_dir = self.base_dir / project_name

        # Create folder structure
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "network_plan").mkdir(exist_ok=True)
        (project_dir / "docs").mkdir(exist_ok=True)

        # Initialize metadata
        metadata = {
            "id": project_name,
            "query": query,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "progress": 0.0,
            "updated_at": datetime.now().isoformat()
        }

        # Write metadata file
        self._write_json(project_dir / "metadata.json", metadata)

        logger.info(f"Created project: {project_name}")
        return metadata

    def save_task(self, project_name: str, task: Task) -> None:
        """
        Save Task object to project.json.

        Args:
            project_name: Project folder name
            task: Task object to save
        """
        project_dir = self.base_dir / project_name
        if not project_dir.exists():
            raise ValueError(f"Project {project_name} does not exist")

        # Convert task to dict and save
        task_dict = task.to_dict()
        self._write_json(project_dir / "project.json", task_dict)

        # Update metadata timestamp
        self.update_metadata(project_name, updated_at=datetime.now().isoformat())

        logger.debug(f"Saved task for project: {project_name}")

    def load_task(self, project_name: str) -> Optional[Task]:
        """
        Load Task object from project.json.

        Args:
            project_name: Project folder name

        Returns:
            Task object or None if not found
        """
        project_dir = self.base_dir / project_name
        project_file = project_dir / "project.json"

        if not project_file.exists():
            return None

        try:
            task_dict = self._read_json(project_file)
            return Task(**task_dict)
        except Exception as e:
            logger.error(f"Failed to load task for project {project_name}: {e}")
            return None

    def update_metadata(self, project_name: str, **kwargs) -> None:
        """
        Update metadata.json with provided fields.

        Args:
            project_name: Project folder name
            **kwargs: Fields to update
        """
        project_dir = self.base_dir / project_name
        metadata_file = project_dir / "metadata.json"

        if not metadata_file.exists():
            raise ValueError(f"Metadata file not found for project {project_name}")

        # Read existing metadata
        metadata = self._read_json(metadata_file)

        # Update fields
        metadata.update(kwargs)
        metadata["updated_at"] = datetime.now().isoformat()

        # Write back
        self._write_json(metadata_file, metadata)

    def list_projects(self) -> List[dict]:
        """
        List all projects with their metadata.

        Returns:
            List of project metadata dictionaries, sorted by created_at desc
        """
        projects = []

        if not self.base_dir.exists():
            return projects

        for project_dir in self.base_dir.iterdir():
            if project_dir.is_dir():
                metadata_file = project_dir / "metadata.json"
                if metadata_file.exists():
                    try:
                        metadata = self._read_json(metadata_file)
                        metadata["id"] = project_dir.name  # Ensure ID matches folder name
                        projects.append(metadata)
                    except Exception as e:
                        logger.warning(f"Failed to read metadata for {project_dir.name}: {e}")

        # Sort by created_at descending (newest first)
        projects.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return projects

    def delete_project(self, project_name: str) -> bool:
        """
        Delete entire project folder.

        Args:
            project_name: Project folder name

        Returns:
            True if deleted successfully, False otherwise
        """
        project_dir = self.base_dir / project_name

        if not project_dir.exists():
            return False

        try:
            shutil.rmtree(project_dir)
            logger.info(f"Deleted project: {project_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete project {project_name}: {e}")
            return False

    def save_stage(self, project_name: str, stage: Stage) -> None:
        """
        Save individual stage to network_plan/{stage.id}.json.

        Args:
            project_name: Project folder name
            stage: Stage object to save
        """
        project_dir = self.base_dir / project_name
        network_plan_dir = project_dir / "network_plan"
        network_plan_dir.mkdir(exist_ok=True)

        stage_file = network_plan_dir / f"{stage.id}.json"
        stage_dict = stage.model_dump()
        self._write_json(stage_file, stage_dict)

        logger.debug(f"Saved stage {stage.id} for project: {project_name}")

    def load_stages(self, project_name: str) -> List[Stage]:
        """
        Load all stages from network_plan/ folder.

        Args:
            project_name: Project folder name

        Returns:
            List of Stage objects, sorted by ID
        """
        project_dir = self.base_dir / project_name
        network_plan_dir = project_dir / "network_plan"

        if not network_plan_dir.exists():
            return []

        stages = []
        for stage_file in network_plan_dir.glob("*.json"):
            try:
                stage_dict = self._read_json(stage_file)
                stages.append(Stage(**stage_dict))
            except Exception as e:
                logger.warning(f"Failed to load stage from {stage_file}: {e}")

        # Sort stages by ID (S1, S2, S3, etc.)
        stages.sort(key=lambda s: s.id)
        return stages

    def _read_json(self, file_path: Path) -> dict:
        """Read JSON file safely with UTF-8 encoding."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _write_json(self, file_path: Path, data: dict) -> None:
        """Write JSON file atomically with UTF-8 encoding."""
        # Write to temporary file first for atomicity
        temp_file = file_path.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic move
            temp_file.replace(file_path)
        except Exception:
            # Clean up temp file on error
            if temp_file.exists():
                temp_file.unlink()
            raise
