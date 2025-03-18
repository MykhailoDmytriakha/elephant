# Elephant Project - Directory Structure

This document outlines the complete directory structure of the Elephant Project, explaining the purpose and contents of each directory and key files.

## Overview

```
elephant/
├── backend/                  # Backend FastAPI application
│   ├── src/                  # Source code
│   │   ├── api/              # API endpoint definitions
│   │   │   ├── routes/       # API route handlers
│   │   │   └── deps.py       # Dependency injection
│   │   ├── model/            # Data models and schemas
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic services
│   │   ├── ai_agents/        # AI agent implementations
│   │   ├── core/             # Core functionality
│   │   └── main.py           # Application entry point
│   ├── tests/                # Test files
│   ├── .env                  # Environment variables
│   ├── .env_example          # Example environment variables
│   ├── console.py            # Debug console
│   └── requirements.txt      # Python dependencies
│
├── frontend/                 # React frontend application
│   ├── src/                  # Source code
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── context/          # React context providers
│   │   ├── utils/            # Utility functions
│   │   ├── constants/        # Constant values
│   │   ├── App.jsx           # Main component
│   │   └── index.js          # Entry point
│   ├── public/               # Static assets
│   ├── package.json          # Node dependencies
│   └── tailwind.config.js    # Tailwind CSS configuration
│
├── data/                     # Data models and examples
│   ├── design/               # Design specifications
│   │   ├── 00_task_metadata.md   # Task metadata specs
│   │   ├── 01_task_creation.md   # Task creation process
│   │   ├── 02_task_scope.md      # Task scope definition
│   │   ├── 03_task_IFR.md        # Ideal Final Result specs
│   │   └── README.md             # Design directory docs
│   ├── example.json          # Example task structure
│   ├── flow.png              # Workflow diagram
│   ├── tasks.db              # SQLite database
│   └── README.md             # Data directory docs
│
├── docs/                     # Documentation
│   ├── API.md                # API reference
│   ├── ARCHITECTURE.md       # System architecture
│   ├── PROJECT_STRUCTURE.md  # This file
│   ├── STATE_TRANSITIONS.md  # State transition rules
│   ├── USER_GUIDE.md         # End-user guide
│   ├── task-mermaid-diagram.md # Task flow diagram
│   └── main-page-mermaid-diagram.md # Main page flow diagram
│
├── .vscode/                  # VSCode settings
├── .idea/                    # IntelliJ IDEA settings
├── .git/                     # Git repository
├── .gitignore                # Git ignore rules
├── README.md                 # Project overview
├── TODO.md                   # Development tasks
├── backend.code-workspace    # VSCode workspace for backend
└── frontend.code-workspace   # VSCode workspace for frontend
```

## Key Directories

### Backend (`/backend`)

The backend directory contains the FastAPI application that provides the REST API for the Elephant project.

- **`/backend/src`**: Main source code
  - **`/backend/src/api`**: API route definitions and endpoint handlers
    - **`/backend/src/api/routes`**: API route handlers for different resources
    - **`/backend/src/api/deps.py`**: Dependency injection for FastAPI
  - **`/backend/src/model`**: Data models for tasks, context, scope, and IFR
  - **`/backend/src/schemas`**: Pydantic models for request/response validation
  - **`/backend/src/services`**: Business logic services for task processing
    - **`/backend/src/services/database_service.py`**: Database operations
    - **`/backend/src/services/openai_service.py`**: OpenAI API integration
    - **`/backend/src/services/problem_analyzer.py`**: Task analysis logic
  - **`/backend/src/ai_agents`**: AI agent implementations for task processing
  - **`/backend/src/core`**: Core functionality and configurations
  - **`/backend/src/main.py`**: Application entry point and server configuration

- **`/backend/tests`**: Test files for the backend application
- **`/backend/requirements.txt`**: Python dependencies
- **`/backend/.env`**: Configuration variables for the application
- **`/backend/console.py`**: Command-line interface for debugging

### Frontend (`/frontend`)

The frontend directory contains the React application that provides the user interface.

- **`/frontend/src`**: Main source code
  - **`/frontend/src/components`**: Reusable UI components
  - **`/frontend/src/pages`**: Page-level components (routes)
    - **`/frontend/src/pages/MainPage.jsx`**: Main dashboard
    - **`/frontend/src/pages/TaskDetailsPage.jsx`**: Task details view
  - **`/frontend/src/hooks`**: Custom React hooks
    - **`/frontend/src/hooks/useTaskDetails.js`**: Task details logic
  - **`/frontend/src/context`**: React context providers
  - **`/frontend/src/utils`**: Utility functions and helpers
  - **`/frontend/src/constants`**: Constant values including task states
  - **`/frontend/src/App.jsx`**: Main component with routing
  - **`/frontend/src/index.js`**: Application entry point

- **`/frontend/public`**: Static assets and HTML template
- **`/frontend/package.json`**: Node.js dependencies
- **`/frontend/tailwind.config.js`**: Tailwind CSS configuration

### Data (`/data`)

The data directory contains data models, design specifications, and example data for the system.

- **`/data/design`**: Design specifications and workflow definitions
  - **`/data/design/00_task_metadata.md`**: Task metadata structure
  - **`/data/design/01_task_creation.md`**: Task creation process
  - **`/data/design/02_task_scope.md`**: Task scope definition using 5W+H
  - **`/data/design/03_task_IFR.md`**: Ideal Final Result methodology
  - **`/data/design/README.md`**: Documentation for design files

- **`/data/example.json`**: Example task data structure
- **`/data/flow.png`**: Task flow diagram
- **`/data/tasks.db`**: SQLite database file
- **`/data/README.md`**: Documentation for data directory

### Documentation (`/docs`)

The docs directory contains project documentation for developers and users.

- **`/docs/API.md`**: API reference documentation
- **`/docs/ARCHITECTURE.md`**: System architecture documentation
- **`/docs/PROJECT_STRUCTURE.md`**: Directory structure documentation (this file)
- **`/docs/STATE_TRANSITIONS.md`**: State transition rules documentation
- **`/docs/USER_GUIDE.md`**: End-user guide
- **`/docs/task-mermaid-diagram.md`**: Mermaid diagram for task processing flow
- **`/docs/main-page-mermaid-diagram.md`**: Mermaid diagram for main page flow

## Root Files

- **`README.md`**: Project overview and getting started guide
- **`TODO.md`**: Development tasks and progress tracking
- **`.gitignore`**: Git ignore rules
- **`backend.code-workspace`**: VSCode workspace configuration for backend
- **`frontend.code-workspace`**: VSCode workspace configuration for frontend

## Development Workflow

1. Frontend development is primarily done in the `/frontend/src` directory
2. Backend development is primarily done in the `/backend/src` directory
3. Design changes should be documented in `/data/design`
4. Database schema changes affect model definitions and should be reflected in appropriate documentation

## Related Documentation

- [System Architecture](ARCHITECTURE.md)
- [API Documentation](API.md)
- [User Guide](USER_GUIDE.md)
- [State Transitions](STATE_TRANSITIONS.md)
- [Main README](../README.md) 