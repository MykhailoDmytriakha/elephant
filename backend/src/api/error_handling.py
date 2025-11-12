import logging
from typing import Callable, Any, TypeVar, ParamSpec, Awaitable
from functools import wraps

from fastapi import HTTPException

from src.constants import (
    HTTP_NOT_FOUND,
    HTTP_BAD_REQUEST,
    HTTP_SERVER_ERROR,
    HTTP_NOT_IMPLEMENTED
)

from src.exceptions import (
    TaskNotFoundException,
    StageNotFoundException,
    WorkNotFoundException,
    ExecutableTaskNotFoundException,
    InvalidStateException,
    MissingComponentException,
    DeserializationException,
    QueryNotFoundException,
    GroupNotFoundException,
    ValidationException
)

logger = logging.getLogger(__name__)

P = ParamSpec('P')
T = TypeVar('T')

class APIErrorHandler:
    """Centralized API error handler"""
    
    @staticmethod
    def _handle_not_found_errors(error: Exception, operation_name: str) -> HTTPException:
        """Handle all 'not found' type errors"""
        logger.error(f"Resource not found during {operation_name}: {error}")
        return HTTPException(status_code=HTTP_NOT_FOUND, detail=str(error))
    
    @staticmethod
    def _handle_bad_request_errors(error: Exception, operation_name: str) -> HTTPException:
        """Handle all 'bad request' type errors"""
        logger.error(f"Bad request error during {operation_name}: {error}")
        return HTTPException(status_code=HTTP_BAD_REQUEST, detail=str(error))
    
    @staticmethod
    def _handle_server_errors(error: Exception, operation_name: str) -> HTTPException:
        """Handle all server errors"""
        logger.error(f"Server error during {operation_name}: {error}", exc_info=True)
        return HTTPException(status_code=HTTP_SERVER_ERROR, detail=f"An internal error occurred during {operation_name}.")
    
    @classmethod
    def handle_exception(cls, error: Exception, operation_name: str) -> HTTPException:
        """
        Central exception handling method
        
        Args:
            error: The exception to handle
            operation_name: Description of the operation
            
        Returns:
            HTTPException with appropriate status code and message
        """
        # Not found errors
        if isinstance(error, (TaskNotFoundException, StageNotFoundException, 
                            WorkNotFoundException, ExecutableTaskNotFoundException,
                            QueryNotFoundException, GroupNotFoundException)):
            return cls._handle_not_found_errors(error, operation_name)
        
        # ValueError handling for "not found" cases
        if isinstance(error, ValueError):
            error_msg = str(error).lower()
            if "not found" in error_msg or "no queries found" in error_msg:
                return cls._handle_not_found_errors(error, operation_name)
            else:
                return cls._handle_bad_request_errors(error, operation_name)
        
        # Bad request errors
        if isinstance(error, (InvalidStateException, MissingComponentException, ValidationException)):
            return cls._handle_bad_request_errors(error, operation_name)
        
        # Server errors
        if isinstance(error, DeserializationException):
            logger.error(f"Deserialization error during {operation_name}: {error}")
            return HTTPException(status_code=HTTP_SERVER_ERROR, detail=str(error))
        
        # Import errors
        if isinstance(error, ImportError):
            logger.error(f"Import error during {operation_name}: {error}")
            return HTTPException(status_code=HTTP_NOT_IMPLEMENTED,
                               detail=f"{operation_name} feature requires additional dependencies.")

        # HTTPException - re-raise as is
        if isinstance(error, HTTPException):
            return error

        # Default to server error
        return cls._handle_server_errors(error, operation_name)


def api_error_handler(operation_name: str) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """
    Decorator for API endpoint functions to standardize error handling.
    
    Args:
        operation_name: A descriptive name for the operation being performed
        
    Returns:
        Decorated function with standardized error handling
    """
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                raise APIErrorHandler.handle_exception(e, operation_name)
        return wrapper
    return decorator 