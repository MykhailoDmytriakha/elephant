"""
Custom exception classes for the API.

These exceptions are raised by various components of the application and are 
caught by the api_error_handler decorator, which translates them into appropriate
HTTP responses.
"""

class BaseAPIException(Exception):
    """Base class for all API exceptions."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

# Resource not found exceptions
class ResourceNotFoundException(BaseAPIException):
    """Base class for all resource not found exceptions."""
    pass

class TaskNotFoundException(ResourceNotFoundException):
    """Raised when a task is not found."""
    pass

class StageNotFoundException(ResourceNotFoundException):
    """Raised when a stage is not found."""
    pass

class WorkNotFoundException(ResourceNotFoundException):
    """Raised when a work package is not found."""
    pass

class ExecutableTaskNotFoundException(ResourceNotFoundException):
    """Raised when an executable task is not found."""
    pass

class GroupNotFoundException(ResourceNotFoundException):
    """Raised when a group is not found in a task scope."""
    pass

class QueryNotFoundException(ResourceNotFoundException):
    """Raised when a user query is not found."""
    pass

# Validation exceptions
class ValidationException(BaseAPIException):
    """Base class for all validation exceptions."""
    pass

class InvalidStateException(ValidationException):
    """Raised when a task is in an invalid state for an operation."""
    pass

class MissingComponentException(ValidationException):
    """Raised when a required component is missing."""
    pass

# Server exceptions
class ServerException(BaseAPIException):
    """Base class for all server exceptions."""
    pass

class DatabaseException(ServerException):
    """Raised when there is a database error."""
    pass

class DeserializationException(ServerException):
    """Raised when there is an error deserializing data."""
    pass

# Feature exceptions
class FeatureNotImplementedException(BaseAPIException):
    """Raised when a feature is not implemented."""
    pass

class ImportException(FeatureNotImplementedException):
    """Raised when there is an error importing a dependency."""
    pass

class SubtaskNotFoundException(ResourceNotFoundException):
    "Raised when a specific subtask is not found within an executable task."
    pass 