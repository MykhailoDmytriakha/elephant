"""
Logging Configuration for FastAPI Backend

This module provides configuration settings for the user activity logging system.
It allows for easy customization of logging behavior, formatters, and output destinations.
"""

import os
from typing import Dict, Any, List
from enum import Enum


class LoggingLevel(Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO" 
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LoggingConfig:
    """Configuration class for user activity logging"""
    
    # Environment-based configuration
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    # Log file settings
    LOG_FILE_PATH = os.getenv("USER_ACTIVITY_LOG_PATH", "logs/user_activity.log")
    LOG_FILE_MAX_SIZE = int(os.getenv("LOG_FILE_MAX_SIZE", "10485760"))  # 10MB
    LOG_FILE_BACKUP_COUNT = int(os.getenv("LOG_FILE_BACKUP_COUNT", "5"))
    
    # Console logging settings
    CONSOLE_LOG_LEVEL = os.getenv("CONSOLE_LOG_LEVEL", LoggingLevel.INFO.value)
    FILE_LOG_LEVEL = os.getenv("FILE_LOG_LEVEL", LoggingLevel.INFO.value)
    
    # Feature flags
    ENABLE_CONSOLE_LOGGING = os.getenv("ENABLE_CONSOLE_LOGGING", "true").lower() == "true"
    ENABLE_FILE_LOGGING = os.getenv("ENABLE_FILE_LOGGING", "true").lower() == "true"
    ENABLE_JSON_LOGGING = os.getenv("ENABLE_JSON_LOGGING", "true").lower() == "true"
    ENABLE_PERFORMANCE_LOGGING = os.getenv("ENABLE_PERFORMANCE_LOGGING", "true").lower() == "true"
    
    # Narrative settings
    ENABLE_EMOJIS = os.getenv("ENABLE_EMOJIS", "true").lower() == "true"
    ENABLE_USER_INFO = os.getenv("ENABLE_USER_INFO", "true").lower() == "true"
    ENABLE_TIMESTAMPS = os.getenv("ENABLE_TIMESTAMPS", "true").lower() == "true"
    
    # Performance thresholds (in milliseconds)
    SLOW_REQUEST_THRESHOLD = float(os.getenv("SLOW_REQUEST_THRESHOLD", "1000"))  # 1 second
    VERY_SLOW_REQUEST_THRESHOLD = float(os.getenv("VERY_SLOW_REQUEST_THRESHOLD", "5000"))  # 5 seconds
    
    # Sensitive data filtering
    MASK_SENSITIVE_DATA = os.getenv("MASK_SENSITIVE_DATA", "true").lower() == "true"
    SENSITIVE_FIELDS = [
        "password", "token", "api_key", "secret", "ssn", "credit_card",
        "authorization", "cookie", "session_id"
    ]
    
    # Request body logging limits
    MAX_REQUEST_BODY_SIZE = int(os.getenv("MAX_REQUEST_BODY_SIZE", "1048576"))  # 1MB
    MAX_RESPONSE_BODY_SIZE = int(os.getenv("MAX_RESPONSE_BODY_SIZE", "1048576"))  # 1MB
    
    # User tracking settings
    TRACK_ANONYMOUS_USERS = os.getenv("TRACK_ANONYMOUS_USERS", "true").lower() == "true"
    SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
    
    @classmethod
    def get_logging_config(cls) -> Dict[str, Any]:
        """
        Get the complete logging configuration dictionary
        
        Returns:
            Dict containing the logging configuration
        """
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(cls.LOG_FILE_PATH), exist_ok=True)
        
        handlers: Dict[str, Any] = {}
        user_activity_handlers: List[str] = []
        main_app_handlers: List[str] = []
        
        # Add console handler if enabled
        if cls.ENABLE_CONSOLE_LOGGING:
            handlers["console"] = {
                "class": "logging.StreamHandler",
                "level": cls.CONSOLE_LOG_LEVEL,
                "formatter": "json" if cls.ENABLE_JSON_LOGGING else "standard",
                "stream": "ext://sys.stdout"
            }
            user_activity_handlers.append("console")
            main_app_handlers.append("console")
        
        # Add file handler if enabled
        if cls.ENABLE_FILE_LOGGING:
            handlers["file"] = {
                "class": "logging.handlers.RotatingFileHandler",
                "level": cls.FILE_LOG_LEVEL,
                "formatter": "json" if cls.ENABLE_JSON_LOGGING else "detailed",
                "filename": cls.LOG_FILE_PATH,
                "maxBytes": cls.LOG_FILE_MAX_SIZE,
                "backupCount": cls.LOG_FILE_BACKUP_COUNT,
                "encoding": "utf8"
            }
            user_activity_handlers.append("file")
            main_app_handlers.append("file")
        
        config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                },
                "detailed": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s - %(filename)s:%(lineno)d - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                },
                "json": {
                    "format": "%(message)s"  # Will be handled by custom formatter
                }
            },
            "handlers": handlers,
            "loggers": {
                "user_activity": {
                    "handlers": user_activity_handlers,
                    "level": cls.CONSOLE_LOG_LEVEL,
                    "propagate": False
                },
                "main_app_activity": {
                    "handlers": main_app_handlers,
                    "level": cls.CONSOLE_LOG_LEVEL,
                    "propagate": False
                }
            }
        }
        
        return config
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if we're in development environment"""
        return cls.ENVIRONMENT.lower() in ["development", "dev", "local"]
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if we're in production environment"""
        return cls.ENVIRONMENT.lower() in ["production", "prod"]
    
    @classmethod
    def should_log_request_body(cls, content_length: int) -> bool:
        """Determine if request body should be logged based on size"""
        return content_length <= cls.MAX_REQUEST_BODY_SIZE
    
    @classmethod
    def should_log_response_body(cls, content_length: int) -> bool:
        """Determine if response body should be logged based on size"""
        return content_length <= cls.MAX_RESPONSE_BODY_SIZE
    
    @classmethod
    def is_slow_request(cls, duration_ms: float) -> bool:
        """Determine if a request is considered slow"""
        return duration_ms >= cls.SLOW_REQUEST_THRESHOLD
    
    @classmethod
    def is_very_slow_request(cls, duration_ms: float) -> bool:
        """Determine if a request is considered very slow"""
        return duration_ms >= cls.VERY_SLOW_REQUEST_THRESHOLD
    
    @classmethod
    def mask_sensitive_field(cls, field_name: str, value: str) -> str:
        """Mask sensitive data in log fields"""
        if not cls.MASK_SENSITIVE_DATA:
            return value
            
        field_lower = field_name.lower()
        if any(sensitive in field_lower for sensitive in cls.SENSITIVE_FIELDS):
            if len(value) <= 4:
                return "*" * len(value)
            else:
                return value[:2] + "*" * (len(value) - 4) + value[-2:]
        
        return value


