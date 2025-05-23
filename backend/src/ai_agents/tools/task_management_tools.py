import logging
import time
from typing import List, Optional, Dict, Any
from src.model.task import Task
from src.model.planning import Stage
from src.model.work import Work
from src.model.executable_task import ExecutableTask
from src.model.subtask import Subtask
from src.api.utils import deserialize_task
from src.core.config import settings

logger = logging.getLogger(__name__)

# Use lazy initialization to avoid circular imports
_db_service = None
_openai_service = None
_problem_analyzer = None

def _get_services():
    """Lazy initialization of services to avoid circular imports."""
    global _db_service, _openai_service, _problem_analyzer
    
    if _db_service is None:
        from src.services.database_service import DatabaseService
        _db_service = DatabaseService()
    
    if _openai_service is None:
        from src.services.openai_service import OpenAIService
        _openai_service = OpenAIService()
    
    if _problem_analyzer is None:
        from src.services.problem_analyzer import ProblemAnalyzer
        _problem_analyzer = ProblemAnalyzer(_openai_service, _db_service)
    
    return _db_service, _openai_service, _problem_analyzer

async def generate_work_packages_for_stage(task_id: str, stage_id: str) -> str:
    """
    Generates work packages for a specific stage in a task.
    
    Args:
        task_id: The ID of the task
        stage_id: The ID of the stage to generate work packages for
        
    Returns:
        String describing the result
    """
    logger.info(f"Generating work packages for task {task_id}, stage {stage_id}")
    
    try:
        # Get services with lazy initialization
        db_service, openai_service, problem_analyzer = _get_services()
        
        # Fetch task from database
        task_data = db_service.fetch_task_by_id(task_id)
        task = deserialize_task(task_data, task_id)
        
        # Generate work packages
        generated_work = await problem_analyzer.generate_stage_work(task, stage_id)
        
        result = f"Successfully generated {len(generated_work)} work packages for stage {stage_id}:\n"
        for i, work in enumerate(generated_work, 1):
            result += f"{i}. {work.name}: {work.description[:100]}{'...' if len(work.description) > 100 else ''}\n"
        
        return result
        
    except Exception as e:
        error_msg = f"Error generating work packages for stage {stage_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg

async def generate_tasks_for_work_package(task_id: str, stage_id: str, work_id: str) -> str:
    """
    Generates executable tasks for a specific work package.
    
    Args:
        task_id: The ID of the task
        stage_id: The ID of the stage
        work_id: The ID of the work package to generate tasks for
        
    Returns:
        String describing the result
    """
    logger.info(f"Generating tasks for task {task_id}, stage {stage_id}, work {work_id}")
    
    try:
        # Get services with lazy initialization
        db_service, openai_service, problem_analyzer = _get_services()
        
        # Fetch task from database
        task_data = db_service.fetch_task_by_id(task_id)
        task = deserialize_task(task_data, task_id)
        
        # Generate tasks
        generated_tasks = await problem_analyzer.generate_tasks_for_work(task, stage_id, work_id)
        
        result = f"Successfully generated {len(generated_tasks)} executable tasks for work package {work_id}:\n"
        for i, task_item in enumerate(generated_tasks, 1):
            result += f"{i}. {task_item.name}: {task_item.description[:80]}{'...' if len(task_item.description) > 80 else ''}\n"
        
        return result
        
    except Exception as e:
        error_msg = f"Error generating tasks for work package {work_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg

