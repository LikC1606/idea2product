```python
# src/features/complete_task.py

from src.database.schema import Task, session

def complete_task(task_id):
    try:
        task = session.query(Task).filter(Task.id == task_id).first()
        if task is None:
            return {"success": False, "message": "Task not found"}

        task.is_complete = True
        session.commit()
        return {"success": True, "message": "Task marked as complete"}
    except Exception as e:
        session.rollback()
        return {"success": False, "message": str(e)}
```
