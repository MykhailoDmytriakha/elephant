# src/ai_agents/task_generation_agent.py
import logging
from typing import List, Optional
from pydantic import BaseModel
from src.core.config import settings
from src.model.task import Task
from src.model.planning import Stage, Artifact
from src.model.work import Work
from src.model.executable_task import ExecutableTask, ExecutableTaskList
from src.ai_agents.utils import detect_language, get_language_instruction

logger = logging.getLogger(__name__)

try:
    from agents import Agent, Runner  # type: ignore # noqa
    model = settings.OPENAI_MODEL
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI Agents SDK not installed. Task Generation functionality will be limited.")
    AGENTS_SDK_AVAILABLE = False

async def generate_tasks_for_work(
    task: Task,
    stage: Stage,
    work: Work,
) -> List[ExecutableTask]:
    """
    Uses AI to decompose a specific Work package into a list of ExecutableTask units.

    Args:
        task: The overall Task object.
        stage: The parent Stage object.
        work: The specific Work package to be decomposed.

    Returns:
        List[ExecutableTask]: A list of generated executable tasks.
    """
    if not AGENTS_SDK_AVAILABLE:
        logger.error("OpenAI Agents SDK not installed for Task Generation.")
        raise ImportError("OpenAI Agents SDK not installed.")

    # Detect language
    user_language = detect_language(task.short_description or "")
    language_instruction = get_language_instruction(user_language)

    # Prepare comprehensive context string, focusing on the target Work package
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
    TARGET WORK PACKAGE TO DECOMPOSE (ID: {work.id}):
    - Work Name: {work.name}
    - Work Description: {work.description}
    - Work Required Inputs: {", ".join([f'{a.name}({a.type})' for a in work.required_inputs]) if work.required_inputs else 'None'}
    - Work Expected Outcome: {work.expected_outcome}
    - Work Generated Artifacts Expected: {", ".join([f'{a.name}({a.type})' for a in work.generated_artifacts]) if work.generated_artifacts else 'None'}
    - Work Validation Criteria: {"\n- ".join(work.validation_criteria) if work.validation_criteria else 'None'}
    ---
    """

    # Instructions for the agent
    instructions = f"""
    You are an Execution Planning Agent. Your goal is to decompose the TARGET WORK PACKAGE detailed below into a sequence of 3-10 small, concrete, atomic `ExecutableTask` steps suitable for automation by specific executors (AI_AGENT or ROBOT).

    {context_summary}

    {language_instruction}

    EXECUTABLE TASK DECOMPOSITION INSTRUCTIONS:
    1.  **Analyze the Work Package:** Understand its specific objective, inputs, expected outcome, and validation criteria based on the TARGET WORK PACKAGE details. Use the OVERALL TASK CONTEXT for constraints, tools, and alignment.
    2.  **Define Executable Tasks:** Break down the work into a logical sequence of atomic actions. For each action, create an `ExecutableTask` object with the following attributes:
        *   `id`: Generate a unique ID like "stage_id" + "_" + "work_id" + "_" + "task_number" (e.g., "S1_W1_ET1", "S1_W1_ET2", "S1_W1_ET3", etc.)
        *   `name`: A concise action verb phrase (e.g., "Fetch User Data", "Calculate Risk Score", "Rotate Arm 90 Degrees").
        *   `description`: A clear explanation of *this specific action*, its inputs, and its immediate effect.
        *   `work_id`: MUST be set to the ID of the TARGET WORK PACKAGE: "{work.id}".
        *   `stage_id`: MUST be set to the ID of the PARENT STAGE: "{stage.id}".
        *   `task_id`: MUST be set to the ID of the TOP-LEVEL TASK: "{task.id}".
        *   `sequence_order`: Assign a 0-based index indicating the execution order within *this Work package*.
        *   `dependencies`: List the `id`s of *other ExecutableTasks within this same Work package* that must be completed first. If it's the first task, leave empty.
        *   `required_inputs`: List specific `Artifact` objects needed for *this action*. Reference artifacts from the parent Work's `required_inputs` or `generated_artifacts` of preceding ExecutableTasks.
        *   `generated_artifacts`: List specific `Artifact` objects produced by *this action*, if any. If the task primarily changes state (e.g., moves a robot, updates config), leave this list empty or null. The `Artifact` location should be standardized.
        *   `validation_criteria`: Define at least ONE specific, measurable, and *automatable* criterion to verify successful completion of *this specific action* (e.g., "API call returns status code 200", "Robot coordinates match [x,y,z] +/- 0.1mm", "File 'output.json' exists and is valid JSON"). Min 1 criterion required.
    3.  **Ensure Flow:** The sequence of `ExecutableTasks` must logically achieve the parent `Work` package's `expected_outcome`. Inputs/outputs should connect (`generated_artifacts` of task N might be `required_inputs` for task N+1).
    4.  **Automation Focus:** Describe actions neutrally assuming automated execution.
    5.  **Output:** Return a JSON object containing a single key `tasks` which holds a list of the generated `ExecutableTask` objects.

    CRITICAL:
    - Ensure all required fields are populated correctly. Min lengths/counts must be met.
    - `generated_artifacts` is OPTIONAL per task. Do not force artifact creation for state-change tasks.
    - `validation_criteria` is MANDATORY per task (at least one).
    - Executor config should be relevant to the executor type and action.
    """

    logger.info(f"Generating ExecutableTasks for Work ID: {work.id}, Stage ID: {stage.id}")

    # Define the agent
    agent = Agent(
        name="TaskGenerationAgent",
        instructions=instructions,
        output_type=ExecutableTaskList, # Expecting a list wrapped in this model
        model=model
    )

    # Run the agent
    try:
        # logger.info(f"Running Agent Generate ExecutableTasks with instructions: {instructions}")
        result = await Runner.run(agent, f"Generate the sequence of ExecutableTask steps for Work Package '{work.name}' (ID: {work.id}).")
        # logger.debug(f"Raw Agent Task Generation Result: {result}")

        # Process and return the response
        task_list_result = result.final_output
        if task_list_result and isinstance(task_list_result.tasks, list):
            generated_tasks = task_list_result.tasks
            logger.info(f"Successfully generated {len(generated_tasks)} ExecutableTasks for Work ID: {work.id}")
            # Ensure parent IDs are correctly set on each generated task
            for exec_task in generated_tasks:
                exec_task.work_id = work.id
                exec_task.stage_id = stage.id
                exec_task.task_id = task.id
                # Ensure generated_artifacts is [] if None
                if exec_task.generated_artifacts is None:
                    exec_task.generated_artifacts = []
            return generated_tasks
        else:
            logger.warning(f"Agent returned unexpected result or empty list for Work ID: {work.id}. Result: {task_list_result}")
            return []
    except Exception as e:
        logger.error(f"Error running TaskGenerationAgent for Work ID {work.id}: {e}", exc_info=True)
        raise # Re-raise the exception to be caught by the service layer