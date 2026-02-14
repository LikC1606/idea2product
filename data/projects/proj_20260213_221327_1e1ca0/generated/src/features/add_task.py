```python
# src/features/add_task.py

from src.database.schema import Task, session

def add_task(title, description=None, due_date=None):
    """
    Adds a new task to the database.

    Args:
        title (str): The title of the task.
        description (str, optional): A brief description of the task. Defaults to None.
        due_date (datetime, optional): The due date for the task. Defaults to None.

    Returns:
        Task: The newly created task object.
    """
    # Create a new Task instance
    new_task = Task(title=title, description=description, due_date=due_date)

    # Add the new task to the session
    session.add(new_task)
    session.commit()

    return new_task

# Example usage
if __name__ == "__main__":
    task = add_task("Buy groceries", "Need to buy milk and eggs", "2023-10-15")
    print(f"Task added: {task.title}")
```
