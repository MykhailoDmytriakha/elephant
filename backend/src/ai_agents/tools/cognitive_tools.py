import logging
from typing import List, Dict, Any, Optional, Union
import os
from openai import OpenAI
from src.core.config import settings

# Import Pydantic for type handling
from pydantic import ConfigDict

# Try to import the OpenAI Agents SDK specific decorator
try:
    from agents import function_tool # type: ignore
    AGENTS_SDK_AVAILABLE = True
    
    # Create a wrapper for function_tool that allows arbitrary types
    def adk_function_tool(func):
        # Add model_config with arbitrary_types_allowed=True to make Pydantic accept ToolContext
        setattr(func, 'model_config', ConfigDict(arbitrary_types_allowed=True))
        return function_tool(func)
        
except ImportError:
    logging.warning("OpenAI Agents SDK not installed. function_tool decorator will not be effective.")
    # Define a dummy decorator if the SDK is not available
    def function_tool(func):
        return func
    
    # Match the API of the real decorator 
    adk_function_tool = function_tool
    
    AGENTS_SDK_AVAILABLE = False

logger = logging.getLogger(__name__)

# Initialize OpenAI client
# Try to get API key from environment or settings
client: Union[OpenAI, None] = None
model = "gpt-4o"  # Default model

try:
    # First check if API key is in settings
    api_key = settings.OPENAI_API_KEY if hasattr(settings, 'OPENAI_API_KEY') else os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        logger.warning("OpenAI API key not found in settings or environment variables")
    else:
        client = OpenAI(api_key=api_key)
        model = settings.OPENAI_MODEL
        logger.info(f"OpenAI client initialized with model: {model}")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}", exc_info=True)
    model = "default-model-error"  # Fallback model name

@adk_function_tool
def evaluate_plan_feasibility(plan_description: str, constraints: Optional[List[str]] = None) -> str:
    """
    Evaluates the feasibility of a given plan description based on known constraints or general knowledge.
    Considers potential difficulties, required effort, and likelihood of success.

    Args:
        plan_description: A detailed description of the plan or steps to be evaluated.
        constraints: Optional list of known constraints (e.g., time limits, resource availability, technical limitations).

    Returns:
        A string analysis summarizing the feasibility, potential challenges, and confidence level.
    """
    logger.info(f"Cognitive Tool: Evaluating plan feasibility for: {plan_description}")
    if not client:
        return "Error: OpenAI client not initialized."

    system_instructions = (
        "You are an expert AI assistant specializing in plan evaluation. "
        "Analyze the provided plan description and constraints to assess its feasibility. "
        "Consider potential difficulties, required effort, resource needs, dependencies, and overall likelihood of success. "
        "Provide a concise summary of your evaluation, highlighting key challenges and your confidence level (e.g., High, Medium, Low)."
    )
    user_input = f"Plan Description:\n{plan_description}\n\n"
    if constraints:
        user_input += f"Known Constraints:\n- {'\n- '.join(constraints)}\n"
    else:
        user_input += "Known Constraints: None provided.\n"
    user_input += "\nPlease provide your feasibility analysis."

    try:
        response = client.responses.create(
            model=model,
            instructions=system_instructions,
            input=user_input,
        )
        return response.output_text
    except Exception as e:
        logger.error(f"Error calling OpenAI API for evaluate_plan_feasibility: {e}", exc_info=True)
        return f"Error during feasibility analysis: {str(e)}"

@adk_function_tool
def identify_required_resources(task_description: str, current_context: Optional[Dict[str, Any]] = None) -> str:
    """
    Identifies the resources (e.g., files, data, APIs, tools, information) needed to complete a given task.

    Args:
        task_description: The description of the task for which resources need to be identified.
        current_context: Optional dictionary providing context about available resources or project state.

    Returns:
        A string listing the identified required resources and potentially missing ones.
    """
    logger.info(f"Cognitive Tool: Identifying resources for task: {task_description}")
    if not client:
        return "Error: OpenAI client not initialized."

    system_instructions = (
        "You are an expert AI assistant specializing in task analysis and resource identification. "
        "Based on the task description and any provided context, identify all necessary resources. "
        "Resources can include specific files, data sets, API endpoints, software tools, external information, or specific expertise. "
        "List the required resources clearly. If context suggests some resources might already be available, note that. Indicate any potentially missing resources."
    )
    user_input = f"Task Description:\n{task_description}\n\n"
    if current_context:
        # Simple context representation; might need more sophisticated handling
        context_str = "\n".join([f"{k}: {str(v)[:100]}..." if len(str(v)) > 100 else f"{k}: {v}" for k, v in current_context.items()])
        user_input += f"Current Context:\n{context_str}\n"
    else:
        user_input += "Current Context: None provided.\n"
    user_input += "\nPlease list the required resources for this task."

    try:
        response = client.responses.create(
            model=model,
            instructions=system_instructions,
            input=user_input,
        )
        return response.output_text
    except Exception as e:
        logger.error(f"Error calling OpenAI API for identify_required_resources: {e}", exc_info=True)
        return f"Error during resource identification: {str(e)}"

