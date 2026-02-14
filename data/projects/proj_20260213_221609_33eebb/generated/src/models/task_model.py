from datetime import datetime
from src.database import Database

class TaskModel:
    def __init__(self, task_id, title, description, priority, is_completed=False, created_at=None):
        self.task_id = task_id
        self.title = title
        self.description = description
        self.priority = priority
        self.is_completed = is_completed
        self.created_at = created_at or datetime.now()

    def create_task(self):
        db = Database()
        db.insert({
            'task_id': self.task_id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'is_completed': self.is_completed,
            'created_at': self.created_at
        })

    def update_task(self, title=None, description=None, priority=None, is_completed=None):
        if title:
            self.title = title
        if description:
            self.description = description
        if priority:
            self.priority = priority
        if is_completed is not None:
            self.is_completed = is_completed
        
        db = Database()
        db.update(self.task_id, {
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'is_completed': self.is_completed
        })

    def delete_task(self):
        db = Database()
        db.delete(self.task_id)

    def mark_completed(self):
        self.is_completed = True
        db = Database()
        db.update(self.task_id, {'is_completed': self.is_completed})

    @staticmethod
    def get_all_tasks():
        db = Database()
        return db.select_all()

    @staticmethod
    def get_task_by_id(task_id):
        db = Database()
        return db.select(task_id)
```
