from app.ui.task_organization import TaskUI
from app.database.db import Database

class TaskOrganization:
    def __init__(self):
        self.db = Database()
        self.ui = TaskUI()

    def create_task(self, title, description, due_date, priority):
        """
        Creates a new task in the database.

        Args:
            title (str): The title of the task.
            description (str): The description of the task.
            due_date (str): The due date of the task.
            priority (int): The priority level of the task.
        
        Returns:
            dict: The newly created task.
        """
        task = {
            'title': title,
            'description': description,
            'due_date': due_date,
            'priority': priority
        }
        self.db.insert_task(task)
        return task

    def get_tasks(self, sort_by=None):
        """
        Retrieves all tasks from the database.

        Args:
            sort_by (str, optional): Field to sort the tasks by. Defaults to None.
        
        Returns:
            list: List of tasks.
        """
        tasks = self.db.get_all_tasks()
        if sort_by:
            tasks = sorted(tasks, key=lambda x: x.get(sort_by))
        return tasks

    def update_task(self, task_id, updates):
        """
        Updates an existing task in the database.

        Args:
            task_id (int): The ID of the task to update.
            updates (dict): The fields to update with their new values.
        
        Returns:
            dict: The updated task.
        """
        task = self.db.update_task(task_id, updates)
        return task

    def delete_task(self, task_id):
        """
        Deletes a task from the database.

        Args:
            task_id (int): The ID of the task to delete.
        
        Returns:
            bool: True if the task was successfully deleted, False otherwise.
        """
        return self.db.delete_task(task_id)

    def organize_tasks(self, criteria):
        """
        Organizes tasks based on the given criteria.

        Args:
            criteria (str): The criteria to organize tasks by (e.g., 'priority', 'due_date').
        
        Returns:
            list: List of organized tasks.
        """
        tasks = self.get_tasks()
        organized_tasks = sorted(tasks, key=lambda x: x.get(criteria))
        return organized_tasks

    def display_tasks(self):
        """
        Displays tasks using the UI component.
        """
        tasks = self.get_tasks()
        self.ui.show_tasks(tasks)