@adk_function_tool
def analyze_potential_risks(action_description: str, context: Optional[str] = None) -> str:
    """
    Analyzes a proposed action or plan to identify potential risks, side effects, or failure modes.

    Args:
        action_description: The specific action or part of a plan to analyze for risks.
        context: Optional context about the environment or state where the action will take place.

    Returns:
        A string summarizing potential risks and their estimated impact or likelihood.
    """
    logger.info(f"Cognitive Tool: Analyzing risks for action: {action_description}")
    if not client:
        return "Error: OpenAI client not initialized."

    system_instructions = (
        "You are an expert AI assistant specializing in risk analysis. "
        "Analyze the proposed action description and any provided context to identify potential risks, negative side effects, or failure modes. "
        "For each identified risk, briefly describe it and estimate its potential impact (e.g., High, Medium, Low) and likelihood (e.g., High, Medium, Low). "
        "Focus on practical and significant risks."
    )
    user_input = f"Action/Plan Description:\n{action_description}\n\n"
    if context:
        user_input += f"Context:\n{context}\n"
    else:
        user_input += "Context: None provided.\n"
    user_input += "\nPlease provide your risk analysis."

    try:
        response = client.responses.create(
            model=model,
            instructions=system_instructions,
            input=user_input,
        )
        return response.output_text
    except Exception as e:
        logger.error(f"Error calling OpenAI API for analyze_potential_risks: {e}", exc_info=True)
        return f"Error during risk analysis: {str(e)}"

@adk_function_tool
def break_down_complex_task(task_description: str, max_depth: int) -> str:
    """
    Decomposes a complex task description into smaller, more manageable sub-tasks.

    Args:
        task_description: The high-level task to break down.
        max_depth: The desired level of decomposition (e.g., 1 for direct sub-tasks).

    Returns:
        A string representing the structured list of sub-tasks (e.g., in JSON or markdown format).
    """
    logger.info(f"Cognitive Tool: Breaking down task: {task_description}")
    if not client:
        return "Error: OpenAI client not initialized."

    system_instructions = (
        "You are an expert AI assistant specializing in task decomposition and planning. "
        "Break down the given complex task description into a sequence of smaller, logical, and actionable sub-tasks. "
        "The goal is to create a clear plan that can be followed step-by-step. "
        "Present the sub-tasks in a structured format, preferably as a numbered or bulleted list."
        # Note: max_depth is hard to enforce reliably with LLM instructions alone, focusing on clear breakdown.
    )
    user_input = f"Complex Task Description:\n{task_description}\n\n"
    user_input += "\nPlease provide the breakdown into sub-tasks."

    try:
        response = client.responses.create(
            model=model,
            instructions=system_instructions,
            input=user_input,
        )
        # Consider adding validation here if a specific format (like JSON) is strictly required.
        return response.output_text
    except Exception as e:
        logger.error(f"Error calling OpenAI API for break_down_complex_task: {e}", exc_info=True)
        return f"Error during task breakdown: {str(e)}"

@adk_function_tool
def verify_step_completion(step_description: str, evidence: Optional[List[str]] = None) -> str:
    """
    Verifies if a described step or prerequisite is likely completed based on available evidence or context.

    Args:
        step_description: The step whose completion needs verification.
        evidence: Optional list of evidence strings (e.g., file contents, API responses, previous step outcomes).

    Returns:
        A string indicating the verification status (e.g., "Confirmed", "Uncertain", "Contradicted") with reasoning.
    """
    logger.info(f"Cognitive Tool: Verifying completion of step: {step_description}")
    if not client:
        return "Error: OpenAI client not initialized."

    system_instructions = (
        "You are an expert AI assistant specializing in verification and evidence assessment. "
        "Evaluate whether the described step has been completed based on the provided evidence. "
        "State your conclusion clearly (e.g., 'Confirmed', 'Likely Completed', 'Uncertain', 'Likely Not Completed', 'Contradicted'). "
        "Provide brief reasoning based *only* on the evidence given. Do not make assumptions beyond the evidence."
    )
    user_input = f"Step Description to Verify:\n{step_description}\n\n"
    if evidence:
        evidence_str = "\n---\n".join(evidence)
        user_input += f"Available Evidence:\n{evidence_str}\n"
    else:
        user_input += "Available Evidence: None provided.\n"
    user_input += "\nPlease provide your verification status and reasoning."

    try:
        response = client.responses.create(
            model=model,
            instructions=system_instructions,
            input=user_input,
        )
        return response.output_text
    except Exception as e:
        logger.error(f"Error calling OpenAI API for verify_step_completion: {e}", exc_info=True)
        return f"Error during step verification: {str(e)}"

