"""
Workspace-Aware Tools for AI Agents

This module creates tools that understand the specific workspace context
for a task, ensuring files are created in the correct project directory
instead of the general .data directory.

Problem solved: Agents creating files in wrong directories due to scope confusion.
"""

import logging
import time
from pathlib import Path
from typing import List, Optional
from src.ai_agents.workspace_manager import get_workspace_manager
from src.ai_agents.agent_tracker import get_tracker

logger = logging.getLogger(__name__)

class WorkspaceAwareTools:
    """Tools that are aware of specific workspace context"""
    
    def __init__(self, task_id: str, session_id: str):
        self.task_id = task_id
        self.session_id = session_id
        self.workspace_manager = get_workspace_manager()
        self.tracker = get_tracker(task_id, session_id)
        
        # Ensure workspace exists and get path
        self.workspace_path = Path(self.workspace_manager.create_or_get_workspace(task_id))
        logger.info(f"WorkspaceAwareTools initialized for task {task_id}, workspace: {self.workspace_path}")
    
    def create_directory(self, path: str) -> str:
        """
        Creates a directory within the specific workspace for this task.
        
        Args:
            path: Relative path within the workspace
            
        Returns:
            Success message or error
        """
        start_time = time.time()
        try:
            # Resolve path relative to workspace, not global .data
            target_path = self.workspace_path / path
            target_path.mkdir(parents=True, exist_ok=True)
            
            relative_display = str(target_path.relative_to(self.workspace_path))
            result = f"✅ Created directory '{relative_display}' in workspace"
            
            execution_time = (time.time() - start_time) * 1000
            self.tracker.log_tool_call(
                "workspace_create_directory", 
                {"path": path, "workspace": str(self.workspace_path)}, 
                result, 
                True, 
                None, 
                execution_time
            )
            
            logger.info(f"Created directory in workspace: {target_path}")
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"❌ Failed to create directory '{path}' in workspace: {str(e)}"
            self.tracker.log_tool_call(
                "workspace_create_directory", 
                {"path": path}, 
                None, 
                False, 
                str(e), 
                execution_time
            )
            logger.error(error_msg)
            return error_msg
    
    def write_file(self, path: str, content: str) -> str:
        """
        Writes a file within the specific workspace for this task.
        
        Args:
            path: Relative path within the workspace
            content: File content
            
        Returns:
            Success message or error
        """
        start_time = time.time()
        try:
            # Resolve path relative to workspace, not global .data
            target_path = self.workspace_path / path
            
            # Ensure parent directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            target_path.write_text(content, encoding='utf-8')
            
            relative_display = str(target_path.relative_to(self.workspace_path))
            result = f"✅ Created file '{relative_display}' in workspace ({len(content)} chars)"
            
            execution_time = (time.time() - start_time) * 1000
            self.tracker.log_tool_call(
                "workspace_write_file", 
                {"path": path, "workspace": str(self.workspace_path), "content_length": len(content)}, 
                result, 
                True, 
                None, 
                execution_time
            )
            
            logger.info(f"Created file in workspace: {target_path}")
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"❌ Failed to create file '{path}' in workspace: {str(e)}"
            self.tracker.log_tool_call(
                "workspace_write_file", 
                {"path": path, "content_length": len(content)}, 
                None, 
                False, 
                str(e), 
                execution_time
            )
            logger.error(error_msg)
            return error_msg
    
    def read_file(self, path: str) -> str:
        """
        Reads a file from the specific workspace for this task.
        
        Args:
            path: Relative path within the workspace
            
        Returns:
            File content or error message
        """
        start_time = time.time()
        try:
            # Resolve path relative to workspace
            target_path = self.workspace_path / path
            
            if not target_path.exists():
                return f"❌ File '{path}' not found in workspace"
            
            content = target_path.read_text(encoding='utf-8')
            relative_display = str(target_path.relative_to(self.workspace_path))
            result = f"📄 Content of '{relative_display}':\n```\n{content}\n```"
            
            execution_time = (time.time() - start_time) * 1000
            self.tracker.log_tool_call(
                "workspace_read_file", 
                {"path": path, "workspace": str(self.workspace_path)}, 
                result[:100] + "..." if len(result) > 100 else result, 
                True, 
                None, 
                execution_time
            )
            
            logger.info(f"Read file from workspace: {target_path}")
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"❌ Failed to read file '{path}' from workspace: {str(e)}"
            self.tracker.log_tool_call(
                "workspace_read_file", 
                {"path": path}, 
                None, 
                False, 
                str(e), 
                execution_time
            )
            logger.error(error_msg)
            return error_msg
    
    def list_directory(self, path: str = ".") -> str:
        """
        Lists contents of a directory within the workspace.
        
        Args:
            path: Relative path within the workspace (default: workspace root)
            
        Returns:
            Directory listing or error message
        """
        start_time = time.time()
        try:
            # Resolve path relative to workspace
            target_path = self.workspace_path / path
            
            if not target_path.exists():
                return f"❌ Directory '{path}' not found in workspace"
            
            if not target_path.is_dir():
                return f"❌ '{path}' is not a directory"
            
            entries = []
            for item in sorted(target_path.iterdir()):
                item_type = "DIR" if item.is_dir() else "FILE"
                size = ""
                if item.is_file():
                    try:
                        size = f" ({item.stat().st_size} bytes)"
                    except:
                        size = ""
                entries.append(f"{item_type}: {item.name}{size}")
            
            if not entries:
                result = f"📁 Directory '{path}' is empty"
            else:
                result = f"📁 Contents of '{path}' in workspace:\n" + "\n".join(entries)
            
            execution_time = (time.time() - start_time) * 1000
            self.tracker.log_tool_call(
                "workspace_list_directory", 
                {"path": path, "workspace": str(self.workspace_path)}, 
                result[:100] + "..." if len(result) > 100 else result, 
                True, 
                None, 
                execution_time
            )
            
            logger.info(f"Listed directory in workspace: {target_path}")
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"❌ Failed to list directory '{path}' in workspace: {str(e)}"
            self.tracker.log_tool_call(
                "workspace_list_directory", 
                {"path": path}, 
                None, 
                False, 
                str(e), 
                execution_time
            )
            logger.error(error_msg)
            return error_msg
    
    def get_workspace_info(self) -> str:
        """
        Get information about the current workspace.
        
        Returns:
            Workspace information
        """
        start_time = time.time()
        try:
            total_files = len(list(self.workspace_path.rglob('*')))
            total_size = sum(f.stat().st_size for f in self.workspace_path.rglob('*') if f.is_file())
            
            result = f"""🏠 **Workspace Information:**
**Task ID:** {self.task_id}
**Path:** {self.workspace_path}
**Total Files:** {total_files}
**Total Size:** {total_size:,} bytes ({total_size / 1024:.1f} KB)
**Type:** Persistent workspace (task-specific scope)

**🎯 Key Feature:** All file operations are scoped to THIS workspace only!
This prevents files from being created in the wrong directories."""
            
            execution_time = (time.time() - start_time) * 1000
            self.tracker.log_tool_call(
                "workspace_get_info", 
                {"task_id": self.task_id}, 
                "Workspace info retrieved", 
                True, 
                None, 
                execution_time
            )
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"❌ Failed to get workspace info: {str(e)}"
            self.tracker.log_tool_call(
                "workspace_get_info", 
                {"task_id": self.task_id}, 
                None, 
                False, 
                str(e), 
                execution_time
            )
            logger.error(error_msg)
            return error_msg


def create_workspace_aware_tools(task_id: str, session_id: str) -> List:
    """
    Creates workspace-aware tools that operate within the specific task's workspace.
    
    These tools prevent the common problem of agents creating files in wrong directories
    by automatically scoping all operations to the task's workspace.
    
    Args:
        task_id: The task ID
        session_id: The session ID
        
    Returns:
        List of workspace-aware tool functions
    """
    workspace_tools = WorkspaceAwareTools(task_id, session_id)
    
    return [
        workspace_tools.create_directory,
        workspace_tools.write_file,
        workspace_tools.read_file,
        workspace_tools.list_directory,
        workspace_tools.get_workspace_info
    ] 