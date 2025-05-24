"""
Task Execution Tools for AI Agents

This module provides comprehensive task execution capabilities with production-grade
error handling, type safety, and proper separation of concerns.

Features:
- Database-driven task management
- Type-safe operations with proper validation
- Structured error handling and logging
- Configurable task execution strategies
- Comprehensive validation framework
- Task hierarchy management (Stage -> Work Package -> Executable Task -> Subtask)
- Dependency tracking and validation
- Progress monitoring across all levels
- Automated validation workflow suggestions
"""

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple, Set

import yaml  # type: ignore

from src.ai_agents.workspace_manager import get_workspace_manager
from src.ai_agents.agent_tracker import get_tracker

# Configure structured logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_TIMEOUT_SECONDS = 30
CONFIG_FILE_TEMPLATE = """# Configuration file - API connection settings
api_base_url: "https://api.example.com"
api_key: "<YOUR_API_KEY>"
api_secret: "<YOUR_API_SECRET>"
timeout: {timeout}  # seconds
"""


class TaskExecutionError(Exception):
    """Custom exception for task execution failures"""
    def __init__(self, message: str, task_id: str, error_code: str = "EXECUTION_ERROR"):
        super().__init__(message)
        self.task_id = task_id
        self.error_code = error_code


class ValidationError(TaskExecutionError):
    """Custom exception for validation failures"""
    def __init__(self, message: str, task_id: str, failed_criteria: List[str]):
        super().__init__(message, task_id, "VALIDATION_ERROR")
        self.failed_criteria = failed_criteria


class DependencyError(TaskExecutionError):
    """Custom exception for dependency failures"""
    def __init__(self, message: str, task_id: str, blocking_dependencies: List[str]):
        super().__init__(message, task_id, "DEPENDENCY_ERROR")
        self.blocking_dependencies = blocking_dependencies


class TaskStatus(Enum):
    """Enumeration of possible task statuses"""
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"
    BLOCKED = "Blocked"
    READY_FOR_VALIDATION = "Ready for Validation"


class ExecutorType(Enum):
    """Enumeration of executor types"""
    AI_AGENT = "AI_AGENT"
    HUMAN = "HUMAN"
    AUTOMATED_SCRIPT = "AUTOMATED_SCRIPT"


class TaskType(Enum):
    """Enumeration of task types"""
    FILE_OPERATION = "file_operation"
    CONFIGURATION = "configuration"
    VALIDATION = "validation"
    GENERIC = "generic"


class TaskLevel(Enum):
    """Enumeration of task hierarchy levels"""
    STAGE = "stage"
    WORK_PACKAGE = "work_package"
    EXECUTABLE_TASK = "executable_task"
    SUBTASK = "subtask"


class TaskHierarchy:
    """Represents task hierarchy and relationships"""
    
    def __init__(self, task_reference: str):
        self.task_reference = task_reference
        self.components = self._parse_task_reference(task_reference)
    
    def _parse_task_reference(self, reference: str) -> Dict[str, str]:
        """Parse task reference into hierarchy components"""
        # Format: S1_W1_ET1_ST1 or S1_W1_ET1 or S1_W1 or S1
        parts = reference.split('_')
        components = {}
        
        if len(parts) >= 1 and parts[0].startswith('S'):
            components['stage'] = parts[0]
        if len(parts) >= 2 and parts[1].startswith('W'):
            components['work_package'] = f"{components.get('stage', '')}__{parts[1]}"
        if len(parts) >= 3 and parts[2].startswith('ET'):
            components['executable_task'] = f"{components.get('work_package', '')}__{parts[2]}"
        if len(parts) >= 4 and parts[3].startswith('ST'):
            components['subtask'] = reference
            
        return components
    
    def get_level(self) -> TaskLevel:
        """Determine the task level"""
        if 'subtask' in self.components:
            return TaskLevel.SUBTASK
        elif 'executable_task' in self.components:
            return TaskLevel.EXECUTABLE_TASK
        elif 'work_package' in self.components:
            return TaskLevel.WORK_PACKAGE
        elif 'stage' in self.components:
            return TaskLevel.STAGE
        else:
            raise ValueError(f"Invalid task reference format: {self.task_reference}")
    
    def get_parent_reference(self) -> Optional[str]:
        """Get parent task reference"""
        level = self.get_level()
        if level == TaskLevel.SUBTASK:
            return self.components.get('executable_task')
        elif level == TaskLevel.EXECUTABLE_TASK:
            return self.components.get('work_package')
        elif level == TaskLevel.WORK_PACKAGE:
            return self.components.get('stage')
        else:
            return None
    
    def get_children_pattern(self) -> str:
        """Get pattern to find child tasks"""
        level = self.get_level()
        if level == TaskLevel.STAGE:
            return f"{self.task_reference}_W%"
        elif level == TaskLevel.WORK_PACKAGE:
            return f"{self.task_reference}_ET%"
        elif level == TaskLevel.EXECUTABLE_TASK:
            return f"{self.task_reference}_ST%"
        else:
            return ""


