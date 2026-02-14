```python
import unittest
from src.features.add_task import add_task

class TestAddTask(unittest.TestCase):
    def setUp(self):
        self.task_list = []

    def test_add_task_success(self):
        task = "Buy groceries"
        add_task(self.task_list, task)
        self.assertIn(task, self.task_list)

    def test_add_empty_task(self):
        task = ""
        with self.assertRaises(ValueError):
            add_task(self.task_list, task)

    def test_add_duplicate_task(self):
        task = "Read a book"
        add_task(self.task_list, task)
        with self.assertRaises(ValueError):
            add_task(self.task_list, task)

if __name__ == "__main__":
    unittest.main()
```