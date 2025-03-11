# Elephant Project - Data Documentation

## Overview
This directory contains the data structures, design documents, and database files used in the Elephant Project, which is an AI-assisted problem analysis and task management system.

## Directory Structure

### Database
- `tasks.db`: SQLite database containing task and query information
  - Contains tables for task metadata, task details, and user queries
  - Used by the backend to persist user queries and task data

### Design Documents
The `design/` directory contains specification documents that define the structure and workflow of the system:

- `00_task_metadata.md` / `00_task_metadata.json`: Defines task metadata structure including:
  - Basic task information fields
  - Task state flow (from Empty to Decomposition)
  - Complexity assessment levels (1-5)
  - Time estimation
  - Task relationships (parent-child)

- `01_task_creation.md` / `01_task_creation.json`: Defines the task creation process:
  - Context gathering process
  - Refinement
  - Task feedback workflow
  - Flow control rules

- `02_task_scope.md` / `02_task_scope.json`: Defines task scope using the 5W+H framework:
  - What, Why, Who (Analyze Requirements)
  - Where, When (Define Boundaries)
  - How (Resource Assessment)
  - Validation criteria

- `03_task_IFR.md` / `03_task_IFR.json`: Defines the Ideal Final Result methodology
  - Used for goal setting and task planning

- `tables.txt`: Contains database schema definitions
  - Defines the structure of task_metadata and tasks tables
  - Details primary keys, foreign keys, and relationships

### Example Data
- `example.json`: Sample task data showing the complete structure of a task
  - Includes task metadata, scope, user interaction, and analysis fields
  - Serves as a reference for developers working with the task data structure

### Flow Diagrams
- `flow.png`: Visual representation of the task processing workflow
  - Illustrates the process from task creation to completion
  - Shows state transitions and decision points

## Database Schema

### Task Metadata Table
```sql
CREATE TABLE task_metadata (
    id UUID PRIMARY KEY UNIQUE,
    parent_task_metadata_id UUID NULL,
    order INT NOT NULL,
    sub_level INT NOT NULL,
    status VARCHAR(50),
    due_date DATE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (parent_task_metadata_id) REFERENCES task_metadata(id)
);
```

### Tasks Table
```sql
CREATE TABLE tasks (
    task_metadata_id UUID PRIMARY KEY UNIQUE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    user_input TEXT,
    scope TEXT,
    ideal_final_result TEXT,
    FOREIGN KEY (task_metadata_id) REFERENCES task_metadata(id)
);
```

## Task State Flow
| State Number | State Name |
|--------------|------------|
| 0 | Empty |
| 1 | Gathering Context |
| 2 | Refinement |
| 3 | Task Feedback |
| 4 | Final Task is defined |
| 5 | Initial Scope |
| 6 | Scope Boundaries |
| 7 | Resource Requirements |
| 8 | Scope Validation |
| 9 | Final Scope is defined |
| 10 | Decomposition |

## Data Usage
The data contained in this directory is used by:
1. The backend API to process and manage tasks
2. The frontend application to display task information
3. The AI components for task analysis and decomposition

## Related Files
For implementation details, please refer to:
- Backend API code in the `/backend/src` directory
- Frontend components in the `/frontend/src` directory 