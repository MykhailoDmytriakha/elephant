import logging
from src.core.config import settings
from src.model.task import Task
from src.model.planning import NetworkPlan, Stage, Connection
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from src.ai_agents.utils import detect_language, get_language_instruction

logger = logging.getLogger(__name__)

# Try to import the OpenAI Agents SDK
try:
    from agents import Agent, Runner, handoff, function_tool, RunContextWrapper  # type: ignore # noqa
    model = settings.OPENAI_MODEL
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI Agents SDK not installed. Some functionality will be limited.")
    AGENTS_SDK_AVAILABLE = False
if not AGENTS_SDK_AVAILABLE:
    logger.error("OpenAI Agents SDK not installed.")
    raise ImportError("OpenAI Agents SDK not installed. Please install with `pip install openai-agents`")

class PlanningContext(BaseModel):
    """
    Class to maintain context and history between agent interactions during planning.
    """
    task: Task
    history: List[Dict[str, Any]] = Field(exclude=True)
    last_updated_plan: Optional[NetworkPlan] = Field(default=None, exclude=True)
    critic_feedback: Optional[str] = Field(default=None, exclude=True)
    iteration: int = Field(exclude=True)
    next_agent: str | None = Field(default=None, exclude=True)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "properties": {
                "task": {"description": "The task to be planned"}
            },
            "required": ["task"]
        }
    )
    
    def __init__(self, **data):
        if "history" not in data:
            data["history"] = []
        if "iteration" not in data:
            data["iteration"] = 0
        super().__init__(**data)
    
    def add_to_history(self, agent_name: str, content: Any) -> None:
        """Add an interaction to the history"""
        self.history.append({
            "agent": agent_name,
            "content": content,
            "iteration": self.iteration
        })
        
    def update_plan(self, plan: NetworkPlan) -> None:
        """Update the current plan"""
        self.last_updated_plan = plan
        
    def next_iteration(self) -> None:
        """Move to the next iteration"""
        self.iteration += 1
        
    def get_history_summary(self) -> str:
        """Get a formatted summary of the history"""
        summary = f"\033[32m History (Total Iterations: {self.iteration}):\033[0m\n"
        for entry in self.history:
            summary += f"- {entry['agent']} (Iteration {entry['iteration']}): "
            if isinstance(entry['content'], str):
                summary += f"{entry['content']}...\n"
            else:
                summary += f"[Object]: {entry['content'].model_dump_json()}\n"
        return summary

# Define the Creator Agent
creator_agent = Agent(
    name="CreatorAgent",
    instructions=(
        "Generate an initial plan based on the task description."
        "The plan should be a network plan (decomposed into stages). Stage is upper level of the plan."
        "Each stage should have a description (minimum of 200 characters) and a list of checkpoints (3-7 checkpoints per stage). Checkpoint (checkmark) responsible for validation of the stage (like result, what was achieved, etc)."
        "Each checkpoint should have a description and a list of validations. Validation is a process that can be performed to proofe that the checkpoint is achieved."
        "IMPORTANT: Create this plan with the understanding that all intellectual and physical work will be performed through automation without human intervention. However, DO NOT explicitly mention AI, ML, or robots in task descriptions."
        "Tasks should be formulated neutrally (e.g., 'perform analysis', 'generate report', 'conduct tests', 'assemble component') without specifying who/what will perform them."
        "Usually after a stage is completed, we have physical or digital artifacts that can be used to proofe that the result is achieved. Artifact is a physical or digital object that repesents the result of the stage. Artifacts has a location."
        "Atifact should have a type, like document, software, website, etc. mentioned in the artifact description."
        "So each checkpoint should have a description of the artifact that proves that the result is achieved and a list of validations (at least 5) that were performed to proofe that the result is achieved."
        "The artifact can be a physical object, a document, a software, a website, etc."
        "The location of the artifact can be a physical place, a digital place, etc."
        "Each stage should have a list of results (at least 5) that are achieved by the stage. Result is a short description of what was achieved by the stage. It's like growing process of final result. We're descibing how it will look like at the end of the stage."
        "Each stage should have a list of what should be delivered after the stage is completed (at least 5). What should be delivered is a list of CONCRETE TANGIBLE ARTIFACTS that remain after the stage is completed - not abstract concepts or outcomes, but SPECIFIC physical or digital items with clear locations."
        "For example, if it's a software development stage → source code repository, database schema files, API documentation, deployment configuration, test suite; if it's construction → foundation, architectural drawings, building permits, inspection certificates, material receipts; if it's research → data collection spreadsheets, analysis reports, visualization graphs, literature review document, experiment logs."
        "Each item in 'what_should_be_delivered' must specify: 1) what the artifact is, 2) its type (document, software, physical object, etc.), and 3) where it's located (repository, database, file system, physical location)."
        "Location Standardization requirement, define a fixed set of approved location names and use them across references accordingly."
        "Avoid any phrases implying human involvement like 'talk to experts', 'gather stakeholder feedback', or 'discuss with team'. Instead, use phrases like 'analyze data', 'compile requirements', or 'generate documentation'."
        "Tasks should be specific enough to be automated but without specifying that automation technology will perform them."
        "Include appropriate validation methods and quality checks that are measurable and objective."
        "And pass it to the CriticAgent."
    ),
    model = model,
    output_type=NetworkPlan
)

