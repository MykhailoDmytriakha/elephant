from .database_service import DatabaseService
from src.services.openai_service import OpenAIService
from src.model.context import ContextSufficiencyResult
from src.model.task import Task, TaskState
from src.model.scope import ScopeFormulationGroup, ScopeQuestion, DraftScope, ValidationScopeResult
from src.model.ifr import IFR, Requirements
from src.model.planning import NetworkPlan, Stage
from src.model.work import Work
from src.model.executable_task import ExecutableTask
import logging
from typing import List, Optional
from datetime import datetime
logger = logging.getLogger(__name__)

class ProblemAnalyzer:

    def __init__(self, openai_service: OpenAIService, db_service: DatabaseService):
        self.openai_service = openai_service
        self.db_service = db_service

    async def clarify_context(self, task: Task, force: bool = False) -> ContextSufficiencyResult:
        """Initial context gathering method"""
        
        if task.is_context_sufficient and not force:
            logger.info(f"Task is already in the context gathered state. Current state: {task.state}")
            task.update_state(TaskState.CONTEXT_GATHERED)
            return ContextSufficiencyResult(
                is_context_sufficient=True,
                questions=[]
            )
        
        if not force:
            task.update_state(TaskState.CONTEXT_GATHERING)
            max_question_rounds = 20
            if task.context_answers and len(task.context_answers) >= max_question_rounds:
                logger.info(f"Force marking context as sufficient after {len(task.context_answers)} rounds of questions")
                result = ContextSufficiencyResult(is_context_sufficient=True, questions=[])
            else:
                result = await self.openai_service.is_context_sufficient(task)

            if not result.is_context_sufficient:
                return result
        else:
            result = ContextSufficiencyResult(is_context_sufficient=True, questions=[])
        
        # If context is sufficient
        task.is_context_sufficient = True
        

        clarified_task = await self.openai_service.summarize_context(task)
        task.context = clarified_task.context
        task.task = clarified_task.task
        
        task.update_state(TaskState.CONTEXT_GATHERED)
        self.db_service.updated_task(task)
        
        # After context is gathered, process it to formulate the task
        return result

    async def define_scope_question(self, task: Task, group: str) -> List[ScopeFormulationGroup]:
        # define scope based on gathered context
        # Use OpenAI service to get suggestions based on the context
        result_ai: List[ScopeQuestion] = await self.openai_service.formulate_scope_questions(task, group)
        
        # Convert questions to ScopeFormulationGroup using list comprehension
        result = [ScopeFormulationGroup(**question.__dict__, group=group) for question in result_ai]
        return result
    
    async def generate_draft_scope(self, task: Task) -> DraftScope:
        draft_scope = await self.openai_service.generate_draft_scope(task)
        return draft_scope
    
    async def validate_scope(self, task: Task, feedback: str) -> ValidationScopeResult:
        validation_result = await self.openai_service.validate_scope(task, feedback)
        return validation_result

    async def generate_IFR(self, task: Task) -> IFR:
        ifr = await self.openai_service.generate_IFR(task)
        return ifr
    
    async def define_requirements(self, task: Task) -> Requirements:
        requirements = await self.openai_service.define_requirements(task)
        return requirements
    
    async def generate_network_plan(self, task: Task) -> NetworkPlan:
        network_plan = await self.openai_service.generate_network_plan(task)
        return network_plan
    
    async def generate_stage_work(self, task: Task, stage_id: str) -> List[Work]:
        """
        Generates Work packages for a specific stage and updates the task.
        """
        logger.info(f"Generating work for Task {task.id}, Stage {stage_id}")

        if not task.network_plan or not task.network_plan.stages:
            logger.error(f"Task {task.id} does not have a network plan or stages.")
            raise ValueError("Network plan with stages must exist before generating work.")

        # Find the target stage
        target_stage: Optional[Stage] = None
        for stage in task.network_plan.stages:
            if stage.id == stage_id:
                target_stage = stage
                break

        if not target_stage:
            logger.error(f"Stage with ID {stage_id} not found in Task {task.id}'s network plan.")
            raise ValueError(f"Stage ID {stage_id} not found in the network plan.")

        # Call the AI service to generate work packages
        generated_work_packages = await self.openai_service.generate_work_for_stage(task, target_stage)

        if not generated_work_packages:
             logger.warning(f"AI service returned no work packages for Stage {stage_id}.")
             # Decide if this is an error or just an empty list case
             # For now, let's treat it as potentially valid (maybe the stage is simple)
             # but update the task anyway
             generated_work_packages = []


        # Update the stage within the task object
        target_stage.work_packages = generated_work_packages

        # Save the updated task back to the database
        self.db_service.updated_task(task)
        logger.info(f"Updated Task {task.id} with {len(generated_work_packages)} work packages for Stage {stage_id}")

        return generated_work_packages
    
    async def generate_tasks_for_work(self, task: Task, stage_id: str, work_id: str) -> List[ExecutableTask]:
        """
        Generates ExecutableTask units for a specific Work package and updates the task.
        """
        logger.info(f"Generating ExecutableTasks for Task {task.id}, Stage {stage_id}, Work {work_id}")

        if not task.network_plan or not task.network_plan.stages:
            logger.error(f"Task {task.id} does not have a network plan or stages.")
            raise ValueError("Network plan with stages must exist before generating tasks.")

        # Find Stage
        target_stage: Optional[Stage] = next((s for s in task.network_plan.stages if s.id == stage_id), None)
        if not target_stage:
            logger.error(f"Stage {stage_id} not found in Task {task.id}.")
            raise ValueError(f"Stage ID {stage_id} not found.")

        # Find Work package
        if not target_stage.work_packages:
             logger.error(f"Stage {stage_id} has no work packages defined.")
             raise ValueError(f"Work packages not generated for Stage {stage_id}.")

        target_work: Optional[Work] = next((w for w in target_stage.work_packages if w.id == work_id), None)
        if not target_work:
            logger.error(f"Work package {work_id} not found in Stage {stage_id}.")
            raise ValueError(f"Work package ID {work_id} not found.")

        # Call the AI service
        generated_tasks = await self.openai_service.generate_tasks_for_work(task, target_stage, target_work)

        if generated_tasks is None: # Explicitly check for None
             logger.warning(f"AI service returned None for executable tasks for Work {work_id}.")
             generated_tasks = []
        elif not isinstance(generated_tasks, list):
             logger.error(f"AI service returned non-list for executable tasks: {type(generated_tasks)}")
             generated_tasks = []


        # Update the work package within the task object
        target_work.tasks = generated_tasks

        # Save the updated task back to the database
        self.db_service.updated_task(task)
        logger.info(f"Updated Task {task.id}, Stage {stage_id}, Work {work_id} with {len(generated_tasks)} executable tasks.")

        return generated_tasks