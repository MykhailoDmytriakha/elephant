import unittest
from datetime import datetime, timedelta
from src.model.task import Task, TaskState
from uuid import UUID

class TestTaskModel(unittest.TestCase):
    def test_initialization(self):
        task = Task()
        self.assertIsNotNone(task.id)
        self.assertEqual(task.state, TaskState.NEW)
        self.assertEqual(task.sub_level, 0)
        self.assertFalse(task.is_context_sufficient)

    def test_state_transition(self):
        task = Task()
        task.update_state(TaskState.CONTEXT_GATHERING)
        self.assertEqual(task.state, TaskState.CONTEXT_GATHERING)

    def test_to_dict(self):
        task = Task()
        task_dict = task.to_dict()
        self.assertIn('id', task_dict)
        self.assertIn('state', task_dict)

    def test_create_new(self):
        task = Task.create_new(task="Test Task", context="Test Context")
        self.assertEqual(task.state, TaskState.NEW)
        self.assertIsNone(task.task)  # Task field should be None until clarified by AI
        self.assertEqual(task.short_description, "Test Task")  # Original query goes to short_description
        self.assertEqual(task.context, "Test Context")

    # New test cases to cover missing lines
    def test_task_id_assignment(self):
        task = Task()
        self.assertIsInstance(UUID(task.id), UUID)

    def test_task_created_at_assignment(self):
        task = Task()
        self.assertIsInstance(datetime.fromisoformat(task.created_at), datetime)

    def test_task_updated_at_assignment(self):
        task = Task()
        created_at = datetime.fromisoformat(task.created_at)
        updated_at = datetime.fromisoformat(task.updated_at)
        self.assertAlmostEqual(created_at, updated_at, delta=timedelta(milliseconds=1))

    def test_task_state_default(self):
        task = Task()
        self.assertEqual(task.state, TaskState.NEW)

    def test_state_transition_to_same_state(self):
        task = Task(state=TaskState.NEW)
        task.update_state(TaskState.NEW)  # Should not raise an error

    def test_context_answers_json_serialization(self):
        """Test that context_answers are properly serialized to/from JSON"""
        from src.model.context import ContextQuestion, UserAnswer, UserAnswers

        # Create task
        task = Task.create_new("Test task")

        # Add pending questions
        questions = [
            ContextQuestion(question="What is the deadline?", options=["Today", "Tomorrow"]),
            ContextQuestion(question="Who will work?", options=["Me", "Team"])
        ]
        task.add_pending_questions(questions)

        # Verify questions were added
        self.assertEqual(len(task.context_answers), 2)
        self.assertEqual(task.context_answers[0].answer, "")
        self.assertEqual(task.context_answers[1].answer, "")

        # Serialize to dict (what save_task does)
        task_dict = task.to_dict()
        self.assertIn('context_answers', task_dict)
        self.assertEqual(len(task_dict['context_answers']), 2)

        # Verify pending questions are detected
        pending = task.get_pending_questions()
        self.assertEqual(len(pending), 2)

        # Create new task from dict (what load_task does)
        loaded_task = Task(**task_dict)
        self.assertEqual(len(loaded_task.context_answers), 2)

        # Verify pending questions work after loading
        loaded_pending = loaded_task.get_pending_questions()
        self.assertEqual(len(loaded_pending), 2)
        self.assertEqual(loaded_pending[0].question, "What is the deadline?")
        self.assertEqual(loaded_pending[1].question, "Who will work?")

        # Test answering questions (only answer the first question)
        answers = UserAnswers(answers=[
            UserAnswer(question="What is the deadline?", answer="Tomorrow")
        ])
        loaded_task.update_answers(answers)

        # Verify answer was updated and unanswered questions were removed
        self.assertEqual(len(loaded_task.context_answers), 1)  # Only answered question remains
        self.assertEqual(loaded_task.context_answers[0].answer, "Tomorrow")
        self.assertEqual(loaded_task.context_answers[0].question, "What is the deadline?")

        # Verify no pending questions left (since unanswered questions were removed)
        final_pending = loaded_task.get_pending_questions()
        self.assertEqual(len(final_pending), 0)

        # Verify that options are removed after answering
        answered_question = loaded_task.context_answers[0]
        self.assertEqual(answered_question.question, "What is the deadline?")
        self.assertEqual(answered_question.answer, "Tomorrow")
        self.assertIsNone(answered_question.options)  # Options should be removed after answering

if __name__ == '__main__':
    unittest.main()