class ValidationResult(BaseModel):
    """Result of the validation process"""
    feedback: str
    score: int
    is_plan_need_improvement: bool
# Define the Critic Agent
critic_agent = Agent(
    name="CriticAgent",
    instructions=(
        "Critique the provided plan, highlighting potential issues and suggesting improvements related to the NetworkPlan structure. "
        "Focus ONLY on the stages and connections in the NetworkPlan object. "
        "IMPORTANT: The plan should be designed for full automation without human intervention, but task descriptions should NOT explicitly mention AI systems, ML algorithms, or robots as performers."
        "Check that task descriptions are formulated neutrally (e.g., 'perform analysis', 'generate report', 'conduct tests') without specifying who/what will perform them."
        "Ensure there is no language implying human involvement like 'talk to experts', 'gather stakeholder feedback', or 'discuss with team'."
        "A NetworkPlan contains: stages (id, name, description, checkpoints) and connections (stage1, stage2). "
        "Evaluate if the stages are clear, well-defined, and have appropriate descriptions. "
        "Assess if the connections between stages are logical and represent proper dependencies. "
        "Evaluate if the checkpoints are clear, well-defined, and have appropriate descriptions. "
        "Evaluate if the validations are clear, well-defined, and appropriate for automated verification without explicitly mentioning automation technologies. "
        "Evaluate if the artifact is well-defined, and if it's physical or digital. "
        "Evaluate if the location is well-defined, and if it's physical or digital. "
        "IMPORTANT: Check that artifact locations are standardized and consistent across all stages using only the designated location names. "
        "DO NOT critique anythink that ARE NOT explicitly part of the NetworkPlan structure. "
        "Keep your critique concise and focused only on improving the NetworkPlan object structure."
        "COMPREHENSIVE VALIDATION CRITERIA:"
        "1. Check that each checkpoint has at least 5 detailed validations as required"
        "2. Verify that all artifact locations use ONLY the standardized location names"
        "3. Ensure artifact types (document, software, etc.) are consistently specified"
        "4. Confirm that stage connections create a logical dependency sequence"
        "5. Validate that each stage has an appropriate number of checkpoints (3-7)"
        "6. Ensure descriptions are detailed and actionable (minimum 200 characters)"
        "7. Check that validations are specific, measurable, and achievable through automation without explicitly mentioning automated systems"
        "8. Verify that artifacts clearly represent tangible deliverables"
        "9. Verify that each 'what_should_be_delivered' item is a CONCRETE TANGIBLE ARTIFACT (not an abstract concept), specifying: 1) what it is, 2) its type (document, software, physical object, etc.), and 3) its specific location"
        "10. Ensure all 'what_should_be_delivered' items are specific physical or digital artifacts that would actually remain after stage completion"
        "11. Ensure the plan has sufficient breadth and depth for the task"
        "12. Check for consistency in terminology and naming conventions"
        "13. Ensure no task descriptions explicitly mention AI systems, ML algorithms, or robots as performers"
        "Evaluate the overall plan quality against a 10-point quality scale based on these criteria. Put the score at the end of the feedback."
    ),
    model = model,
    output_type=ValidationResult
)

