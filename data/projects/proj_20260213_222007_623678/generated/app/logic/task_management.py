# app/logic/task_management.py

from app.ui.task_management import TaskUI
from app.database.db import Database

class TaskManagement:
    def __init__(self):
        self.db = Database()
        self.ui = TaskUI()

    def create_task(self, title, description, due_date=None):
        task = {
            'title': title,
            'description': description,
            'due_date': due_date,
            'completed': False
        }
        self.db.add_task(task)
        self.ui.display_task_created(task)

    def manage_task(self, task_id, action):
        task = self.db.get_task(task_id)
        if not task:
            self.ui.display_error(f"Task with ID {task_id} not found.")
            return

        if action == 'complete':
            task['completed'] = True
            self.db.update_task(task_id, task)
            self.ui.display_task_completed(task)
        elif action == 'edit':
            updated_task = self.ui.prompt_task_edit(task)
            self.db.update_task(task_id, updated_task)
            self.ui.display_task_updated(updated_task)
        elif action == 'delete':
            self.db.delete_task(task_id)
            self.ui.display_task_deleted(task_id)
        else:
            self.ui.display_error(f"Unknown action: {action}")

    def organize_tasks(self, criterion='due_date'):
        tasks = self.db.get_all_tasks()
        if criterion == 'due_date':
            tasks.sort(key=lambda x: (x['due_date'] is None, x['due_date']))
        elif criterion == 'title':
            tasks.sort(key=lambda x: x['title'])
        self.ui.display_tasks(tasks)