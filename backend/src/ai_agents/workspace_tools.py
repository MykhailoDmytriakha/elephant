"""
Workspace Management Tools for AI Agents

These tools allow agents to actively manage their persistent workspaces,
including updating project notes, managing status, and viewing context.
"""

import logging
from typing import List, Dict, Any, Optional
from src.ai_agents.workspace_manager import get_workspace_manager

logger = logging.getLogger(__name__)

def update_workspace_notes(task_id: str, notes: str) -> str:
    """
    Update project notes in the workspace.
    
    Args:
        task_id: The task ID
        notes: Notes to add to the project
        
    Returns:
        Success message
    """
    try:
        workspace_manager = get_workspace_manager()
        # Ensure workspace exists
        workspace_manager.create_or_get_workspace(task_id)
        workspace_manager.update_project_notes(task_id, notes)
        return f"✅ Updated project notes for task {task_id}"
    except Exception as e:
        error_msg = f"❌ Failed to update project notes: {str(e)}"
        logger.error(error_msg)
        return error_msg

def update_workspace_status(task_id: str, current_focus: Optional[str] = None, 
                          completed_tasks: Optional[List[str]] = None,
                          next_actions: Optional[List[str]] = None,
                          files_created: Optional[List[str]] = None) -> str:
    """
    Update the current status of the workspace.
    
    Args:
        task_id: The task ID
        current_focus: What the agent is currently focusing on
        completed_tasks: List of completed tasks
        next_actions: List of planned next actions
        files_created: List of files created in this session
        
    Returns:
        Success message
    """
    try:
        workspace_manager = get_workspace_manager()
        # Ensure workspace exists
        workspace_manager.create_or_get_workspace(task_id)
        
        updates = {}
        if current_focus is not None:
            updates['current_focus'] = current_focus
        if completed_tasks is not None:
            updates['completed_tasks'] = completed_tasks
        if next_actions is not None:
            updates['next_actions'] = next_actions
        if files_created is not None:
            updates['files_created'] = files_created
        
        if updates:
            workspace_manager.update_status(task_id, **updates)
            return f"✅ Updated workspace status for task {task_id}: {list(updates.keys())}"
        else:
            return "⚠️ No updates provided"
            
    except Exception as e:
        error_msg = f"❌ Failed to update workspace status: {str(e)}"
        logger.error(error_msg)
        return error_msg

def get_workspace_context(task_id: str) -> str:
    """
    Get a summary of the workspace context including previous work and current status.
    
    Args:
        task_id: The task ID
        
    Returns:
        Human-readable workspace context summary
    """
    try:
        workspace_manager = get_workspace_manager()
        # Ensure workspace exists
        workspace_manager.create_or_get_workspace(task_id)
        context_summary = workspace_manager.get_context_summary(task_id)
        return context_summary
    except Exception as e:
        error_msg = f"❌ Failed to get workspace context: {str(e)}"
        logger.error(error_msg)
        return error_msg

def get_workspace_session_history(task_id: str, last_n_sessions: int = 5) -> str:
    """
    Get recent session history from the workspace.
    
    Args:
        task_id: The task ID
        last_n_sessions: Number of recent sessions to return
        
    Returns:
        Recent session history
    """
    try:
        workspace_manager = get_workspace_manager()
        # Ensure workspace exists
        workspace_manager.create_or_get_workspace(task_id)
        context = workspace_manager.load_context(task_id)
        
        if 'session_history' not in context:
            return "No session history found in workspace"
        
        session_history = context['session_history']
        
        # Parse sessions
        sessions = []
        current_session = []
        
        for line in session_history.split('\n'):
            if line.startswith('=== Session'):
                if current_session:
                    sessions.append('\n'.join(current_session))
                current_session = [line]
            elif current_session:
                current_session.append(line)
        
        if current_session:
            sessions.append('\n'.join(current_session))
        
        # Return last N sessions
        recent_sessions = sessions[-last_n_sessions:] if sessions else []
        
        if not recent_sessions:
            return "No recent sessions found"
        
        result = f"📖 Last {len(recent_sessions)} session(s):\n\n"
        result += "\n\n".join(recent_sessions)
        
        return result
        
    except Exception as e:
        error_msg = f"❌ Failed to get session history: {str(e)}"
        logger.error(error_msg)
        return error_msg

