# Elephant Project - API Documentation

## API Overview

The Elephant Project's backend exposes a RESTful API built with FastAPI. This document outlines the available endpoints, their request/response formats, and usage examples.

## Base URL

For local development: `http://localhost:8000`

## Authentication

Currently, the API does not implement authentication. Future versions will include authentication mechanisms.

## Common Response Formats

### Success Response

```json
{
  "status": "success",
  "data": {
    // Response data specific to the endpoint
  }
}
```

### Error Response

```json
{
  "status": "error",
  "message": "Error message describing the issue",
  "details": {
    // Optional additional error details
  }
}
```

## API Endpoints

### User Queries

#### Get All User Queries

Retrieves a list of all user queries.

- **URL**: `/user-queries/`
- **Method**: `GET`
- **Response**:
  ```json
  [
    {
      "id": 1,
      "query": "How does the internet work?",
      "created_at": "2023-12-06T23:30:55.776380",
      "task_id": "uuid-string",
      "status": "PENDING",
      "progress": 0.0
    },
    // More queries...
  ]
  ```

#### Create User Query

Creates a new user query and associated task.

- **URL**: `/user-queries/`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "query": "What is the status of my order?"
  }
  ```
- **Response**:
  ```json
  {
    "id": 1,
    "query": "What is the status of my order?",
    "created_at": "2023-12-06T23:30:55.776380",
    "task_id": "uuid-string",
    "status": "PENDING",
    "progress": 0.0
  }
  ```

#### Delete All User Queries

Deletes all user queries and associated tasks.

- **URL**: `/user-queries/`
- **Method**: `DELETE`
- **Response**:
  ```json
  {
    "message": "All user queries deleted successfully"
  }
  ```

#### Get User Query by ID

Retrieves a specific user query by its ID.

- **URL**: `/user-queries/{query_id}`
- **Method**: `GET`
- **URL Parameters**:
  - `query_id` - Integer ID of the query
- **Response**:
  ```json
  {
    "id": 1,
    "query": "How does the internet work?",
    "created_at": "2023-12-06T23:30:55.776380",
    "task_id": "uuid-string",
    "status": "PENDING",
    "progress": 0.0
  }
  ```

#### Get User Queries by Task ID

Retrieves all user queries associated with a specific task.

- **URL**: `/user-queries/tasks/{task_id}`
- **Method**: `GET`
- **URL Parameters**:
  - `task_id` - UUID of the task
- **Response**:
  ```json
  [
    {
      "id": 1,
      "query": "How does the internet work?",
      "created_at": "2023-12-06T23:30:55.776380",
      "task_id": "uuid-string",
      "status": "PENDING",
      "progress": 0.0
    },
    // More queries...
  ]
  ```

### Tasks

#### Get Task by ID

Retrieves a specific task by its ID.

- **URL**: `/tasks/{task_id}`
- **Method**: `GET`
- **URL Parameters**:
  - `task_id` - UUID of the task
- **Response**: Complete task object with all properties

#### Delete All Tasks

Deletes all tasks in the system.

- **URL**: `/tasks/`
- **Method**: `DELETE`
- **Response**:
  ```json
  {
    "message": "All tasks deleted successfully"
  }
  ```

#### Delete a Specific Task

Deletes a task by ID.

- **URL**: `/tasks/{task_id}`
- **Method**: `DELETE`
- **URL Parameters**:
  - `task_id` - UUID of the task
- **Response**:
  ```json
  {
    "message": "Task deleted successfully"
  }
  ```

### Task Analysis Pipeline

The following endpoints represent the task analysis pipeline stages. Each stage advances the task through the workflow.

#### Context Gathering

Gathers and processes context information for a task.

- **URL**: `/tasks/{task_id}/context-questions`
- **Method**: `POST`
- **URL Parameters**:
  - `task_id` - UUID of the task
- **Query Parameters**:
  - `force` - Boolean to force context gathering even if context is sufficient (default: false)
- **Request Body**: (Optional)
  ```json
  {
    "answers": [
      {
        "question": "What is the main purpose of your project?",
        "answer": "To build a web application for task management"
      },
      // More answers...
    ]
  }
  ```
- **Response**:
  ```json
  {
    "is_sufficient": false,
    "follow_up_questions": [
      "What specific features do you need in your task management app?",
      "Who are the intended users of this application?"
    ]
  }
  ```

#### Scope Formulation - Get Questions for Group

Gets formulation questions for a specific group.

- **URL**: `/tasks/{task_id}/formulate/{group}`
- **Method**: `GET`
- **URL Parameters**:
  - `task_id` - UUID of the task
  - `group` - Name of the formulation group (e.g., "what", "where", "who", "when", "why", "how")
- **Response**: Array of formulation questions for the specified group

#### Scope Formulation - Submit Answers

Submits formulation answers for a specific group.

- **URL**: `/tasks/{task_id}/formulate/{group}`
- **Method**: `POST`
- **URL Parameters**:
  - `task_id` - UUID of the task
  - `group` - Name of the formulation group
- **Request Body**:
  ```json
  {
    "answers": [
      {
        "question": "What is the main goal of this task?",
        "answer": "To develop a user authentication system"
      },
      // More answers...
    ]
  }
  ```
- **Response**:
  ```json
  {
    "message": "Formulation answers submitted successfully"
  }
  ```

#### Get Draft Scope

Retrieves the draft scope for a task.

- **URL**: `/tasks/{task_id}/draft-scope`
- **Method**: `GET`
- **URL Parameters**:
  - `task_id` - UUID of the task
- **Response**:
  ```json
  {
    "scope": "This task involves developing a user authentication system with login, registration, and password reset functionality.",
    "validation_criteria": [
      "The scope clearly defines the objective",
      "The scope includes necessary functionality",
      "The scope has appropriate boundaries"
    ]
  }
  ```

#### Validate Scope

Validates the scope for a task, providing feedback if not approved.

- **URL**: `/tasks/{task_id}/validate-scope`
- **Method**: `POST`
- **URL Parameters**:
  - `task_id` - UUID of the task
- **Request Body**:
  ```json
  {
    "isApproved": false,
    "feedback": "The scope needs to include two-factor authentication"
  }
  ```
- **Response**:
  ```json
  {
    "updatedScope": "This task involves developing a user authentication system with login, registration, password reset, and two-factor authentication functionality.",
    "changes": [
      "Added two-factor authentication to the scope"
    ]
  }
  ```

#### Generate Ideal Final Result (IFR)

Generates an ideal final result for a task.

- **URL**: `/tasks/{task_id}/ifr`
- **Method**: `POST`
- **URL Parameters**:
  - `task_id` - UUID of the task
- **Response**: Complete IFR object with all properties

### Utilities

#### Clear Task Scope

Clears the scope of a specific task.

- **URL**: `/utils/tasks/{task_id}/clear-scope`
- **Method**: `DELETE`
- **URL Parameters**:
  - `task_id` - UUID of the task
- **Response**:
  ```json
  {
    "message": "Task scope has been successfully cleared"
  }
  ```

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid input parameters |
| 404 | Not Found - Resource not found |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error - Server-side issue |

## Rate Limiting

Currently, no rate limiting is implemented. Future versions will include rate limiting to prevent API abuse.

## Pagination

Currently, list endpoints return all results. Future versions will implement pagination for large result sets.

## API Versioning

The API does not currently implement versioning. Future updates will include version prefixes in the URL path.

## Examples

### Example: Creating a new task and processing it through the pipeline

1. Create a new user query:
   ```bash
   curl -X POST http://localhost:8000/user-queries/ \
     -H "Content-Type: application/json" \
     -d '{"query": "How does the internet work?"}'
   ```

2. Gather context:
TODO: need to update this section

3. Continue through each stage of the pipeline in sequence:
   - `/tasks/{task_id}/formulate`
   - `/tasks/{task_id}/analyze`
   - `/tasks/{task_id}/typify`
   - `/tasks/{task_id}/clarify`
   - `/tasks/{task_id}/approaches`
   - `/tasks/{task_id}/decompose` 