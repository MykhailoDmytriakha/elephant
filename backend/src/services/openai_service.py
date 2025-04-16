import logging
import functools
from typing import List, Optional
from src.model.context import ContextSufficiencyResult
from src.model.scope import ScopeQuestion
from openai import OpenAI
from src.core.config import settings
from src.model.task import Task
from src.model.context import ClarifiedTask
from src.model.scope import DraftScope, ValidationScopeResult
from src.ai_agents import context_sufficiency_agent, summarize_context_agent, scope_formulation_agent, ifr_agent, planning_agent, work_generation_agent, task_generation_agent, subtask_generation_agent
from src.model.ifr import IFR, Requirements
from src.model.planning import NetworkPlan, Stage
from src.model.work import Work
from src.model.executable_task import ExecutableTask
from src.model.subtask import Subtask

logger = logging.getLogger(__name__)

def _agent_call(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except ImportError as e:
            logger.warning(f"OpenAI Agents SDK not installed: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
    return wrapper

class OpenAIService:
    def __init__(self):
        logger.info("Initializing OpenAIService")
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        if not self.api_key:
            logger.error("OpenAI API key is not set!")
            raise ValueError("OpenAI API key is not set!")
        self.client = OpenAI(api_key=self.api_key)
    
    @_agent_call
    async def summarize_context(self, task: Task, feedback: Optional[str] = None) -> ClarifiedTask:
        """
        Summarizes the context of the task based on user answers about the context,
        optionally incorporating feedback to refine the summary.
        
        Args:
            task: The task containing the context information.
            feedback: Optional user feedback to guide the summarization/refinement.
            
        Returns:
            ClarifiedTask: Containing the summarized/refined task description and context.
        """
        if feedback:
            logger.info(f"Called summarize_context method with feedback for task {task.id}")
        else:
            logger.info(f"Called summarize_context method for task {task.id}")
            
        return await summarize_context_agent.summarize_context(task, feedback=feedback)

    
    @_agent_call
    async def is_context_sufficient(self, task: Task) -> ContextSufficiencyResult:
        """
        Determines if the gathered context is sufficient to understand and proceed with the task.
        
        Args:
            task: The task containing the context information
            
        Returns:
            ContextSufficiencyResult: Result indicating if context is sufficient and any follow-up questions with options
        """
        logger.info("Called is_context_sufficient method")
        
        return await context_sufficiency_agent.analyze_context_sufficiency(task)
            

    @_agent_call
    async def formulate_scope_questions(self, task: Task, group: str) -> List[ScopeQuestion]:
        """
        Formulate scope questions for a given group
        
        Args:
            task: The task containing the context information
            group: The group of scope questions to formulate
            
        Returns:
            List[ScopeQuestion]: List of scope questions
        """
        logger.info("Called formulate_scope_questions method")
        return await scope_formulation_agent.formulate_scope_questions(task, group)
    
    @_agent_call
    async def generate_draft_scope(self, task: Task) -> DraftScope:
        """
        Generate a draft scope for a given task
        
        Args:
            task: The task containing the context information
            
        Returns:
            str: Draft scope for the task
        """
        logger.info("Called generate_draft_scope method")
        return await scope_formulation_agent.generate_draft_scope(task)
    
    @_agent_call
    async def validate_scope(self, task: Task, feedback: str) -> ValidationScopeResult:
        """
        Validate the scope for a given task
        """
        logger.info("Called validate_scope method")
        return await scope_formulation_agent.validate_scope(task, feedback)
    
    @_agent_call
    async def generate_IFR(self, task: Task) -> IFR:
        """
        Generate an ideal final result for a given task
        """
        logger.info("Called generate_IFR method")
        return await ifr_agent.generate_IFR(task)
    
    @_agent_call
    async def define_requirements(self, task: Task) -> Requirements:
        """
        Define requirements for a given task
        """
        logger.info("Called define_requirements method")
        return await ifr_agent.define_requirements(task)
    
    @_agent_call
    async def generate_network_plan(self, task: Task) -> NetworkPlan:
        """
        Generate a network plan for a given task
        """
        logger.info("Called generate_network_plan method")
        return await planning_agent.generate_network_plan(task)
    
    @_agent_call
    async def generate_work_for_stage(self, task: Task, stage: Stage) -> List[Work]:
        """
        Generates a list of Work packages for a specific Stage.
        """
        logger.info(f"Called generate_work_for_stage for Stage ID: {stage.id}")
        return await work_generation_agent.generate_work_packages_for_stage(task, stage)

    @_agent_call
    async def generate_tasks_for_work(self, task: Task, stage: Stage, work: Work) -> List[ExecutableTask]:
        """
        Generates a list of ExecutableTask units for a specific Work package.
        """
        logger.info(f"Called generate_tasks_for_work for Work ID: {work.id}")
        return await task_generation_agent.generate_tasks_for_work(task, stage, work)
    
    @_agent_call
    async def generate_subtasks_for_executable_task(self, task: Task, stage: Stage, work: Work, executable_task: ExecutableTask) -> List[Subtask]:
        """
        Generates a list of Subtask units for a specific ExecutableTask.
        """
        logger.info(f"Called generate_subtasks_for_executable_task for ExecutableTask ID: {executable_task.id}")
        return await subtask_generation_agent.generate_subtasks(task, stage, work, executable_task)