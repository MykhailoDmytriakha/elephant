#!/usr/bin/env python3
"""
Example Usage of User Activity Logging System

This script demonstrates how to use the user activity logging system
with various examples of user actions and scenarios.

Run this script to see sample log output and understand how the system works.
"""

import asyncio
import time
from datetime import datetime, UTC
from typing import Optional

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


def create_sample_user_session(user_id: Optional[str] = None) -> UserSession:
    """Create a sample user session for demonstration"""
    return UserSession(
        session_id=f"session-{int(time.time())}",
        user_id=user_id,
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        current_page="/dashboard",
        referrer="/login"
    )


def demonstrate_basic_logging():
    """Demonstrate basic logging functionality"""
    print("=" * 60)
    print("🚀 BASIC LOGGING DEMONSTRATION")
    print("=" * 60)
    
    logger = UserActivityLogger("demo_logger")
    
    # Create user sessions
    authenticated_user = create_sample_user_session("user123")
    anonymous_user = create_sample_user_session()
    
    print("\n1. User Navigation:")
    logger.log_page_visit("/dashboard", authenticated_user)
    
    print("\n2. API Calls:")
    logger.log_api_request(
        method="GET",
        endpoint="/api/users",
        status_code=200,
        duration_ms=45.32,
        user_session=authenticated_user,
        request_data={"limit": 10}
    )
    
    print("\n3. Form Submissions:")
    logger.log_form_submission(
        form_name="Profile Update",
        success=True,
        user_session=authenticated_user
    )
    
    print("\n4. Error Logging:")
    logger.log_error(
        error_type="ValidationError",
        error_message="Email format is invalid",
        context={"field": "email", "value": "invalid-email"},
        user_session=anonymous_user
    )


def demonstrate_action_types():
    """Demonstrate different action types"""
    print("\n" + "=" * 60)
    print("🎯 ACTION TYPES DEMONSTRATION")
    print("=" * 60)
    
    logger = UserActivityLogger("action_demo")
    user_session = create_sample_user_session("alice")
    
    # Navigation
    action = UserAction(
        action_type=ActionType.NAVIGATION,
        description="/products/laptops",
        result="Category page loaded"
    )
    logger.log_user_action(action, user_session)
    
    # Search
    action = UserAction(
        action_type=ActionType.SEARCH,
        description="MacBook Pro 2023",
        data={"category": "laptops", "price_range": "1000-3000"},
        result="Found 12 results"
    )
    logger.log_user_action(action, user_session)
    
    # Click
    action = UserAction(
        action_type=ActionType.CLICK,
        description="on product page",
        element="add-to-cart-button",
        result="Item added to cart"
    )
    logger.log_user_action(action, user_session)
    
    # Download
    action = UserAction(
        action_type=ActionType.DOWNLOAD,
        description="Product specification PDF",
        data={"file_size": "2.5MB", "file_type": "PDF"},
        result="Download completed",
        duration_ms=1500.0
    )
    logger.log_user_action(action, user_session)


def demonstrate_performance_logging():
    """Demonstrate performance monitoring"""
    print("\n" + "=" * 60)
    print("⚡ PERFORMANCE MONITORING DEMONSTRATION")
    print("=" * 60)
    
    logger = UserActivityLogger("performance_demo")
    user_session = create_sample_user_session("performance_user")
    
    # Fast request
    logger.log_api_request(
        method="GET",
        endpoint="/api/quick-data",
        status_code=200,
        duration_ms=85.5,
        user_session=user_session
    )
    
    # Slow request
    logger.log_api_request(
        method="POST",
        endpoint="/api/heavy-processing",
        status_code=200,
        duration_ms=1250.0,  # Above slow threshold
        user_session=user_session
    )
    
    # Very slow request
    logger.log_api_request(
        method="GET",
        endpoint="/api/complex-report",
        status_code=200,
        duration_ms=6500.0,  # Above very slow threshold
        user_session=user_session
    )


def demonstrate_error_scenarios():
    """Demonstrate error logging scenarios"""
    print("\n" + "=" * 60)
    print("❌ ERROR SCENARIOS DEMONSTRATION")
    print("=" * 60)
    
    logger = UserActivityLogger("error_demo")
    user_session = create_sample_user_session("error_user")
    
    # Validation errors
    validation_errors = ["Email is required", "Password too short"]
    logger.log_form_submission(
        form_name="Registration Form",
        success=False,
        validation_errors=validation_errors,
        user_session=user_session
    )
    
    # API errors
    logger.log_api_request(
        method="POST",
        endpoint="/api/create-user",
        status_code=400,
        duration_ms=120.0,
        user_session=user_session
    )
    
    # Server errors
    logger.log_error(
        error_type="DatabaseConnectionError",
        error_message="Failed to connect to database",
        context={
            "database": "users_db",
            "retry_count": 3,
            "last_error": "Connection timeout"
        },
        user_session=user_session
    )


