"""
Database Tools for AI Agents

These tools allow agents to query the database and compare database state
with workspace state for better context understanding.
"""

import logging
import json
import time
from typing import List, Dict, Any, Optional
from src.services.database_service import DatabaseService
from src.ai_agents.agent_tracker import get_tracker

logger = logging.getLogger(__name__)

def get_task_from_database(task_id: str) -> str:
    """
    Get task data from the database by task ID.
    
    Args:
        task_id: The task ID to retrieve
        
    Returns:
        Task data as formatted string
    """
    try:
        db_service = DatabaseService()
        task_data = db_service.fetch_task_by_id(task_id)
        
        if not task_data:
            return f"❌ Task {task_id} not found in database"
        
        # Parse the JSON data
        task_json = json.loads(task_data['task_json'])
        
        # Format the output nicely
        result = f"📋 **Task from Database**: {task_id}\n\n"
        result += f"**Basic Info:**\n"
        result += f"  • ID: {task_json.get('id', 'N/A')}\n"
        result += f"  • Task: {task_json.get('task', 'N/A')}\n"
        result += f"  • Description: {task_json.get('short_description', 'N/A')}\n"
        result += f"  • State: {task_json.get('state', 'N/A')}\n"
        result += f"  • Sub Level: {task_json.get('sub_level', 0)}\n"
        result += f"  • Created: {task_json.get('created_at', 'N/A')}\n"
        result += f"  • Updated: {task_json.get('updated_at', 'N/A')}\n"
        
        # Show stages if available
        if task_json.get('network_plan') and task_json['network_plan'].get('stages'):
            stages = task_json['network_plan']['stages']
            result += f"\n**Stages ({len(stages)}):**\n"
            for stage in stages:
                work_count = len(stage.get('work_packages', []))
                result += f"  • {stage.get('id', 'N/A')}: {stage.get('name', 'Unnamed')} ({work_count} work packages)\n"
        
        # Show context answers if available
        if task_json.get('context_answers'):
            result += f"\n**Context Answers:** {len(task_json['context_answers'])} answers\n"
        
        return result
        
    except Exception as e:
        error_msg = f"❌ Failed to get task from database: {str(e)}"
        logger.error(error_msg)
        return error_msg

def get_task_stages_from_database(task_id: str) -> str:
    """
    Get detailed stage information from the database.
    
    Args:
        task_id: The task ID to retrieve stages for
        
    Returns:
        Detailed stage information as formatted string
    """
    try:
        db_service = DatabaseService()
        task_data = db_service.fetch_task_by_id(task_id)
        
        if not task_data:
            return f"❌ Task {task_id} not found in database"
        
        task_json = json.loads(task_data['task_json'])
        
        if not task_json.get('network_plan') or not task_json['network_plan'].get('stages'):
            return f"📋 Task {task_id} has no stages in database"
        
        stages = task_json['network_plan']['stages']
        result = f"🏗️ **Stages from Database**: {task_id}\n\n"
        
        for stage in stages:
            stage_id = stage.get('id', 'N/A')
            stage_name = stage.get('name', 'Unnamed')
            stage_desc = stage.get('description', 'No description')
            work_packages = stage.get('work_packages', [])
            
            result += f"## {stage_id}: {stage_name}\n"
            result += f"   **Description**: {stage_desc}\n"
            result += f"   **Work Packages**: {len(work_packages)}\n"
            
            for i, work in enumerate(work_packages, 1):
                work_id = work.get('id', f'W{i}')
                work_name = work.get('name', 'Unnamed work package')
                exec_tasks = work.get('executable_tasks', [])
                result += f"     • {work_id}: {work_name} ({len(exec_tasks)} executable tasks)\n"
            
            result += "\n"
        
        return result
        
    except Exception as e:
        error_msg = f"❌ Failed to get stages from database: {str(e)}"
        logger.error(error_msg)
        return error_msg

