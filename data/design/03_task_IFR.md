# Task Scope Alignment Process

## Process Overview
- **Process Name**: task_scope_alignment
- **Description**: Process to align task requirements with scope to determine the ideal final result

## Process Stages

### 1. Alignment Analysis
- **Inputs**: final_task, final_scope
- **Outputs**: alignment_assessment
- **Possible Outcomes**:
  - fully_aligned
  - partial_alignment
  - misaligned

### 2. IFR Definition
- **Inputs**: alignment_assessment
- **Outputs**: draft_ifr
- **Possible Outcomes**:
  - ifr_defined
  - needs_refinement

### 3. IFR Validation
- **Inputs**: draft_ifr
- **Outputs**: final_ifr
- **Possible Outcomes**:
  - ifr_approved
  - revision_needed

## Flow Controls

| Outcome | Action |
|---------|--------|
| partial_alignment | Return to: alignment_analysis |
| misaligned | Return to: alignment_analysis |
| needs_refinement | Return to: ifr_definition |
| revision_needed | Return to: ifr_definition |

## Object Example

### Final Task
"Provide a comprehensive overview of how the internet works, including general information, interesting facts, schemas, and illustrations."

### Final Scope
- **What**:
  - ...
  - ...
- **Why**:
  - ...
  - ...
- **Who**:
  - ...
  - ...
- **Where**:
  - ...
  - ...
- **When**:
  - ...
  - ...
- **How**:
  - ...
  - ...

### Alignment Assessment
- **Alignment Score**: ... number from 0 to 1
- **Alignment Notes**:
  - ...
  - ...

### Final IFR (Ideal Final Result)
- **Ideal Final Result**: ...
- **Success Criteria**:
  - ...
  - ...
- **Expected Outcomes**:
  - ...
  - ...
- **Quality Metrics**:
  | Metric Name | Metric Value |
  |-------------|--------------|
  | ... | ... |
- **Validation Checklist**:
  | Validation Item | Validation Status |
  |-----------------|-------------------|
  | ... | ... | 