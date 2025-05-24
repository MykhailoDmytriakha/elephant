"""
Task Generation Service

Encapsulates all logic for generating work packages, executable tasks, and subtasks.
Provides a clean service layer between routes and the problem analyzer.
"""

import logging
from typing import List, Optional, cast

# Model imports
from src.model.task import Task
from src.model.planning import Stage, NetworkPlan
from src.model.work import Work
from src.model.executable_task import ExecutableTask
from src.model.subtask import Subtask

# Service imports
from src.services.problem_analyzer import ProblemAnalyzer
from src.services.database_service import DatabaseService

# Utility imports
from src.api.utils import find_stage_by_id, find_work_package_by_id, find_executable_task_by_id
from src.api.validators import TaskValidator, NetworkPlanValidator, StageValidator, WorkValidator

logger = logging.getLogger(__name__)


class TaskGenerationService:
    """Service for generating tasks at various levels of the hierarchy"""
    
    def __init__(self, analyzer: ProblemAnalyzer, db: DatabaseService):
        """
        Initialize the task generation service.
        
        Args:
            analyzer: Problem analyzer for AI-powered generation
            db: Database service for persistence
        """
        self.analyzer = analyzer
        self.db = db
    
    async def generate_work_for_stage(self, task: Task, stage_id: str) -> List[Work]:
        """
        Generate work packages for a specific stage.
        
        Args:
            task: The task containing the stage
            stage_id: ID of the stage to generate work for
            
        Returns:
            List of generated work packages
            
        Raises:
            MissingComponentException: If task lacks network plan
            StageNotFoundException: If stage is not found
        """
        logger.info(f"Generating work packages for stage {stage_id} in task {task.id}")
        
        # Find the stage
        stage = find_stage_by_id(task, stage_id)
        
        # Generate work packages using the analyzer
        work_packages = await self.analyzer.generate_work_for_stage(task, stage)
        
        # Update the stage with the generated work packages
        stage.work_packages = work_packages
        
        # Save the updated task
        self.db.updated_task(task)
        
        logger.info(f"Generated {len(work_packages)} work packages for stage {stage_id}")
        return work_packages
    
    async def generate_work_for_all_stages(self, task: Task) -> NetworkPlan:
        """
        Generate work packages for all stages in the task's network plan.
        
        Args:
            task: The task to generate work packages for
            
        Returns:
            Updated network plan with work packages
            
        Raises:
            MissingComponentException: If task lacks network plan or stages
        """
        logger.info(f"Generating work packages for all stages in task {task.id}")
        
        # Validate task has network plan
        TaskValidator.validate_task_network_plan(task, task.id)
        network_plan = cast(NetworkPlan, task.network_plan)
        
        # Validate network plan has stages
        if not NetworkPlanValidator.has_stages(network_plan):
            raise MissingComponentException(f"Task {task.id} network plan has no stages")
        
        stages = cast(List[Stage], network_plan.stages)
        total_generated = 0
        
        # Generate work packages for each stage
        for stage in stages:
            logger.info(f"Generating work packages for stage {stage.id}")
            
            work_packages = await self.analyzer.generate_work_for_stage(task, stage)
            stage.work_packages = work_packages
            total_generated += len(work_packages)
            
            logger.info(f"Generated {len(work_packages)} work packages for stage {stage.id}")
        
        # Save the updated task
        self.db.updated_task(task)
        
        logger.info(f"Generated total of {total_generated} work packages across all stages")
        return network_plan
    
    async def generate_tasks_for_work(self, task: Task, stage_id: str, work_id: str) -> List[ExecutableTask]:
        """
        Generate executable tasks for a specific work package.
        
        Args:
            task: The task containing the work package
            stage_id: ID of the stage containing the work package
            work_id: ID of the work package to generate tasks for
            
        Returns:
            List of generated executable tasks
            
        Raises:
            StageNotFoundException: If stage is not found
            WorkNotFoundException: If work package is not found
        """
        logger.info(f"Generating tasks for work {work_id} in stage {stage_id} of task {task.id}")
        
        # Find the stage and work package
        stage = find_stage_by_id(task, stage_id)
        work_package = find_work_package_by_id(stage, work_id)
        
        # Generate executable tasks using the analyzer
        executable_tasks = await self.analyzer.generate_tasks_for_work(task, stage, work_package)
        
        # Update the work package with the generated tasks
        work_package.tasks = executable_tasks
        
        # Save the updated task
        self.db.updated_task(task)
        
        logger.info(f"Generated {len(executable_tasks)} executable tasks for work {work_id}")
        return executable_tasks
    
    async def generate_tasks_for_all_works_in_stage(self, task: Task, stage_id: str) -> List[Work]:
        """
        Generate executable tasks for all work packages in a stage.
        
        Args:
            task: The task containing the stage
            stage_id: ID of the stage to generate tasks for
            
        Returns:
            List of updated work packages with generated tasks
            
        Raises:
            StageNotFoundException: If stage is not found
            MissingComponentException: If stage has no work packages
        """
        logger.info(f"Generating tasks for all work packages in stage {stage_id} of task {task.id}")
        
        # Find the stage
        stage = find_stage_by_id(task, stage_id)
        
        # Validate stage has work packages
        if not StageValidator.has_work_packages(stage):
            raise MissingComponentException(f"Stage {stage_id} has no work packages")
        
        work_packages = cast(List[Work], stage.work_packages)
        total_generated = 0
        
        # Generate tasks for each work package
        for work_package in work_packages:
            logger.info(f"Generating tasks for work package {work_package.id}")
            
            executable_tasks = await self.analyzer.generate_tasks_for_work(task, stage, work_package)
            work_package.tasks = executable_tasks
            total_generated += len(executable_tasks)
            
            logger.info(f"Generated {len(executable_tasks)} tasks for work package {work_package.id}")
        
        # Save the updated task
        self.db.updated_task(task)
        
        logger.info(f"Generated total of {total_generated} tasks for stage {stage_id}")
        return work_packages
    
    async def generate_tasks_for_all_stages(self, task: Task) -> NetworkPlan:
        """
        Generate executable tasks for all work packages in all stages.
        
        Args:
            task: The task to generate tasks for
            
        Returns:
            Updated network plan with generated tasks
            
        Raises:
            MissingComponentException: If task lacks network plan or stages
        """
        logger.info(f"Generating tasks for all stages in task {task.id}")
        
        # Validate task has network plan
        TaskValidator.validate_task_network_plan(task, task.id)
        network_plan = cast(NetworkPlan, task.network_plan)
        
        # Validate network plan has stages
        if not NetworkPlanValidator.has_stages(network_plan):
            raise MissingComponentException(f"Task {task.id} network plan has no stages")
        
        stages = cast(List[Stage], network_plan.stages)
        total_generated = 0
        
        # Generate tasks for each stage
        for stage in stages:
            if not StageValidator.has_work_packages(stage):
                logger.warning(f"Stage {stage.id} has no work packages, skipping")
                continue
            
            work_packages = cast(List[Work], stage.work_packages)
            
            # Generate tasks for each work package in the stage
            for work_package in work_packages:
                logger.info(f"Generating tasks for work package {work_package.id} in stage {stage.id}")
                
                executable_tasks = await self.analyzer.generate_tasks_for_work(task, stage, work_package)
                work_package.tasks = executable_tasks
                total_generated += len(executable_tasks)
                
                logger.info(f"Generated {len(executable_tasks)} tasks for work package {work_package.id}")
        
        # Save the updated task
        self.db.updated_task(task)
        
        logger.info(f"Generated total of {total_generated} tasks across all stages")
        return network_plan
    
    async def generate_subtasks_for_task(
        self, 
        task: Task, 
        stage_id: str, 
        work_id: str, 
        executable_task_id: str
    ) -> List[Subtask]:
        """
        Generate subtasks for a specific executable task.
        
        Args:
            task: The task containing the executable task
            stage_id: ID of the stage containing the executable task
            work_id: ID of the work package containing the executable task
            executable_task_id: ID of the executable task to generate subtasks for
            
        Returns:
            List of generated subtasks
            
        Raises:
            StageNotFoundException: If stage is not found
            WorkNotFoundException: If work package is not found
            ExecutableTaskNotFoundException: If executable task is not found
        """
        logger.info(f"Generating subtasks for executable task {executable_task_id}")
        
        # Find the executable task
        stage = find_stage_by_id(task, stage_id)
        work_package = find_work_package_by_id(stage, work_id)
        executable_task = find_executable_task_by_id(work_package, executable_task_id)
        
        # Generate subtasks using the analyzer
        subtasks = await self.analyzer.generate_subtasks_for_task(task, stage, work_package, executable_task)
        
        # Update the executable task with the generated subtasks
        executable_task.subtasks = subtasks
        
        # Save the updated task
        self.db.updated_task(task)
        
        logger.info(f"Generated {len(subtasks)} subtasks for executable task {executable_task_id}")
        return subtasks
    
    async def generate_subtasks_for_all_tasks_in_work(
        self, 
        task: Task, 
        stage_id: str, 
        work_id: str
    ) -> List[ExecutableTask]:
        """
        Generate subtasks for all executable tasks in a work package.
        
        Args:
            task: The task containing the work package
            stage_id: ID of the stage containing the work package
            work_id: ID of the work package to generate subtasks for
            
        Returns:
            List of updated executable tasks with generated subtasks
            
        Raises:
            StageNotFoundException: If stage is not found
            WorkNotFoundException: If work package is not found
            MissingComponentException: If work package has no tasks
        """
        logger.info(f"Generating subtasks for all tasks in work package {work_id}")
        
        # Find the work package
        stage = find_stage_by_id(task, stage_id)
        work_package = find_work_package_by_id(stage, work_id)
        
        # Validate work package has tasks
        if not WorkValidator.has_tasks(work_package):
            raise MissingComponentException(f"Work package {work_id} has no tasks")
        
        executable_tasks = cast(List[ExecutableTask], work_package.tasks)
        total_generated = 0
        
        # Generate subtasks for each executable task
        for executable_task in executable_tasks:
            logger.info(f"Generating subtasks for executable task {executable_task.id}")
            
            subtasks = await self.analyzer.generate_subtasks_for_task(
                task, stage, work_package, executable_task
            )
            executable_task.subtasks = subtasks
            total_generated += len(subtasks)
            
            logger.info(f"Generated {len(subtasks)} subtasks for executable task {executable_task.id}")
        
        # Save the updated task
        self.db.updated_task(task)
        
        logger.info(f"Generated total of {total_generated} subtasks for work package {work_id}")
        return executable_tasks 