@adk_function_tool
def compare_alternative_approaches(goal: str, approaches: List[str]) -> str:
    """
    Compares two or more alternative approaches for achieving a specific goal based on specified criteria (e.g., efficiency, risk, cost).

    Args:
        goal: The objective the approaches aim to achieve.
        approaches: A list of strings, each describing an alternative approach.

    Returns:
        A string providing a comparative analysis and potentially recommending an approach.
    """
    logger.info(f"Cognitive Tool: Comparing approaches for goal: {goal}")
    if not client:
        return "Error: OpenAI client not initialized."
    if len(approaches) < 2:
        return "Error: At least two approaches are needed for comparison."

    system_instructions = (
        "You are an expert AI assistant specializing in comparative analysis and strategic decision-making. "
        "Compare the provided alternative approaches for achieving the specified goal. "
        "Evaluate them based on likely effectiveness, efficiency, potential risks, complexity, and resource requirements (implicitly or explicitly mentioned). "
        "Provide a balanced comparison, highlighting the pros and cons of each approach relative to the goal. "
        "Conclude with a recommendation if one approach seems clearly superior, or state if the choice depends on specific priorities."
    )
    user_input = f"Goal:\n{goal}\n\nAlternative Approaches to Compare:\n"
    for i, approach in enumerate(approaches):
        user_input += f"{i+1}. {approach}\n"
    user_input += "\nPlease provide your comparative analysis and recommendation."

    try:
        response = client.responses.create(
            model=model,
            instructions=system_instructions,
            input=user_input,
        )
        return response.output_text
    except Exception as e:
        logger.error(f"Error calling OpenAI API for compare_alternative_approaches: {e}", exc_info=True)
        return f"Error during approach comparison: {str(e)}"

@adk_function_tool
def synthesize_information(information_pieces: List[str], desired_output_format: str) -> str:
    """
    Synthesizes multiple pieces of information (e.g., tool outputs, context data) into a cohesive summary or conclusion.

    Args:
        information_pieces: A list of strings containing the information to synthesize.
        desired_output_format: A description of the desired output (e.g., "a bulleted list of key findings", "a paragraph summarizing the situation").

    Returns:
        A string containing the synthesized information in the desired format.
    """
    logger.info(f"Cognitive Tool: Synthesizing {len(information_pieces)} pieces of information.")
    if not client:
        return "Error: OpenAI client not initialized."
    if not information_pieces:
        return "Error: No information pieces provided for synthesis."

    system_instructions = (
        "You are an expert AI assistant specializing in information synthesis and summarization. "
        "Combine the provided pieces of information into a single, cohesive output that addresses the user's desired format. "
        "Identify key themes, connections, or conclusions from the input data. Avoid simple concatenation; aim for genuine synthesis. "
        "Ensure the final output strictly adheres to the requested format."
    )
    user_input = "Pieces of Information to Synthesize:\n\n"
    for i, piece in enumerate(information_pieces):
        user_input += f"--- Piece {i+1} ---\n{piece}\n\n"
    user_input += f"---\nDesired Output Format: {desired_output_format}\n\n"
    user_input += "Please provide the synthesized information in the requested format."

    try:
        response = client.responses.create(
            model=model,
            instructions=system_instructions,
            input=user_input,
        )
        return response.output_text
    except Exception as e:
        logger.error(f"Error calling OpenAI API for synthesize_information: {e}", exc_info=True)
        return f"Error during information synthesis: {str(e)}"

# List of all cognitive tools for easy import
cognitive_tools_list = [
    evaluate_plan_feasibility,
    identify_required_resources,
    analyze_potential_risks,
    break_down_complex_task,
    verify_step_completion,
    compare_alternative_approaches,
    synthesize_information,
]