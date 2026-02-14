import unittest
from app.logic.task_creation import create_task

class TestTaskCreation(unittest.TestCase):
    def setUp(self):
        # Setup any required dependencies or initial data
        self.task_title = "Test Task"
        self.task_description = "This is a test task description."

    def test_create_task_with_valid_data(self):
        # Test creating a task with valid data
        task = create_task(self.task_title, self.task_description)
        self.assertIsNotNone(task)
        self.assertEqual(task.title, self.task_title)
        self.assertEqual(task.description, self.task_description)

    def test_create_task_with_empty_title(self):
        # Test creating a task with an empty title
        empty_title = ""
        task = create_task(empty_title, self.task_description)
        self.assertIsNone(task)

    def test_create_task_with_empty_description(self):
        # Test creating a task with an empty description
        empty_description = ""
        task = create_task(self.task_title, empty_description)
        self.assertIsNotNone(task)
        self.assertEqual(task.title, self.task_title)
        self.assertEqual(task.description, empty_description)

    def test_create_task_with_none_title(self):
        # Test creating a task with None as title
        task = create_task(None, self.task_description)
        self.assertIsNone(task)

    def test_create_task_with_none_description(self):
        # Test creating a task with None as description
        task = create_task(self.task_title, None)
        self.assertIsNotNone(task)
        self.assertEqual(task.title, self.task_title)
        self.assertIsNone(task.description)

if __name__ == '__main__':
    unittest.main()