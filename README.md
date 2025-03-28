# Elephant Project 🐘

**An AI-powered system for understanding, decomposing, and managing complex user requests.**

## Project Purpose

The Elephant Project aims to leverage advanced AI capabilities to understand user needs deeply, break down complex requests (intellectual or physical tasks) into manageable components, and generate detailed plans suitable for automated execution by AI agents and robotic systems. By combining intelligent context gathering, structured problem formulation, and automated hierarchical planning, Elephant strives to be a powerful assistant for architecting and managing the future of automated work.

## Overview

Elephant employs a methodical problem-solving pipeline:

1.  **Context Gathering:** Intelligently interacts with the user to ensure a thorough understanding of the project, problem, constraints, and goals before proceeding.
2.  **Task Scope Formulation:** Defines clear boundaries and objectives using the 5W+H framework (What, Why, Who, Where, When, How).
3.  **Ideal Final Result (IFR) Generation:** Creates a precise definition of the perfect solution, including success criteria, outcomes, and metrics.
4.  **Requirements Definition:** Generates detailed technical requirements based on the IFR and scope.
5.  **Network Plan Generation:** Creates a structured plan with stages and checkpoints for execution.
6.  **Hierarchical Task Decomposition:** Breaks down the Network Plan into executable steps using a detailed hierarchy (**Stage -> Work -> ExecutableTask -> Subtask**) tailored for AI/robot consumption.
7.  *(Future)* **Execution Management:** Orchestrates or tracks the completion of decomposed tasks and subtasks.

The system adapts its interactions and responses based on the detected language of the user's input.

## Key Features

*   **AI-Powered Context Gathering:** Uses conversational AI to ensure sufficient understanding before acting.
*   **Structured Scope Definition:** Employs the 5W+H framework for precise task boundaries.
*   **Ideal Final Result (IFR):** Defines clear success criteria and measurable outcomes.
*   **Automated Requirements Generation:** Creates detailed technical requirements from the scope and IFR.
*   **Network Planning:** Generates a visual plan with stages, connections, and checkpoints.
*   **Hierarchical Decomposition:** Automatically breaks down stages into Work packages, ExecutableTasks, and atomic Subtasks with defined inputs, outputs, dependencies, and executor types (AI_AGENT, ROBOT, HUMAN).
*   **Web-Based Interface:** User-friendly React frontend for interaction and visualization (including network graph and task hierarchy).
*   **RESTful API:** FastAPI backend providing structured access to functionality.
*   **Task Persistence:** Uses SQLite to store query and task progress.

## Task Processing Pipeline

The Elephant system processes user requests through a structured pipeline:

### 1. Context Gathering Phase (Critical First Step)

This phase ensures the AI fully understands the user's needs before analysis begins.

*   **Initial Assessment:** Evaluates the initial query for sufficiency based on project info, task specifics, and context depth.
*   **Interactive Dialog:** If context is insufficient (usually the case initially), the system asks focused questions via the UI.
*   **Context Evaluation:** Re-evaluates sufficiency after each user response, refining its understanding and follow-up questions.
*   **Transition:** Once sufficient context is gathered, the system summarizes the information and moves to Scope Formulation.

### 2. Task Scope Formulation (5W+H)

Defines precise boundaries for the task.

*   **Iterative Questioning:** Asks specific questions for each dimension (What, Why, Who, Where, When, How), adapting to request complexity.
*   **Draft Generation:** Creates a draft scope statement based on user answers.
*   **Validation:** Presents the draft scope and validation criteria to the user for approval or feedback.

### 3. Ideal Final Result (IFR) Generation

Creates a definition of the perfect solution.

*   **IFR Statement:** A concise description of the optimal outcome.
*   **Success Criteria:** Measurable functional requirements (WHAT the system does).
*   **Expected Outcomes:** Benefits and results the user will receive.
*   **Quality Metrics:** Precise measurements with target values (HOW WELL the system performs).
*   **Validation Checklist:** Specific tests with pass/fail criteria.

### 4. Requirements Definition

Generates detailed technical specifications.

*   **Requirements:** Functional and non-functional requirements.
*   **Constraints:** Limitations on the implementation.
*   **Limitations:** Boundaries of the system's capabilities.
*   **Resources:** Required inputs.
*   **Tools:** Technologies to be used or integrated with.
*   **Definitions:** Glossary of key terms.

### 5. Network Plan Generation

Creates a high-level execution plan.

*   **Stages:** Major milestones or phases represented as nodes.
*   **Connections:** Dependencies between stages.
*   **Checkpoints:** Verifiable steps within each stage, including artifacts and validation criteria.

### 6. Hierarchical Task Decomposition

This stage breaks down the Network Plan into finer-grained, executable steps suitable for automated systems.

*   **Hierarchical Breakdown:** Decomposes the plan following the structure: **Stage -> Work -> ExecutableTask -> Subtask**. AI generates the details for each level, including dependencies, inputs, outputs, and validation.
*   **Executor Specification:** Subtasks specify the intended executor type (AI_AGENT, ROBOT, HUMAN).
*   *(Planned)* **Execution Management:** Future work involves orchestrating or tracking the completion of these detailed steps.

