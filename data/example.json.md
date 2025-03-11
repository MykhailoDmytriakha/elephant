# Example.json Documentation

## Overview
The `example.json` file demonstrates the complete structure of a task in the Elephant system. It serves as a reference implementation for developers working with the task data model.

## File Structure
The file contains a fully populated task object with all relevant fields and nested structures:

```
{
    "id": "cb21f386-5312-4f1f-9214-27fc24a83702",
    "sub_level": 0,
    "created_at": "2024-12-06T23:30:55.776380",
    "updated_at": "2024-12-06T23:35:34.420021",
    "task": "Provide a comprehensive overview of how the internet works...",
    "short_description": "How does the internet work?",
    "state": "10. Decomposition",
    "is_context_sufficient": true,
    "context": "The individual is interested in general knowledge...",
    "level": "LEVEL_2 (complex task: requires adaptation of known solutions)",
    "complexity": 2,
    "eta_to_complete": "1 week",
    "contribution_to_parent_task": null,
    "scope": {
        "boundaries": {
            "includes": [...],
            "excludes": [...]
        },
        "constraints": [...],
        "dependencies": [...],
        "deliverables": [...]
    },
    "user_interaction": [...],
    "analysis": {
        "ideal_final_result": "...",
        "parameters": [...]
    }
}
```

## Field Descriptions

### Metadata Fields
- **id**: Unique UUID identifier for the task
- **sub_level**: Hierarchical depth level (0 = top level task)
- **created_at**: ISO timestamp of creation
- **updated_at**: ISO timestamp of last update
- **task**: The complete task description
- **short_description**: Brief summary of the task
- **state**: Current state in the task workflow (e.g., "10. Decomposition")
- **is_context_sufficient**: Boolean indicating if enough context exists
- **context**: Background information about the task
- **level**: Complexity level with description
- **complexity**: Numeric representation of complexity (1-5)
- **eta_to_complete**: Estimated time to completion
- **contribution_to_parent_task**: For subtasks, describes relationship to parent

### Scope Object
Defines the boundaries and requirements of the task:

- **boundaries**:
  - **includes**: Array of items within scope
  - **excludes**: Array of items explicitly out of scope
- **constraints**: Array of limitations or conditions
- **dependencies**: Array of required resources or prerequisites
- **deliverables**: Array of expected outputs

### User Interaction
Array of interaction objects capturing the conversation history:
```
"user_interaction": [
    {
        "query": "What specific aspects of how the internet works are you interested in?",
        "answer": "general and some intresting facts, schemas and illustration"
    }
]
```

### Analysis Object
Contains the detailed problem analysis:

- **ideal_final_result**: The optimal outcome statement
- **parameters**: Array of specific details to guide implementation

## Usage in Development
- Backend developers can reference this file when implementing data models and API endpoints
- Frontend developers can use it to understand the data structure to display in the UI
- Testing can validate actual outputs against this example structure

## Related Files
- `00_task_metadata.md` - For detailed metadata field documentation
- `02_task_scope.md` - For scope definition methodology
- `03_task_IFR.md` - For ideal final result implementation details 