def demonstrate_user_journey():
    """Demonstrate a complete user journey"""
    print("\n" + "=" * 60)
    print("🗺️ COMPLETE USER JOURNEY DEMONSTRATION")
    print("=" * 60)
    
    logger = UserActivityLogger("journey_demo")
    
    # Anonymous user starts journey
    anonymous_session = create_sample_user_session()
    anonymous_session.current_page = "/"
    
    print("\n📍 Anonymous user visits homepage:")
    logger.log_page_visit("/", anonymous_session)
    
    print("\n🔍 User searches for products:")
    logger.log_search("wireless headphones", 25, anonymous_session)
    
    print("\n👆 User clicks on product:")
    log_click("product-card-1", "/search-results")
    
    print("\n📝 User attempts to register:")
    log_form_submission("Registration Form", success=False, validation_errors=["Email already exists"])
    
    # User successfully logs in
    authenticated_session = create_sample_user_session("new_user_456")
    authenticated_session.current_page = "/login"
    
    print("\n🔐 User logs in successfully:")
    action = UserAction(
        action_type=ActionType.AUTH,
        description="User login successful",
        data={"login_method": "email", "remember_me": True},
        result="Authentication successful"
    )
    logger.log_user_action(action, authenticated_session)
    
    print("\n🔌 User adds item to cart:")
    logger.log_api_request(
        method="POST",
        endpoint="/api/cart/add",
        status_code=201,
        duration_ms=95.0,
        user_session=authenticated_session
    )
    
    print("\n💳 User completes purchase:")
    action = UserAction(
        action_type=ActionType.FORM_SUBMISSION,
        description="Purchase completed",
        data={"total_amount": 129.99, "items_count": 1, "payment_method": "credit_card"},
        result="Order #12345 created successfully"
    )
    logger.log_user_action(action, authenticated_session)


def demonstrate_helper_functions():
    """Demonstrate helper functions"""
    print("\n" + "=" * 60)
    print("🛠️ HELPER FUNCTIONS DEMONSTRATION")
    print("=" * 60)
    
    print("\n1. Quick click logging:")
    log_click("newsletter-signup", "/homepage")
    
    print("\n2. Quick search logging:")
    log_search("python fastapi tutorial", 142)
    
    print("\n3. Quick form submission logging:")
    log_form_submission("Contact Form", success=True)
    
    print("\n4. Quick error logging:")
    log_error("TimeoutError", "Request timeout after 30 seconds", {"endpoint": "/api/slow"})


async def demonstrate_async_logging():
    """Demonstrate async logging patterns"""
    print("\n" + "=" * 60)
    print("🔄 ASYNC LOGGING DEMONSTRATION")
    print("=" * 60)
    
    logger = UserActivityLogger("async_demo")
    user_session = create_sample_user_session("async_user")
    
    # Simulate async operations
    print("\n⏳ Simulating async user actions...")
    
    # Start long-running task
    start_time = time.perf_counter()
    
    action = UserAction(
        action_type=ActionType.API_CALL,
        description="Starting background job",
        result="Job queued successfully"
    )
    logger.log_user_action(action, user_session)
    
    # Simulate work
    await asyncio.sleep(0.1)
    
    # Complete task
    duration_ms = (time.perf_counter() - start_time) * 1000
    action = UserAction(
        action_type=ActionType.PERFORMANCE,
        description="Background job completed",
        duration_ms=duration_ms,
        result="Job completed successfully"
    )
    logger.log_user_action(action, user_session)


def main():
    """Main demonstration function"""
    print("🚀 User Activity Logging System - Demonstration")
    print("=" * 60)
    print("This script demonstrates various features of the user activity logging system.")
    print("Watch the console output to see how logs are formatted!")
    print()
    
    # Run demonstrations
    demonstrate_basic_logging()
    demonstrate_action_types()
    demonstrate_performance_logging()
    demonstrate_error_scenarios()
    demonstrate_user_journey()
    demonstrate_helper_functions()
    
    # Run async demo
    asyncio.run(demonstrate_async_logging())
    
    print("\n" + "=" * 60)
    print("✅ DEMONSTRATION COMPLETE!")
    print("=" * 60)
    print()
    print("📁 Check the 'user_activity.log' file for the complete structured JSON logs.")
    print("🎯 Try different environment variables to see how they affect the output:")
    print("   - ENABLE_EMOJIS=false (disable emojis)")
    print("   - ENABLE_JSON_LOGGING=false (use plain text format)")
    print("   - CONSOLE_LOG_LEVEL=DEBUG (show more details)")
    print()
    print("🔧 Integration tips:")
    print("   - Add the middleware to your FastAPI app for automatic logging")
    print("   - Use helper functions for quick logging")
    print("   - Customize action types for your specific use cases")
    print("   - Set up log rotation for production environments")


if __name__ == "__main__":
    main() 