def get_work_package_details_from_database(task_id: str, stage_id: str, work_id: str) -> str:
    """
    Get detailed work package information from the database.
    
    Args:
        task_id: The task ID
        stage_id: The stage ID (e.g., 'S1')
        work_id: The work package ID (e.g., 'S1_W1')
        
    Returns:
        Detailed work package information as formatted string
    """
    try:
        db_service = DatabaseService()
        task_data = db_service.fetch_task_by_id(task_id)
        
        if not task_data:
            return f"❌ Task {task_id} not found in database"
        
        task_json = json.loads(task_data['task_json'])
        
        # Find the stage
        stages = task_json.get('network_plan', {}).get('stages', [])
        target_stage = None
        for stage in stages:
            if stage.get('id') == stage_id:
                target_stage = stage
                break
        
        if not target_stage:
            return f"❌ Stage {stage_id} not found in database"
        
        # Find the work package
        work_packages = target_stage.get('work_packages', [])
        target_work = None
        for work in work_packages:
            if work.get('id') == work_id:
                target_work = work
                break
        
        if not target_work:
            return f"❌ Work package {work_id} not found in stage {stage_id}"
        
        # Format the detailed information
        result = f"📦 **Work Package from Database**: {work_id}\n\n"
        result += f"**Stage**: {stage_id} - {target_stage.get('name', 'Unnamed')}\n"
        result += f"**Work Package**: {target_work.get('name', 'Unnamed')}\n"
        result += f"**Description**: {target_work.get('description', 'No description')}\n"
        
        # Show executable tasks
        exec_tasks = target_work.get('executable_tasks', [])
        if exec_tasks:
            result += f"\n**Executable Tasks ({len(exec_tasks)}):**\n"
            for i, task in enumerate(exec_tasks, 1):
                task_name = task.get('name', f'Task {i}')
                task_desc = task.get('description', 'No description')
                subtasks = task.get('subtasks', [])
                result += f"  {i}. **{task_name}**\n"
                result += f"     Description: {task_desc}\n"
                result += f"     Subtasks: {len(subtasks)}\n"
                
                if subtasks:
                    for j, subtask in enumerate(subtasks[:3], 1):  # Show first 3 subtasks
                        subtask_name = subtask.get('name', f'Subtask {j}')
                        result += f"       • {subtask_name}\n"
                    if len(subtasks) > 3:
                        result += f"       • ... and {len(subtasks) - 3} more subtasks\n"
                result += "\n"
        else:
            result += f"\n**Executable Tasks**: None generated yet\n"
        
        return result
        
    except Exception as e:
        error_msg = f"❌ Failed to get work package details from database: {str(e)}"
        logger.error(error_msg)
        return error_msg

def compare_workspace_with_database(task_id: str) -> str:
    """
    Compare workspace status with database state.
    
    Args:
        task_id: The task ID to compare
        
    Returns:
        Comparison report as formatted string
    """
    try:
        # Get database data
        db_service = DatabaseService()
        task_data = db_service.fetch_task_by_id(task_id)
        
        if not task_data:
            return f"❌ Task {task_id} not found in database for comparison"
        
        task_json = json.loads(task_data['task_json'])
        
        # Get workspace data
        from src.ai_agents.workspace_manager import get_workspace_manager
        workspace_manager = get_workspace_manager()
        workspace_context = workspace_manager.load_context(task_id)
        
        # Start comparison report
        result = f"🔄 **Workspace vs Database Comparison**: {task_id}\n\n"
        
        # Compare basic task info
        result += f"## Basic Task Information\n"
        result += f"**Database State**: {task_json.get('state', 'N/A')}\n"
        result += f"**Database Updated**: {task_json.get('updated_at', 'N/A')}\n"
        
        workspace_status = workspace_context.get('current_status', {})
        result += f"**Workspace Focus**: {workspace_status.get('current_focus', 'Not set')}\n"
        result += f"**Workspace Updated**: {workspace_status.get('last_updated', 'N/A')}\n"
        
        # Compare stages
        db_stages = task_json.get('network_plan', {}).get('stages', [])
        result += f"\n## Stages Comparison\n"
        result += f"**Database Stages**: {len(db_stages)} stages\n"
        
        for stage in db_stages:
            stage_id = stage.get('id', 'N/A')
            work_count = len(stage.get('work_packages', []))
            result += f"  • {stage_id}: {work_count} work packages\n"
        
        # Compare completed tasks
        workspace_completed = workspace_status.get('completed_tasks', [])
        result += f"\n**Workspace Completed Tasks**: {len(workspace_completed)}\n"
        for task in workspace_completed:
            result += f"  • {task}\n"
        
        # Compare files
        workspace_files = workspace_context.get('generated_files', [])
        result += f"\n**Workspace Generated Files**: {len(workspace_files)}\n"
        for file in workspace_files[:5]:  # Show first 5
            result += f"  • {file}\n"
        if len(workspace_files) > 5:
            result += f"  • ... and {len(workspace_files) - 5} more files\n"
        
        # Synchronization recommendations
        result += f"\n## 🎯 **Synchronization Status**\n"
        
        # Check if workspace is ahead of database
        if workspace_completed or workspace_files:
            result += f"✅ **Workspace has additional progress** not reflected in database\n"
            result += f"   Recommendation: Consider updating database with workspace progress\n"
        
        # Check if database has stages but workspace doesn't mention them
        if db_stages and not any('stage' in str(item).lower() for item in workspace_completed):
            result += f"⚠️ **Database has stages** but workspace progress doesn't mention stage work\n"
            result += f"   Recommendation: Review stage implementation status\n"
        
        if not workspace_completed and not db_stages:
            result += f"📝 **Both are in early stage** - minimal data to compare\n"
        
        return result
        
    except Exception as e:
        error_msg = f"❌ Failed to compare workspace with database: {str(e)}"
        logger.error(error_msg)
        return error_msg