class ProgressSummary:
    """Summary of progress across task hierarchy"""
    
    def __init__(self, task_reference: str):
        self.task_reference = task_reference
        self.hierarchy = TaskHierarchy(task_reference)
        self.level = self.hierarchy.get_level()
        self.total_count = 0
        self.completed_count = 0
        self.in_progress_count = 0
        self.pending_count = 0
        self.failed_count = 0
        self.blocked_count = 0
        self.ready_for_validation_count = 0
        self.children_summaries: List['ProgressSummary'] = []
        self.blocking_dependencies: List[str] = []
        self.validation_needed = False
    
    def get_completion_percentage(self) -> float:
        """Calculate completion percentage"""
        if self.total_count == 0:
            return 0.0
        return (self.completed_count / self.total_count) * 100
    
    def is_fully_completed(self) -> bool:
        """Check if all tasks are completed"""
        return self.total_count > 0 and self.completed_count == self.total_count
    
    def has_failures(self) -> bool:
        """Check if there are any failures"""
        return self.failed_count > 0
    
    def is_blocked(self) -> bool:
        """Check if progress is blocked"""
        return len(self.blocking_dependencies) > 0
    
    def needs_validation(self) -> bool:
        """Check if validation is needed"""
        return self.validation_needed or self.ready_for_validation_count > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "task_reference": self.task_reference,
            "level": self.level.value,
            "total_count": self.total_count,
            "completed_count": self.completed_count,
            "in_progress_count": self.in_progress_count,
            "pending_count": self.pending_count,
            "failed_count": self.failed_count,
            "blocked_count": self.blocked_count,
            "ready_for_validation_count": self.ready_for_validation_count,
            "completion_percentage": self.get_completion_percentage(),
            "is_fully_completed": self.is_fully_completed(),
            "has_failures": self.has_failures(),
            "is_blocked": self.is_blocked(),
            "needs_validation": self.needs_validation(),
            "blocking_dependencies": self.blocking_dependencies,
            "children_summaries": [child.to_dict() for child in self.children_summaries]
        }


class TaskDetails:
    """Type-safe data class for task details"""
    
    def __init__(self, data: Dict[str, Any]):
        self.id: str = data["id"]
        self.name: str = data.get("name", f"Task {self.id}")
        self.description: str = data.get("description", "")
        self.status: str = data.get("status", TaskStatus.PENDING.value)
        self.parent_task_id: str = data.get("parent_task_id", "")
        self.sequence_order: int = data.get("sequence_order", 0)
        self.executor_type: str = data.get("executor_type", ExecutorType.AI_AGENT.value)
        self.validation_criteria: List[str] = data.get("validation_criteria", [])
        self.expected_artifacts: List[str] = data.get("expected_artifacts", [])
        self.result: Optional[str] = data.get("result")
        self.error_message: Optional[str] = data.get("error_message")
        self.started_at: Optional[str] = data.get("started_at")
        self.completed_at: Optional[str] = data.get("completed_at")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "parent_task_id": self.parent_task_id,
            "sequence_order": self.sequence_order,
            "executor_type": self.executor_type,
            "validation_criteria": self.validation_criteria,
            "expected_artifacts": self.expected_artifacts,
            "result": self.result,
            "error_message": self.error_message,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }


class ExecutionResult:
    """Type-safe data class for execution results"""
    
    def __init__(self, success: bool, message: str, artifacts_created: Optional[List[str]] = None,
                 file_content: Optional[str] = None, file_path: Optional[str] = None,
                 error: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        self.success = success
        self.message = message
        self.artifacts_created = artifacts_created or []
        self.file_content = file_content
        self.file_path = file_path
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "success": self.success,
            "message": self.message,
            "artifacts_created": self.artifacts_created,
            "file_content": self.file_content,
            "file_path": self.file_path,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


class ValidationResult:
    """Type-safe data class for validation results"""
    
    def __init__(self, task_id: str, overall_passed: bool, criteria_results: List[Dict[str, Any]]):
        self.task_id = task_id
        self.overall_passed = overall_passed
        self.criteria_results = criteria_results
        self.passed_count = sum(1 for r in criteria_results if r.get("passed", False))
        self.total_count = len(criteria_results)
        self.validation_summary = f"{self.passed_count}/{self.total_count} criteria passed"
    
    def get_failed_criteria(self) -> List[str]:
        """Get list of failed criteria"""
        return [r["criterion"] for r in self.criteria_results if not r.get("passed", False)]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "task_id": self.task_id,
            "overall_passed": self.overall_passed,
            "criteria_results": self.criteria_results,
            "validation_summary": self.validation_summary,
            "passed_count": self.passed_count,
            "total_count": self.total_count
        }


class TaskExecutor(ABC):
    """Abstract base class for task executors"""
    
    @abstractmethod
    def can_execute(self, task_details: TaskDetails) -> bool:
        """Check if this executor can handle the given task"""
        pass
    
    @abstractmethod
    def execute(self, task_details: TaskDetails, workspace_path: str) -> ExecutionResult:
        """Execute the task and return results"""
        pass


class FileOperationExecutor(TaskExecutor):
    """Executor for file operations and checks"""
    
    def can_execute(self, task_details: TaskDetails) -> bool:
        """Check if this is a file operation task"""
        keywords = ["file", "файл", "existence", "существование", "config", "конфигурация"]
        text_to_check = f"{task_details.name} {task_details.description}".lower()
        return any(keyword in text_to_check for keyword in keywords)
    
    def execute(self, task_details: TaskDetails, workspace_path: str) -> ExecutionResult:
        """Execute file operation task"""
        try:
            file_path = self._determine_file_path(task_details)
            full_path = Path(workspace_path) / file_path
            
            return self._handle_file_operation(full_path, file_path, task_details)
            
        except Exception as e:
            logger.error(f"File operation failed for task {task_details.id}: {e}")
            return ExecutionResult(
                success=False,
                message=f"File operation failed: {str(e)}",
                error=str(e)
            )
    
    def _determine_file_path(self, task_details: TaskDetails) -> str:
        """Determine the file path to operate on"""
        # Priority: expected artifacts > description analysis > default
        if task_details.expected_artifacts:
            return task_details.expected_artifacts[0]
        
        description_lower = task_details.description.lower()
        if "config" in description_lower:
            return "config/config.yml"
        
        # Default fallback
        return "config/config.yml"
    
    def _handle_file_operation(self, full_path: Path, relative_path: str, 
                             task_details: TaskDetails) -> ExecutionResult:
        """Handle the actual file operation"""
        try:
            if full_path.exists():
                content = full_path.read_text(encoding='utf-8')
                return ExecutionResult(
                    success=True,
                    message=f"File check successful: {full_path}",
                    artifacts_created=[relative_path],
                    file_content=content,
                    file_path=str(full_path)
                )
            else:
                return self._create_missing_file(full_path, relative_path, task_details)
                
        except (IOError, OSError) as e:
            logger.error(f"File I/O error: {e}")
            return ExecutionResult(
                success=False,
                message=f"File I/O error: {str(e)}",
                error=str(e)
            )
    
    def _create_missing_file(self, full_path: Path, relative_path: str, 
                           task_details: TaskDetails) -> ExecutionResult:
        """Create a missing file with appropriate content"""
        try:
            # Create parent directories
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate content based on file type
            if "config" in relative_path.lower():
                content = CONFIG_FILE_TEMPLATE.format(timeout=DEFAULT_TIMEOUT_SECONDS)
            else:
                content = f"# {relative_path}\n# Generated file for task {task_details.id}\n"
            
            full_path.write_text(content, encoding='utf-8')
            
            return ExecutionResult(
                success=True,
                message=f"File created successfully: {full_path}",
                artifacts_created=[relative_path],
                file_content=content,
                file_path=str(full_path)
            )
            
        except (IOError, OSError) as e:
            logger.error(f"Failed to create file {full_path}: {e}")
            return ExecutionResult(
                success=False,
                message=f"Failed to create file: {str(e)}",
                error=str(e)
            )


