# Elephant Project

## Project Purpose
The Elephant Project is an advanced AI-powered system designed to understand, decompose, and fulfill user requests. With the rapid evolution of AI capabilities, we're developing a system that can handle both intellectual and (eventually) physical tasks through effective understanding, planning, and execution.

The core innovation of Elephant is its ability to break down complex user queries into manageable components, thoroughly understanding requirements through intelligent conversation before executing tasks.

## Overview
Elephant follows a methodical problem-solving approach that begins with understanding the user's needs through context gathering, followed by task formulation, analysis, and decomposition into executable steps. 

The system intelligently interacts with users to gather necessary information, leveraging AI to determine when it has sufficient context to proceed with solving tasks effectively.

## Project Structure
This project follows a classic client-server architecture:

- **Frontend**: React application with React Router for navigation
- **Backend**: FastAPI-based REST API service with AI integration

For a detailed directory structure, see the [Project Structure Documentation](docs/PROJECT_STRUCTURE.md).

## Task Processing Pipeline

### 1. Context Gathering Phase (Critical First Phase)
The context gathering phase is the foundation of the Elephant system and a critical first step in successfully processing any user request.

#### Purpose
Before the AI can effectively help users, it must thoroughly understand:
- The project or domain the user is working on
- The specific problem or requirement that needs addressing
- Key constraints, requirements, and user preferences
- Relevant background information that impacts solution design

#### How Context Gathering Works
1. **Initial Assessment**: When a user creates a query, the system immediately evaluates whether the provided information is sufficient using specific criteria:
   - Project Information (purpose, users, technologies, current state)
   - Task-Specific Information (problems, desired outcomes, constraints)
   - Context Depth (level of detail provided)

2. **Interactive Dialog**: If context is insufficient (which is nearly always the case initially), the system:
   - Shows a context gathering interface to the user
   - Asks focused, targeted questions to gather the most critical missing information
   - Progressively builds understanding through multiple turns of conversation

3. **Context Evaluation**: After each user response, the system:
   - Re-evaluates if context is now sufficient
   - Updates its understanding of the user's requirements
   - Formulates increasingly specific follow-up questions as needed

4. **Transition to Task Formation**: Once sufficient context is gathered, the system:
   - Summarizes the collected information
   - Transitions to formulating a precise task definition
   - Proceeds to deeper analysis of the now well-understood problem

#### Key Challenges Addressed
- Preventing premature task execution with insufficient understanding
- Ensuring AI asks the right questions to gather critical information
- Providing a user-friendly conversation experience
- Balancing thoroughness with efficiency in information gathering

### 2. Task Formulation
Once sufficient context is gathered, the system formulates a clear problem statement that includes:
- Clear objectives
- Scope boundaries (what's included and excluded)
- Key requirements and constraints
- Expected deliverables

### 3. Problem Analysis
The system then analyzes the formulated task to understand:
- The nature of the problem
- Required approaches and methodologies
- Resources needed
- Potential challenges

### 4. Task Typification
The problem is categorized based on:
- Domain (e.g., software development, design, research)
- Complexity level
- Required expertise
- Time sensitivity

### 5. Clarification (If Needed)
Additional clarifications may be requested based on:
- Ambiguities discovered during analysis
- Conflicting requirements
- Areas requiring deeper understanding

### 6. Approach Generation
The system suggests possible approaches to solve the problem:
- Analytical tools and methods
- Practical implementation strategies
- Frameworks and technologies

### 7. Task Decomposition
Finally, the system breaks down the task into smaller, manageable subtasks:
- Hierarchical structure with dependencies
- Clear progression path
- Manageable work units

## User Flow

### 1. User Query Creation
- Users start on the main dashboard where they can see a list of existing queries
- They can create a new query by clicking the "New Query" button
- The query is sent to the backend API which creates a new task associated with the query

### 2. Task Details View
- Users can click on a task to view its details
- The page displays context gathering dialog if more information is needed
- Once context is gathered, the system displays analysis results including:
  - Problem statement
  - Analysis results
  - Problem type
  - Possible approaches
  - Task decomposition

### 3. Task Progress Tracking
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
- OpenAI integration for intelligent context gathering and analysis
- Database service for data persistence

## Getting Started

### Backend Setup
1. Navigate to the `backend` directory
2. Create a virtual environment: `python -m venv .venv`
3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Unix/MacOS: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env_example` to `.env` and configure environment variables (OpenAI API key and model)
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
- `GET /tasks/{task_id}` - Get a specific task
- `DELETE /tasks/` - Delete all tasks
- `DELETE /tasks/{task_id}` - Delete a specific task
- `POST /tasks/{task_id}/context-questions` - Update task context
- `GET /tasks/{task_id}/formulate/{group}` - Formulate a specific aspect of the task
- `POST /tasks/{task_id}/formulate/{group}` - Submit formulation answers
- `GET /tasks/{task_id}/draft-scope` - Get the draft scope for a task
- `POST /tasks/{task_id}/validate-scope` - Validate the task scope
- `POST /tasks/{task_id}/ifr` - Generate ideal final result

## Documentation

The project includes comprehensive documentation in the [docs](docs/README.md) directory:

- [Project Structure Documentation](docs/PROJECT_STRUCTURE.md)
- [State Transition Rules](docs/STATE_TRANSITIONS.md) - Understanding task state transitions and workflow
- [API Documentation](docs/API.md)
- [User Guide](docs/USER_GUIDE.md)

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

## Running Backend Tests

To run the backend tests, use the following script:

```bash
./scripts/backend/run_test.sh
```

This script sets the necessary environment variables and runs the tests using pytest. 