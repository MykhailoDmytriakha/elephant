# backend/src/constants.py

# HTTP Status Codes
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_CONFLICT = 409
HTTP_SERVER_ERROR = 500
HTTP_NOT_IMPLEMENTED = 501
HTTP_SERVICE_UNAVAILABLE = 503

# Error messages
ERROR_TASK_NOT_FOUND = "Task with ID {task_id} not found"
ERROR_TASK_STATE_INVALID = "Task{id_str} must be in state '{required_state}' to perform this operation. Current state: '{current_state}'"
ERROR_TASK_NO_NETWORK_PLAN = "Task{id_str} does not have a network plan."
ERROR_STAGE_NOT_FOUND = "Stage ID {stage_id} not found."
ERROR_WORK_NOT_FOUND = "Work ID {work_id} not found."
ERROR_EXECUTABLE_TASK_NOT_FOUND = "ExecutableTask ID {task_id} not found."
ERROR_STAGE_NO_WORK = "Stage {stage_id} does not have any work packages."
ERROR_WORK_NO_TASKS = "Work {work_id} does not have any tasks."
ERROR_QUERY_NOT_FOUND = "User query with ID {query_id} not found"
ERROR_NO_QUERIES_FOR_TASK = "No queries found for task ID: {task_id}"
ERROR_TASK_DESERIALIZE = "Failed to load task data"
ERROR_TASK_GROUP_NOT_FOUND = "Group {group} not found in task {task_id}"
ERROR_CREATE_QUERY = "Failed to create user query: {error}"
ERROR_INVALID_SCOPE_REQUEST = "Invalid scope validation request"
ERROR_MISSING_FEEDBACK = "Feedback is required when rejecting scope"
ERROR_DATABASE_OPERATION = "Database operation failed: {operation}"
ERROR_BATCH_OPERATION = "Batch operation failed: {operation}"
ERROR_EMPTY_LIST = "List cannot be empty: {list_name}"
ERROR_BATCH_TASK_GENERATION = "Failed to generate tasks for work {work_id}: {error}"
ERROR_BATCH_WORK_GENERATION = "Failed to generate work for stage {stage_id}: {error}"
ERROR_BATCH_SUBTASK_GENERATION = "Failed to generate subtasks for task {task_id}: {error}"
ERROR_CONCURRENT_OPERATION = "Concurrent operation failed: {operation}"
ERROR_PARTIAL_SUCCESS = "Operation partially succeeded: {success_count}/{total_count} items processed"

# Success messages
SUCCESS_TASK_DELETED = "Task with ID {task_id} successfully deleted"
SUCCESS_ALL_TASKS_DELETED = "All tasks deleted successfully"
SUCCESS_ALL_QUERIES_DELETED = "All user queries deleted successfully"
SUCCESS_SCOPE_CLEARED = "Task scope for ID {task_id} has been successfully cleared"
SUCCESS_GROUP_CLEARED = "Group {group} for task {task_id} has been successfully cleared"
SUCCESS_DRAFT_CLEARED = "Task draft scope for ID {task_id} has been successfully cleared"
SUCCESS_REQUIREMENTS_CLEARED = "Task requirements for ID {task_id} have been successfully cleared"

# API operation names
OP_SUBTASK_GENERATION = "subtask generation"
OP_TASK_GENERATION = "task generation"
OP_BATCH_TASK_GENERATION = "batch task generation"
OP_WORK_GENERATION = "work generation"
OP_BATCH_WORK_GENERATION = "batch work generation"
OP_BATCH_SUBTASK_GENERATION = "batch subtask generation"
OP_SCOPE_VALIDATION = "scope validation"
OP_IFR_GENERATION = "IFR generation"
OP_REQUIREMENTS_GENERATION = "requirements generation"
OP_NETWORK_PLAN_GENERATION = "network plan generation"
OP_CREATE_TASK = "create task"
OP_UPDATE_TASK = "update task"
OP_CREATE_QUERY = "query creation"
OP_GET_QUERIES = "query retrieval"
OP_GET_TASK = "task retrieval"
OP_DELETE_QUERIES = "query deletion"
OP_TASK_DELETION = "task deletion"
OP_SCOPE_CLEARING = "scope clearing"
OP_GROUP_CLEARING = "group clearing"
OP_DRAFT_CLEARING = "draft clearing"
OP_REQUIREMENTS_CLEARING = "requirements clearing"
OP_FORMULATE_TASK = "formulate task"

# Operation names for error handling
OP_GET_TASK = "get task"
OP_CREATE_TASK = "create task"
OP_UPDATE_TASK = "update task"
OP_TASK_DELETION = "task deletion"
OP_CREATE_QUERY = "create query"
OP_GET_QUERIES = "get queries"
OP_DELETE_QUERIES = "delete queries"
OP_SCOPE_CLEARING = "scope clearing"
OP_GROUP_CLEARING = "group clearing"
OP_DRAFT_CLEARING = "draft clearing"
OP_REQUIREMENTS_CLEARING = "requirements clearing" 