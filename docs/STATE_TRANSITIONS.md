# Task State Transition Rules

This document explains the various states in the task workflow and the rules for transitioning between them.

## Overview of Task States

Tasks progress through a series of states from creation to completion. Each state has specific entry conditions and exit criteria.

| State | Description |
|-------|-------------|
| 1. New | Initial state when a task is first created |
| 2. Context Gathering | Collecting information about the task |
| 3. Context Gathered | Sufficient context has been collected |
| 3.5. Task Formation | Formulating a clear definition of the task |
| 4. Analysis | Analyzing the task to understand requirements |
| 5. Typify | Categorizing the task type |
| 6. Clarifying | Asking clarification questions |
| 7. Clarification Complete | All necessary clarifications obtained |
| 8. Approach Formation | Forming potential approaches to solve the task |
| 9. Method Selection | Selecting specific methods from available approaches |
| 10. Decomposition | Breaking down the task into smaller sub-tasks |
| 11. Method Application | Applying selected methods to solve the task |
| 12. Solution Development | Developing a concrete solution |
| 13. Evaluation | Evaluating the solution against requirements |
| 14. Integration | Integrating the solution with existing systems |
| 15. Output Generation | Generating final outputs |
| 16. Completed | Task has been completed successfully |

## State Transition Rules

### 1. New → 2. Context Gathering
- **Trigger**: When a user creates a new task
- **Requirements**: None
- **Action**: System begins gathering context by asking questions
- **Implementation**: Occurs automatically when a task is created

### 2. Context Gathering → 3. Context Gathered
- **Trigger**: When the system determines sufficient context has been provided
- **Requirements**: 
  - User has provided enough information to understand the task
  - Context sufficiency check passes (AI evaluation)
- **Action**: System transitions to Context Gathered state
- **Implementation**: `ProblemAnalyzer.clarify_context()` method sets `task.is_context_sufficient = True` and updates the state

### 3. Context Gathered → 3.5. Task Formation
- **Trigger**: When user initiates task formation
- **Requirements**: Context is deemed sufficient
- **Action**: System formulates a clear definition of the task
- **Implementation**: User clicks "Formulate Task" button, calling `formulate_task` endpoint

### 3.5. Task Formation → 4. Analysis
- **Trigger**: When task formulation is complete
- **Requirements**: Task has been properly defined
- **Action**: System begins analyzing the task
- **Implementation**: Task formulation completion automatically triggers analysis

### 4. Analysis → 5. Typify
- **Trigger**: When analysis is complete
- **Requirements**: Task has been analyzed to understand requirements
- **Action**: System categorizes the task type
- **Implementation**: Analysis completion automatically triggers typification or user clicks "Typify" button

### 5. Typify → 6. Clarifying
- **Trigger**: When typification is complete
- **Requirements**: Task has been categorized
- **Action**: System asks clarification questions specific to the task type
- **Implementation**: Typification completion automatically triggers clarification or user clicks "Clarify" button

### 6. Clarifying → 7. Clarification Complete
- **Trigger**: When all necessary clarifications have been obtained
- **Requirements**: User has answered clarification questions
- **Action**: System marks clarification as complete
- **Implementation**: After user answers final clarification question, system updates state

### 7. Clarification Complete → 8. Approach Formation
- **Trigger**: When clarification is complete
- **Requirements**: All necessary clarifications obtained
- **Action**: System begins forming approaches to solve the task
- **Implementation**: Clarification completion automatically triggers approach formation

### 8. Approach Formation → 9. Method Selection
- **Trigger**: When approaches have been formed
- **Requirements**: System has generated potential approaches
- **Action**: User selects specific methods from available approaches
- **Implementation**: Approach formation completion allows user to select methods

### 9. Method Selection → 10. Decomposition
- **Trigger**: When methods have been selected
- **Requirements**: User has selected methods to use
- **Action**: System decomposes the task into smaller sub-tasks
- **Implementation**: User submits selected methods, triggering decomposition

### 10. Decomposition → 11. Method Application
- **Trigger**: When task decomposition is complete
- **Requirements**: Task has been broken down into manageable sub-tasks
- **Action**: System begins applying selected methods to sub-tasks
- **Implementation**: Decomposition completion automatically triggers method application

### 11. Method Application → 12. Solution Development
- **Trigger**: When methods have been applied
- **Requirements**: Selected methods have been applied to sub-tasks
- **Action**: System begins developing a concrete solution
- **Implementation**: Method application completion automatically triggers solution development

### 12. Solution Development → 13. Evaluation
- **Trigger**: When solution development is complete
- **Requirements**: A concrete solution has been developed
- **Action**: System evaluates the solution against requirements
- **Implementation**: Solution development completion automatically triggers evaluation

### 13. Evaluation → 14. Integration
- **Trigger**: When evaluation is complete
- **Requirements**: Solution has been evaluated against requirements
- **Action**: System begins integrating the solution
- **Implementation**: Evaluation completion automatically triggers integration

### 14. Integration → 15. Output Generation
- **Trigger**: When integration is complete
- **Requirements**: Solution has been integrated
- **Action**: System generates final outputs
- **Implementation**: Integration completion automatically triggers output generation

### 15. Output Generation → 16. Completed
- **Trigger**: When output generation is complete
- **Requirements**: Final outputs have been generated
- **Action**: System marks the task as completed
- **Implementation**: Output generation completion automatically marks task as completed

## State Rollback Rules

In certain cases, a task may need to return to a previous state:

### Re-analysis
- **Trigger**: User requests re-analysis
- **Action**: System returns to Analysis state and performs analysis again
- **Implementation**: User clicks "Re-analyze" button

### Re-typification
- **Trigger**: User requests re-typification
- **Action**: System returns to Typify state and performs typification again
- **Implementation**: User clicks "Re-typify" button

### Re-decomposition
- **Trigger**: User requests re-decomposition
- **Action**: System returns to Decomposition state and performs decomposition again
- **Implementation**: User clicks "Re-decompose" button

## State Check Implementation

The system checks the current state before allowing certain operations:

```python
# Example of checking if a task can be analyzed
if task.state != TaskState.CONTEXT_GATHERED and task.state != TaskState.TASK_FORMATION:
    raise HTTPException(status_code=400, detail="Task must have sufficient context before analysis")
```

## Automated vs. Manual Transitions

Some transitions happen automatically when certain conditions are met, while others require user action:

### Automated Transitions
- New → Context Gathering
- Context Gathering → Context Gathered (when AI determines context is sufficient)
- Analysis → Typify
- Typify → Clarifying
- Clarification Complete → Approach Formation

### Manual Transitions (Requiring User Action)
- Context Gathered → Task Formation (user must initiate)
- Method Selection → Decomposition (user must select methods)

## Transition Prevention

The system prevents invalid state transitions:

1. Cannot skip states in the sequence
2. Cannot move to a later state if prerequisites aren't met
3. Certain transitions require specific user input or actions

## Visualizing Current State

The StateInfoPanel component shows:
- Current state
- Explanation of current state
- Next state (if applicable)
- Requirements to progress to next state
- Recommended actions

Click "View detailed state analysis" to see additional information about state requirements and recommendations. 