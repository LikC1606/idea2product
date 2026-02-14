import unittest
from app.logic.task_management import TaskManager

class TestTaskManagement(unittest.TestCase):

    def setUp(self):
        self.task_manager = TaskManager()

    def test_create_task(self):
        task_name = "Buy groceries"
        result = self.task_manager.create_task(task_name)
        self.assertTrue(result)
        self.assertEqual(len(self.task_manager.get_all_tasks()), 1)
        self.assertEqual(self.task_manager.get_all_tasks()[0].name, task_name)

    def test_create_task_empty_name(self):
        task_name = ""
        result = self.task_manager.create_task(task_name)
        self.assertFalse(result)
        self.assertEqual(len(self.task_manager.get_all_tasks()), 0)

    def test_complete_task(self):
        task_name = "Complete assignment"
        self.task_manager.create_task(task_name)
        task = self.task_manager.get_all_tasks()[0]
        result = self.task_manager.complete_task(task.id)
        self.assertTrue(result)
        self.assertTrue(task.completed)

    def test_complete_task_invalid_id(self):
        result = self.task_manager.complete_task("invalid-id")
        self.assertFalse(result)

    def test_delete_task(self):
        task_name = "Clean the house"
        self.task_manager.create_task(task_name)
        task = self.task_manager.get_all_tasks()[0]
        result = self.task_manager.delete_task(task.id)
        self.assertTrue(result)
        self.assertEqual(len(self.task_manager.get_all_tasks()), 0)

    def test_delete_task_invalid_id(self):
        result = self.task_manager.delete_task("invalid-id")
        self.assertFalse(result)

    def test_organize_tasks_by_priority(self):
        self.task_manager.create_task("Task 1", priority=3)
        self.task_manager.create_task("Task 2", priority=1)
        self.task_manager.create_task("Task 3", priority=2)
        organized_tasks = self.task_manager.organize_tasks_by_priority()
        self.assertEqual([task.name for task in organized_tasks], ["Task 2", "Task 3", "Task 1"])

    def test_get_all_tasks(self):
        self.task_manager.create_task("Task A")
        self.task_manager.create_task("Task B")
        tasks = self.task_manager.get_all_tasks()
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0].name, "Task A")
        self.assertEqual(tasks[1].name, "Task B")

if __name__ == '__main__':
    unittest.main()