async def generate_subtasks_for_executable_task(task_id: str, stage_id: str, work_id: str, executable_task_id: str) -> str:
    """
    Generates subtasks for a specific executable task.
    
    Args:
        task_id: The ID of the task
        stage_id: The ID of the stage
        work_id: The ID of the work package
        executable_task_id: The ID of the executable task to generate subtasks for
        
    Returns:
        String describing the result
    """
    logger.info(f"Generating subtasks for executable task {executable_task_id}")
    
    try:
        # Get services with lazy initialization
        db_service, openai_service, problem_analyzer = _get_services()
        
        # Fetch task from database
        task_data = db_service.fetch_task_by_id(task_id)
        task = deserialize_task(task_data, task_id)
        
        # Generate subtasks
        generated_subtasks = await problem_analyzer.generate_subtasks_for_executable_task(task, stage_id, work_id, executable_task_id)
        
        result = f"Successfully generated {len(generated_subtasks)} subtasks for executable task {executable_task_id}:\n"
        for i, subtask in enumerate(generated_subtasks, 1):
            result += f"{i}. {subtask.name}: {subtask.description[:60]}{'...' if len(subtask.description) > 60 else ''}\n"
        
        return result
        
    except Exception as e:
        error_msg = f"Error generating subtasks for executable task {executable_task_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg

def get_task_stages_summary(task_id: str) -> str:
    """
    Gets a summary of all stages in a task and their work packages status.
    
    Args:
        task_id: The ID of the task
        
    Returns:
        String describing the task stages and their status
    """
    logger.info(f"Getting task stages summary for task {task_id}")
    
    try:
        # Get services with lazy initialization
        db_service, openai_service, problem_analyzer = _get_services()
        
        # Fetch task from database
        task_data = db_service.fetch_task_by_id(task_id)
        task = deserialize_task(task_data, task_id)
        
        if not task.network_plan or not task.network_plan.stages:
            return f"Task {task_id} has no network plan or stages."
        
        result = f"Task {task_id} - {task.task}\n"
        result += f"Total stages: {len(task.network_plan.stages)}\n\n"
        
        for i, stage in enumerate(task.network_plan.stages, 1):
            result += f"Stage {i} (ID: {stage.id}): {stage.name}\n"
            result += f"  Description: {stage.description[:100]}{'...' if len(stage.description) > 100 else ''}\n"
            
            if stage.work_packages is None:
                result += f"  ⚠️  Work packages: NOT GENERATED\n"
            elif len(stage.work_packages) == 0:
                result += f"  ⚠️  Work packages: EMPTY\n"
            else:
                result += f"  ✅ Work packages: {len(stage.work_packages)} generated\n"
                for j, work in enumerate(stage.work_packages, 1):
                    task_count = len(work.tasks) if work.tasks else 0
                    result += f"    - {j}. {work.name} ({task_count} tasks)\n"
            result += "\n"
        
        return result
        
    except Exception as e:
        error_msg = f"Error getting task stages summary: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg

def suggest_next_action(task_id: str) -> str:
    """
    Analyzes the current state of a task and suggests the next logical action.
    
    Args:
        task_id: The ID of the task
        
    Returns:
        String with suggestions for next actions
    """
    logger.info(f"Getting next action suggestions for task {task_id}")
    
    try:
        # Get services with lazy initialization
        db_service, openai_service, problem_analyzer = _get_services()
        
        # Fetch task from database
        task_data = db_service.fetch_task_by_id(task_id)
        task = deserialize_task(task_data, task_id)
        
        if not task.network_plan or not task.network_plan.stages:
            return "❌ No network plan found. Please generate a network plan first."
        
        stages_without_work = []
        work_packages_without_tasks = []
        tasks_without_subtasks = []
        
        for stage in task.network_plan.stages:
            if stage.work_packages is None or len(stage.work_packages) == 0:
                stages_without_work.append(stage)
            else:
                for work in stage.work_packages:
                    if work.tasks is None or len(work.tasks) == 0:
                        work_packages_without_tasks.append((stage, work))
                    else:
                        for task_item in work.tasks:
                            if task_item.subtasks is None or len(task_item.subtasks) == 0:
                                tasks_without_subtasks.append((stage, work, task_item))
        
        suggestions = []
        
        if stages_without_work:
            suggestions.append(f"🔧 Generate work packages for {len(stages_without_work)} stages:")
            for stage in stages_without_work[:3]:  # Show max 3
                suggestions.append(f"   - Stage {stage.id}: {stage.name}")
            suggestions.append(f"   Use: generate_work_packages_for_stage('{task_id}', '<stage_id>')")
            
        elif work_packages_without_tasks:
            suggestions.append(f"🔧 Generate tasks for {len(work_packages_without_tasks)} work packages:")
            for stage, work in work_packages_without_tasks[:3]:  # Show max 3
                suggestions.append(f"   - {work.name} in Stage {stage.id}")
            suggestions.append(f"   Use: generate_tasks_for_work_package('{task_id}', '<stage_id>', '<work_id>')")
            
        elif tasks_without_subtasks:
            suggestions.append(f"🔧 Generate subtasks for {len(tasks_without_subtasks)} executable tasks:")
            for stage, work, task_item in tasks_without_subtasks[:3]:  # Show max 3
                suggestions.append(f"   - {task_item.name} in {work.name}")
            suggestions.append(f"   Use: generate_subtasks_for_executable_task('{task_id}', '<stage_id>', '<work_id>', '<task_id>')")
            
        else:
            suggestions.append("✅ All components are generated! Task is ready for execution.")
            suggestions.append("   You can now execute subtasks using the ExecutorAgent.")
        
        return "\n".join(suggestions)
        
    except Exception as e:
        error_msg = f"Error getting next action suggestions: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg

# --- Create tracked task management tools ---
def create_tracked_task_management_tools(task_id: str, session_id: str):
    """
    Creates tracked versions of task management tools for enhanced monitoring.
    
    Args:
        task_id: The task ID for tracking
        session_id: The session ID for tracking
        
    Returns:
        List of tracked task management tool functions
    """
    from src.ai_agents.agent_tracker import get_tracker
    tracker = get_tracker(task_id, session_id)
    
    def tracked_generate_work_packages_for_stage(task_id: str, stage_id: str) -> str:
        """Tracked version of generate_work_packages_for_stage"""
        start_time = time.time()
        try:
            import asyncio
            # Check if we're already in an async context
            try:
                loop = asyncio.get_running_loop()
                # If we're already in an async context, use asyncio.create_task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, generate_work_packages_for_stage(task_id, stage_id))
                    result = future.result()
            except RuntimeError:
                # No running loop, safe to use asyncio.run
                result = asyncio.run(generate_work_packages_for_stage(task_id, stage_id))
            
            execution_time = (time.time() - start_time) * 1000
            tracker.log_tool_call(
                tool_name="generate_work_packages_for_stage",
                execution_time_ms=execution_time,
                parameters={"task_id": task_id, "stage_id": stage_id},
                result=result[:200] + "..." if len(result) > 200 else result,
                success=True
            )
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Error in generate_work_packages_for_stage: {str(e)}"
            tracker.log_tool_call(
                tool_name="generate_work_packages_for_stage",
                execution_time_ms=execution_time,
                parameters={"task_id": task_id, "stage_id": stage_id},
                result=error_msg,
                success=False
            )
            return error_msg

    def tracked_generate_tasks_for_work_package(task_id: str, stage_id: str, work_id: str) -> str:
        """Tracked version of generate_tasks_for_work_package"""
        start_time = time.time()
        try:
            import asyncio
            # Check if we're already in an async context
            try:
                loop = asyncio.get_running_loop()
                # If we're already in an async context, use asyncio.create_task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, generate_tasks_for_work_package(task_id, stage_id, work_id))
                    result = future.result()
            except RuntimeError:
                # No running loop, safe to use asyncio.run
                result = asyncio.run(generate_tasks_for_work_package(task_id, stage_id, work_id))
            
            execution_time = (time.time() - start_time) * 1000
            tracker.log_tool_call(
                tool_name="generate_tasks_for_work_package",
                execution_time_ms=execution_time,
                parameters={"task_id": task_id, "stage_id": stage_id, "work_id": work_id},
                result=result[:200] + "..." if len(result) > 200 else result,
                success=True
            )
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Error in generate_tasks_for_work_package: {str(e)}"
            tracker.log_tool_call(
                tool_name="generate_tasks_for_work_package", 
                execution_time_ms=execution_time,
                parameters={"task_id": task_id, "stage_id": stage_id, "work_id": work_id},
                result=error_msg,
                success=False
            )
            return error_msg
    
    def tracked_generate_subtasks_for_executable_task(task_id: str, stage_id: str, work_id: str, executable_task_id: str) -> str:
        """Tracked version of generate_subtasks_for_executable_task"""
        start_time = time.time()
        try:
            import asyncio
            # Check if we're already in an async context
            try:
                loop = asyncio.get_running_loop()
                # If we're already in an async context, use asyncio.create_task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, generate_subtasks_for_executable_task(task_id, stage_id, work_id, executable_task_id))
                    result = future.result()
            except RuntimeError:
                # No running loop, safe to use asyncio.run
                result = asyncio.run(generate_subtasks_for_executable_task(task_id, stage_id, work_id, executable_task_id))
            
            execution_time = (time.time() - start_time) * 1000
            tracker.log_tool_call(
                tool_name="generate_subtasks_for_executable_task",
                execution_time_ms=execution_time,
                parameters={"task_id": task_id, "stage_id": stage_id, "work_id": work_id, "executable_task_id": executable_task_id},
                result=result[:200] + "..." if len(result) > 200 else result,
                success=True
            )
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Error in generate_subtasks_for_executable_task: {str(e)}"
            tracker.log_tool_call(
                tool_name="generate_subtasks_for_executable_task",
                execution_time_ms=execution_time,
                parameters={"task_id": task_id, "stage_id": stage_id, "work_id": work_id, "executable_task_id": executable_task_id},
                result=error_msg,
                success=False
            )
            return error_msg

    def tracked_get_task_stages_summary(task_id: str) -> str:
        """Tracked version of get_task_stages_summary"""
        start_time = time.time()
        try:
            result = get_task_stages_summary(task_id)
            
            execution_time = (time.time() - start_time) * 1000
            tracker.log_tool_call(
                tool_name="get_task_stages_summary",
                execution_time_ms=execution_time,
                parameters={"task_id": task_id},
                result=result[:200] + "..." if len(result) > 200 else result,
                success=True
            )
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Error in get_task_stages_summary: {str(e)}"
            tracker.log_tool_call(
                tool_name="get_task_stages_summary",
                execution_time_ms=execution_time,
                parameters={"task_id": task_id},
                result=error_msg,
                success=False
            )
            return error_msg

    def tracked_suggest_next_action(task_id: str) -> str:
        """Tracked version of suggest_next_action"""
        start_time = time.time()
        try:
            result = suggest_next_action(task_id)
            
            execution_time = (time.time() - start_time) * 1000
            tracker.log_tool_call(
                tool_name="suggest_next_action",
                execution_time_ms=execution_time,
                parameters={"task_id": task_id},
                result=result[:200] + "..." if len(result) > 200 else result,
                success=True
            )
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Error in suggest_next_action: {str(e)}"
            tracker.log_tool_call(
                tool_name="suggest_next_action",
                execution_time_ms=execution_time,
                parameters={"task_id": task_id},
                result=error_msg,
                success=False
            )
            return error_msg

    return [
        tracked_generate_work_packages_for_stage,
        tracked_generate_tasks_for_work_package,
        tracked_generate_subtasks_for_executable_task,
        tracked_get_task_stages_summary,
        tracked_suggest_next_action
    ]

# List of all task management tools for Google ADK integration
task_management_tools_list = [
    generate_work_packages_for_stage,
    generate_tasks_for_work_package,
    generate_subtasks_for_executable_task,
    get_task_stages_summary,
    suggest_next_action
] 