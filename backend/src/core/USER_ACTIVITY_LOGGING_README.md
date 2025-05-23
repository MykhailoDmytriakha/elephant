# User Activity Logging System

A comprehensive user flow tracking system for FastAPI applications that creates readable, structured logs designed to be understood like a "read book" format.

## 📖 Overview

This logging system provides detailed tracking of user interactions, API calls, form submissions, and navigation patterns. The logs are designed to tell a story of the user's journey through your application, making it easy for developers to understand user behavior and troubleshoot issues.

## 🚀 Features

- **Readable Narrative Logs**: Logs that read like natural language with emojis and clear descriptions
- **Automatic Request/Response Tracking**: Middleware automatically logs all API requests and responses
- **User Session Tracking**: Track user sessions across multiple requests
- **Performance Monitoring**: Track slow requests and performance metrics
- **Error Tracking**: Comprehensive error logging with user context
- **Structured JSON Output**: Both human-readable and machine-parsable formats
- **Configurable**: Extensive configuration options via environment variables
- **Privacy-Aware**: Automatic masking of sensitive data

## 📝 Example Log Output

### Console Output (Human-Readable)
```
[INFO] 📍 User user123 navigated to '/user-queries' at 14:30:25 → ✅ Result: Page loaded successfully
[INFO] 🔌 User user123 made API call to 'GET /user-queries' at 14:30:25 → ✅ Result: HTTP 200 SUCCESS (took 45.32ms)
[INFO] 📝 Anonymous user from 192.168.1.100 submitted form 'Create User Query' at 14:31:12 → ✅ Result: Query created successfully
[ERROR] ❌ User user123 encountered error: 'ValidationError: Query cannot be empty' at 14:32:45 → ❌ Result: Error occurred
```

### Structured JSON Output
```json
{
  "event": "user_action",
  "narrative": "🔌 User user123 made API call to 'GET /user-queries' at 14:30:25 → ✅ Result: HTTP 200 SUCCESS (took 45.32ms)",
  "action": {
    "action_type": "api_call",
    "description": "GET /user-queries",
    "duration_ms": 45.32,
    "result": "HTTP 200 SUCCESS",
    "success": true,
    "timestamp": "2024-01-15T14:30:25.123456Z"
  },
  "session": {
    "session_id": "uuid-123-456",
    "user_id": "user123",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "current_page": "/user-queries"
  },
  "context": {
    "request_id": "req-789-012",
    "method": "GET",
    "url": "http://localhost:8000/user-queries"
  }
}
```

## 🛠 Installation & Setup

### 1. Import and Configure

The system is already integrated into your FastAPI application. The middleware is added in `main.py`:

```python
from src.core.user_activity_logger import UserActivityMiddleware, UserActivityLogger

# Initialize user activity logger
user_activity_logger = UserActivityLogger("main_app_activity")

# Add middleware to FastAPI app
app.add_middleware(UserActivityMiddleware, logger=user_activity_logger)
```

### 2. Environment Configuration

Configure the logging system using environment variables:

```bash
# Basic Configuration
ENVIRONMENT=development
ENABLE_CONSOLE_LOGGING=true
ENABLE_FILE_LOGGING=true
ENABLE_JSON_LOGGING=true

# Log File Settings
USER_ACTIVITY_LOG_PATH=logs/user_activity.log
LOG_FILE_MAX_SIZE=10485760  # 10MB
LOG_FILE_BACKUP_COUNT=5

# Narrative Settings
ENABLE_EMOJIS=true
ENABLE_USER_INFO=true
ENABLE_TIMESTAMPS=true

# Performance Monitoring
SLOW_REQUEST_THRESHOLD=1000      # 1 second
VERY_SLOW_REQUEST_THRESHOLD=5000 # 5 seconds

# Privacy
MASK_SENSITIVE_DATA=true
MAX_REQUEST_BODY_SIZE=1048576    # 1MB
```

## 💻 Usage Examples

### Automatic Logging (via Middleware)