*(Further stages like Evaluation are planned)*

## Technical Architecture

Elephant uses a client-server architecture:

*   **Frontend:** React application (`/frontend`) using React Router, Axios, Tailwind CSS, and `@xyflow/react` for graph visualization.
*   **Backend:** FastAPI application (`/backend`) using Pydantic, OpenAI Agents SDK, and SQLite for data persistence.

## Project Structure

```
elephant/
├── backend/          # FastAPI Backend
├── frontend/         # React Frontend
├── scripts/          # Utility Scripts
├── .env              # Environment variables (backend)
└── README.md         # This file
```

## Getting Started

### Prerequisites

*   Node.js and npm (for Frontend)
*   Python 3.10+ and pip (for Backend)
*   An OpenAI API Key

### Backend Setup

1.  Navigate to the `backend` directory:
    ```bash
    cd backend
    ```
2.  Create and activate a virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Create a `.env` file from `.env_example` and add your `OPENAI_API_KEY`:
    ```bash
    cp .env_example .env
    # Edit .env and add your key
    ```
5.  Run the backend server:
    ```bash
    python -m src.main
    ```
    The API will be available at `http://localhost:8000`.

### Frontend Setup

1.  Navigate to the `frontend` directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Start the development server:
    ```bash
    npm start
    ```
    The application will be available at `http://localhost:3000`.

## Running Backend Tests

Navigate to the project root and run the test script:

```bash
./scripts/backend/run_test.sh
```

This script uses `pytest` and `coverage` to run tests located in `backend/tests/`. An HTML coverage report is generated in `htmlcov/`.

## API Endpoints

The backend exposes a RESTful API for managing queries and tasks. Key endpoints include:

*   `GET /user-queries/`: List all queries.
*   `POST /user-queries/`: Create a new query.
*   `GET /tasks/{task_id}`: Get task details.
*   `DELETE /tasks/{task_id}`: Delete a specific task.
*   `POST /tasks/{task_id}/context-questions`: Get context questions or submit answers (handles both GET-like and POST logic).
*   `GET /tasks/{task_id}/formulate/{group}`: Get scope questions for a specific 5W+H group.
*   `POST /tasks/{task_id}/formulate/{group}`: Submit scope answers for a group.
*   `GET /tasks/{task_id}/draft-scope`: Generate draft scope after all groups are answered.
*   `POST /tasks/{task_id}/validate-scope`: Approve or request changes to the draft scope.
*   `POST /tasks/{task_id}/ifr`: Generate Ideal Final Result.
*   `POST /tasks/{task_id}/requirements`: Generate Requirements.
*   `POST /tasks/{task_id}/network-plan`: Generate Network Plan (Stages and Connections).
*   `POST /tasks/{task_id}/stages/{stage_id}/generate-work`: Generate Work packages for a specific Stage.
*   `POST /tasks/{task_id}/stages/generate-work`: Generate Work packages for ALL Stages.
*   `POST /tasks/{task_id}/stages/{stage_id}/works/generate-tasks`: Generate ExecutableTasks for ALL Work packages in a Stage.
*   `POST /tasks/{task_id}/stages/{stage_id}/work/{work_id}/generate-tasks`: Generate ExecutableTasks for a specific Work package.
*   `POST /tasks/{task_id}/stages/{stage_id}/work/{work_id}/tasks/generate-subtasks`: Generate Subtasks for ALL ExecutableTasks in a Work package.
*   `POST /tasks/{task_id}/stages/{stage_id}/work/{work_id}/tasks/{executable_task_id}/generate-subtasks`: Generate Subtasks for a specific ExecutableTask.
*   *(Utility Endpoints under `/utils` for cleanup)*

## Development Status & Roadmap

The project is under active development. Current status and future goals:

**Implemented:**
*   Core pipeline stages 1-6 (Context Gathering to Hierarchical Decomposition).
*   AI-driven generation for context questions, scope questions, draft scope, IFR, requirements, network plan, work packages, executable tasks, and subtasks.
*   React frontend with visualization for network plan and task hierarchy.
*   FastAPI backend with SQLite persistence.

**Priorities & Future Work:**
*   **Execution Management:** Implementing orchestration/tracking for decomposed tasks/subtasks.
*   **Performance Optimization:** Addressing API call delays and database performance.
*   **State Management:** Improving validation and robustness of task state transitions.
*   **UI/UX Improvements:** Enhancing loading states, filtering, error handling, and user feedback for decomposition steps.
*   **Error Handling & Recovery:** More robust error handling in the backend agents.
*   **Testing:** Expanding test coverage, especially for decomposition logic.

## Contributing

Contributions are welcome! Please follow these steps:

1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some feature'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Open a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details (assuming an MIT license, please create this file if it doesn't exist).