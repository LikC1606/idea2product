```python
from src.database.schema import Task, session

def delete_task(task_id):
    """
    Deletes a task from the database given its task_id.

    :param task_id: The unique identifier of the task to delete.
    :return: None
    """
    try:
        task = session.query(Task).filter(Task.id == task_id).one_or_none()
        if task is None:
            print(f"No task found with id: {task_id}")
            return

        session.delete(task)
        session.commit()
        print(f"Task with id {task_id} has been deleted.")
        
    except Exception as e:
        session.rollback()
        print(f"An error occurred while trying to delete the task: {e}")
```
