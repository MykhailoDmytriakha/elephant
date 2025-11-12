#!/usr/bin/env python3
"""
Test script for context_answers JSON serialization
"""

import sys
import os
import json
from pathlib import Path

# Add backend src to path
sys.path.insert(0, '/Users/mykhailo/MyProjects/elephant/backend/src')

from model.task import Task
from model.context import UserAnswer, ContextQuestion

def test_json_serialization():
    """Test that context_answers are properly serialized to/from JSON"""

    print("=== Testing JSON Serialization ===")

    # 1. Create a task
    task = Task.create_new("Test task")
    print(f"Created task: {task.id}")

    # 2. Add pending questions
    questions = [
        ContextQuestion(question="What is the deadline?", options=["Today", "Tomorrow", "Next week"]),
        ContextQuestion(question="Who will work on this?", options=["Me", "Team", "External contractor"]),
    ]

    task.add_pending_questions(questions)
    print(f"Added {len(questions)} pending questions")
    print(f"Task has {len(task.context_answers)} context_answers")

    # 3. Convert to dict (this is what save_task does)
    task_dict = task.to_dict()
    print(f"Task dict keys: {list(task_dict.keys())}")
    print(f"context_answers in dict: {task_dict.get('context_answers', 'NOT FOUND')}")

    # 4. Serialize to JSON string (simulate file save)
    json_str = json.dumps(task_dict, indent=2, ensure_ascii=False)
    print(f"JSON serialization successful, length: {len(json_str)}")

    # 5. Parse back from JSON (simulate file load)
    loaded_dict = json.loads(json_str)
    print(f"JSON parsing successful")
    print(f"Loaded dict context_answers: {loaded_dict.get('context_answers', 'NOT FOUND')}")

    # 6. Create Task from dict (this is what load_task does)
    loaded_task = Task(**loaded_dict)
    print(f"Task reconstruction successful")
    print(f"Loaded task has {len(loaded_task.context_answers)} context_answers")

    # 7. Check that pending questions are restored
    pending = loaded_task.get_pending_questions()
    print(f"Restored {len(pending)} pending questions:")
    for i, q in enumerate(pending):
        print(f"  {i+1}. {q.question}")

    # 8. Verify data integrity
    assert len(loaded_task.context_answers) == 2, f"Expected 2 context_answers, got {len(loaded_task.context_answers)}"
    assert len(pending) == 2, f"Expected 2 pending questions, got {len(pending)}"

    for original, loaded in zip(task.context_answers, loaded_task.context_answers):
        assert original.question == loaded.question, f"Question mismatch: {original.question} != {loaded.question}"
        assert original.answer == loaded.answer, f"Answer mismatch: '{original.answer}' != '{loaded.answer}'"

    print("\n✅ JSON serialization test PASSED!")
    return True

if __name__ == "__main__":
    test_json_serialization()
