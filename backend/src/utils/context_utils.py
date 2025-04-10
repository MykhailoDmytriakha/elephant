# backend/src/utils/context_utils.py
from typing import Dict, Any, Optional, List
import logging

# Model imports
from src.model.task import Task
from src.model.artifact import Artifact
from src.model.planning import Stage
from src.model.work import Work
from src.model.executable_task import ExecutableTask
from src.model.subtask import Subtask

# Util imports
from src.utils.task_utils import (
    get_stage, get_work, get_executable_task, get_subtask,
    find_stage_by_id, find_work_by_id, find_executable_task_by_id, find_subtask_by_id
)

logger = logging.getLogger(__name__)

# --- Helper Functions ---

def _format_artifacts(artifacts: Optional[List[Artifact]], label: str) -> str:
    """Formats a list of artifacts under a given label. Returns empty string if no artifacts."""
    if not artifacts:
        return ""
    formatted_items = "\n".join([f"  - {a.name} ({a.type}): {a.description}" for a in artifacts])
    return f"{label}:\n{formatted_items}"

def _format_list(items: Optional[List[str]], label: str) -> str:
    """Formats a list of strings under a given label. Returns empty string if no items."""
    if not items:
        return ""
    formatted_items = "\n".join([f"  - {item}" for item in items])
    return f"{label}:\n{formatted_items}"

def _append_line_if_value(lines: List[str], label: str, value: Any):
    """Appends a formatted line to the list if the value is truthy."""
    if value:
        lines.append(f"{label}: {value}")

# --- Context Extraction Functions (Using Full Path) ---

def get_base_context(task: Task) -> str:
    """Extracts base context from Task as a formatted string, omitting empty fields."""
    lines = [f"--- Base Task Context (ID: {task.id}) ---"]
    _append_line_if_value(lines, "Short Description", task.short_description)
    _append_line_if_value(lines, "Task Description", task.task)
    _append_line_if_value(lines, "Task Context", task.context)
    if task.scope:
        _append_line_if_value(lines, "Scope", task.scope.scope)
    if task.ifr:
        _append_line_if_value(lines, "Ideal Final Result", task.ifr.ideal_final_result)
        outcomes_text = _format_list(task.ifr.expected_outcomes, "Expected Outcomes")
        if outcomes_text: lines.append(outcomes_text)
        criteria_text = _format_list(task.ifr.success_criteria, "Success Criteria")
        if criteria_text: lines.append(criteria_text)

    return "\n".join(lines) if len(lines) > 1 else ""

def get_stage_context(task: Task, stage_id: str) -> str:
    """Extracts context for a Stage (using full path) as a formatted string, omitting empty fields."""
    stage = get_stage(task, stage_id)
    lines = [f"--- Stage Context (ID: {stage.id}) ---"]
    _append_line_if_value(lines, "Name", stage.name)
    _append_line_if_value(lines, "Description", stage.description)
    result_shaping_text = _format_list(stage.result, "Result Shaping")
    if result_shaping_text: lines.append(result_shaping_text)
    deliverables_text = _format_list(stage.what_should_be_delivered, "Deliverables")
    if deliverables_text: lines.append(deliverables_text)

    return "\n".join(lines) if len(lines) > 1 else ""

def get_work_context(task: Task, stage_id: str, work_id: str) -> str:
    """Extracts context for a Work package (using full path) as a formatted string, omitting empty fields."""
    work = get_work(task, stage_id, work_id)
    lines = [f"--- Work Package Context (ID: {work.id}) ---"]
    _append_line_if_value(lines, "Name", work.name)
    _append_line_if_value(lines, "Description", work.description)
    _append_line_if_value(lines, "Expected Outcome", work.expected_outcome)
    inputs_text = _format_artifacts(work.required_inputs, "Required Inputs")
    if inputs_text: lines.append(inputs_text)
    artifacts_text = _format_artifacts(work.generated_artifacts, "Generated Artifacts")
    if artifacts_text: lines.append(artifacts_text)

    return "\n".join(lines) if len(lines) > 1 else ""

def get_executable_task_context(task: Task, stage_id: str, work_id: str, executable_task_id: str) -> str:
    """Extracts context for an ExecutableTask (using full path) as a formatted string, omitting empty fields."""
    executable_task = get_executable_task(task, stage_id, work_id, executable_task_id)
    lines = [f"--- Executable Task Context (ID: {executable_task.id}) ---"]
    _append_line_if_value(lines, "Name", executable_task.name)
    _append_line_if_value(lines, "Description", executable_task.description)
    dependencies_text = _format_list(executable_task.dependencies, "Dependencies (ExecutableTask IDs)")
    if dependencies_text: lines.append(dependencies_text)
    inputs_text = _format_artifacts(executable_task.required_inputs, "Required Inputs")
    if inputs_text: lines.append(inputs_text)
    artifacts_text = _format_artifacts(executable_task.generated_artifacts, "Generated Artifacts")
    if artifacts_text: lines.append(artifacts_text)
    validation_text = _format_list(executable_task.validation_criteria, "Validation Criteria")
    if validation_text: lines.append(validation_text)

    return "\n".join(lines) if len(lines) > 1 else ""

