import logging
from typing import List
from pydantic import BaseModel
from src.core.config import settings
from src.model.task import Task
from src.model.planning import Stage # Assuming Stage is in planning.py
from src.model.work import Work, WorkList # Import from the new file
from src.ai_agents.utils import detect_language, get_language_instruction

logger = logging.getLogger(__name__)

try:
    from agents import Agent, Runner  # type: ignore # noqa
    model = settings.OPENAI_MODEL
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI Agents SDK not installed. Some functionality will be limited.")
    AGENTS_SDK_AVAILABLE = False

async def generate_work_packages_for_stage(
    task: Task,
    stage: Stage,
) -> List[Work]:
    """
    Uses AI to decompose a specific Stage into a list of Work packages.

    Args:
        task: The overall Task object containing context, scope, requirements, etc.
        stage: The specific Stage object to be decomposed.

    Returns:
        List[Work]: A list of generated Work packages for the given stage.
    """
    if not AGENTS_SDK_AVAILABLE:
        logger.error("OpenAI Agents SDK not installed for Work Generation.")
        raise ImportError("OpenAI Agents SDK not installed.")

    # Detect language
    user_language = detect_language(task.short_description or "")
    language_instruction = get_language_instruction(user_language)

    # Prepare comprehensive context string
    context_summary = f"""
    TASK DETAILS:
    Task: {task.task}
    Context: {task.context}
    Scope: {task.scope.scope if task.scope else 'Not defined'}
    IFR: {task.ifr.ideal_final_result if task.ifr else 'Not defined'}
    Success criteria: {"\n- ".join(task.ifr.success_criteria) if task.ifr else 'Not defined'}
    Expected outcomes: {"\n- ".join(task.ifr.expected_outcomes) if task.ifr else 'Not defined'}
    Requerements: {"\n- ".join(task.requirements.requirements) if task.requirements else 'Not defined'}
    Constraints: {"\n- ".join(task.requirements.constraints) if task.requirements else 'Not defined'}
    Limitations: {"\n- ".join(task.requirements.limitations) if task.requirements else 'Not defined'}
    Resources: {"\n- ".join(task.requirements.resources) if task.requirements else 'Not defined'}
    Tools: {"\n- ".join(task.requirements.tools) if task.requirements else 'Not defined'}
    Definitions: {"\n- ".join(task.requirements.definitions) if task.requirements else 'Not defined'}
    Network Plan Overview: {len(task.network_plan.stages) if task.network_plan else 0} total stages.
    ---
    TARGET STAGE TO DECOMPOSE (ID: {stage.id}):
    - Stage Name: {stage.name}
    - Stage Description: {stage.description}
    - Stage Results: {", ".join(stage.result) if stage.result else 'None'}
    - Stage Deliverables: {", ".join(stage.what_should_be_delivered) if stage.what_should_be_delivered else 'None'}
    - Stage Checkpoints: {len(stage.checkpoints) if stage.checkpoints else 0} checkpoints defined.
    ---
    """

    # Instructions for the agent
    instructions = f"""
    You are a Work Decomposition Agent. Your goal is to break down the provided STAGE (within the context of the overall TASK) into logical, manageable 'Work' packages suitable for automated execution by AI agents or robots.

    {context_summary}

    {language_instruction}

    STAGE DECOMPOSITION INSTRUCTIONS:
    1.  **Analyze the Stage:** Understand the stage's purpose, description, expected results, deliverables, and checkpoints based on the TARGET STAGE details provided above.
    2.  **Identify Sub-Goals:** Determine the logical sub-goals or major capabilities that need to be achieved within this stage. Aim for 3-7 major Work packages per stage, depending on complexity.
    3.  **Define Work Packages:** For each sub-goal, create a `Work` package object with the following attributes:
        *   `id`: Generate a new UUID (this will be handled by the model, just define the structure). like stage.id + "_" + work_package_number (S1_W1, S1_W2, etc.)
        *   `name`: A concise, descriptive name (e.g., "Process Raw Sensor Data", "Generate Initial Design Mockups", "Assemble Component A"). Min 5 chars.
        *   `description`: A clear explanation of this work package's specific objective, inputs, outputs, and boundaries. Min 20 chars.
        *   `stage_id`: MUST be set to the ID of the TARGET STAGE: "{stage.id}".
        *   `sequence_order`: Assign a 0-based index indicating the logical execution order within this stage.
        *   `dependencies`: List the `id`s of *other Work packages within this same stage* that must be completed first. Keep dependencies simple for now (mostly sequential). If it's the first work package, leave this empty.
        *   `required_inputs`: List necessary `Artifact` objects (name, type, description, location) needed to start this work. These might come from previous stages' deliverables or previous work packages' generated artifacts within this stage. Use standardized locations.
        *   `expected_outcome`: Describe the specific state or capability achieved when this work is done. Min 10 chars.
        *   `generated_artifacts`: List the specific, tangible `Artifact` objects (name, type, description, location) produced by this work. Use standardized locations. These artifacts might be inputs for later work packages or contribute to the stage's final deliverables.
        *   `validation_criteria`: Define at least one specific, measurable, and *automatable* criterion to verify successful completion (e.g., "Output file 'processed_data.csv' exists in 'S3_BUCKET_PROCESSED_DATA' and contains > 1000 rows", "Component A passes continuity test", "API endpoint '/status' returns 200 OK").
    4.  **Ensure Completeness:** The generated Work packages, when executed in order, should collectively achieve the `Stage`'s description, results, and deliverables. Ensure artifacts flow logically (`generated_artifacts` of one work become `required_inputs` of another).
    5.  **Automation Focus:** Frame descriptions, outcomes, and validation criteria assuming automated execution without explicit human intervention. Use neutral language.
    6.  **Output:** Return a JSON object containing a single key `work_packages` which holds a list of the generated `Work` objects.

    CRITICAL: Ensure all fields in the `Work` model are correctly populated according to the defined structure and constraints (like min_length, enums). Pay close attention to generating valid `Artifact` structures for inputs and outputs, including standardized `location` names where applicable. Define clear, automatable `validation_criteria`.
    """

    logger.info(f"Generating Work packages for Stage ID: {stage.id}")
    # logger.info(f"Agent Instructions: {instructions}")

    # Define the agent
    agent = Agent(
        name="WorkGenerationAgent",
        instructions=instructions,
        output_type=WorkList, # Expecting a list wrapped in this model
        model=model
    )

    # Run the agent
    result = await Runner.run(agent, f"Generate the list of Work packages for Stage '{stage.name}' (ID: {stage.id}).")
    
    logger.info(f"Agent Work Generation Result: {result}")

    # Process and return the response
    work_list_result = result.final_output
    if work_list_result and isinstance(work_list_result.work_packages, list):
        logger.info(f"Successfully generated {len(work_list_result.work_packages)} Work packages for Stage ID: {stage.id}")
        # Ensure stage_id is correctly set on each generated work package
        for work_pkg in work_list_result.work_packages:
            work_pkg.stage_id = stage.id
        return work_list_result.work_packages
    else:
        logger.error(f"Failed to generate valid Work packages for Stage ID: {stage.id}. Result: {work_list_result}")
        return []