# Example usage and environment variable documentation
ENV_VARS_DOCUMENTATION = """
Environment Variables for User Activity Logging:

# General Configuration
ENVIRONMENT=development|production                    # Application environment
ENABLE_CONSOLE_LOGGING=true|false                    # Enable console output
ENABLE_FILE_LOGGING=true|false                       # Enable file output
ENABLE_JSON_LOGGING=true|false                       # Use JSON format
ENABLE_PERFORMANCE_LOGGING=true|false               # Track performance metrics

# Log File Configuration  
USER_ACTIVITY_LOG_PATH=logs/user_activity.log       # Log file path
LOG_FILE_MAX_SIZE=10485760                           # Max file size in bytes (10MB)
LOG_FILE_BACKUP_COUNT=5                              # Number of backup files

# Log Levels
CONSOLE_LOG_LEVEL=INFO                               # Console logging level
FILE_LOG_LEVEL=INFO                                  # File logging level

# Narrative Configuration
ENABLE_EMOJIS=true|false                             # Use emojis in narratives
ENABLE_USER_INFO=true|false                          # Include user info
ENABLE_TIMESTAMPS=true|false                         # Include timestamps

# Performance Thresholds (milliseconds)
SLOW_REQUEST_THRESHOLD=1000                          # Slow request threshold
VERY_SLOW_REQUEST_THRESHOLD=5000                     # Very slow request threshold

# Data Privacy
MASK_SENSITIVE_DATA=true|false                       # Mask sensitive fields
MAX_REQUEST_BODY_SIZE=1048576                        # Max request body to log (1MB)
MAX_RESPONSE_BODY_SIZE=1048576                       # Max response body to log (1MB)

# User Tracking
TRACK_ANONYMOUS_USERS=true|false                     # Track anonymous users
SESSION_TIMEOUT_MINUTES=30                           # Session timeout
""" 