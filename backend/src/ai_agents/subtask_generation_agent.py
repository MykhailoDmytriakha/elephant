# src/ai_agents/subtask_generation_agent.py
import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from src.core.config import settings
from src.model.task import Task
from src.model.planning import Stage
from src.model.work import Work
from src.model.executable_task import ExecutableTask
from src.model.subtask import Subtask, SubtaskList # Import Subtask models
from src.ai_agents.utils import detect_language, get_language_instruction

logger = logging.getLogger(__name__)

try:
    from agents import Agent, Runner # type: ignore # noqa
    model = settings.OPENAI_MODEL
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI Agents SDK not installed. Subtask Generation functionality will be limited.")
    AGENTS_SDK_AVAILABLE = False

async def generate_subtasks(
    task: Task,
    stage: Stage,
    work: Work,
    executable_task: ExecutableTask,
) -> List[Subtask]:
    """
    Uses AI to decompose a specific ExecutableTask into a list of Subtask units.

    Args:
        task: The overall Task object.
        stage: The parent Stage object.
        work: The parent Work package object.
        executable_task: The specific ExecutableTask to be decomposed.

    Returns:
        List[Subtask]: A list of generated atomic subtasks.
    """
    if not AGENTS_SDK_AVAILABLE:
        logger.error("OpenAI Agents SDK not installed for Subtask Generation.")
        raise ImportError("OpenAI Agents SDK not installed.")

    # Detect language
    user_language = detect_language(task.short_description or "")
    language_instruction = get_language_instruction(user_language)

    # Prepare comprehensive context string
    context_summary = f"""
    OVERALL TASK CONTEXT:
    Task Description: {task.task}
    Task Context: {task.context}
    Task Scope: {task.scope.scope if task.scope else 'Not defined'}
    Requerements: {"\n- ".join(task.requirements.requirements) if task.requirements else 'Not defined'}
    Constraints: {"\n- ".join(task.requirements.constraints) if task.requirements else 'Not defined'}
    Limitations: {"\n- ".join(task.requirements.limitations) if task.requirements else 'Not defined'}
    Resources: {"\n- ".join(task.requirements.resources) if task.requirements else 'Not defined'}
    Tools: {"\n- ".join(task.requirements.tools) if task.requirements else 'Not defined'}
    Definitions: {"\n- ".join(task.requirements.definitions) if task.requirements else 'Not defined'}
    ---
    PARENT STAGE (ID: {stage.id}):
    - Stage Name: {stage.name}
    - Stage Description: {stage.description}
    - Stage Results: {", ".join(stage.result) if stage.result else 'None'}
    ---
    PARENT WORK PACKAGE (ID: {work.id}):
    - Work Name: {work.name}
    - Work Description: {work.description}
    - Work Expected Outcome: {work.expected_outcome}
    ---
    TARGET EXECUTABLE TASK TO DECOMPOSE (ID: {executable_task.id}):
    - Executable Task Name: {executable_task.name}
    - Executable Task Description: {executable_task.description}
    - Required Inputs: {", ".join([f'{a.name}({a.type})' for a in executable_task.required_inputs]) if executable_task.required_inputs else 'None'}
    - Expected Generated Artifacts: {", ".join([f'{a.name}({a.type})' for a in executable_task.generated_artifacts]) if executable_task.generated_artifacts else 'None'}
    - Validation Criteria: {"\n- ".join(executable_task.validation_criteria) if executable_task.validation_criteria else 'None'}
    ---
    """

    # Instructions for the agent
    instructions = f"""
    You are a Subtask Decomposition Agent. Your goal is to break down the TARGET EXECUTABLE TASK into a sequence of 3-7 extremely small, atomic `Subtask` steps, each designed for a *specific* type of automated executor (AI_AGENT, ROBOT, or HUMAN_REVIEW).

    {context_summary}

    {language_instruction}

    SUBTASK DECOMPOSITION INSTRUCTIONS:
    1.  **Analyze Executable Task:** Understand its specific action, inputs, expected outputs, and validation based on the TARGET EXECUTABLE TASK details. Use the broader context (Work, Stage, Task) for constraints and overall goals.
    2.  **Identify Atomic Actions:** Break the executable task into the smallest possible individual steps. Each step should be a single command or operation.
    3.  **Define Subtasks:** For each atomic action, create a `Subtask` object with the following attributes:
        *   `id`: Generate a unique ID like "stage_id" + "_" + "work_id" + "_" + "task_number" + "_" + "subtask_number" (e.g., "S1_W1_ET1_ST1", "S1_W1_ET1_ST2", "S1_W1_ET1_ST3", etc.)
        *   `name`: A very concise action phrase (e.g., "Set Joint Angle", "Format API Request", "Check Sensor Value", "Verify Output Schema").
        *   `description`: A precise instruction for *this single atomic action*.
        *   `parent_executable_task_id`: MUST be "{executable_task.id}".
        *   `parent_work_id`: MUST be "{work.id}".
        *   `parent_stage_id`: MUST be "{stage.id}".
        *   `parent_task_id`: MUST be "{task.id}".
        *   `sequence_order`: Assign a 0-based index indicating the execution order *within this ExecutableTask*.
        *   `executor_type`: Choose ONE:
            *   `AI_AGENT`: For tasks involving data processing, API calls, analysis, text generation, complex logic.
            *   `ROBOT`: For physical manipulation, movement, sensor interaction.
            *   `HUMAN`: Only if unavoidable for quality checks or critical decisions not suitable for automation *within the defined constraints*. Use sparingly.
    4.  **Ensure Sequence:** The sequence of `Subtasks` must logically perform the parent `ExecutableTask`'s action.
    5.  **Atomicity:** Each `Subtask` should represent the smallest indivisible unit of work.
    6.  **Output:** Return a JSON object containing a single key `subtasks` which holds a list of the generated `Subtask` objects.

    CRITICAL:
    - Ensure `executor_type` is chosen correctly based on the action.
    - `parameters` must be structured and contain all necessary details for the executor.
    - `validation_params` should enable automated verification where possible.
    - Parent IDs (`parent_executable_task_id`, `parent_work_id`, etc.) MUST be correctly set.
    - Generate 3-15 subtasks per executable task.
    """

    logger.info(f"Generating Subtasks for ExecutableTask ID: {executable_task.id}")

    # Define the agent
    agent = Agent(
        name="SubtaskGenerationAgent",
        instructions=instructions,
        output_type=SubtaskList, # Expecting a list wrapped in this model
        model=model
    )

    # Run the agent
    try:
        # logger.debug(f"Running Agent Generate Subtasks with instructions:\n{instructions}")
        result = await Runner.run(agent, f"Generate the sequence of atomic Subtask steps for ExecutableTask '{executable_task.name}' (ID: {executable_task.id}).")
        logger.debug(f"Raw Agent Subtask Generation Result: {result}")

        # Process and return the response
        subtask_list_result = result.final_output
        if subtask_list_result and isinstance(subtask_list_result.subtasks, list):
            generated_subtasks = subtask_list_result.subtasks
            logger.info(f"Successfully generated {len(generated_subtasks)} Subtasks for ExecutableTask ID: {executable_task.id}")
            # Ensure parent IDs are correctly set on each generated subtask
            for sub_task in generated_subtasks:
                sub_task.parent_executable_task_id = executable_task.id
                sub_task.parent_work_id = work.id
                sub_task.parent_stage_id = stage.id
                sub_task.parent_task_id = task.id
            return generated_subtasks
        else:
            logger.warning(f"Agent returned unexpected result or empty list for ExecutableTask ID: {executable_task.id}. Result: {subtask_list_result}")
            return []
    except Exception as e:
        logger.error(f"Error running SubtaskGenerationAgent for ExecutableTask ID {executable_task.id}: {e}", exc_info=True)
        raise # Re-raise the exception