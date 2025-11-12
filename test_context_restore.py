#!/usr/bin/env python3
"""
Test script for context questions restoration functionality
"""

import sys
import os
sys.path.insert(0, '/Users/mykhailo/MyProjects/elephant/backend/src')

from model.task import Task
from model.context import UserAnswer, UserAnswers, ContextQuestion

def test_context_restore_logic():
    """Test the context restore logic"""

    # Create a task
    task = Task.create_new("Test task")

    # Simulate that questions were generated and saved
    questions = [
        ContextQuestion(question="What is the deadline?", options=["Today", "Tomorrow", "Next week"]),
        ContextQuestion(question="Who will work on this?", options=["Me", "Team", "External contractor"]),
        ContextQuestion(question="What is the budget?", options=["Low", "Medium", "High"])
    ]

    print("1. Simulating question generation...")
    task.add_pending_questions(questions)
    print(f"   Added {len(questions)} pending questions")
    print(f"   Task has {len(task.context_answers)} context_answers")

    # Simulate task being saved and then loaded (like in real scenario)
    print("\n2. Simulating task save/load cycle...")
    task_dict = task.to_dict()
    loaded_task = Task(**task_dict)
    print(f"   Loaded task has {len(loaded_task.context_answers)} context_answers")

    print("\n3. Testing question restoration logic...")
    # This simulates what frontend does
    pending_answers = [a for a in loaded_task.context_answers if a.answer.strip() == ""]
    print(f"   Found {len(pending_answers)} pending questions")

    # Transform to frontend format (simulated)
    restored_questions = []
    for answer in pending_answers:
        restored_questions.append({
            'question': answer.question,
            'options': []  # Simplified, in real frontend this would be more complex
        })

    print(f"   Restored {len(restored_questions)} questions:")
    for i, q in enumerate(restored_questions):
        print(f"     {i+1}. {q['question']}")

    assert len(restored_questions) == 3, f"Expected 3 restored questions, got {len(restored_questions)}"

    print("\n4. Testing answer submission simulation...")
    # Simulate user answering first question
    answers_to_submit = UserAnswers(answers=[
        UserAnswer(question="What is the deadline?", answer="Tomorrow")
    ])
    task.update_answers(answers_to_submit)

    print("   After answering first question:")
    pending_after_answer = [a for a in task.context_answers if a.answer.strip() == ""]
    print(f"   Remaining pending: {len(pending_after_answer)}")
    print("   All context_answers:")
    for i, answer in enumerate(task.context_answers):
        status = "ANSWERED" if answer.answer.strip() else "PENDING"
        print(f"     {i+1}. {answer.question} -> '{answer.answer}' [{status}]")

    assert len(pending_after_answer) == 2, f"Expected 2 pending after answer, got {len(pending_after_answer)}"

    print("\n✅ All restoration logic tests passed!")

if __name__ == "__main__":
    test_context_restore_logic()
