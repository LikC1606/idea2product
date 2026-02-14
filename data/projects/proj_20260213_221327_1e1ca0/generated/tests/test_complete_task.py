```python
import unittest
from src.features.complete_task import complete_task
from src.models.task import Task

class TestCompleteTask(unittest.TestCase):
    def setUp(self):
        self.task = Task(id=1, description="Test Task", completed=False)

    def test_complete_task(self):
        # Ensure task is initially incomplete
        self.assertFalse(self.task.completed)
        
        # Complete the task
        complete_task(self.task)
        
        # Verify the task is marked as complete
        self.assertTrue(self.task.completed)

    def test_complete_task_already_completed(self):
        # Set up the task as already completed
        self.task.completed = True
        
        # Complete the task again
        complete_task(self.task)
        
        # Verify the task remains completed
        self.assertTrue(self.task.completed)

if __name__ == '__main__':
    unittest.main()
```