def get_all_tasks_from_database() -> str:
    """
    Get a summary of all tasks in the database.
    
    Returns:
        Summary of all tasks as formatted string
    """
    try:
        db_service = DatabaseService()
        all_tasks = db_service.fetch_tasks()
        
        if not all_tasks:
            return "📭 No tasks found in database"
        
        result = f"📋 **All Tasks in Database** ({len(all_tasks)} total)\n\n"
        
        for i, task_data in enumerate(all_tasks, 1):
            try:
                if not task_data or not task_data.get('task_json'):
                    result += f"{i}. **Invalid task data** (ID: {task_data.get('task_id', 'unknown') if task_data else 'unknown'})\n\n"
                    continue
                    
                task_json = json.loads(task_data['task_json'])
                task_id = task_json.get('id', 'N/A')
                task_desc = task_json.get('short_description', 'No description')[:50]
                task_state = task_json.get('state', 'N/A')
                
                # Count stages
                stages = task_json.get('network_plan', {}).get('stages', [])
                stage_count = len(stages)
                
                result += f"{i}. **{task_id}**\n"
                result += f"   Description: {task_desc}{'...' if len(task_desc) == 50 else ''}\n"
                result += f"   State: {task_state}\n"
                result += f"   Stages: {stage_count}\n"
                result += f"   Updated: {task_json.get('updated_at', 'N/A')}\n\n"
                
            except json.JSONDecodeError:
                result += f"{i}. **Invalid JSON data** (ID: {task_data.get('task_id', 'unknown')})\n\n"
            except Exception as e:
                result += f"{i}. **Error processing task** (ID: {task_data.get('task_id', 'unknown') if task_data else 'unknown'}): {str(e)}\n\n"
        
        return result
        
    except Exception as e:
        error_msg = f"❌ Failed to get all tasks from database: {str(e)}"
        logger.error(error_msg)
        return error_msg

def get_user_queries_from_database(task_id: Optional[str] = None) -> str:
    """
    Get user queries from the database, optionally filtered by task ID.
    
    Args:
        task_id: Optional task ID to filter queries
        
    Returns:
        User queries as formatted string
    """
    try:
        db_service = DatabaseService()
        
        if task_id:
            queries = db_service.fetch_user_queries_by_task_id(task_id)
            result = f"💬 **User Queries for Task {task_id}**\n\n"
        else:
            queries = db_service.fetch_user_queries()
            result = f"💬 **All User Queries** ({len(queries)} total)\n\n"
        
        if not queries:
            return result + "No queries found."
        
        for i, query in enumerate(queries, 1):
            query_text = query.get('query', 'No query text')[:60]
            status = query.get('status', 'unknown')
            progress = query.get('progress', 0)
            created = query.get('created_at', 'unknown')
            
            result += f"{i}. **Query ID {query.get('id', 'N/A')}**\n"
            result += f"   Text: {query_text}{'...' if len(query_text) == 60 else ''}\n"
            result += f"   Status: {status}\n"
            result += f"   Progress: {progress * 100:.1f}%\n"
            result += f"   Created: {created}\n"
            result += f"   Task ID: {query.get('task_id', 'N/A')}\n\n"
        
        return result
        
    except Exception as e:
        error_msg = f"❌ Failed to get user queries from database: {str(e)}"
        logger.error(error_msg)
        return error_msg

# ========================================
# Status Update Tools for Agents
# ========================================