The middleware automatically logs all requests and responses:

```python
# This is automatic - no code needed
# GET /user-queries → Logs navigation and API call
# POST /user-queries → Logs form submission and API call
```

### Manual Logging in Endpoints

Add detailed logging in your API endpoints:

```python
from src.core.user_activity_logger import user_activity_logger, UserAction, ActionType

@router.post("/items")
async def create_item(item: Item, request: Request):
    user_session = get_user_session_from_request(request)
    
    try:
        # Your business logic here
        created_item = create_item_logic(item)
        
        # Log successful creation
        action = UserAction(
            action_type=ActionType.FORM_SUBMISSION,
            description=f"Item created: '{item.name}'",
            data={"item_id": created_item.id, "category": item.category},
            result="Item created successfully",
            success=True
        )
        user_activity_logger.log_user_action(action, user_session)
        
        return created_item
        
    except ValidationError as e:
        # Log validation error
        user_activity_logger.log_error(
            error_type="ValidationError",
            error_message=str(e),
            context={"item_data": item.dict()},
            user_session=user_session
        )
        raise
```

### Helper Functions

Use convenient helper functions for common actions:

```python
from src.core.user_activity_logger import log_click, log_search, log_form_submission

# Log user clicks
log_click(element="submit-button", page="/create-item")

# Log searches
log_search(query="python tutorials", results_count=150)

# Log form submissions
log_form_submission(
    form_name="Contact Form",
    success=True,
    validation_errors=None
)
```

## 🎯 Action Types

The system supports various action types:

| Action Type | Description | Example Use Case |
|-------------|-------------|------------------|
| `NAVIGATION` | Page visits, route changes | User navigates to dashboard |
| `CLICK` | Button clicks, link clicks | User clicks "Submit" button |
| `FORM_SUBMISSION` | Form submissions | User submits contact form |
| `API_CALL` | API requests/responses | User calls GET /users endpoint |
| `SEARCH` | Search queries | User searches for "python" |
| `DOWNLOAD` | File downloads | User downloads PDF report |
| `UPLOAD` | File uploads | User uploads profile image |
| `AUTH` | Authentication actions | User logs in/out |
| `ERROR` | Error occurrences | Validation error, server error |
| `PERFORMANCE` | Performance metrics | Slow query detection |

## 📊 User Session Tracking

User sessions are automatically tracked and include:

- **Session ID**: Unique identifier for the session
- **User ID**: Authenticated user identifier (if available)
- **IP Address**: Client IP address
- **User Agent**: Browser/client information
- **Current Page**: Current page/endpoint
- **Referrer**: Previous page (if available)

## ⚡ Performance Monitoring

The system automatically tracks performance metrics:

- **Request Duration**: Time taken for each request
- **Slow Request Detection**: Automatic flagging of slow requests
- **Performance Thresholds**: Configurable thresholds for alerts

```python
# Automatic performance logging
# Requests > 1000ms are flagged as slow
# Requests > 5000ms are flagged as very slow
```

## 🔒 Privacy & Security

### Sensitive Data Masking

The system automatically masks sensitive data:

```python
# Automatically masked fields:
password = "mypassword123" → "my*******23"
api_key = "sk-1234567890" → "sk*******90"
token = "abcd" → "****"
```

### Configurable Privacy Settings

```bash
MASK_SENSITIVE_DATA=true                 # Enable/disable masking
MAX_REQUEST_BODY_SIZE=1048576           # Limit request body logging
MAX_RESPONSE_BODY_SIZE=1048576          # Limit response body logging
TRACK_ANONYMOUS_USERS=true              # Track anonymous users
```

## 📁 Log File Management

### File Rotation

Logs are automatically rotated to prevent disk space issues:

```bash
logs/
├── user_activity.log        # Current log file
├── user_activity.log.1      # Previous log file
├── user_activity.log.2      # Older log file
└── ...                      # Up to LOG_FILE_BACKUP_COUNT files
```

### Log Levels

Different log levels for different purposes:

