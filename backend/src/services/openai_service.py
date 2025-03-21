import logging
from typing import List
from src.model.context import ContextSufficiencyResult
from src.model.scope import ScopeQuestion
from openai import OpenAI
from src.core.config import settings
from src.model.task import Task
from src.model.context import ClarifiedTask
from src.model.scope import DraftScope, ValidationScopeResult
from src.ai_agents import context_sufficiency_agent, summarize_context_agent, scope_formulation_agent, ifr_agent, planning_agent
from src.model.ifr import IFR, Requirements
from src.model.planning import NetworkPlan

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        logger.info("Initializing OpenAIService")
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        if not self.api_key:
            logger.error("OpenAI API key is not set!")
            raise ValueError("OpenAI API key is not set!")
        self.client = OpenAI(api_key=self.api_key)
    
    async def summarize_context(self, task: Task) -> ClarifiedTask:
        """
        Summarizes the context of the task base on user answers about the context.
        
        Args:
            task: The task containing the context information
            
        Returns:
            str: Summary of the context
        """
        logger.info("Called summarize_context method")
        try:
            # Use the extracted agent logic from the dedicated module
            return await summarize_context_agent.summarize_context(task)
        except ImportError as e:
            logger.warning(f"OpenAI Agents SDK not installed: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Error in summarize_context: {str(e)}")
            raise e

    
    async def is_context_sufficient(self, task: Task) -> ContextSufficiencyResult:
        """
        Determines if the gathered context is sufficient to understand and proceed with the task.
        
        Args:
            task: The task containing the context information
            
        Returns:
            ContextSufficiencyResult: Result indicating if context is sufficient and any follow-up questions with options
        """
        logger.info("Called is_context_sufficient method")
        
        try:
            # Use the extracted agent logic from the dedicated module
            return await context_sufficiency_agent.analyze_context_sufficiency(task)
        except ImportError as e:
            logger.warning(f"OpenAI Agents SDK not installed: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Error in is_context_sufficient: {str(e)}")
            raise e
            

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
        try:
            # Use the extracted agent logic from the dedicated module
            return await scope_formulation_agent.formulate_scope_questions(task, group)
        except ImportError as e:
            logger.warning(f"OpenAI Agents SDK not installed: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Error in formulate_scope_questions: {str(e)}")
            raise e
    
    async def generate_draft_scope(self, task: Task) -> DraftScope:
        """
        Generate a draft scope for a given task
        
        Args:
            task: The task containing the context information
            
        Returns:
            str: Draft scope for the task
        """
        logger.info("Called generate_draft_scope method")
        try:
            # Use the extracted agent logic from the dedicated module
            return await scope_formulation_agent.generate_draft_scope(task)
        except ImportError as e:
            logger.warning(f"OpenAI Agents SDK not installed: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Error in generate_draft_scope: {str(e)}")
            raise e
    
    async def validate_scope(self, task: Task, feedback: str) -> ValidationScopeResult:
        """
        Validate the scope for a given task
        """
        logger.info("Called validate_scope method")
        try:
            # Use the extracted agent logic from the dedicated module
            return await scope_formulation_agent.validate_scope(task, feedback)
        except ImportError as e:
            logger.warning(f"OpenAI Agents SDK not installed: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Error in validate_scope: {str(e)}")
            raise e
    
    async def generate_IFR(self, task: Task) -> IFR:
        """
        Generate an ideal final result for a given task
        """
        logger.info("Called generate_IFR method")
        try:
            # Use the extracted agent logic from the dedicated module
            return await ifr_agent.generate_IFR(task)
        except ImportError as e:
            logger.warning(f"OpenAI Agents SDK not installed: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Error in generate_IFR: {str(e)}")
            raise e
    
    async def define_requirements(self, task: Task) -> Requirements:
        """
        Define requirements for a given task
        """
        logger.info("Called define_requirements method")
        try:
            # Use the extracted agent logic from the dedicated module
            return await ifr_agent.define_requirements(task)
        except ImportError as e:
            logger.warning(f"OpenAI Agents SDK not installed: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Error in define_requirements: {str(e)}")
            raise e
    
    async def generate_network_plan(self, task: Task) -> NetworkPlan:
        """
        Generate a network plan for a given task
        """
        logger.info("Called generate_network_plan method")
        try:
            # Use the extracted agent logic from the dedicated module
            return await planning_agent.generate_network_plan(task)
        except ImportError as e:
            logger.warning(f"OpenAI Agents SDK not installed: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Error in generate_network_plan: {str(e)}")
            raise e