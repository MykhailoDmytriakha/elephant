"""
User Activity Logging System for FastAPI Backend

This module provides comprehensive user flow tracking with readable, structured logs.
The logs are designed to be easily readable like a "read book" format, allowing developers
to quickly understand user journey, actions performed, and results.

Features:
- Request/Response middleware logging
- User action tracking
- Structured JSON logging with human-readable messages
- Context tracking across requests
- Performance metrics
- Error tracking with user context
"""

import json
import time
import uuid
from datetime import datetime, UTC
from typing import Dict, Any, Optional, List
from enum import Enum
import logging
from contextvars import ContextVar
from dataclasses import dataclass, asdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
import asyncio


# Context variables for tracking user session
request_context: ContextVar[Dict[str, Any]] = ContextVar('request_context', default={})


class ActionType(Enum):
    """Types of user actions that can be tracked"""
    NAVIGATION = "navigation"
    CLICK = "click"
    FORM_SUBMISSION = "form_submission"
    API_CALL = "api_call"
    SEARCH = "search"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    AUTH = "authentication"
    ERROR = "error"
    PERFORMANCE = "performance"


class LogLevel(Enum):
    """Custom log levels for user activity"""
    USER_ACTION = "USER_ACTION"
    USER_FLOW = "USER_FLOW"
    USER_ERROR = "USER_ERROR"
    USER_PERFORMANCE = "USER_PERFORMANCE"


@dataclass
class UserAction:
    """Represents a single user action"""
    action_type: ActionType
    description: str
    element: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    duration_ms: Optional[float] = None
    result: Optional[str] = None
    success: bool = True
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)


@dataclass
class UserSession:
    """Represents a user session context"""
    session_id: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    start_time: Optional[datetime] = None
    current_page: Optional[str] = None
    referrer: Optional[str] = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now(UTC)