- **INFO**: Normal user actions, API calls
- **WARNING**: Slow requests, unusual behavior
- **ERROR**: Errors, exceptions, failures
- **DEBUG**: Detailed debugging information

## 🔧 Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Application environment |
| `ENABLE_CONSOLE_LOGGING` | `true` | Enable console output |
| `ENABLE_FILE_LOGGING` | `true` | Enable file logging |
| `ENABLE_JSON_LOGGING` | `true` | Use JSON format |
| `USER_ACTIVITY_LOG_PATH` | `logs/user_activity.log` | Log file path |
| `LOG_FILE_MAX_SIZE` | `10485760` | Max file size (10MB) |
| `LOG_FILE_BACKUP_COUNT` | `5` | Number of backup files |
| `CONSOLE_LOG_LEVEL` | `INFO` | Console logging level |
| `FILE_LOG_LEVEL` | `INFO` | File logging level |
| `ENABLE_EMOJIS` | `true` | Use emojis in narratives |
| `SLOW_REQUEST_THRESHOLD` | `1000` | Slow request threshold (ms) |
| `MASK_SENSITIVE_DATA` | `true` | Mask sensitive fields |

## 🎨 Customization

### Custom Action Types

Extend the system with custom action types:

```python
# Add to ActionType enum
class ActionType(Enum):
    # ... existing types ...
    CUSTOM_ACTION = "custom_action"

# Use in logging
action = UserAction(
    action_type=ActionType.CUSTOM_ACTION,
    description="Custom business logic executed",
    data={"custom_field": "value"}
)
```

### Custom Formatters

Create custom log formatters:

```python
class CustomFormatter(UserActivityFormatter):
    def format(self, record):
        # Custom formatting logic
        return super().format(record)
```

## 🔍 Monitoring & Analytics

### Log Analysis

Use the structured JSON logs for analytics:

```bash
# Count user actions by type
jq '.action.action_type' user_activity.log | sort | uniq -c

# Find slow requests
jq 'select(.action.duration_ms > 1000)' user_activity.log

# Track user journey for specific user
jq 'select(.session.user_id == "user123")' user_activity.log
```

### Integration with Monitoring Tools

The logs can be integrated with:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Prometheus** + **Grafana**
- **Datadog**
- **New Relic**
- **Splunk**

## 🐛 Troubleshooting

### Common Issues

1. **Logs not appearing**
   - Check `ENABLE_CONSOLE_LOGGING` and `ENABLE_FILE_LOGGING`
   - Verify log file permissions
   - Check log level configuration

2. **Large log files**
   - Adjust `LOG_FILE_MAX_SIZE`
   - Increase `LOG_FILE_BACKUP_COUNT`
   - Enable log rotation

3. **Sensitive data in logs**
   - Enable `MASK_SENSITIVE_DATA`
   - Add custom sensitive fields to `SENSITIVE_FIELDS`
   - Reduce `MAX_REQUEST_BODY_SIZE`

### Debug Mode

Enable debug logging for troubleshooting:

```bash
CONSOLE_LOG_LEVEL=DEBUG
FILE_LOG_LEVEL=DEBUG
```

## 📈 Best Practices

1. **Use Descriptive Messages**: Make log descriptions clear and informative
2. **Include Relevant Context**: Add data that helps understand the action
3. **Handle Errors Gracefully**: Always log errors with proper context
4. **Monitor Performance**: Use performance thresholds to catch issues
5. **Protect Privacy**: Ensure sensitive data is properly masked
6. **Regular Log Review**: Regularly review logs for insights
7. **Log Rotation**: Keep log files manageable with rotation
8. **Structured Data**: Use structured logging for better analytics

## 🤝 Contributing

To extend the logging system:

1. Add new action types to `ActionType` enum
2. Extend `UserAction` dataclass for new fields
3. Create custom formatters for specialized output
4. Add new helper functions for common patterns
5. Update configuration for new features

## 📄 License

This user activity logging system is part of your FastAPI application and follows the same license terms. 