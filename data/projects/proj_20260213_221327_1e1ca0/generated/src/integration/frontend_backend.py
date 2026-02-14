```python
# File: src/integration/frontend_backend.py

from src.ui.design import TodoUI
from src.features.add_task import add_task
from src.features.delete_task import delete_task
from src.features.complete_task import complete_task

class TodoAppIntegration:
    def __init__(self):
        self.ui = TodoUI()
        self.tasks = []

    def setup_ui(self):
        self.ui.setup()
        self.ui.set_add_task_callback(self.add_task_callback)
        self.ui.set_delete_task_callback(self.delete_task_callback)
        self.ui.set_complete_task_callback(self.complete_task_callback)
        self.refresh_ui()

    def add_task_callback(self, task_description):
        task = add_task(task_description)
        if task:
            self.tasks.append(task)
            self.refresh_ui()

    def delete_task_callback(self, task_id):
        if delete_task(self.tasks, task_id):
            self.refresh_ui()

    def complete_task_callback(self, task_id):
        if complete_task(self.tasks, task_id):
            self.refresh_ui()

    def refresh_ui(self):
        self.ui.display_tasks(self.tasks)

if __name__ == '__main__':
    app_integration = TodoAppIntegration()
    app_integration.setup_ui()
    app_integration.ui.run()
```