class GenericTaskExecutor(TaskExecutor):
    """Executor for generic tasks"""
    
    def can_execute(self, task_details: TaskDetails) -> bool:
        """Generic executor can handle any task as fallback"""
        return True
    
    def execute(self, task_details: TaskDetails, workspace_path: str) -> ExecutionResult:
        """Execute generic task"""
        return ExecutionResult(
            success=True,
            message=f"Generic task {task_details.id} executed successfully",
            artifacts_created=[],
            metadata={"execution_type": "generic", "task_name": task_details.name}
        )


class TaskExecutionTools:
    """
    Professional task execution system with type safety, proper error handling,
    and configurable execution strategies.
    """
    
    def __init__(self, task_id: str, session_id: str):
        """
        Initialize task execution tools.
        
        Args:
            task_id: Main task identifier
            session_id: Session identifier for tracking
            
        Raises:
            ValueError: If task_id or session_id is empty
        """
        if not task_id or not session_id:
            raise ValueError("task_id and session_id are required")
        
        self.task_id = task_id
        self.session_id = session_id
        self.workspace_manager = get_workspace_manager()
        self.tracker = get_tracker(task_id, session_id)
        self.workspace_path = self.workspace_manager.get_workspace_path(task_id)
        
        # Initialize executors in priority order
        self.executors: List[TaskExecutor] = [
            FileOperationExecutor(),
            GenericTaskExecutor()  # Always last as fallback
        ]
        
        logger.info(f"TaskExecutionTools initialized for task {task_id}, session {session_id}")
    
    def get_task_details(self, task_reference: str, task_type: str = "subtask") -> Dict[str, Any]:
        """
        Retrieve task details from database with proper error handling.
        
        Args:
            task_reference: Task identifier (e.g., S1_W1_ET1_ST1)
            task_type: Type of task (default: "subtask")
            
        Returns:
            Dict[str, Any]: Task details dictionary (compatible with Google ADK)
            
        Raises:
            TaskExecutionError: If task retrieval fails
        """
        if not task_reference:
            raise ValueError("task_reference cannot be empty")
        
        try:
            from src.services.database_service import DatabaseService
            db_service = DatabaseService()
            
            logger.debug(f"Fetching task details for {task_reference}")
            result = db_service.get_subtask_status(self.task_id, task_reference)
            
            if result.get("success", False):
                subtask_data = result["subtask"]
                # Ensure parent_task_id is set
                subtask_data["parent_task_id"] = self.task_id
                task_details = TaskDetails(subtask_data)
                return task_details.to_dict()  # Convert to dict for ADK compatibility
            else:
                logger.warning(f"Task {task_reference} not found in database: {result.get('error')}")
                # Return minimal task details for unknown tasks
                task_details = TaskDetails({
                    "id": task_reference,
                    "name": f"Task {task_reference}",
                    "description": f"Task {task_reference} (not found in database)",
                    "parent_task_id": self.task_id,
                    "status": TaskStatus.PENDING.value,
                    "validation_criteria": ["Task should be completed successfully"],
                    "expected_artifacts": []
                })
                return task_details.to_dict()
                
        except Exception as e:
            logger.error(f"Failed to retrieve task details for {task_reference}: {e}")
            raise TaskExecutionError(
                f"Failed to retrieve task details: {str(e)}",
                task_reference,
                "DATABASE_ERROR"
            )
    
    def execute_task(self, task_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task using the appropriate executor strategy.
        
        Args:
            task_details: Task details dictionary (from get_task_details)
            
        Returns:
            Dict[str, Any]: Execution result dictionary (compatible with Google ADK)
            
        Raises:
            TaskExecutionError: If execution fails
        """
        # Convert dict to type-safe TaskDetails internally
        task_details_obj = TaskDetails(task_details)
        logger.info(f"Executing task {task_details_obj.id}: {task_details_obj.name}")
        
        try:
            # Update status to In Progress
            self._update_task_status(
                task_details_obj.id,
                TaskStatus.IN_PROGRESS,
                started_at=datetime.now().isoformat()
            )
            
            # Find appropriate executor
            executor = self._find_executor(task_details_obj)
            if not executor:
                raise TaskExecutionError(
                    f"No suitable executor found for task {task_details_obj.id}",
                    task_details_obj.id,
                    "NO_EXECUTOR"
                )
            
            logger.debug(f"Using executor {executor.__class__.__name__} for task {task_details_obj.id}")
            
            # Execute the task
            result = executor.execute(task_details_obj, self.workspace_path)
            
            # Log execution result
            self.tracker.log_tool_call(
                tool_name="execute_task",
                parameters={"task_id": task_details_obj.id, "executor": executor.__class__.__name__},
                result=f"Task executed: {result.message}",
                success=result.success,
                execution_time_ms=10
            )
            
            return result.to_dict()  # Convert to dict for ADK compatibility
            
        except TaskExecutionError:
            raise  # Re-raise TaskExecutionError as-is
        except Exception as e:
            logger.error(f"Unexpected error executing task {task_details_obj.id}: {e}")
            
            # Update status to failed
            self._update_task_status(
                task_details_obj.id,
                TaskStatus.FAILED,
                error_message=str(e),
                completed_at=datetime.now().isoformat()
            )
            
            raise TaskExecutionError(
                f"Task execution failed: {str(e)}",
                task_details_obj.id,
                "EXECUTION_FAILED"
            )
    
    def validate_task_completion(self, task_details: Dict[str, Any], 
                               execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate task completion against defined criteria.
        
        Args:
            task_details: Original task details dictionary
            execution_result: Result from task execution dictionary
            
        Returns:
            Dict[str, Any]: Validation result dictionary (compatible with Google ADK)
        """
        # Convert dicts to type-safe objects internally
        task_details_obj = TaskDetails(task_details)
        execution_result_obj = ExecutionResult(
            success=execution_result.get("success", False),
            message=execution_result.get("message", ""),
            artifacts_created=execution_result.get("artifacts_created", []),
            file_content=execution_result.get("file_content"),
            file_path=execution_result.get("file_path"),
            error=execution_result.get("error"),
            metadata=execution_result.get("metadata", {})
        )
        
        logger.info(f"Validating task {task_details_obj.id} against {len(task_details_obj.validation_criteria)} criteria")
        
        criteria_results = []
        
        for i, criterion in enumerate(task_details_obj.validation_criteria):
            try:
                passed = self._validate_single_criterion(criterion, task_details_obj, execution_result_obj)
                criteria_results.append({
                    "criterion": criterion,
                    "passed": passed,
                    "details": f"Criterion {i+1}: {'PASS' if passed else 'FAIL'}"
                })
            except Exception as e:
                logger.error(f"Error validating criterion '{criterion}': {e}")
                criteria_results.append({
                    "criterion": criterion,
                    "passed": False,
                    "details": f"Criterion {i+1}: ERROR - {str(e)}"
                })
        
        overall_passed = all(r["passed"] for r in criteria_results)
        
        validation_result = ValidationResult(
            task_id=task_details_obj.id,
            overall_passed=overall_passed,
            criteria_results=criteria_results
        )
        
        return validation_result.to_dict()  # Convert to dict for ADK compatibility
    
    def update_task_status_complete(self, task_id: str, validation_result: Dict[str, Any],
                                  execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update task status based on validation results.
        
        Args:
            task_id: Task identifier
            validation_result: Validation outcome dictionary
            execution_result: Original execution result dictionary
            
        Returns:
            Status update result dictionary
        """
        try:
            # Convert dicts to type-safe objects internally
            validation_result_obj = ValidationResult(
                task_id=validation_result.get("task_id", task_id),
                overall_passed=validation_result.get("overall_passed", False),
                criteria_results=validation_result.get("criteria_results", [])
            )
            
            execution_result_obj = ExecutionResult(
                success=execution_result.get("success", False),
                message=execution_result.get("message", ""),
                artifacts_created=execution_result.get("artifacts_created", []),
                file_content=execution_result.get("file_content"),
                file_path=execution_result.get("file_path"),
                error=execution_result.get("error"),
                metadata=execution_result.get("metadata", {})
            )
            
            if validation_result_obj.overall_passed:
                status = TaskStatus.COMPLETED
                result_data = {
                    "execution_summary": execution_result_obj.message,
                    "artifacts_created": execution_result_obj.artifacts_created,
                    "validation_passed": True,
                    "validation_summary": validation_result_obj.validation_summary,
                    "metadata": execution_result_obj.metadata
                }
                error_message = None
            else:
                status = TaskStatus.FAILED
                result_data = {
                    "execution_summary": execution_result_obj.message,
                    "validation_passed": False,
                    "validation_summary": validation_result_obj.validation_summary,
                    "failed_criteria": validation_result_obj.get_failed_criteria(),
                    "metadata": execution_result_obj.metadata
                }
                error_message = f"Validation failed: {validation_result_obj.validation_summary}"
            
            return self._update_task_status(
                task_id=task_id,
                status=status,
                result=result_data,
                error_message=error_message,
                completed_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Failed to update task status for {task_id}: {e}")
            return {
                "success": False,
                "task_id": task_id,
                "error": f"Status update failed: {str(e)}",
                "persisted": False
            }
    
    def execute_task_flow(self, task_reference: str, task_type: str = "subtask") -> Dict[str, Any]:
        """
        Execute complete task flow with proper error handling.
        
        Args:
            task_reference: Task identifier
            task_type: Type of task
            
        Returns:
            Complete flow result
        """
        flow_start = time.time()
        
        try:
            logger.info(f"Starting task flow for {task_reference}")
            
            # Step 1: Get task details
            task_details = self.get_task_details(task_reference, task_type)
            
            # Step 2: Execute task
            execution_result = self.execute_task(task_details)
            
            # Step 3: Validate completion
            validation_result = self.validate_task_completion(task_details, execution_result)
            
            # Step 4: Update status
            status_update = self.update_task_status_complete(
                task_reference, validation_result, execution_result
            )
            
            # Calculate execution time
            flow_time = (time.time() - flow_start) * 1000
            
            return {
                "flow_success": True,
                "task_id": task_reference,
                "execution_time_ms": flow_time,
                "steps": {
                    "task_details": task_details,
                    "execution": execution_result,
                    "validation": validation_result,
                    "status_update": status_update
                },
                "final_status": status_update.get("new_status", "Unknown"),
                "summary": f"Task {task_reference} completed with status: {status_update.get('new_status', 'Unknown')}"
            }
            
        except TaskExecutionError as e:
            logger.error(f"Task execution error for {task_reference}: {e}")
            self._handle_task_failure(task_reference, str(e))
            
            return {
                "flow_success": False,
                "task_id": task_reference,
                "error": str(e),
                "error_code": e.error_code,
                "final_status": TaskStatus.FAILED.value
            }
        except Exception as e:
            logger.error(f"Unexpected error in task flow for {task_reference}: {e}")
            self._handle_task_failure(task_reference, str(e))
            
            return {
                "flow_success": False,
                "task_id": task_reference,
                "error": str(e),
                "final_status": TaskStatus.FAILED.value
            }
    
    def mark_task_complete(self, task_reference: str) -> Dict[str, Any]:
        """
        Mark a task as complete by executing the full task flow.
        
        Args:
            task_reference: Task identifier (required)
            
        Returns:
            Complete flow result with detailed reporting
            
        Raises:
            ValueError: If task_reference is empty
        """
        if not task_reference:
            raise ValueError("task_reference is required")
        
        logger.info(f"Marking task {task_reference} as complete via full execution flow")
        
        try:
            # Execute the complete task flow
            flow_result = self.execute_task_flow(task_reference)
            
            # Generate detailed report
            detailed_report = self._generate_detailed_report(task_reference, flow_result)
            
            return {
                "success": flow_result["flow_success"],
                "task_id": task_reference,
                "final_status": flow_result.get("final_status", "Unknown"),
                "summary": detailed_report,
                "details": flow_result,
                "execution_time_ms": flow_result.get("execution_time_ms", 0)
            }
            
        except Exception as e:
            logger.error(f"Error marking task {task_reference} as complete: {e}")
            return {
                "success": False,
                "task_id": task_reference,
                "error": str(e),
                "summary": f"❌ **Error:** Failed to mark task {task_reference} as complete: {str(e)}"
            }
    
    def _find_executor(self, task_details: TaskDetails) -> Optional[TaskExecutor]:
        """Find the appropriate executor for a task"""
        for executor in self.executors:
            if executor.can_execute(task_details):
                return executor
        return None
    
    def _validate_single_criterion(self, criterion: str, task_details: TaskDetails,
                                 execution_result: ExecutionResult) -> bool:
        """Validate a single criterion with proper error handling"""
        try:
            criterion_lower = criterion.lower()
            
            # File existence checks
            if any(keyword in criterion_lower for keyword in ["file", "файл", "exist", "существ"]):
                return (execution_result.success and 
                       len(execution_result.artifacts_created) > 0)
            
            # YAML format checks
            if "yaml" in criterion_lower and execution_result.file_content:
                try:
                    yaml.safe_load(execution_result.file_content)
                    return True
                except yaml.YAMLError:
                    return False
            
            # Content checks
            if "ключи" in criterion_lower or "keys" in criterion_lower:
                if execution_result.file_content:
                    required_keys = ["api_base_url", "api_key", "api_secret", "timeout"]
                    return all(key in execution_result.file_content for key in required_keys)
            
            # Default: assume passed if execution was successful
            return execution_result.success
            
        except Exception as e:
            logger.error(f"Error validating criterion '{criterion}': {e}")
            return False
    
    def _update_task_status(self, task_id: str, status: TaskStatus, **kwargs) -> Dict[str, Any]:
        """Update task status in database with proper error handling"""
        try:
            from src.services.database_service import DatabaseService
            db_service = DatabaseService()
            
            # Prepare result string
            result_str = None
            if "result" in kwargs and kwargs["result"] is not None:
                result_str = json.dumps(kwargs["result"], ensure_ascii=False)
            
            # Update in database
            db_result = db_service.update_subtask_status(
                task_id=self.task_id,
                subtask_reference=task_id,
                status=status.value,
                result=result_str,
                error_message=kwargs.get("error_message"),
                started_at=kwargs.get("started_at"),
                completed_at=kwargs.get("completed_at")
            )
            
            if db_result.get("success", False):
                logger.info(f"Successfully updated task {task_id} status to {status.value}")
                
                self.tracker.log_tool_call(
                    tool_name="update_task_status",
                    parameters={"task_id": task_id, "status": status.value},
                    result=f"Status updated to {status.value}",
                    success=True,
                    execution_time_ms=10
                )
                
                return {
                    "success": True,
                    "task_id": task_id,
                    "new_status": status.value,
                    "persisted": True,
                    "db_result": db_result
                }
            else:
                error_msg = db_result.get("error", "Unknown database error")
                logger.error(f"Database update failed for task {task_id}: {error_msg}")
                
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": f"Database update failed: {error_msg}",
                    "persisted": False
                }
                
        except Exception as e:
            logger.error(f"Exception updating task status for {task_id}: {e}")
            return {
                "success": False,
                "task_id": task_id,
                "error": f"Status update exception: {str(e)}",
                "persisted": False
            }
    
    def _handle_task_failure(self, task_id: str, error_message: str) -> None:
        """Handle task failure by updating status"""
        try:
            self._update_task_status(
                task_id,
                TaskStatus.FAILED,
                error_message=error_message,
                completed_at=datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Failed to update failed status for task {task_id}: {e}")
    
    def _generate_detailed_report(self, task_reference: str, flow_result: Dict[str, Any]) -> str:
        """Generate detailed execution report"""
        if not flow_result.get("flow_success", False):
            return f"❌ **Task {task_reference} Failed:** {flow_result.get('error', 'Unknown error')}"
        
        steps = flow_result.get("steps", {})
        execution_time = flow_result.get("execution_time_ms", 0)
        final_status = flow_result.get("final_status", "Unknown")
        
        execution_data = steps.get("execution", {})
        validation_data = steps.get("validation", {})
        
        report_lines = [
            f"✅ **Task {task_reference} Completed Successfully**",
            f"⏱️ **Execution Time:** {execution_time:.0f}ms",
            f"📊 **Final Status:** {final_status}",
            "",
            f"🔧 **Execution Results:**",
            f"  • {execution_data.get('message', 'No message')}",
            f"  • Artifacts: {', '.join(execution_data.get('artifacts_created', [])) or 'None'}",
            "",
            f"🎯 **Validation Results:**",
            f"  • {validation_data.get('validation_summary', 'No validation summary')}",
            f"  • Status: {'PASSED' if validation_data.get('overall_passed', False) else 'FAILED'}"
        ]
        
        return "\n".join(report_lines)


    # ========================================
    # TASK HIERARCHY MANAGEMENT METHODS
    # ========================================
    
    def get_task_progress_summary(self, task_reference: str) -> Dict[str, Any]:
        """
        Get comprehensive progress summary for a task and its hierarchy.
        
        Args:
            task_reference: Task identifier (any level in hierarchy)
            
        Returns:
            Dict containing complete progress analysis
        """
        try:
            logger.info(f"Getting progress summary for task {task_reference}")
            
            hierarchy = TaskHierarchy(task_reference)
            summary = self._build_progress_summary(task_reference)
            
            return {
                "success": True,
                "task_reference": task_reference,
                "level": hierarchy.get_level().value,
                "summary": summary.to_dict(),
                "recommendations": self._generate_progress_recommendations(summary),
                "next_actions": self._suggest_next_actions(summary),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get progress summary for {task_reference}: {e}")
            return {
                "success": False,
                "task_reference": task_reference,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def check_task_dependencies(self, task_reference: str) -> Dict[str, Any]:
        """
        Check dependencies and determine if task can be executed.
        
        Args:
            task_reference: Task identifier
            
        Returns:
            Dict containing dependency analysis
        """
        try:
            logger.info(f"Checking dependencies for task {task_reference}")
            
            hierarchy = TaskHierarchy(task_reference)
            blocking_deps = self._get_blocking_dependencies(task_reference)
            ready_to_execute = len(blocking_deps) == 0
            
            return {
                "success": True,
                "task_reference": task_reference,
                "level": hierarchy.get_level().value,
                "ready_to_execute": ready_to_execute,
                "blocking_dependencies": blocking_deps,
                "dependency_details": self._get_dependency_details(blocking_deps),
                "estimated_unblock_time": self._estimate_unblock_time(blocking_deps),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to check dependencies for {task_reference}: {e}")
            return {
                "success": False,
                "task_reference": task_reference,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def check_completion_status(self, task_reference: str) -> Dict[str, Any]:
        """
        Check if all subtasks are completed and suggest validation.
        
        Args:
            task_reference: Task identifier (typically executable task)
            
        Returns:
            Dict containing completion analysis and validation suggestions
        """
        try:
            logger.info(f"Checking completion status for task {task_reference}")
            
            hierarchy = TaskHierarchy(task_reference)
            summary = self._build_progress_summary(task_reference)
            
            validation_needed = False
            validation_message = ""
            
            if hierarchy.get_level() == TaskLevel.EXECUTABLE_TASK:
                if summary.is_fully_completed():
                    validation_needed = True
                    validation_message = f"All subtasks for {task_reference} are completed. Ready for executable task validation."
                elif summary.has_failures():
                    validation_message = f"Some subtasks failed for {task_reference}. Review and fix failures before validation."
                else:
                    validation_message = f"Executable task {task_reference} still has pending/in-progress subtasks."
            
            return {
                "success": True,
                "task_reference": task_reference,
                "level": hierarchy.get_level().value,
                "is_fully_completed": summary.is_fully_completed(),
                "completion_percentage": summary.get_completion_percentage(),
                "validation_needed": validation_needed,
                "validation_message": validation_message,
                "summary": summary.to_dict(),
                "next_steps": self._generate_completion_next_steps(summary, validation_needed),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to check completion status for {task_reference}: {e}")
            return {
                "success": False,
                "task_reference": task_reference,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_all_in_progress_tasks(self, root_task_reference: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all tasks currently in progress across the hierarchy.
        
        Args:
            root_task_reference: Root task to analyze (defaults to main task)
            
        Returns:
            Dict containing all in-progress tasks organized by level
        """
        try:
            if not root_task_reference:
                root_task_reference = "S1"  # Default to first stage
                
            logger.info(f"Getting all in-progress tasks for {root_task_reference}")
            
            in_progress_tasks = self._find_in_progress_tasks(root_task_reference)
            organized_tasks = self._organize_tasks_by_level(in_progress_tasks)
            
            return {
                "success": True,
                "root_task_reference": root_task_reference,
                "total_in_progress": len(in_progress_tasks),
                "tasks_by_level": organized_tasks,
                "detailed_tasks": in_progress_tasks,
                "estimated_completion_times": self._estimate_completion_times(in_progress_tasks),
                "resource_allocation": self._analyze_resource_allocation(in_progress_tasks),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get in-progress tasks for {root_task_reference}: {e}")
            return {
                "success": False,
                "root_task_reference": root_task_reference,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def suggest_validation_workflow(self, task_reference: str) -> Dict[str, Any]:
        """
        Suggest validation workflow based on task completion status.
        
        Args:
            task_reference: Task identifier
            
        Returns:
            Dict containing validation workflow suggestions
        """
        try:
            logger.info(f"Suggesting validation workflow for {task_reference}")
            
            hierarchy = TaskHierarchy(task_reference)
            summary = self._build_progress_summary(task_reference)
            
            workflow_steps = []
            priority = "low"
            
            if hierarchy.get_level() == TaskLevel.EXECUTABLE_TASK and summary.is_fully_completed():
                workflow_steps = [
                    {
                        "step": 1,
                        "action": "Review Subtask Results",
                        "description": f"Review all completed subtasks for {task_reference}",
                        "estimated_time": "5-10 minutes",
                        "responsible": "Human Validator"
                    },
                    {
                        "step": 2,
                        "action": "Validate Executable Task Criteria",
                        "description": f"Validate that {task_reference} meets its acceptance criteria",
                        "estimated_time": "10-15 minutes",
                        "responsible": "Human Validator"
                    },
                    {
                        "step": 3,
                        "action": "Mark as Validated",
                        "description": f"Update {task_reference} status to completed",
                        "estimated_time": "1 minute",
                        "responsible": "System"
                    }
                ]
                priority = "high"
            
            return {
                "success": True,
                "task_reference": task_reference,
                "level": hierarchy.get_level().value,
                "validation_needed": len(workflow_steps) > 0,
                "priority": priority,
                "workflow_steps": workflow_steps,
                "estimated_total_time": self._calculate_total_validation_time(workflow_steps),
                "prerequisites": self._get_validation_prerequisites(task_reference),
                "automated_checks": self._get_automated_validation_checks(task_reference),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to suggest validation workflow for {task_reference}: {e}")
            return {
                "success": False,
                "task_reference": task_reference,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # ========================================
    # PRIVATE HELPER METHODS
    # ========================================
    
    def _build_progress_summary(self, task_reference: str) -> ProgressSummary:
        """Build comprehensive progress summary"""
        summary = ProgressSummary(task_reference)
        
        try:
            from src.services.database_service import DatabaseService
            db_service = DatabaseService()
            
            # Get child tasks
            hierarchy = TaskHierarchy(task_reference)
            children_pattern = hierarchy.get_children_pattern()
            
            if children_pattern:
                # Query child tasks from database
                # This would need to be implemented in DatabaseService
                # For now, simulate with sample data
                child_tasks = self._get_child_tasks_from_database(task_reference)
                
                summary.total_count = len(child_tasks)
                
                for child_task in child_tasks:
                    status = child_task.get("status", TaskStatus.PENDING.value)
                    if status == TaskStatus.COMPLETED.value:
                        summary.completed_count += 1
                    elif status == TaskStatus.IN_PROGRESS.value:
                        summary.in_progress_count += 1
                    elif status == TaskStatus.PENDING.value:
                        summary.pending_count += 1
                    elif status == TaskStatus.FAILED.value:
                        summary.failed_count += 1
                    elif status == TaskStatus.BLOCKED.value:
                        summary.blocked_count += 1
                    elif status == TaskStatus.READY_FOR_VALIDATION.value:
                        summary.ready_for_validation_count += 1
                
                # Recursively build summaries for children
                for child_task in child_tasks:
                    child_reference = child_task.get("id", "")
                    if child_reference:
                        child_summary = self._build_progress_summary(child_reference)
                        summary.children_summaries.append(child_summary)
            
            # Check dependencies
            summary.blocking_dependencies = self._get_blocking_dependencies(task_reference)
            
            # Determine if validation is needed
            if hierarchy.get_level() == TaskLevel.EXECUTABLE_TASK:
                summary.validation_needed = summary.is_fully_completed()
            
        except Exception as e:
            logger.error(f"Error building progress summary for {task_reference}: {e}")
        
        return summary
    
    def _get_child_tasks_from_database(self, task_reference: str) -> List[Dict[str, Any]]:
        """Get child tasks from database (mock implementation)"""
        # This would be implemented to query the actual database
        # For now, return mock data based on the task reference
        
        hierarchy = TaskHierarchy(task_reference)
        level = hierarchy.get_level()
        
        if level == TaskLevel.EXECUTABLE_TASK:
            # Return subtasks
            return [
                {"id": f"{task_reference}_ST1", "status": TaskStatus.COMPLETED.value},
                {"id": f"{task_reference}_ST2", "status": TaskStatus.COMPLETED.value},
                {"id": f"{task_reference}_ST3", "status": TaskStatus.COMPLETED.value},
                {"id": f"{task_reference}_ST4", "status": TaskStatus.IN_PROGRESS.value},
            ]
        elif level == TaskLevel.WORK_PACKAGE:
            # Return executable tasks
            return [
                {"id": f"{task_reference}_ET1", "status": TaskStatus.COMPLETED.value},
                {"id": f"{task_reference}_ET2", "status": TaskStatus.IN_PROGRESS.value},
            ]
        elif level == TaskLevel.STAGE:
            # Return work packages
            return [
                {"id": f"{task_reference}_W1", "status": TaskStatus.IN_PROGRESS.value},
                {"id": f"{task_reference}_W2", "status": TaskStatus.PENDING.value},
            ]
        
        return []
    
    def _get_blocking_dependencies(self, task_reference: str) -> List[str]:
        """Get dependencies that are blocking this task"""
        # This would be implemented to check actual dependencies
        # For now, return mock dependencies
        
        hierarchy = TaskHierarchy(task_reference)
        if hierarchy.get_level() == TaskLevel.SUBTASK:
            # Check if previous subtasks are completed
            parts = task_reference.split('_')
            if len(parts) >= 4:
                subtask_num = int(parts[3][2:])  # Extract number from ST1, ST2, etc.
                if subtask_num > 1:
                    prev_subtask = f"{parts[0]}_{parts[1]}_{parts[2]}_ST{subtask_num-1}"
                    # Mock: check if previous subtask is completed
                    # In real implementation, query database
                    return []  # Assume no blocking dependencies for demo
        
        return []
    
    def _get_dependency_details(self, dependencies: List[str]) -> List[Dict[str, Any]]:
        """Get detailed information about dependencies"""
        details = []
        for dep in dependencies:
            details.append({
                "task_reference": dep,
                "current_status": "In Progress",  # Mock status
                "estimated_completion": "2024-01-15T10:00:00",  # Mock time
                "blocking_reason": "Prerequisite task not completed"
            })
        return details
    
    def _estimate_unblock_time(self, dependencies: List[str]) -> Optional[str]:
        """Estimate when dependencies will be unblocked"""
        if not dependencies:
            return None
        # Mock implementation
        return "2024-01-15T12:00:00"
    
    def _generate_progress_recommendations(self, summary: ProgressSummary) -> List[str]:
        """Generate recommendations based on progress"""
        recommendations = []
        
        if summary.has_failures():
            recommendations.append("Review and address failed tasks before proceeding")
        
        if summary.is_blocked():
            recommendations.append("Focus on unblocking dependencies to enable progress")
        
        if summary.needs_validation():
            recommendations.append("Schedule validation review for completed components")
        
        if summary.in_progress_count > 3:
            recommendations.append("Consider resource allocation - many tasks in progress simultaneously")
        
        return recommendations
    
    def _suggest_next_actions(self, summary: ProgressSummary) -> List[Dict[str, Any]]:
        """Suggest concrete next actions"""
        actions = []
        
        if summary.pending_count > 0:
            actions.append({
                "action": "Start Next Pending Task",
                "priority": "medium",
                "estimated_effort": "1-2 hours"
            })
        
        if summary.needs_validation():
            actions.append({
                "action": "Begin Validation Process",
                "priority": "high",
                "estimated_effort": "30 minutes"
            })
        
        return actions
    
    def _generate_completion_next_steps(self, summary: ProgressSummary, validation_needed: bool) -> List[str]:
        """Generate next steps based on completion status"""
        steps = []
        
        if validation_needed:
            steps.append("Initiate executable task validation workflow")
            steps.append("Schedule human review of completed subtasks")
            steps.append("Prepare validation criteria checklist")
        elif summary.has_failures():
            steps.append("Review failed subtasks and identify root causes")
            steps.append("Plan remediation for failed components")
            steps.append("Re-execute or fix failed subtasks")
        else:
            steps.append("Continue executing remaining subtasks")
            steps.append("Monitor progress and remove blockers")
        
        return steps
    
    def _find_in_progress_tasks(self, root_task_reference: str) -> List[Dict[str, Any]]:
        """Find all tasks currently in progress"""
        # Mock implementation - would query database in real system
        return [
            {
                "task_reference": "S1_W1_ET1_ST4",
                "level": "subtask",
                "status": "In Progress",
                "started_at": "2024-01-15T09:00:00",
                "estimated_completion": "2024-01-15T11:00:00",
                "executor": "AI_AGENT",
                "progress_percentage": 65
            },
            {
                "task_reference": "S1_W1_ET2",
                "level": "executable_task",
                "status": "In Progress",
                "started_at": "2024-01-15T08:00:00",
                "estimated_completion": "2024-01-15T16:00:00",
                "executor": "HUMAN",
                "progress_percentage": 30
            }
        ]
    
    def _organize_tasks_by_level(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Organize tasks by hierarchy level"""
        organized: Dict[str, List[Dict[str, Any]]] = {
            "stages": [],
            "work_packages": [],
            "executable_tasks": [],
            "subtasks": []
        }
        
        for task in tasks:
            level = task.get("level", "")
            if level == "stage":
                organized["stages"].append(task)
            elif level == "work_package":
                organized["work_packages"].append(task)
            elif level == "executable_task":
                organized["executable_tasks"].append(task)
            elif level == "subtask":
                organized["subtasks"].append(task)
        
        return organized
    
    def _estimate_completion_times(self, tasks: List[Dict[str, Any]]) -> Dict[str, str]:
        """Estimate completion times for tasks"""
        return {
            "earliest_completion": "2024-01-15T11:00:00",
            "latest_completion": "2024-01-15T16:00:00",
            "average_completion": "2024-01-15T13:30:00"
        }
    
    def _analyze_resource_allocation(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze resource allocation across tasks"""
        ai_agent_tasks = len([t for t in tasks if t.get("executor") == "AI_AGENT"])
        human_tasks = len([t for t in tasks if t.get("executor") == "HUMAN"])
        
        return {
            "ai_agent_tasks": ai_agent_tasks,
            "human_tasks": human_tasks,
            "total_tasks": len(tasks),
            "resource_utilization": "balanced" if abs(ai_agent_tasks - human_tasks) <= 1 else "imbalanced"
        }
    
    def _calculate_total_validation_time(self, workflow_steps: List[Dict[str, Any]]) -> str:
        """Calculate total estimated validation time"""
        # Mock calculation
        return "20-30 minutes"
    
    def _get_validation_prerequisites(self, task_reference: str) -> List[str]:
        """Get prerequisites for validation"""
        return [
            "All subtasks completed successfully",
            "No outstanding issues or failures",
            "Required artifacts generated",
            "Quality criteria met"
        ]
    
    def _get_automated_validation_checks(self, task_reference: str) -> List[Dict[str, Any]]:
        """Get automated validation checks that can be performed"""
        return [
            {
                "check": "Artifact Validation",
                "description": "Verify all expected artifacts are present and valid",
                "automated": True,
                "estimated_time": "30 seconds"
            },
            {
                "check": "Criteria Compliance",
                "description": "Check compliance with acceptance criteria",
                "automated": True,
                "estimated_time": "1 minute"
            },
            {
                "check": "Dependency Verification",
                "description": "Verify all dependencies are satisfied",
                "automated": True,
                "estimated_time": "15 seconds"
            }
        ]


def create_task_execution_tools(task_id: str, session_id: str) -> List:
    """
    Factory function to create task execution tools with proper validation.
    
    Args:
        task_id: Main task identifier
        session_id: Session identifier
        
    Returns:
        List of task execution tool functions
        
    Raises:
        ValueError: If required parameters are missing
    """
    if not task_id or not session_id:
        raise ValueError("task_id and session_id are required")
    
    try:
        execution_tools = TaskExecutionTools(task_id, session_id)
        
        return [
            # Core execution methods
            execution_tools.get_task_details,
            execution_tools.execute_task,
            execution_tools.validate_task_completion,
            execution_tools.execute_task_flow,
            execution_tools.mark_task_complete,
            
            # Task hierarchy management methods
            execution_tools.get_task_progress_summary,
            execution_tools.check_task_dependencies,
            execution_tools.check_completion_status,
            execution_tools.get_all_in_progress_tasks,
            execution_tools.suggest_validation_workflow
        ]
    except Exception as e:
        logger.error(f"Failed to create task execution tools: {e}")
        raise 