def get_subtask_context(task: Task, stage_id: str, work_id: str, executable_task_id: str, subtask_id: str) -> str:
    """Extracts context for a Subtask (using full path) as a formatted string, omitting empty fields."""
    subtask = get_subtask(task, stage_id, work_id, executable_task_id, subtask_id)
    lines = [f"--- Subtask Context (ID: {subtask.id}) ---"]
    _append_line_if_value(lines, "Name", subtask.name)
    _append_line_if_value(lines, "Description", subtask.description)
    _append_line_if_value(lines, "Executor Type", subtask.executor_type)

    return "\n".join(lines) if len(lines) > 1 else ""

# --- Context Extraction Functions (Searching by ID) ---

def _format_stage_context(stage: Stage) -> str:
    """Formats the context string for a given Stage object."""
    lines = [f"--- Stage Context (ID: {stage.id}) ---"]
    _append_line_if_value(lines, "Name", stage.name)
    _append_line_if_value(lines, "Description", stage.description)
    result_shaping_text = _format_list(stage.result, "Result Shaping")
    if result_shaping_text: lines.append(result_shaping_text)
    deliverables_text = _format_list(stage.what_should_be_delivered, "Deliverables")
    if deliverables_text: lines.append(deliverables_text)
    return "\n".join(lines) if len(lines) > 1 else ""

def _format_work_context(work: Work) -> str:
    """Formats the context string for a given Work object."""
    lines = [f"--- Work Package Context (ID: {work.id}) ---"]
    _append_line_if_value(lines, "Name", work.name)
    _append_line_if_value(lines, "Description", work.description)
    _append_line_if_value(lines, "Expected Outcome", work.expected_outcome)
    inputs_text = _format_artifacts(work.required_inputs, "Required Inputs")
    if inputs_text: lines.append(inputs_text)
    artifacts_text = _format_artifacts(work.generated_artifacts, "Generated Artifacts")
    if artifacts_text: lines.append(artifacts_text)
    return "\n".join(lines) if len(lines) > 1 else ""

def _format_executable_task_context(executable_task: ExecutableTask) -> str:
    """Formats the context string for a given ExecutableTask object."""
    lines = [f"--- Executable Task Context (ID: {executable_task.id}) ---"]
    _append_line_if_value(lines, "Name", executable_task.name)
    _append_line_if_value(lines, "Description", executable_task.description)
    dependencies_text = _format_list(executable_task.dependencies, "Dependencies (ExecutableTask IDs)")
    if dependencies_text: lines.append(dependencies_text)
    inputs_text = _format_artifacts(executable_task.required_inputs, "Required Inputs")
    if inputs_text: lines.append(inputs_text)
    artifacts_text = _format_artifacts(executable_task.generated_artifacts, "Generated Artifacts")
    if artifacts_text: lines.append(artifacts_text)
    validation_text = _format_list(executable_task.validation_criteria, "Validation Criteria")
    if validation_text: lines.append(validation_text)
    return "\n".join(lines) if len(lines) > 1 else ""

def _format_subtask_context(subtask: Subtask) -> str:
    """Formats the context string for a given Subtask object."""
    lines = [f"--- Subtask Context (ID: {subtask.id}) ---"]
    _append_line_if_value(lines, "Name", subtask.name)
    _append_line_if_value(lines, "Description", subtask.description)
    _append_line_if_value(lines, "Executor Type", subtask.executor_type)
    return "\n".join(lines) if len(lines) > 1 else ""

def get_stage_context_by_id(task: Task, stage_id: str) -> str:
    """Extracts context for a Stage found by its ID. Returns empty string if not found."""
    stage = find_stage_by_id(task, stage_id)
    if not stage:
        logger.warning(f"Stage context requested but Stage ID '{stage_id}' not found in Task '{task.id}'.")
        return "" # Or return f"Stage {stage_id} not found."
    return _format_stage_context(stage)

def get_work_context_by_id(task: Task, work_id: str) -> str:
    """Extracts context for a Work package found by its ID. Returns empty string if not found."""
    work = find_work_by_id(task, work_id)
    if not work:
        logger.warning(f"Work context requested but Work ID '{work_id}' not found in Task '{task.id}'.")
        return "" # Or return f"Work {work_id} not found."
    return _format_work_context(work)

def get_executable_task_context_by_id(task: Task, executable_task_id: str) -> str:
    """Extracts context for an ExecutableTask found by its ID. Returns empty string if not found."""
    executable_task = find_executable_task_by_id(task, executable_task_id)
    if not executable_task:
        logger.warning(f"ExecutableTask context requested but ExecutableTask ID '{executable_task_id}' not found in Task '{task.id}'.")
        return "" # Or return f"ExecutableTask {executable_task_id} not found."
    return _format_executable_task_context(executable_task)

def get_subtask_context_by_id(task: Task, subtask_id: str) -> str:
    """Extracts context for a Subtask found by its ID. Returns empty string if not found."""
    subtask = find_subtask_by_id(task, subtask_id)
    if not subtask:
        logger.warning(f"Subtask context requested but Subtask ID '{subtask_id}' not found in Task '{task.id}'.")
        return "" # Or return f"Subtask {subtask_id} not found."
    return _format_subtask_context(subtask) 