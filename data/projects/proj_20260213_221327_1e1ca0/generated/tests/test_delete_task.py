```python
import unittest
from src.features.delete_task import delete_task
from src.features.todo_list import TodoList

class TestDeleteTask(unittest.TestCase):

    def setUp(self):
        self.todo_list = TodoList()
        self.todo_list.add_task("Task 1")
        self.todo_list.add_task("Task 2")
        self.todo_list.add_task("Task 3")

    def test_delete_existing_task(self):
        task_to_delete = "Task 2"
        delete_task(self.todo_list, task_to_delete)
        self.assertNotIn(task_to_delete, self.todo_list.tasks)

    def test_delete_non_existing_task(self):
        initial_task_count = len(self.todo_list.tasks)
        delete_task(self.todo_list, "Task 4")
        self.assertEqual(len(self.todo_list.tasks), initial_task_count)

    def test_delete_task_empty_list(self):
        empty_todo_list = TodoList()
        delete_task(empty_todo_list, "Task 1")
        self.assertEqual(len(empty_todo_list.tasks), 0)

    def test_delete_all_tasks(self):
        for task in self.todo_list.tasks.copy():
            delete_task(self.todo_list, task)
        self.assertEqual(len(self.todo_list.tasks), 0)

if __name__ == '__main__':
    unittest.main()
```