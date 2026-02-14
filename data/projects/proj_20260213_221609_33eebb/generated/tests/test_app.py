import unittest
from src.app import TodoListApp, Task

class TestTodoListApp(unittest.TestCase):

    def setUp(self):
        self.app = TodoListApp()

    def test_task_creation(self):
        task = self.app.create_task("Test Task", priority=3)
        self.assertIn(task, self.app.tasks)
        self.assertEqual(task.name, "Test Task")
        self.assertEqual(task.priority, 3)
        self.assertFalse(task.completed)

    def test_task_editing(self):
        task = self.app.create_task("Old Task", priority=2)
        self.app.edit_task(task, name="New Task", priority=5)
        self.assertEqual(task.name, "New Task")
        self.assertEqual(task.priority, 5)

    def test_task_deletion(self):
        task = self.app.create_task("Delete Task", priority=1)
        self.app.delete_task(task)
        self.assertNotIn(task, self.app.tasks)

    def test_task_prioritization(self):
        task1 = self.app.create_task("Task 1", priority=1)
        task2 = self.app.create_task("Task 2", priority=5)
        task3 = self.app.create_task("Task 3", priority=3)
        sorted_tasks = self.app.get_tasks_sorted_by_priority()
        self.assertEqual(sorted_tasks, [task2, task3, task1])

    def test_task_completion(self):
        task = self.app.create_task("Complete Task", priority=4)
        self.app.complete_task(task)
        self.assertTrue(task.completed)

if __name__ == '__main__':
    unittest.main()