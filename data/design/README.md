# Elephant Project - Design Documentation

## Overview
This directory contains the design specifications and workflow definitions for the Elephant Project's task management system. These documents define the structure, states, and processes used to manage and analyze tasks within the application.

## File Structure
The design documents are provided in both Markdown (`.md`) and JSON (`.json`) formats:
- Markdown files are human-readable documentation
- JSON files contain the structured data used by the application

## Design Components

### 1. Task Metadata (`00_task_metadata.md` / `00_task_metadata.json`)
Defines the core metadata structure for tasks:

- **Basic Information**:
  - ID: Unique task identifier
  - Sub Level: Hierarchy depth level
  - Created/Updated timestamps
  
- **Task State Flow**:
  - Defines the progression of a task from creation through completion
  - States range from 0 (Empty) to 10+ (Decomposition and beyond)
  
- **Complexity Assessment**:
  - Level scale from 1-5
  - Definitions for each complexity level
  
- **Time Estimation**:
  - ETA calculation methodology
  - Reasoning for time estimates
  
- **Task Relationships**:
  - Parent-child task connections
  - Subtask structuring
  - Order of execution

### 2. Task Creation Process (`01_task_creation.md` / `01_task_creation.json`)
Defines the workflow for creating a new task:

- **Process Stages**:
  1. Gather Context: Collecting initial information
  2. Refinement: Shaping the task definition
  3. Task Feedback: Validation and approval
  
- **Flow Controls**:
  - Decision points and routing rules
  - Conditions for returning to previous stages
  
- **Examples**:
  - Initial task definition
  - Context gathering examples
  - Task refinement samples

### 3. Task Scope Definition (`02_task_scope.md` / `02_task_scope.json`)
Implements the 5W+H framework (What, Why, Who, Where, When, How) for comprehensive task scoping:

- **Process Stages**:
  1. Analyze Requirements (What, Why, Who)
  2. Define Boundaries (Where, When)
  3. Resource Assessment (How)
  4. Scope Validation
  
- **Flow Controls**:
  - Rules for scope refinement
  - Validation criteria
  
- **Examples**:
  - Sample scope definitions
  - Validation question sets

### 4. Ideal Final Result (`03_task_IFR.md` / `03_task_IFR.json`)
Documents the Ideal Final Result methodology used for goal setting:

- **Definition**: The best possible outcome for the task
- **Characteristics**: Clear, concise, measurable
- **Function**: Guides the task execution process
- **Examples**: Sample IFR statements for different task types

### 5. Database Schema (`tables.txt`)
Contains the technical SQL schema definitions for the database:

- **Task Metadata Table**: Core storage structure for task metadata
- **Tasks Table**: Detailed task information storage
- **Relationships**: Foreign key definitions and constraints

## Implementation Guidelines

### Using Design Documents
These design documents serve as the blueprint for implementation in both the frontend and backend:

1. **Backend Implementation**:
   - The JSON schemas define the data structures used in the FastAPI endpoints
   - The workflow definitions inform the processing pipeline logic

2. **Frontend Implementation**:
   - UI components should reflect the task state progression
   - Form structures should align with the defined metadata fields
   - Workflows should follow the defined process stages

### Extending the Design
When extending the application with new features:

1. First update the relevant design document(s)
2. Ensure consistency with existing design patterns
3. Update both the Markdown and JSON versions
4. Reference the updated design in implementation code

## Related Documents
- Main project README in the root directory
- Data directory README for overall data structure
- Backend API documentation for implementation details 