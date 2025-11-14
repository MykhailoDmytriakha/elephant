# backend/src/services/problem_analyzer.py
from src.services.file_storage_service import FileStorageService
from src.services.openai_service import OpenAIService
from src.model.context import ContextSufficiencyResult, ClarifiedTask
from src.model.task import Task, TaskState
from src.model.scope import ScopeFormulationGroup, ScopeQuestion, DraftScope, ValidationScopeResult
from src.model.ifr import IFR, Requirements
from src.model.planning import NetworkPlan, Stage
from src.model.work import Work
from src.model.executable_task import ExecutableTask
from src.model.subtask import Subtask
import logging
from typing import List, Optional
from datetime import datetime
import json # Import json for potential logging needs

logger = logging.getLogger(__name__)

class ProblemAnalyzer:

    def __init__(self, openai_service: OpenAIService, storage_service: FileStorageService):
        self.openai_service = openai_service
        self.storage_service = storage_service

    async def clarify_context(self, task: Task, force: bool = False) -> ContextSufficiencyResult:
        """Initial context gathering method"""
        logger.info(f"Task {task.id}: Clarifying context (force={force}). Current state: {task.state}")

        if task.is_context_sufficient and not force:
            logger.info(f"Task {task.id}: Context already sufficient.")
            if task.state != TaskState.CONTEXT_GATHERED: # Only update if not already gathered
                 task.update_state(TaskState.CONTEXT_GATHERED)
                 # Task will be saved by calling code
            return ContextSufficiencyResult(is_context_sufficient=True, questions=[])

        if not force:
            task.update_state(TaskState.CONTEXT_GATHERING)
            # Maximum number of context elements (questions + answers) to prevent infinite loops
            # This limits the total accumulation of context_answers array elements
            max_context_answers = 20 # Consider making this configurable
            if task.context_answers and len(task.context_answers) >= max_context_answers:
                logger.warning(f"Task {task.id}: Force marking context sufficient after {len(task.context_answers)} accumulated context elements (limit: {max_context_answers}).")
                result = ContextSufficiencyResult(is_context_sufficient=True, questions=[])
            else:
                logger.info(f"Task {task.id}: Calling AI for context sufficiency analysis.")
                result = await self.openai_service.is_context_sufficient(task)
                logger.info(f"Task {task.id}: AI context sufficiency result: sufficient={result.is_context_sufficient}, questions asked={len(result.questions)}")

            if not result.is_context_sufficient:
                # Task will be saved by calling code # Save state change even if more questions needed
                return result
        else:
            logger.info(f"Task {task.id}: Forcing context sufficiency check bypass.")
            result = ContextSufficiencyResult(is_context_sufficient=True, questions=[]) # Assume sufficient on force

        # If context is sufficient (or forced)
        task.is_context_sufficient = True
        logger.info(f"Task {task.id}: Context deemed sufficient. Proceeding to summarize.")

        try:
            clarified_task = await self.openai_service.summarize_context(task)
            task.context = clarified_task.context
            task.task = clarified_task.task
            logger.info(f"Task {task.id}: Context summarized successfully.")
        except Exception as e:
            logger.error(f"Task {task.id}: Failed to summarize context: {e}", exc_info=True)
            # Decide how to handle summarization failure - perhaps proceed without summary?
            # For now, we'll still mark as gathered but log the error.
            task.context = task.context or "Context summarization failed." # Add a note

        task.update_state(TaskState.CONTEXT_GATHERED)
        # Task will be saved by calling code
        logger.info(f"Task {task.id}: State updated to {TaskState.CONTEXT_GATHERED}.")

        return result

    async def define_scope_question(self, task: Task, group: str) -> List[ScopeFormulationGroup]:
        logger.info(f"Task {task.id}: Defining scope questions for group '{group}'.")
        result_ai: List[ScopeQuestion] = await self.openai_service.formulate_scope_questions(task, group)
        result = [ScopeFormulationGroup(**question.model_dump(), group=group) for question in result_ai] # Use model_dump
        logger.info(f"Task {task.id}: Generated {len(result)} scope questions for group '{group}'.")
        return result

    async def generate_draft_scope(self, task: Task) -> DraftScope:
        logger.info(f"Task {task.id}: Generating draft scope.")
        draft_scope = await self.openai_service.generate_draft_scope(task)
        logger.info(f"Task {task.id}: Draft scope generated.")
        return draft_scope

    async def validate_scope(self, task: Task, feedback: str) -> ValidationScopeResult:
        logger.info(f"Task {task.id}: Validating scope with feedback.")
        validation_result = await self.openai_service.validate_scope(task, feedback)
        logger.info(f"Task {task.id}: Scope validation complete. Changes: {len(validation_result.changes)}")
        return validation_result

    async def generate_IFR(self, task: Task) -> IFR:
        logger.info(f"Task {task.id}: Generating IFR.")
        ifr = await self.openai_service.generate_IFR(task)
        logger.info(f"Task {task.id}: IFR generated.")
        return ifr

    async def define_requirements(self, task: Task) -> Requirements:
        logger.info(f"Task {task.id}: Defining requirements.")
        requirements = await self.openai_service.define_requirements(task)
        logger.info(f"Task {task.id}: Requirements defined.")
        return requirements

    async def generate_network_plan(self, task: Task) -> NetworkPlan:
        logger.info(f"Task {task.id}: Generating network plan.")
        network_plan = await self.openai_service.generate_network_plan(task)
        logger.info(f"Task {task.id}: Network plan generated with {len(network_plan.stages)} stages.")
        return network_plan

    async def generate_stage_work(self, task: Task, stage_id: str) -> List[Work]:
        """Generates Work packages for a specific stage and updates the task."""
        logger.info(f"Task {task.id}, Stage {stage_id}: Generating work packages.")

        if not task.network_plan or not task.network_plan.stages:
            logger.error(f"Task {task.id}: Network plan/stages missing for work generation.")
            raise ValueError("Network plan with stages must exist before generating work.")

        target_stage = next((s for s in task.network_plan.stages if s.id == stage_id), None)
        if not target_stage:
            logger.error(f"Task {task.id}: Stage {stage_id} not found.")
            raise ValueError(f"Stage ID {stage_id} not found in the network plan.")

        generated_work_packages = await self.openai_service.generate_work_for_stage(task, target_stage)
        if generated_work_packages is None: generated_work_packages = [] # Ensure list

        logger.info(f"Task {task.id}, Stage {stage_id}: AI generated {len(generated_work_packages)} work packages.")
        target_stage.work_packages = generated_work_packages
        # Task will be saved by calling code
        logger.info(f"Task {task.id}: Updated with work packages for Stage {stage_id}")
        return generated_work_packages

    async def generate_tasks_for_work(self, task: Task, stage_id: str, work_id: str) -> List[ExecutableTask]:
        """Generates ExecutableTask units for a specific Work package and updates the task."""
        logger.info(f"Task {task.id}, Stage {stage_id}, Work {work_id}: Generating executable tasks.")

        # --- Find Stage and Work (with validation) ---
        if not task.network_plan or not task.network_plan.stages:
            raise ValueError(f"Task {task.id}: Network plan/stages missing.")
        target_stage = next((s for s in task.network_plan.stages if s.id == stage_id), None)
        if not target_stage: raise ValueError(f"Stage {stage_id} not found.")
        if not target_stage.work_packages: raise ValueError(f"Stage {stage_id} has no work packages.")
        target_work = next((w for w in target_stage.work_packages if w.id == work_id), None)
        if not target_work: raise ValueError(f"Work {work_id} not found.")
        # --- End Finding ---

        generated_tasks = await self.openai_service.generate_tasks_for_work(task, target_stage, target_work)
        if generated_tasks is None: generated_tasks = [] # Ensure list

        logger.info(f"Task {task.id}, Stage {stage_id}, Work {work_id}: AI generated {len(generated_tasks)} tasks.")
        target_work.tasks = generated_tasks
        # Task will be saved by calling code
        logger.info(f"Task {task.id}: Updated with executable tasks for Work {work_id}")
        return generated_tasks

    async def generate_subtasks_for_executable_task(self, task: Task, stage_id: str, work_id: str, executable_task_id: str) -> List[Subtask]:
        """Generates Subtask units for a specific ExecutableTask and updates the task."""
        logger.info(f"Task {task.id}, Stage {stage_id}, Work {work_id}, ExecTask {executable_task_id}: Generating subtasks.")

        # --- Find Stage, Work, ExecutableTask (with validation) ---
        if not task.network_plan or not task.network_plan.stages:
            raise ValueError(f"Task {task.id}: Network plan/stages missing.")
        target_stage = next((s for s in task.network_plan.stages if s.id == stage_id), None)
        if not target_stage: raise ValueError(f"Stage {stage_id} not found.")
        if not target_stage.work_packages: raise ValueError(f"Stage {stage_id} has no work packages.")
        target_work = next((w for w in target_stage.work_packages if w.id == work_id), None)
        if not target_work: raise ValueError(f"Work {work_id} not found.")
        if not target_work.tasks: raise ValueError(f"Work {work_id} has no tasks.")
        target_executable_task = next((et for et in target_work.tasks if et.id == executable_task_id), None)
        if not target_executable_task: raise ValueError(f"ExecutableTask {executable_task_id} not found.")
         # --- End Finding ---

        generated_subtasks = await self.openai_service.generate_subtasks_for_executable_task(task, target_stage, target_work, target_executable_task)
        if generated_subtasks is None: generated_subtasks = [] # Ensure list

        logger.info(f"Task {task.id}, ..., ExecTask {executable_task_id}: AI generated {len(generated_subtasks)} subtasks.")
        target_executable_task.subtasks = generated_subtasks
        # Task will be saved by calling code
        logger.info(f"Task {task.id}: Updated with subtasks for ExecutableTask {executable_task_id}")
        return generated_subtasks

    async def edit_context_summary(self, task: Task, feedback: str) -> Task:
        """Edits the context summary and task description based on user feedback."""
        logger.info(f"Task {task.id}: Editing context summary with feedback.")
        
        # Call the OpenAI service to get the refined summary based on feedback
        # We assume the openai_service will have a method like summarize_context_with_feedback
        # or we adapt the existing summarize_context method
        try:
            # Use existing summarize_context and pass feedback
            # The AI agent needs to be adapted to handle this feedback parameter
            refined_clarified_task: ClarifiedTask = await self.openai_service.summarize_context(task, feedback=feedback)
            
            # Update the task object with the refined context and task description
            task.context = refined_clarified_task.context
            task.task = refined_clarified_task.task
            
            logger.info(f"Task {task.id}: Context summary refined successfully based on feedback.")
            
            # Save the updated task to the database
            # Task will be saved by calling code
            logger.info(f"Task {task.id}: Updated task saved to DB after context edit.")
            
            return task
            
        except Exception as e:
            logger.error(f"Task {task.id}: Failed to edit context summary: {e}", exc_info=True)
            # Re-raise or handle the error appropriately. 
            # For now, let's re-raise to signal failure to the API layer.
            # Consider adding a specific exception type if needed.
            raise Exception(f"Failed to process context feedback: {e}")