# Tool 1: Create Plan
@function_tool
def create_plan(wrapper: RunContextWrapper[PlanningContext]) -> NetworkPlan:
    """
    Generate an initial network plan based on the task description and context.
    
    Args:
        task_id: The identifier of the task in the current planning context
    """
    logger.info(f"\033[32m Creator: Creating plan\033[0m")
    # We'll use a global context that's maintained by the triage agent
    context = wrapper.context
    if not context:
        raise ValueError("No planning context available")
    
    context.next_iteration()
    logger.info(f"\033[32m Creator: Next iteration: {context.iteration}\033[0m")
    if context.iteration == 3:
        logger.info(f"\033[31m Creator:\033[0m It's last iteration. After generating the plan, we'll return it.")
        
    # Detect language from task description
    user_language = detect_language(context.task.short_description or "")
    # logger.info(f"Detected language: {user_language}")
    language_instruction = get_language_instruction(user_language)
    
    if context.last_updated_plan is None:
        prompt = f"""
        TASK DETAILS:
        Task: {context.task.task}
        Context: {context.task.context}
        Scope: {context.task.scope.scope}
        IFR: {context.task.ifr.ideal_final_result}
        Success criteria: {"\n- ".join(context.task.ifr.success_criteria)}
        Expected outcomes: {"\n- ".join(context.task.ifr.expected_outcomes)}
        Requerements: {"\n- ".join(context.task.requirements.requirements)}
        Constraints: {"\n- ".join(context.task.requirements.constraints)}
        Limitations: {"\n- ".join(context.task.requirements.limitations)}
        Resources: {"\n- ".join(context.task.requirements.resources)}
        Tools: {"\n- ".join(context.task.requirements.tools)}
        Definitions: {"\n- ".join(context.task.requirements.definitions)}
        ---
        {language_instruction}
        
        Generate network plan for the task.
        """
    else:
        prompt = f"""
        TASK DETAILS:
        Task: {context.task.task}
        Context: {context.task.context}
        Scope: {context.task.scope.scope}
        IFR: {context.task.ifr.ideal_final_result}
        Success criteria: {"\n- ".join(context.task.ifr.success_criteria)}
        Expected outcomes: {"\n- ".join(context.task.ifr.expected_outcomes)}
        Requerements: {"\n- ".join(context.task.requirements.requirements)}
        Constraints: {"\n- ".join(context.task.requirements.constraints)}
        Limitations: {"\n- ".join(context.task.requirements.limitations)}
        Resources: {"\n- ".join(context.task.requirements.resources)}
        Tools: {"\n- ".join(context.task.requirements.tools)}
        Definitions: {"\n- ".join(context.task.requirements.definitions)}
        ---
        PREVIOUS PLAN: {context.last_updated_plan.model_dump_json()}
        ---
        CRITIC FEEDBACK: {context.critic_feedback}
        ---
        
        {language_instruction}
        
        Please generate an improved network plan taking into account the TASK DETAILS, PREVIOUS PLAN, and CRITIC FEEDBACK.
        """
    
    result = Runner.run_sync(creator_agent, prompt)
    result = result.final_output
    context.add_to_history("CreatorAgent", result)
    context.update_plan(result)
    context.next_agent = "CriticAgent"
    logger.info(f"\033[31m Creator:\033[0m Network plan: {result}")
    return result

# Tool 2: Critic Plan
@function_tool
def critic_plan(wrapper: RunContextWrapper[PlanningContext]) -> str:
    """
    Critique the provided plan, highlighting potential issues and suggesting improvements.
    """
    logger.info(f"\033[32m Critic: Critiquing plan\033[0m")
    # We'll use a global context that's maintained by the triage agent
    context = wrapper.context
    if not context:
        raise ValueError("No planning context available")
    
    if not context.last_updated_plan:
        raise ValueError("No plan available in context to critique")
    
    # Detect language from task description
    user_language = detect_language(context.task.short_description or "")
    # logger.info(f"Detected language: {user_language}")
    language_instruction = get_language_instruction(user_language)
    
    prompt = f"""
    TASK DETAILS:
    Task: {context.task.task}
    Context: {context.task.context}
    Scope: {context.task.scope.scope}
    IFR: {context.task.ifr.ideal_final_result}
    Success criteria: {"\n- ".join(context.task.ifr.success_criteria)}
    Expected outcomes: {"\n- ".join(context.task.ifr.expected_outcomes)}
    Requerements: {"\n- ".join(context.task.requirements.requirements)}
    Constraints: {"\n- ".join(context.task.requirements.constraints)}
    Limitations: {"\n- ".join(context.task.requirements.limitations)}
    Resources: {"\n- ".join(context.task.requirements.resources)}
    Tools: {"\n- ".join(context.task.requirements.tools)}
    Definitions: {"\n- ".join(context.task.requirements.definitions)}
    ---
    Critique the following plan: {context.last_updated_plan.model_dump_json()}
    ---
    {language_instruction}
    
    Remember to focus ONLY on the NetworkPlan structure (stages, checkpoints and connections). Do not critique implementation details, 
    methodologies, or features that aren't explicitly part of the NetworkPlan object.
    Think about number of stages and connections, names of stages, descriptions of stages, and connections between stages, checkpoints, artifacts, locations and validations.
    """
    result = Runner.run_sync(critic_agent, prompt)
    result = result.final_output
    context.add_to_history("CriticAgent", result.feedback)
    context.critic_feedback = result.feedback
    
    if result.is_plan_need_improvement or result.score < 8:
        logger.info(f"\033[31m Critic:\033[0m Plan is not good enough. Routing to CreatorAgent")
        context.next_agent = "CreatorAgent"
    else:
        logger.info(f"\033[31m Critic:\033[0m Plan is good enough. Returning plan")
        context.next_agent = None
    logger.info(f"\033[31m Critic:\033[0m {result}")
    return result

