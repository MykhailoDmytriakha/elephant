from enum import Enum

class StatusEnum(Enum):
    """
    Enum representing the execution status of tasks, works, stages, and subtasks.
    """
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled" 
    WAITING = "Waiting"