class UserActivityLogger:
    """
    Main class for logging user activities in a readable format.
    Creates logs that read like a story of the user's journey.
    """
    
    def __init__(self, logger_name: str = "user_activity"):
        self.logger = logging.getLogger(logger_name)
        self._setup_logger()
        
    def _setup_logger(self):
        """Setup structured logging configuration"""
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            
        # Create custom formatter for readable logs
        formatter = UserActivityFormatter()
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        
        # File handler for production logs
        file_handler = logging.FileHandler('user_activity.log')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)
        
    def log_user_action(self, action: UserAction, session: Optional[UserSession] = None):
        """
        Log a user action in a readable narrative format
        
        Args:
            action: UserAction object containing action details
            session: Optional UserSession object for context
        """
        context = request_context.get({})
        
        # Build readable narrative message
        narrative = self._build_narrative(action, session, context)
        
        # Create structured log data
        log_data = {
            "event": "user_action",
            "narrative": narrative,
            "action": asdict(action),
            "session": asdict(session) if session else None,
            "context": context,
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        # Log with appropriate level
        if action.action_type == ActionType.ERROR:
            self.logger.error(json.dumps(log_data, indent=2, default=str))
        else:
            self.logger.info(json.dumps(log_data, indent=2, default=str))
            
    def _build_narrative(self, action: UserAction, session: Optional[UserSession], context: Dict[str, Any]) -> str:
        """
        Build a human-readable narrative describing the user action
        
        Returns:
            str: A readable sentence describing what happened
        """
        timestamp = action.timestamp.strftime("%H:%M:%S") if action.timestamp else "unknown time"
        user_info = ""
        
        if session:
            if session.user_id:
                user_info = f"User {session.user_id}"
            else:
                user_info = f"Anonymous user from {session.ip_address}"
        else:
            user_info = "Unknown user"
            
        # Build narrative based on action type
        narratives = {
            ActionType.NAVIGATION: f"📍 {user_info} navigated to '{action.description}' at {timestamp}",
            ActionType.CLICK: f"👆 {user_info} clicked on '{action.element or action.description}' at {timestamp}",
            ActionType.FORM_SUBMISSION: f"📝 {user_info} submitted form '{action.description}' at {timestamp}",
            ActionType.API_CALL: f"🔌 {user_info} made API call to '{action.description}' at {timestamp}",
            ActionType.SEARCH: f"🔍 {user_info} searched for '{action.description}' at {timestamp}",
            ActionType.DOWNLOAD: f"⬇️ {user_info} downloaded '{action.description}' at {timestamp}",
            ActionType.UPLOAD: f"⬆️ {user_info} uploaded '{action.description}' at {timestamp}",
            ActionType.AUTH: f"🔐 {user_info} performed authentication: '{action.description}' at {timestamp}",
            ActionType.ERROR: f"❌ {user_info} encountered error: '{action.description}' at {timestamp}",
            ActionType.PERFORMANCE: f"⚡ Performance metric for {user_info}: '{action.description}' at {timestamp}"
        }
        
        base_narrative = narratives.get(action.action_type, f"📊 {user_info} performed '{action.description}' at {timestamp}")
        
        # Add result information
        if action.result:
            result_emoji = "✅" if action.success else "❌"
            base_narrative += f" → {result_emoji} Result: {action.result}"
            
        # Add duration if available
        if action.duration_ms:
            base_narrative += f" (took {action.duration_ms:.2f}ms)"
            
        return base_narrative
        
    def log_page_visit(self, page_path: str, user_session: Optional[UserSession] = None):
        """Log when a user visits a page"""
        action = UserAction(
            action_type=ActionType.NAVIGATION,
            description=page_path,
            result="Page loaded successfully"
        )
        self.log_user_action(action, user_session)
        
    def log_api_request(self, method: str, endpoint: str, status_code: int, 
                       duration_ms: float, user_session: Optional[UserSession] = None,
                       request_data: Optional[Dict] = None):
        """Log API request with outcome"""
        success = 200 <= status_code < 400
        result = f"HTTP {status_code} {'SUCCESS' if success else 'ERROR'}"
        
        action = UserAction(
            action_type=ActionType.API_CALL,
            description=f"{method} {endpoint}",
            data=request_data,
            duration_ms=duration_ms,
            result=result,
            success=success
        )
        self.log_user_action(action, user_session)
        
    def log_user_click(self, element: str, page: str, user_session: Optional[UserSession] = None):
        """Log when a user clicks on an element"""
        action = UserAction(
            action_type=ActionType.CLICK,
            description=f"on page '{page}'",
            element=element,
            result="Click registered"
        )
        self.log_user_action(action, user_session)
        
    def log_form_submission(self, form_name: str, success: bool, 
                          validation_errors: Optional[List[str]] = None,
                          user_session: Optional[UserSession] = None):
        """Log form submission with validation results"""
        result = "Form submitted successfully" if success else f"Form validation failed: {', '.join(validation_errors or [])}"
        
        action = UserAction(
            action_type=ActionType.FORM_SUBMISSION,
            description=form_name,
            data={"validation_errors": validation_errors} if validation_errors else None,
            result=result,
            success=success
        )
        self.log_user_action(action, user_session)
        
    def log_search(self, query: str, results_count: int, user_session: Optional[UserSession] = None):
        """Log search action with results"""
        action = UserAction(
            action_type=ActionType.SEARCH,
            description=query,
            data={"results_count": results_count},
            result=f"Found {results_count} results"
        )
        self.log_user_action(action, user_session)
        
    def log_error(self, error_type: str, error_message: str, context: Optional[Dict] = None,
                 user_session: Optional[UserSession] = None):
        """Log errors with user context"""
        action = UserAction(
            action_type=ActionType.ERROR,
            description=f"{error_type}: {error_message}",
            data=context,
            success=False,
            result="Error occurred"
        )
        self.log_user_action(action, user_session)


class UserActivityFormatter(logging.Formatter):
    """Custom formatter for user activity logs"""
    
    def format(self, record):
        # Try to parse JSON log data for pretty printing
        try:
            if hasattr(record, 'msg') and isinstance(record.msg, str):
                log_data = json.loads(record.msg)
                if 'narrative' in log_data:
                    # Return just the narrative for console output (readable)
                    return f"[{record.levelname}] {log_data['narrative']}"
        except (json.JSONDecodeError, KeyError):
            pass
            
        # Fallback to default formatting
        return super().format(record)


class UserActivityMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatically tracking user requests and responses
    """
    
    def __init__(self, app, logger: Optional[UserActivityLogger] = None):
        super().__init__(app)
        self.activity_logger = logger or UserActivityLogger()
        
    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()
        
        # Extract user session info
        user_session = self._extract_user_session(request, request_id)
        
        # Set request context
        context = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "start_time": start_time
        }
        request_context.set(context)
        
        # Log incoming request
        self.activity_logger.log_page_visit(
            page_path=request.url.path,
            user_session=user_session
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Extract request body if available
            request_data = await self._extract_request_data(request)
            
            # Log API request with response
            self.activity_logger.log_api_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                user_session=user_session,
                request_data=request_data
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Log error with user context
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            self.activity_logger.log_error(
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "endpoint": request.url.path,
                    "method": request.method,
                    "duration_ms": duration_ms
                },
                user_session=user_session
            )
            raise
            
    def _extract_user_session(self, request: Request, request_id: str) -> UserSession:
        """Extract user session information from request"""
        return UserSession(
            session_id=request_id,
            user_id=request.headers.get("X-User-ID"),  # Assuming user ID in header
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
            current_page=request.url.path,
            referrer=request.headers.get("Referer")
        )
        
    async def _extract_request_data(self, request: Request) -> Optional[Dict]:
        """Safely extract request data"""
        try:
            if request.method in ["POST", "PUT", "PATCH"]:
                # Clone the request to avoid consuming the body
                body = await request.body()
                if body:
                    return {"body_size": len(body), "content_type": request.headers.get("content-type")}
        except Exception:
            pass
        return None


# Singleton instance for easy import
user_activity_logger = UserActivityLogger()


# Helper functions for easy logging
def log_user_action(action_type: ActionType, description: str, **kwargs):
    """Helper function to log user action"""
    action = UserAction(action_type=action_type, description=description, **kwargs)
    user_activity_logger.log_user_action(action)


def log_click(element: str, page: str):
    """Helper function to log clicks"""
    user_activity_logger.log_user_click(element, page)


def log_form_submission(form_name: str, success: bool, validation_errors: Optional[List[str]] = None):
    """Helper function to log form submissions"""
    user_activity_logger.log_form_submission(form_name, success, validation_errors)


def log_search(query: str, results_count: int):
    """Helper function to log searches"""
    user_activity_logger.log_search(query, results_count)


def log_error(error_type: str, error_message: str, context: Optional[Dict] = None):
    """Helper function to log errors"""
    user_activity_logger.log_error(error_type, error_message, context) 