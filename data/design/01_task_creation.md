# Task Creation Process

## Process Overview
- **Process Name**: task_creation

## Process Stages

### 1. Gather Context
- **Inputs**: user_input
- **Outputs**: context
- **Possible Outcomes**:
  - context_sufficient
  - additional_context_needed

### 2. Refinement
- **Inputs**: context
- **Outputs**: draft_task
- **Possible Outcomes**:
  - task_ready_for_feedback
  - refinement_needed

### 3. Task Feedback
- **Inputs**: draft_task
- **Outputs**: final_task
- **Possible Outcomes**:
  - task_approved
  - needs_revision

## Flow Controls

| Outcome | Action |
|---------|--------|
| additional_context_needed | Return to: gather_context |
| refinement_needed | Return to: refinement |
| needs_revision | Return to: refinement |

## Object Example

### Initial Task
"How does the internet work?"

### Gathered Context
- **Question**: ...
- **Answer**: ...

### Drafts
- **Draft**: ...
- **Approved**: ...

### Feedback on Task
- **Question**: ...
- **Answer**: ...

### Clarified Task
"Provide a comprehensive overview of how the internet works, including general information, interesting facts, schemas, and illustrations." 