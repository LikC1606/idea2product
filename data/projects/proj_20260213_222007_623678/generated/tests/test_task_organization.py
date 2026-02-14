import unittest
from app.logic.task_organization import TaskOrganizer, Task

class TestTaskOrganization(unittest.TestCase):

    def setUp(self):
        self.organizer = TaskOrganizer()
        self.task1 = Task(id=1, title="Buy groceries", priority=2)
        self.task2 = Task(id=2, title="Read a book", priority=1)
        self.task3 = Task(id=3, title="Write report", priority=3)
        self.organizer.add_task(self.task1)
        self.organizer.add_task(self.task2)
        self.organizer.add_task(self.task3)

    def test_add_task(self):
        self.assertEqual(len(self.organizer.tasks), 3)
        new_task = Task(id=4, title="Go for a walk", priority=2)
        self.organizer.add_task(new_task)
        self.assertEqual(len(self.organizer.tasks), 4)
        self.assertIn(new_task, self.organizer.tasks)

    def test_remove_task(self):
        self.organizer.remove_task(self.task1.id)
        self.assertEqual(len(self.organizer.tasks), 2)
        self.assertNotIn(self.task1, self.organizer.tasks)

    def test_get_task_by_id(self):
        task = self.organizer.get_task_by_id(self.task2.id)
        self.assertEqual(task, self.task2)

    def test_get_task_by_id_not_found(self):
        task = self.organizer.get_task_by_id(999)
        self.assertIsNone(task)

    def test_organize_tasks_by_priority(self):
        self.organizer.organize_tasks_by_priority()
        self.assertEqual(self.organizer.tasks[0], self.task2)
        self.assertEqual(self.organizer.tasks[1], self.task1)
        self.assertEqual(self.organizer.tasks[2], self.task3)

    def test_update_task_priority(self):
        self.organizer.update_task_priority(self.task1.id, 1)
        self.assertEqual(self.task1.priority, 1)
        self.organizer.organize_tasks_by_priority()
        self.assertEqual(self.organizer.tasks[0], self.task1)

    def test_update_task_priority_task_not_found(self):
        with self.assertRaises(ValueError):
            self.organizer.update_task_priority(999, 1)

if __name__ == "__main__":
    unittest.main()