def save_file_to_workspace(task_id: str, filename: str, content: str, 
                          subfolder: str = "generated_files") -> str:
    """
    Save a file to the workspace's generated_files directory.
    
    Args:
        task_id: The task ID
        filename: Name of the file to save
        content: Content to save
        subfolder: Subfolder within workspace (default: generated_files)
        
    Returns:
        Success message with file path
    """
    try:
        workspace_manager = get_workspace_manager()
        # Ensure workspace exists
        workspace_manager.create_or_get_workspace(task_id)
        workspace_path = workspace_manager.get_workspace_path(task_id)
        
        from pathlib import Path
        target_dir = Path(workspace_path) / subfolder
        target_dir.mkdir(exist_ok=True)
        
        file_path = target_dir / filename
        file_path.write_text(content, encoding='utf-8')
        
        # Update status to include this file
        workspace_manager.update_status(
            task_id, 
            files_created=[filename]  # This will be merged with existing files
        )
        
        return f"✅ Saved file: {file_path}"
        
    except Exception as e:
        error_msg = f"❌ Failed to save file to workspace: {str(e)}"
        logger.error(error_msg)
        return error_msg

def list_workspace_files(task_id: str) -> str:
    """
    List all files in the workspace.
    
    Args:
        task_id: The task ID
        
    Returns:
        List of files in the workspace
    """
    try:
        workspace_manager = get_workspace_manager()
        # Ensure workspace exists
        workspace_manager.create_or_get_workspace(task_id)
        context = workspace_manager.load_context(task_id)
        
        result = f"📁 Workspace files for task {task_id}:\n\n"
        
        # Core files
        result += "**Core Files:**\n"
        result += "- session_history.txt (conversation log)\n"
        result += "- project_notes.md (agent's understanding)\n"
        result += "- current_status.json (progress tracking)\n\n"
        
        # Generated files
        generated_files = context.get('generated_files', [])
        if generated_files:
            result += f"**Generated Files ({len(generated_files)}):**\n"
            for file in generated_files:
                result += f"- {file}\n"
        else:
            result += "**Generated Files:** None yet\n"
        
        return result
        
    except Exception as e:
        error_msg = f"❌ Failed to list workspace files: {str(e)}"
        logger.error(error_msg)
        return error_msg

def get_workspace_path_info(task_id: str) -> str:
    """
    Get the workspace path and basic information.
    
    Args:
        task_id: The task ID
        
    Returns:
        Workspace path and info
    """
    try:
        workspace_manager = get_workspace_manager()
        workspace_path = workspace_manager.get_workspace_path(task_id)
        
        from pathlib import Path
        workspace_dir = Path(workspace_path)
        
        if workspace_dir.exists():
            # Count files
            total_files = len(list(workspace_dir.rglob('*')))
            total_size = sum(f.stat().st_size for f in workspace_dir.rglob('*') if f.is_file())
            
            result = f"📁 Workspace Information:\n"
            result += f"**Path:** {workspace_path}\n"
            result += f"**Status:** ✅ Exists\n"
            result += f"**Total Files:** {total_files}\n"
            result += f"**Total Size:** {total_size:,} bytes ({total_size / 1024:.1f} KB)\n"
            result += f"**Type:** Persistent (no random suffix)\n"
        else:
            result = f"📁 Workspace Information:\n"
            result += f"**Path:** {workspace_path}\n"
            result += f"**Status:** ❌ Not created yet\n"
            result += f"**Type:** Persistent (will be created on first use)\n"
        
        return result
        
    except Exception as e:
        error_msg = f"❌ Failed to get workspace info: {str(e)}"
        logger.error(error_msg)
        return error_msg

# Tool creation functions for agent integration
def create_workspace_management_tools(task_id: str, session_id: str) -> List:
    """Create workspace management tools for agent use"""
    
    def workspace_update_notes(notes: str) -> str:
        return update_workspace_notes(task_id, notes)
    
    def workspace_update_status(current_focus: Optional[str] = None, 
                              completed_tasks: Optional[List[str]] = None,
                              next_actions: Optional[List[str]] = None,
                              files_created: Optional[List[str]] = None) -> str:
        return update_workspace_status(task_id, current_focus, completed_tasks, next_actions, files_created)
    
    def workspace_get_context() -> str:
        return get_workspace_context(task_id)
    
    def workspace_get_history(last_n_sessions: int = 5) -> str:
        return get_workspace_session_history(task_id, last_n_sessions)
    
    def workspace_save_file(filename: str, content: str, subfolder: str = "generated_files") -> str:
        return save_file_to_workspace(task_id, filename, content, subfolder)
    
    def workspace_list_files() -> str:
        return list_workspace_files(task_id)
    
    def workspace_get_info() -> str:
        return get_workspace_path_info(task_id)
    
    return [
        workspace_update_notes,
        workspace_update_status,
        workspace_get_context,
        workspace_get_history,
        workspace_save_file,
        workspace_list_files,
        workspace_get_info
    ] 