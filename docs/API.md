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
  {
    "status": "success",
    "data": {
      "queries": [
        {
          "id": "uuid-string",
          "query": "How does the internet work?",
          "created_at": "2023-12-06T23:30:55.776380",
          "task_id": "uuid-string"
        },
        // Additional queries
      ]
    }
  }
  ```

#### Create a New User Query

Creates a new query and initializes the associated task.

- **URL**: `/user-queries/`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "query": "How does the internet work?"
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "data": {
      "query_id": "uuid-string",
      "task_id": "uuid-string",
      "query": "How does the internet work?"
    }
  }
  ```

#### Get a Specific User Query

Retrieves details of a specific query by ID.

- **URL**: `/user-queries/{query_id}`
- **Method**: `GET`
- **URL Parameters**:
  - `query_id` - UUID of the query
- **Response**:
  ```json
  {
    "status": "success",
    "data": {
      "id": "uuid-string",
      "query": "How does the internet work?",
      "created_at": "2023-12-06T23:30:55.776380",
      "task_id": "uuid-string"
    }
  }
  ```

#### Delete All User Queries

Deletes all user queries and associated tasks.

- **URL**: `/user-queries/`
- **Method**: `DELETE`
- **Response**:
  ```json
  {
    "status": "success",
    "data": {
      "message": "All user queries deleted successfully"
    }
  }
  ```

### Tasks

#### Delete All Tasks

Deletes all tasks in the system.

- **URL**: `/tasks/`
- **Method**: `DELETE`
- **Response**:
  ```json
  {
    "status": "success",
    "data": {
      "message": "All tasks deleted successfully"
    }
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
    "status": "success",
    "data": {
      "message": "Task deleted successfully"
    }
  }
  ```

### Task Analysis Pipeline

The following endpoints represent the task analysis pipeline stages. Each stage advances the task through the workflow.

#### Context Gathering

Gathers and processes context information for a task.

- **URL**: `/tasks/{task_id}/context`
- **Method**: `POST`
- **URL Parameters**:
  - `task_id` - UUID of the task
- **Request Body**:
  ```json
  {
    "context": "The user wants general information about how the internet works, along with interesting facts, schemas, and illustrations."
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "data": {
      "task_id": "uuid-string",
      "context": "The user wants general information...",
      "is_context_sufficient": true
    }
  }
  ```

#### Task Formulation

Formulates a clear problem statement based on the gathered context.

- **URL**: `/tasks/{task_id}/formulate`
- **Method**: `POST`
- **URL Parameters**:
  - `task_id` - UUID of the task
- **Response**:
  ```json
  {
    "status": "success",
    "data": {
      "task_id": "uuid-string",
      "task": "Provide a comprehensive overview of how the internet works, including general information, interesting facts, schemas, and illustrations."
    }
  }
  ```

#### Task Analysis

Analyzes the task to understand its requirements.

- **URL**: `/tasks/{task_id}/analyze`
- **Method**: `POST`
- **URL Parameters**:
  - `task_id` - UUID of the task
- **Response**:
  ```json
  {
    "status": "success",
    "data": {
      "task_id": "uuid-string",
      "analysis": {
        "ideal_final_result": "A comprehensive overview of how the internet works...",
        "parameters": [
          "General knowledge about the internet's functioning",
          "Interesting facts about the internet",
          // Additional parameters
        ]
      }
    }
  }
  ```

#### Task Typification

Categorizes the problem by type and complexity.

- **URL**: `/tasks/{task_id}/typify`
- **Method**: `POST`
- **URL Parameters**:
  - `task_id` - UUID of the task
- **Response**:
  ```json
  {
    "status": "success",
    "data": {
      "task_id": "uuid-string",
      "level": "LEVEL_2 (complex task: requires adaptation of known solutions)",
      "complexity": 2,
      "eta_to_complete": "1 week"
    }
  }
  ```

#### Task Clarification

Requests additional clarification for the task if needed.

- **URL**: `/tasks/{task_id}/clarify`
- **Method**: `POST`
- **URL Parameters**:
  - `task_id` - UUID of the task
- **Request Body**:
  ```json
  {
    "query": "What specific aspects of how the internet works are you interested in?",
    "answer": "general and some interesting facts, schemas and illustration"
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "data": {
      "task_id": "uuid-string",
      "user_interaction": [
        {
          "query": "What specific aspects of how the internet works are you interested in?",
          "answer": "general and some interesting facts, schemas and illustration"
        }
      ]
    }
  }
  ```

#### Task Approaches

Generates possible approaches to solve the problem.

- **URL**: `/tasks/{task_id}/approaches`
- **Method**: `POST`
- **URL Parameters**:
  - `task_id` - UUID of the task
- **Response**:
  ```json
  {
    "status": "success",
    "data": {
      "task_id": "uuid-string",
      "approaches": [
        "Research-based approach: Gather information from credible sources...",
        "Visual-first approach: Start with creating schemas and diagrams...",
        // Additional approaches
      ]
    }
  }
  ```

#### Task Decomposition

Breaks down the task into smaller, manageable subtasks.

- **URL**: `/tasks/{task_id}/decompose`
- **Method**: `POST`
- **URL Parameters**:
  - `task_id` - UUID of the task
- **Response**:
  ```json
  {
    "status": "success",
    "data": {
      "task_id": "uuid-string",
      "subtasks": [
        {
          "id": "uuid-string",
          "task": "Research and outline the basic structure of the internet",
          "short_description": "Internet structure research",
          "sub_level": 1,
          "order": 1
        },
        // Additional subtasks
      ]
    }
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
   ```bash
   curl -X POST http://localhost:8000/tasks/{task_id}/context \
     -H "Content-Type: application/json" \
     -d '{"context": "The user wants general information about how the internet works."}'
   ```

3. Continue through each stage of the pipeline in sequence:
   - `/tasks/{task_id}/formulate`
   - `/tasks/{task_id}/analyze`
   - `/tasks/{task_id}/typify`
   - `/tasks/{task_id}/clarify`
   - `/tasks/{task_id}/approaches`
   - `/tasks/{task_id}/decompose` 