import unittest
from datetime import datetime, timedelta
from app.controllers.task_controller import TaskController

class TestTodoListApplication(unittest.TestCase):

    def setUp(self):
        self.task_controller = TaskController()

    def test_task_creation(self):
        task_name = "Write unit tests"
        task = self.task_controller.create_task(task_name)
        self.assertEqual(task.name, task_name)
        self.assertFalse(task.completed)

    def test_task_management(self):
        task_name = "Review PRs"
        task = self.task_controller.create_task(task_name)
        self.task_controller.mark_task_completed(task.id)
        self.assertTrue(task.completed)

    def test_task_prioritization(self):
        task_name_low = "Do laundry"
        task_name_high = "Finish project report"
        low_priority_task = self.task_controller.create_task(task_name_low, priority=1)
        high_priority_task = self.task_controller.create_task(task_name_high, priority=5)
        tasks = self.task_controller.get_tasks_sorted_by_priority()
        self.assertEqual(tasks[0].name, task_name_high)
        self.assertEqual(tasks[1].name, task_name_low)

    def test_due_date_assignment(self):
        task_name = "Submit assignment"
        due_date = datetime.now() + timedelta(days=3)
        task = self.task_controller.create_task(task_name, due_date=due_date)
        self.assertEqual(task.due_date, due_date)

    def test_task_notifications(self):
        task_name = "Prepare presentation"
        due_date = datetime.now() + timedelta(days=1)
        task = self.task_controller.create_task(task_name, due_date=due_date)
        notifications = self.task_controller.get_due_tasks_for_notification()
        self.assertIn(task, notifications)

if __name__ == '__main__':
    unittest.main()