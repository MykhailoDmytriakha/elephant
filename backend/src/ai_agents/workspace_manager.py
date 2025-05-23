"""
Persistent Workspace Manager for AI Agents

This module implements a persistent workspace system where each task/project 
gets ONE workspace that persists across all sessions and messages.
No more random suffixes creating hundreds of duplicate folders.

Inspired by Manus AI and Cursor AI patterns for workspace persistence.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from src.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class SessionEntry:
    """Represents a single session entry in the history"""
    timestamp: str
    user_message: str
    agent_response: str
    session_id: str

@dataclass
class ProjectStatus:
    """Current status of the project"""
    last_updated: str
    current_focus: str
    completed_tasks: List[str]
    next_actions: List[str]
    files_created: List[str]
    user_preferences: Dict[str, Any]

class PersistentWorkspaceManager:
    """Manages persistent workspaces for AI agents"""
    
    def __init__(self, base_dir: Optional[str] = None):
        """Initialize the workspace manager"""
        if base_dir:
            self.base_dir = Path(base_dir) / "projects"
        else:
            # Use the ALLOWED_BASE_DIR if available, otherwise current working directory
            base_path = Path(settings.ALLOWED_BASE_DIR_RESOLVED or Path.cwd())
            # Check if we're already in .data directory to avoid double nesting
            if base_path.name == ".data":
                self.base_dir = base_path / "projects"
            else:
                self.base_dir = base_path / ".data" / "projects"
        
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized PersistentWorkspaceManager with base_dir: {self.base_dir}")
    
    def get_workspace_path(self, task_id: str) -> str:
        """Get persistent workspace path for a task (no random suffix!)"""
        workspace_path = self.base_dir / f"task_{task_id}"
        return str(workspace_path)
    
    def create_or_get_workspace(self, task_id: str) -> str:
        """
        Create workspace if it doesn't exist, or return existing one.
        This ensures ONE workspace per task, persistent across sessions.
        """
        workspace_path = Path(self.get_workspace_path(task_id))
        
        # If workspace exists, just return it (persistence!)
        if workspace_path.exists():
            logger.info(f"Found existing workspace for task {task_id}: {workspace_path}")
            return str(workspace_path)
        
        # Create new workspace structure
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (workspace_path / "generated_files").mkdir(exist_ok=True)
        (workspace_path / "temp").mkdir(exist_ok=True)
        
        # Create initial context files
        self._initialize_context_files(workspace_path, task_id)
        
        logger.info(f"Created new workspace for task {task_id}: {workspace_path}")
        return str(workspace_path)
    
    def _initialize_context_files(self, workspace_path: Path, task_id: str):
        """Initialize context files for a new workspace"""
        
        # Create empty session history
        session_history_path = workspace_path / "session_history.txt"
        with open(session_history_path, 'w', encoding='utf-8') as f:
            f.write(f"# Session History for Task {task_id}\n")
            f.write(f"# Created: {datetime.now().isoformat()}\n\n")
        
        # Create initial project notes
        project_notes_path = workspace_path / "project_notes.md"
        with open(project_notes_path, 'w', encoding='utf-8') as f:
            f.write(f"# Project Notes - Task {task_id}\n\n")
            f.write("## Overview\n")
            f.write("- Goal: [To be determined]\n")
            f.write("- Status: Just started\n\n")
            f.write("## Progress\n")
            f.write("- ✅ Workspace created\n\n")
            f.write("## Key Decisions\n")
            f.write("- [Decisions will be recorded here]\n\n")
        
        # Create initial current status
        current_status_path = workspace_path / "current_status.json"
        initial_status = ProjectStatus(
            last_updated=datetime.now().isoformat(),
            current_focus="Initial setup",
            completed_tasks=[],
            next_actions=["Analyze task requirements"],
            files_created=["session_history.txt", "project_notes.md", "current_status.json"],
            user_preferences={}
        )
        with open(current_status_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(initial_status), f, indent=2, ensure_ascii=False)
    
    def load_context(self, task_id: str) -> Dict[str, Any]:
        """Load existing context for a task workspace"""
        workspace_path = Path(self.get_workspace_path(task_id))
        context: Dict[str, Any] = {}
        
        # Load session history
        session_history_path = workspace_path / "session_history.txt"
        if session_history_path.exists():
            with open(session_history_path, 'r', encoding='utf-8') as f:
                context['session_history'] = f.read()
        
        # Load project notes
        project_notes_path = workspace_path / "project_notes.md"
        if project_notes_path.exists():
            with open(project_notes_path, 'r', encoding='utf-8') as f:
                context['project_notes'] = f.read()
        
        # Load current status
        current_status_path = workspace_path / "current_status.json"
        if current_status_path.exists():
            try:
                with open(current_status_path, 'r', encoding='utf-8') as f:
                    context['current_status'] = json.load(f)
            except json.JSONDecodeError as e:
                logger.warning(f"Could not parse current_status.json: {e}")
                context['current_status'] = {}
        
        # List generated files
        generated_files_path = workspace_path / "generated_files"
        if generated_files_path.exists():
            context['generated_files'] = [
                str(f.relative_to(generated_files_path)) 
                for f in generated_files_path.rglob('*') 
                if f.is_file()
            ]
        else:
            context['generated_files'] = []
        
        logger.info(f"Loaded context for task {task_id}: {len(context)} components")
        return context
    
    def save_session(self, task_id: str, user_message: str, agent_response: str, session_id: str):
        """Save a session interaction to the workspace"""
        workspace_path = Path(self.get_workspace_path(task_id))
        session_history_path = workspace_path / "session_history.txt"
        
        # Append session to history
        timestamp = datetime.now().isoformat()
        with open(session_history_path, 'a', encoding='utf-8') as f:
            f.write(f"\n=== Session {timestamp} ===\n")
            f.write(f"Session ID: {session_id}\n")
            f.write(f"User: {user_message}\n")
            f.write(f"Agent: {agent_response}\n")
        
        logger.info(f"Saved session to workspace for task {task_id}")
    
    def update_project_notes(self, task_id: str, notes_update: str):
        """Update project notes with new information"""
        workspace_path = Path(self.get_workspace_path(task_id))
        project_notes_path = workspace_path / "project_notes.md"
        
        timestamp = datetime.now().isoformat()
        with open(project_notes_path, 'a', encoding='utf-8') as f:
            f.write(f"\n## Update - {timestamp}\n")
            f.write(f"{notes_update}\n")
        
        logger.info(f"Updated project notes for task {task_id}")
    
    def update_status(self, task_id: str, **updates):
        """Update the current status with new information"""
        workspace_path = Path(self.get_workspace_path(task_id))
        current_status_path = workspace_path / "current_status.json"
        
        # Load existing status
        status = {}
        if current_status_path.exists():
            try:
                with open(current_status_path, 'r', encoding='utf-8') as f:
                    status = json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not load existing status, creating new one")
        
        # Update with new values
        status.update(updates)
        status['last_updated'] = datetime.now().isoformat()
        
        # Save updated status
        with open(current_status_path, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Updated status for task {task_id}: {list(updates.keys())}")
    
    def get_context_summary(self, task_id: str) -> str:
        """Get a human-readable summary of the workspace context"""
        context = self.load_context(task_id)
        workspace_path = self.get_workspace_path(task_id)
        
        summary = f"# Workspace Context for Task {task_id}\n\n"
        summary += f"**Workspace Path**: {workspace_path}\n\n"
        
        # Current status
        if 'current_status' in context:
            status = context['current_status']
            summary += f"**Current Focus**: {status.get('current_focus', 'Not set')}\n"
            summary += f"**Last Updated**: {status.get('last_updated', 'Unknown')}\n"
            
            if status.get('completed_tasks'):
                summary += f"**Completed Tasks**: {', '.join(status['completed_tasks'])}\n"
            
            if status.get('next_actions'):
                summary += f"**Next Actions**: {', '.join(status['next_actions'])}\n"
        
        # Generated files
        if context.get('generated_files'):
            summary += f"**Generated Files**: {len(context['generated_files'])} files\n"
            for file in context['generated_files'][:5]:  # Show first 5
                summary += f"  - {file}\n"
            if len(context['generated_files']) > 5:
                summary += f"  - ... and {len(context['generated_files']) - 5} more\n"
        
        # Session history summary
        if 'session_history' in context:
            lines = context['session_history'].split('\n')
            session_count = len([line for line in lines if line.startswith('=== Session')])
            summary += f"**Previous Sessions**: {session_count} sessions\n"
        
        return summary
    
    def cleanup_old_workspaces(self, keep_days: int = 30):
        """Clean up workspaces older than specified days (future enhancement)"""
        # This could be implemented to clean up very old workspaces
        # For now, we'll keep all workspaces since persistence is the goal
        logger.info(f"Cleanup would run for workspaces older than {keep_days} days")
    
    def migrate_existing_workspaces(self, old_workspace_dir: str, task_id: str):
        """Migrate files from old random-suffix workspaces to persistent workspace"""
        old_dir = Path(old_workspace_dir)
        if not old_dir.exists():
            logger.warning(f"Old workspace directory not found: {old_dir}")
            return
        
        # Ensure the persistent workspace exists first
        workspace_path = self.create_or_get_workspace(task_id)
        workspace_dir = Path(workspace_path)
        
        migration_dir = workspace_dir / "migrated_files"
        migration_dir.mkdir(exist_ok=True)
        
        # Copy files from old workspace
        files_migrated = 0
        for file_path in old_dir.rglob('*'):
            if file_path.is_file():
                try:
                    # Create relative path structure
                    rel_path = file_path.relative_to(old_dir)
                    new_path = migration_dir / rel_path
                    new_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    new_path.write_bytes(file_path.read_bytes())
                    files_migrated += 1
                except Exception as e:
                    logger.warning(f"Could not migrate file {file_path}: {e}")
        
        logger.info(f"Migrated {files_migrated} files from {old_dir} to {migration_dir}")
        
        # Update project notes about migration
        self.update_project_notes(
            task_id, 
            f"Migrated {files_migrated} files from old workspace: {old_dir}"
        )

# Global instance
_workspace_manager = None

def get_workspace_manager() -> PersistentWorkspaceManager:
    """Get the global workspace manager instance"""
    global _workspace_manager
    if _workspace_manager is None:
        _workspace_manager = PersistentWorkspaceManager()
    return _workspace_manager 