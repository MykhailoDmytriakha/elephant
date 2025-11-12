#!/usr/bin/env python3
"""
Test script for FileStorageService context_answers integration
"""

import sys
import os
import tempfile
from pathlib import Path

# Add backend src to path
sys.path.insert(0, '/Users/mykhailo/MyProjects/elephant/backend/src')

from services.file_storage_service import FileStorageService
from model.task import Task
from model.context import ContextQuestion

def test_storage_integration():
    """Test that FileStorageService properly saves/loads context_answers"""

    print("=== Testing FileStorageService Integration ===")

    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create storage service
        storage = FileStorageService(temp_path)
        project_name = "test_project"

        # Create project
        storage.create_project(project_name, "Test query")
        print(f"Created project: {project_name}")

        # Create task with context_answers
        task = Task.create_new("Test task")

        # Add pending questions
        questions = [
            ContextQuestion(question="What is the deadline?", options=["Today", "Tomorrow"]),
            ContextQuestion(question="Who will work?", options=["Me", "Team"])
        ]
        task.add_pending_questions(questions)
        print(f"Added {len(questions)} pending questions to task")
        print(f"Task context_answers count: {len(task.context_answers)}")

        # Save task
        storage.save_task(project_name, task)
        print("Task saved to storage")

        # Load task back
        loaded_task = storage.load_task(project_name)
        print("Task loaded from storage")

        if loaded_task is None:
            print("❌ ERROR: Loaded task is None!")
            return False

        print(f"Loaded task context_answers count: {len(loaded_task.context_answers)}")

        # Check that context_answers are preserved
        assert len(loaded_task.context_answers) == 2, f"Expected 2 context_answers, got {len(loaded_task.context_answers)}"

        # Check pending questions
        pending = loaded_task.get_pending_questions()
        assert len(pending) == 2, f"Expected 2 pending questions, got {len(pending)}"

        print("✅ FileStorageService integration test PASSED!")
        return True

if __name__ == "__main__":
    test_storage_integration()
