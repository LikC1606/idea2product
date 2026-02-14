from app.ui.task_creation import TaskCreationUI
from app.database.db import Database

class TaskCreationLogic:
    def __init__(self):
        self.ui = TaskCreationUI()
        self.db = Database()

    def create_task(self, title, description, due_date=None, priority='Normal'):
        if not title:
            raise ValueError("Task title cannot be empty")
        
        task = {
            'title': title,
            'description': description,
            'due_date': due_date,
            'priority': priority,
            'status': 'Pending'
        }
        
        self.db.insert_task(task)
        self.ui.display_task_creation_success(task)

    def validate_task_data(self, title, description, due_date, priority):
        if not title:
            return False, "Title cannot be empty"
        # Add more validation as needed
        return True, "Validation successful"

    def handle_task_creation(self):
        task_data = self.ui.get_task_input()
        is_valid, message = self.validate_task_data(
            task_data['title'],
            task_data['description'],
            task_data.get('due_date'),
            task_data.get('priority', 'Normal')
        )
        
        if is_valid:
            self.create_task(
                task_data['title'],
                task_data['description'],
                task_data.get('due_date'),
                task_data.get('priority', 'Normal')
            )
        else:
            self.ui.display_validation_error(message)