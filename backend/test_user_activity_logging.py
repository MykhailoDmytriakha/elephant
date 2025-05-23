#!/usr/bin/env python3
"""
Test script for User Activity Logging System

This script tests the basic functionality of the user activity logging system
to ensure it's working correctly.
"""

import sys
import os
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from src.core.user_activity_logger import (
    UserActivityLogger,
    UserAction,
    ActionType,
    UserSession,
    log_click,
    log_search,
    log_form_submission,
    log_error
)
import logging

def test_basic_logging():
    """Test basic logging functionality"""
    print("🧪 Testing User Activity Logging System...")
    print("=" * 50)
    
    # Initialize logger
    logger = UserActivityLogger("test_logger")
    
    # Create a test user session
    user_session = UserSession(
        session_id="test-session-123",
        user_id="test_user",
        ip_address="127.0.0.1",
        user_agent="Test Agent",
        current_page="/test",
        referrer="/home"
    )
    
    print("\n1. Testing user action logging:")
    action = UserAction(
        action_type=ActionType.NAVIGATION,
        description="/dashboard",
        result="Page loaded successfully"
    )
    logger.log_user_action(action, user_session)
    
    print("\n2. Testing API request logging:")
    logger.log_api_request(
        method="GET",
        endpoint="/api/test",
        status_code=200,
        duration_ms=45.5,
        user_session=user_session
    )
    
    print("\n3. Testing form submission logging:")
    logger.log_form_submission(
        form_name="Test Form",
        success=True,
        user_session=user_session
    )
    
    print("\n4. Testing error logging:")
    logger.log_error(
        error_type="TestError",
        error_message="This is a test error",
        context={"test": "context"},
        user_session=user_session
    )
    
    print("\n5. Testing helper functions:")
    log_click("test-button", "/test-page")
    log_search("test query", 42)
    log_form_submission("Helper Form", success=True)
    log_error("HelperError", "Helper test error")
    
    print("\n✅ All tests completed successfully!")
    print("📁 Check 'user_activity.log' for the complete log output.")


if __name__ == "__main__":
    test_basic_logging() 