def update_subtask_status_in_database(task_id: str, subtask_reference: str, status: str, 
                                     result: Optional[str] = None, error_message: Optional[str] = None) -> str:
    """
    Update a subtask's status directly in the database.
    
    Args:
        task_id: The task ID containing the subtask
        subtask_reference: Reference like "S1_W1_ET1_ST1" or subtask ID
        status: New status ("Pending", "In Progress", "Completed", "Failed", "Cancelled", "Waiting")
        result: Result string (for completed tasks)
        error_message: Error message (for failed tasks)
        
    Returns:
        Status update result as formatted string
    """
    try:
        db_service = DatabaseService()
        
        # Validate status
        valid_statuses = ["Pending", "In Progress", "Completed", "Failed", "Cancelled", "Waiting"]
        if status not in valid_statuses:
            return f"❌ Invalid status '{status}'. Must be one of: {valid_statuses}"
        
        # Perform the update
        update_result = db_service.update_subtask_status(
            task_id=task_id,
            subtask_reference=subtask_reference,
            status=status,
            result=result,
            error_message=error_message
        )
        
        if update_result["success"]:
            result_msg = f"✅ **Status Update Successful**: {subtask_reference}\n\n"
            result_msg += f"**Task ID**: {task_id}\n"
            result_msg += f"**Subtask**: {subtask_reference}\n"
            result_msg += f"**Status**: {update_result['old_status']} → **{update_result['new_status']}**\n"
            result_msg += f"**Updated Fields**: {', '.join(update_result['updated_fields'])}\n"
            result_msg += f"**Message**: {update_result['message']}\n"
            return result_msg
        else:
            return f"❌ **Status Update Failed**: {update_result.get('error', 'Unknown error')}"
        
    except Exception as e:
        error_msg = f"❌ Failed to update subtask status: {str(e)}"
        logger.error(error_msg)
        return error_msg

def complete_subtask_in_database(task_id: str, subtask_reference: str, result_text: str = "Task completed successfully") -> str:
    """
    Mark a subtask as completed in the database.
    
    Args:
        task_id: The task ID containing the subtask
        subtask_reference: Reference like "S1_W1_ET1_ST1" or subtask ID
        result_text: Result description
        
    Returns:
        Completion result as formatted string
    """
    return update_subtask_status_in_database(
        task_id=task_id,
        subtask_reference=subtask_reference,
        status="Completed",
        result=result_text
    )

def fail_subtask_in_database(task_id: str, subtask_reference: str, error_message: str = "Task failed") -> str:
    """
    Mark a subtask as failed in the database.
    
    Args:
        task_id: The task ID containing the subtask
        subtask_reference: Reference like "S1_W1_ET1_ST1" or subtask ID
        error_message: Error description
        
    Returns:
        Failure result as formatted string
    """
    return update_subtask_status_in_database(
        task_id=task_id,
        subtask_reference=subtask_reference,
        status="Failed",
        error_message=error_message
    )

def get_subtask_status_from_database(task_id: str, subtask_reference: str) -> str:
    """
    Get the current status of a subtask from the database.
    
    Args:
        task_id: The task ID containing the subtask
        subtask_reference: Reference like "S1_W1_ET1_ST1" or subtask ID
        
    Returns:
        Subtask status as formatted string
    """
    try:
        db_service = DatabaseService()
        result = db_service.get_subtask_status(task_id, subtask_reference)
        
        if result["success"]:
            subtask = result["subtask"]
            status_msg = f"📋 **Subtask Status**: {subtask_reference}\n\n"
            status_msg += f"**Task ID**: {task_id}\n"
            status_msg += f"**Name**: {subtask.get('name', 'N/A')}\n"
            status_msg += f"**Status**: {subtask.get('status', 'Pending')}\n"
            status_msg += f"**Executor**: {subtask.get('executor_type', 'N/A')}\n"
            
            if subtask.get('started_at'):
                status_msg += f"**Started**: {subtask['started_at']}\n"
            if subtask.get('completed_at'):
                status_msg += f"**Completed**: {subtask['completed_at']}\n"
            if subtask.get('result'):
                status_msg += f"**Result**: {subtask['result']}\n"
            if subtask.get('error_message'):
                status_msg += f"**Error**: {subtask['error_message']}\n"
            
            return status_msg
        else:
            return f"❌ {result.get('error', 'Unknown error')}"
        
    except Exception as e:
        error_msg = f"❌ Failed to get subtask status: {str(e)}"
        logger.error(error_msg)
        return error_msg

