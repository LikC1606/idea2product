import unittest
from src.models.task_model import Task

class TestTaskModel(unittest.TestCase):

    def setUp(self):
        self.task = Task(title="Sample Task", description="This is a sample task.", priority=1, completed=False)

    def test_task_creation(self):
        self.assertEqual(self.task.title, "Sample Task")
        self.assertEqual(self.task.description, "This is a sample task.")
        self.assertEqual(self.task.priority, 1)
        self.assertFalse(self.task.completed)

    def test_task_editing(self):
        self.task.title = "Updated Task"
        self.task.description = "Updated description."
        self.task.priority = 2

        self.assertEqual(self.task.title, "Updated Task")
        self.assertEqual(self.task.description, "Updated description.")
        self.assertEqual(self.task.priority, 2)

    def test_task_completion(self):
        self.task.completed = True
        self.assertTrue(self.task.completed)

    def test_task_deletion(self):
        task_list = [self.task]
        task_list.remove(self.task)
        self.assertNotIn(self.task, task_list)

    def test_task_prioritization(self):
        low_priority_task = Task(title="Low Priority Task", description="Another task", priority=5, completed=False)
        task_list = [self.task, low_priority_task]
        task_list.sort(key=lambda x: x.priority)
        
        self.assertEqual(task_list[0], self.task)
        self.assertEqual(task_list[1], low_priority_task)

if __name__ == '__main__':
    unittest.main()