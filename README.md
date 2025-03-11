# Elephant Project

## Overview
The Elephant Project is an AI-assisted problem analysis and task management system. It helps users break down complex problems or tasks into structured, manageable pieces, leveraging AI for analysis and problem-solving steps.

## Project Structure
This project follows a classic client-server architecture:

- **Frontend**: React application with React Router for navigation
- **Backend**: FastAPI-based REST API service

For a detailed directory structure, see the [Project Structure Documentation](docs/PROJECT_STRUCTURE.md).

## User Flow

### 1. User Query Creation
- Users start on the main dashboard where they can see a list of existing queries
- They can create a new query by clicking the "New Query" button
- The query is sent to the backend API which creates a new task associated with the query

### 2. Task Analysis Process
The backend follows a structured problem-solving approach:

1. **Context Gathering**: Evaluates if there's enough information to understand the problem
2. **Task Formulation**: Formulates a clear problem statement
3. **Problem Analysis**: Analyzes the task to understand its requirements
4. **Task Typification**: Categorizes the problem
5. **Clarification**: May ask for clarifications if needed
6. **Approach Generation**: Suggests possible approaches to solve the problem
7. **Task Decomposition**: Breaks down the task into smaller, manageable subtasks

### 3. Task Details View
- Users can click on a task to view its details
- The page displays the analysis results including:
  - Problem statement
  - Analysis results
  - Problem type
  - Possible approaches
  - Task decomposition

### 4. Task Progress Tracking
- Tasks progress through different states
- Progress is tracked and displayed in the UI with status badges

## Technical Components

### Frontend
- React.js for the UI framework
- React Router for navigation
- Axios for API calls
- Tailwind CSS for styling

### Backend
- FastAPI for the REST API endpoints
- Structured task processing pipeline
- Database service for data persistence

## Getting Started

### Backend Setup
1. Navigate to the `backend` directory
2. Create a virtual environment: `python -m venv .venv`
3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Unix/MacOS: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env_example` to `.env` and configure environment variables
6. Run the server: `python -m src.main`

### Frontend Setup
1. Navigate to the `frontend` directory
2. Install dependencies: `npm install`
3. Start the development server: `npm start`
4. The application should be available at `http://localhost:3000`

## API Endpoints

For a complete API reference, please see the [API Documentation](docs/API.md).

Key endpoints include:

### User Queries
- `GET /user-queries/` - Get all user queries
- `POST /user-queries/` - Create a new user query
- `GET /user-queries/{query_id}` - Get a specific user query
- `DELETE /user-queries/` - Delete all user queries

### Tasks
- `DELETE /tasks/` - Delete all tasks
- `DELETE /tasks/{task_id}` - Delete a specific task
- Various endpoints for the task analysis pipeline:
  - `/tasks/{task_id}/context`
  - `/tasks/{task_id}/formulate`
  - `/tasks/{task_id}/analyze`
  - `/tasks/{task_id}/typify`
  - `/tasks/{task_id}/clarify`
  - `/tasks/{task_id}/approaches`
  - `/tasks/{task_id}/decompose`

## Documentation

The project includes comprehensive documentation in the [docs](docs/README.md) directory:

- [User Guide](docs/USER_GUIDE.md) - Guide for end users on how to use the application
- [API Documentation](docs/API.md) - Complete API reference for developers
- [Architecture](docs/ARCHITECTURE.md) - Technical architecture and system design
- [Project Structure](docs/PROJECT_STRUCTURE.md) - Directory structure and file organization
- [Data Structure](data/README.md) - Documentation of the data models and formats
- [Design Documentation](data/design/README.md) - Design methodology and workflow definitions

## Development

### Task Management
Development tasks and progress are tracked in the [TODO.md](TODO.md) file.

### Project Structure
- `frontend/` - React frontend application
- `backend/` - FastAPI backend service
- `data/` - Data models, examples, and design documents
- `docs/` - Documentation files

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License
[MIT License](LICENSE) 