# Tool creation functions for agent integration
def create_tracked_database_tools(task_id: str, session_id: str) -> List:
    """Create tracked database tools for agent use"""
    
    tracker = get_tracker(task_id, session_id)
    
    def tracked_get_task_from_database(task_id_param: str) -> str:
        start_time = time.time()
        try:
            result = get_task_from_database(task_id_param)
            execution_time = int((time.time() - start_time) * 1000)
            tracker.log_tool_call(
                tool_name="get_task_from_database",
                parameters={"task_id": task_id_param},
                result=result[:100] + "..." if len(result) > 100 else result,
                success=True,
                execution_time_ms=execution_time
            )
            return result
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            tracker.log_tool_call(
                tool_name="get_task_from_database",
                parameters={"task_id": task_id_param},
                success=False,
                execution_time_ms=execution_time,
                error_message=str(e)
            )
            raise
    
    def tracked_get_task_stages_from_database(task_id_param: str) -> str:
        start_time = time.time()
        try:
            result = get_task_stages_from_database(task_id_param)
            execution_time = int((time.time() - start_time) * 1000)
            tracker.log_tool_call(
                tool_name="get_task_stages_from_database",
                parameters={"task_id": task_id_param},
                result=result[:100] + "..." if len(result) > 100 else result,
                success=True,
                execution_time_ms=execution_time
            )
            return result
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            tracker.log_tool_call(
                tool_name="get_task_stages_from_database",
                parameters={"task_id": task_id_param},
                success=False,
                execution_time_ms=execution_time,
                error_message=str(e)
            )
            raise
    
    def tracked_get_work_package_details_from_database(task_id_param: str, stage_id: str, work_id: str) -> str:
        start_time = time.time()
        try:
            result = get_work_package_details_from_database(task_id_param, stage_id, work_id)
            execution_time = int((time.time() - start_time) * 1000)
            tracker.log_tool_call(
                tool_name="get_work_package_details_from_database",
                parameters={"task_id": task_id_param, "stage_id": stage_id, "work_id": work_id},
                result=result[:100] + "..." if len(result) > 100 else result,
                success=True,
                execution_time_ms=execution_time
            )
            return result
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            tracker.log_tool_call(
                tool_name="get_work_package_details_from_database",
                parameters={"task_id": task_id_param, "stage_id": stage_id, "work_id": work_id},
                success=False,
                execution_time_ms=execution_time,
                error_message=str(e)
            )
            raise
    
    def tracked_compare_workspace_with_database(task_id_param: str) -> str:
        start_time = time.time()
        try:
            result = compare_workspace_with_database(task_id_param)
            execution_time = int((time.time() - start_time) * 1000)
            tracker.log_tool_call(
                tool_name="compare_workspace_with_database",
                parameters={"task_id": task_id_param},
                result=result[:100] + "..." if len(result) > 100 else result,
                success=True,
                execution_time_ms=execution_time
            )
            return result
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            tracker.log_tool_call(
                tool_name="compare_workspace_with_database",
                parameters={"task_id": task_id_param},
                success=False,
                execution_time_ms=execution_time,
                error_message=str(e)
            )
            raise
    
    def tracked_get_all_tasks_from_database() -> str:
        start_time = time.time()
        try:
            result = get_all_tasks_from_database()
            execution_time = int((time.time() - start_time) * 1000)
            tracker.log_tool_call(
                tool_name="get_all_tasks_from_database",
                parameters={},
                result=result[:100] + "..." if len(result) > 100 else result,
                success=True,
                execution_time_ms=execution_time
            )
            return result
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            tracker.log_tool_call(
                tool_name="get_all_tasks_from_database",
                parameters={},
                success=False,
                execution_time_ms=execution_time,
                error_message=str(e)
            )
            raise
    
    def tracked_get_user_queries_from_database(task_id_param: Optional[str] = None) -> str:
        start_time = time.time()
        try:
            result = get_user_queries_from_database(task_id_param)
            execution_time = int((time.time() - start_time) * 1000)
            tracker.log_tool_call(
                tool_name="get_user_queries_from_database",
                parameters={"task_id": task_id_param},
                result=result[:100] + "..." if len(result) > 100 else result,
                success=True,
                execution_time_ms=execution_time
            )
            return result
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            tracker.log_tool_call(
                tool_name="get_user_queries_from_database",
                parameters={"task_id": task_id_param},
                success=False,
                execution_time_ms=execution_time,
                error_message=str(e)
            )
            raise
    
    # Status update tools
    def tracked_update_subtask_status_in_database(task_id_param: str, subtask_reference: str, status: str, 
                                                 result: Optional[str] = None, error_message: Optional[str] = None) -> str:
        start_time = time.time()
        try:
            result_str = update_subtask_status_in_database(task_id_param, subtask_reference, status, result, error_message)
            execution_time = int((time.time() - start_time) * 1000)
            tracker.log_tool_call(
                tool_name="update_subtask_status_in_database",
                parameters={"task_id": task_id_param, "subtask_reference": subtask_reference, "status": status},
                result=result_str[:100] + "..." if len(result_str) > 100 else result_str,
                success=True,
                execution_time_ms=execution_time
            )
            return result_str
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            tracker.log_tool_call(
                tool_name="update_subtask_status_in_database",
                parameters={"task_id": task_id_param, "subtask_reference": subtask_reference, "status": status},
                success=False,
                execution_time_ms=execution_time,
                error_message=str(e)
            )
            raise
    
    def tracked_complete_subtask_in_database(task_id_param: str, subtask_reference: str, result_text: str = "Task completed successfully") -> str:
        start_time = time.time()
        try:
            result_str = complete_subtask_in_database(task_id_param, subtask_reference, result_text)
            execution_time = int((time.time() - start_time) * 1000)
            tracker.log_tool_call(
                tool_name="complete_subtask_in_database",
                parameters={"task_id": task_id_param, "subtask_reference": subtask_reference, "result_text": result_text},
                result=result_str[:100] + "..." if len(result_str) > 100 else result_str,
                success=True,
                execution_time_ms=execution_time
            )
            return result_str
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            tracker.log_tool_call(
                tool_name="complete_subtask_in_database",
                parameters={"task_id": task_id_param, "subtask_reference": subtask_reference, "result_text": result_text},
                success=False,
                execution_time_ms=execution_time,
                error_message=str(e)
            )
            raise
    
    def tracked_fail_subtask_in_database(task_id_param: str, subtask_reference: str, error_message: str = "Task failed") -> str:
        start_time = time.time()
        try:
            result_str = fail_subtask_in_database(task_id_param, subtask_reference, error_message)
            execution_time = int((time.time() - start_time) * 1000)
            tracker.log_tool_call(
                tool_name="fail_subtask_in_database",
                parameters={"task_id": task_id_param, "subtask_reference": subtask_reference, "error_message": error_message},
                result=result_str[:100] + "..." if len(result_str) > 100 else result_str,
                success=True,
                execution_time_ms=execution_time
            )
            return result_str
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            tracker.log_tool_call(
                tool_name="fail_subtask_in_database",
                parameters={"task_id": task_id_param, "subtask_reference": subtask_reference, "error_message": error_message},
                success=False,
                execution_time_ms=execution_time,
                error_message=str(e)
            )
            raise
    
    def tracked_get_subtask_status_from_database(task_id_param: str, subtask_reference: str) -> str:
        start_time = time.time()
        try:
            result_str = get_subtask_status_from_database(task_id_param, subtask_reference)
            execution_time = int((time.time() - start_time) * 1000)
            tracker.log_tool_call(
                tool_name="get_subtask_status_from_database",
                parameters={"task_id": task_id_param, "subtask_reference": subtask_reference},
                result=result_str[:100] + "..." if len(result_str) > 100 else result_str,
                success=True,
                execution_time_ms=execution_time
            )
            return result_str
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            tracker.log_tool_call(
                tool_name="get_subtask_status_from_database",
                parameters={"task_id": task_id_param, "subtask_reference": subtask_reference},
                success=False,
                execution_time_ms=execution_time,
                error_message=str(e)
            )
            raise
    
    return [
        tracked_get_task_from_database,
        tracked_get_task_stages_from_database,
        tracked_get_work_package_details_from_database,
        tracked_compare_workspace_with_database,
        tracked_get_all_tasks_from_database,
        tracked_get_user_queries_from_database,
        tracked_update_subtask_status_in_database,
        tracked_complete_subtask_in_database,
        tracked_fail_subtask_in_database,
        tracked_get_subtask_status_from_database
    ] 