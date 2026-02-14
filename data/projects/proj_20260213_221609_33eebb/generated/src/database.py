import sqlite3
from contextlib import closing

class Database:
    def __init__(self, db_path="todo_list.db"):
        self.db_path = db_path
        self._initialize_database()

    def _initialize_database(self):
        """Initializes the database with the required tables."""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            priority INTEGER DEFAULT 0,
            completed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        with closing(self._get_connection()) as conn, conn:
            conn.execute(create_table_query)

    def _get_connection(self):
        """Establishes and returns a database connection."""
        return sqlite3.connect(self.db_path)

    def add_task(self, title, description="", priority=0):
        """Adds a new task to the database."""
        query = """
        INSERT INTO tasks (title, description, priority, completed)
        VALUES (?, ?, ?, 0);
        """
        with closing(self._get_connection()) as conn, conn:
            conn.execute(query, (title, description, priority))

    def update_task(self, task_id, title=None, description=None, priority=None, completed=None):
        """Updates an existing task."""
        fields = []
        values = []
        
        if title is not None:
            fields.append("title = ?")
            values.append(title)
        if description is not None:
            fields.append("description = ?")
            values.append(description)
        if priority is not None:
            fields.append("priority = ?")
            values.append(priority)
        if completed is not None:
            fields.append("completed = ?")
            values.append(int(completed))

        query = f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?;"
        values.append(task_id)

        with closing(self._get_connection()) as conn, conn:
            conn.execute(query, tuple(values))

    def delete_task(self, task_id):
        """Deletes a task from the database."""
        query = "DELETE FROM tasks WHERE id = ?;"
        with closing(self._get_connection()) as conn, conn:
            conn.execute(query, (task_id,))

    def get_all_tasks(self):
        """Retrieves all tasks from the database."""
        query = "SELECT * FROM tasks ORDER BY priority DESC, created_at ASC;"
        with closing(self._get_connection()) as conn:
            cursor = conn.execute(query)
            return cursor.fetchall()

    def get_task(self, task_id):
        """Retrieves a single task by ID."""
        query = "SELECT * FROM tasks WHERE id = ?;"
        with closing(self._get_connection()) as conn:
            cursor = conn.execute(query, (task_id,))
            return cursor.fetchone()

    def mark_task_completed(self, task_id):
        """Marks a task as completed."""
        query = "UPDATE tasks SET completed = 1 WHERE id = ?;"
        with closing(self._get_connection()) as conn, conn:
            conn.execute(query, (task_id,))

# Example usage:
# db = Database()
# db.add_task("Buy groceries", "Milk, Eggs, Bread", priority=1)
# db.get_all_tasks()