@function_tool
def what_tool_to_call_next(wrapper: RunContextWrapper[PlanningContext]):
    """
    Route the task to the appropriate agent
    
    Returns:
        A direct reference to the exact tool that must be called next, or clear instruction 
        if the planning process is complete
    """
    logger.info(f"\033[32m Triage:\033[0m Determining what tool to call next")
    context = wrapper.context
    if not context:
        raise ValueError("No planning context available")
    
    if context.iteration == 0:
        logger.info(f"\033[31m Triage:\033[0m Routing to CreatorAgent for the first time")
        return create_plan  # Return direct function reference
    elif context.iteration == 3: 
        logger.info(f"\033[31m Triage:\033[0m Reached max iterations")
        return "STOP_AND_RETURN_PLAN"  # Clear terminal instruction
    elif context.next_agent == "CreatorAgent":
        logger.info(f"\033[31m Triage:\033[0m Routing to CreatorAgent")
        return create_plan  # Return direct function reference
    elif context.next_agent == "CriticAgent":
        logger.info(f"\033[31m Triage:\033[0m Routing to CriticAgent")
        return critic_plan  # Return direct function reference
    else:
        logger.info(f"\033[31m Triage:\033[0m No routing agent found")
        return "STOP_AND_RETURN_PLAN"  # Clear terminal instruction

triage_agent = Agent(
    name="TriageAgent",
    instructions=(
        "You are orchestrating a workflow between specialized agents to generate a network plan. "
        "Call the `what_tool_to_call_next` tool to determine which tool to call next."
        "The `what_tool_to_call_next` tool will return either:"
        "1. A direct reference to a function that MUST be called next (create_plan or critic_plan)"
        "2. A 'STOP_AND_RETURN_PLAN' instruction indicating that planning is complete"
        "IMPORTANT: After calling any tool and getting its result, you MUST ALWAYS explicitly call `what_tool_to_call_next` again to determine the next step. Never proceed to another tool without first calling `what_tool_to_call_next`."
        "Follow this exact pattern: 1) Call what_tool_to_call_next, 2) Call the exact tool it returns if it's a function, or finish if it returns STOP_AND_RETURN_PLAN, 3) Call what_tool_to_call_next again, 4) Repeat."
        "You have NO DISCRETION in tool selection - you must call EXACTLY the tool returned by what_tool_to_call_next."
    ),
    model = 'gpt-4o-mini',
    tools=[what_tool_to_call_next, create_plan, critic_plan]
)

async def generate_network_plan(
    task: Task,
) -> NetworkPlan:
    """
    Generates a hierarchical network plan.
    
    This approach creates a structured network diagram where:
    - Stages (represented as nodes/circles) define major project milestones
    
    Args:
        task: The task containing all scope and IFR information
        
    Returns:
        NetworkPlan: A complete hierarchical project plan with stages and connections
    """
    
    # Create a context to maintain state between agents
    context = PlanningContext(task=task)
    
    # Pass the context to the triage agent
    try:
        logger.info(f"Starting network plan generation for task: {task.id}")
        result = await Runner.run(
            triage_agent, 
            f"call the `what_tool_to_call_next` tool to determine which tool to call next.",
            context=context,
            max_turns=30
        )
    except Exception as e:
        logger.error(f"Error generating network plan: {e}")
        if context.last_updated_plan:
            logger.info(f"BACKUP: Returning last stored plan: {context.last_updated_plan}")
            result = context.last_updated_plan
            logger.info(f"BACKUP: Final network plan: {result}")
            return result
        else:
            raise e
    
    result = result.final_output
    # logger.info(f"History: {context.get_history_summary()}")
    logger.info(f"Final network plan: {context.last_updated_plan}")
    logger.info(f"It takes {context.iteration} iterations to generate the plan")
    logger.info(f"final_output: {result}")
    if context.last_updated_plan:
        return context.last_updated_plan
    raise Exception("No plan generated")