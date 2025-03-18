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
        with self.assertRaises(ValueError):
            task.update_state(TaskState.COMPLETED)  # Invalid transition

    def test_to_dict(self):
        task = Task()
        task_dict = task.to_dict()
        self.assertIn('id', task_dict)
        self.assertIn('state', task_dict)

    def test_create_new(self):
        task = Task.create_new(task="Test Task", context="Test Context")
        self.assertEqual(task.state, TaskState.NEW)
        self.assertEqual(task.task, "Test Task")
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

if __name__ == '__main__':
    unittest.main()
