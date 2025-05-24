# backend/src/api/validators.py
import logging
from typing import Optional, List, cast

from src.constants import (
    ERROR_TASK_STATE_INVALID,
    ERROR_TASK_NO_NETWORK_PLAN,
    ERROR_TASK_NO_SCOPE,
    ERROR_TASK_NO_SCOPE_GROUP,
    ERROR_STAGE_NO_WORK,
    ERROR_WORK_NO_TASKS
)

from src.exceptions import (
    InvalidStateException,
    MissingComponentException,
    GroupNotFoundException
)

# Forward references for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.model.task import Task, TaskState
    from src.model.planning import Stage, NetworkPlan
    from src.model.work import Work

logger = logging.getLogger(__name__)

class TaskValidator:
    """Validator class for task-related validations"""
    
    @staticmethod
    def validate_task_state(task: 'Task', required_state: 'TaskState', task_id: Optional[str] = None) -> bool:
        """
        Validate that a task is in the required state.
        
        Args:
            task: The task object to validate
            required_state: The required state for the task
            task_id: Optional ID for better error messages
        
        Returns:
            True if the task is in the required state
        
        Raises:
            InvalidStateException: If the task is not in the required state
        """
        id_str = f" {task_id}" if task_id else ""
        
        if not TaskValidator.is_task_in_states(task, [required_state]):
            # For error message, ensure we get the string value safely
            current_state = task.state.value if hasattr(task.state, 'value') else str(task.state)
            required_state_value = required_state.value if hasattr(required_state, 'value') else str(required_state)
            
            error_message = ERROR_TASK_STATE_INVALID.format(
                id_str=id_str,
                required_state=required_state_value,
                current_state=current_state
            )
            logger.error(f"Task state validation failed: {error_message}")
            raise InvalidStateException(error_message)
        
        return True
    
    @staticmethod
    def is_task_in_states(task: 'Task', states: List['TaskState']) -> bool:
        """
        Checks if a task's state matches any of the provided states, handling both enum and string comparisons.
        
        This function handles the case where task.state might be a string or an enum, 
        by comparing both the enum instance and its string value.
        
        Args:
            task: The task to check
            states: List of valid states to check against
            
        Returns:
            True if task state matches any of the provided states, False otherwise
        """
        from src.model.task import TaskState
        
        # Check if task.state is directly one of the provided enum states
        if any(task.state == state for state in states):
            return True
            
        # If task.state is a string, compare with string values of the enum states
        if isinstance(task.state, str):
            return any(task.state == state.value for state in states)
            
        # If task.state is an enum, compare with string values
        if hasattr(task.state, 'value'):
            return any(task.state.value == state.value for state in states)
        
        return False
    
    @staticmethod
    def validate_task_network_plan(task: 'Task', task_id: Optional[str] = None) -> bool:
        """
        Validate that a task has a network plan.
        
        Args:
            task: The task object to validate
            task_id: Optional ID for better error messages
        
        Returns:
            True if the task has a network plan
        
        Raises:
            MissingComponentException: If the task does not have a network plan
        """
        id_str = f" {task_id}" if task_id else ""
        
        if not TaskValidator.has_network_plan(task):
            error_message = ERROR_TASK_NO_NETWORK_PLAN.format(id_str=id_str)
            logger.error(error_message)
            raise MissingComponentException(error_message)
        
        return True
    
    @staticmethod
    def validate_task_scope_group(task: 'Task', group: str, task_id: Optional[str] = None) -> bool:
        """
        Validate that a task scope has the given group.
        
        Args:
            task: The task object to validate
            group: The group to check for
            task_id: Optional ID for better error messages
        
        Returns:
            True if the task scope has the given group
        
        Raises:
            MissingComponentException: If the task does not have the group
        """
        id_str = f" {task_id}" if task_id else ""
        
        if not task.scope:
            error_message = ERROR_TASK_NO_SCOPE.format(id_str=id_str)
            logger.error(error_message)
            raise MissingComponentException(error_message)
        
        scope_dict = task.scope.model_dump()
        if group not in scope_dict:
            error_message = ERROR_TASK_NO_SCOPE_GROUP.format(id_str=id_str, group=group)
            logger.error(error_message)
            raise GroupNotFoundException(error_message)
        
        return True
    
    @staticmethod
    def has_network_plan(task: 'Task') -> bool:
        """
        Type guard to check if task has a network plan.
        
        Args:
            task: The task object to check
        
        Returns:
            True if the task has a network plan, False otherwise
        """
        return task.network_plan is not None


class NetworkPlanValidator:
    """Validator class for network plan related validations"""
    
    @staticmethod
    def has_stages(network_plan: 'NetworkPlan') -> bool:
        """
        Type guard to check if network plan has stages.
        
        Args:
            network_plan: The network plan to check
        
        Returns:
            True if the network plan has stages, False otherwise
        """
        return network_plan.stages is not None and len(network_plan.stages) > 0


class StageValidator:
    """Validator class for stage related validations"""
    
    @staticmethod
    def has_work_packages(stage: 'Stage') -> bool:
        """
        Type guard to check if stage has work packages.
        
        Args:
            stage: The stage to check
        
        Returns:
            True if the stage has work packages, False otherwise
        """
        return stage.work_packages is not None and len(stage.work_packages) > 0


class WorkValidator:
    """Validator class for work package related validations"""
    
    @staticmethod
    def has_tasks(work: 'Work') -> bool:
        """
        Type guard to check if work has tasks.
        
        Args:
            work: The work to check
        
        Returns:
            True if the work has tasks, False otherwise
        """
        return work.tasks is not None and len(work.tasks) > 0 