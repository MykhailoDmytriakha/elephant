# Elephant Project - Directory Structure

This document outlines the complete directory structure of the Elephant Project, explaining the purpose and contents of each directory and key files.

## Overview

```
elephant/
├── backend/                  # Backend FastAPI application
│   ├── src/                  # Source code
│   │   ├── api/              # API endpoint definitions
│   │   ├── db/               # Database models and access
│   │   ├── models/           # Data models and schemas
│   │   ├── services/         # Business logic services
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
│   │   ├── services/         # API service calls
│   │   ├── utils/            # Utility functions
│   │   ├── App.js            # Main component
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
│   └── USER_GUIDE.md         # End-user guide
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
  - **`/backend/src/db`**: Database models, migrations, and access layer
  - **`/backend/src/models`**: Pydantic models for request/response validation
  - **`/backend/src/services`**: Business logic services for task processing
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
  - **`/frontend/src/services`**: API service calls to backend
  - **`/frontend/src/utils`**: Utility functions and helpers
  - **`/frontend/src/App.js`**: Main component with routing
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
- **`/docs/USER_GUIDE.md`**: End-user guide

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
4. Database schema changes affect `/backend/src/db` and should be reflected in `/data/design/tables.txt`

## Related Documentation

- [System Architecture](ARCHITECTURE.md)
- [API Documentation](API.md)
- [User Guide](USER_GUIDE.md)
- [Main README](../README.md) 