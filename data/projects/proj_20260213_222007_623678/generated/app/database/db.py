import sqlite3

class Database:
    def __init__(self, db_name='todo_list.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_tasks_table()

    def create_tasks_table(self):
        query = '''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL CHECK(status IN ('pending', 'completed')) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
        self.conn.execute(query)
        self.conn.commit()

    def add_task(self, title, description=''):
        query = 'INSERT INTO tasks (title, description) VALUES (?, ?)'
        self.conn.execute(query, (title, description))
        self.conn.commit()

    def get_tasks(self, status=None):
        query = 'SELECT id, title, description, status, created_at FROM tasks'
        if status:
            query += ' WHERE status = ?'
            return self.conn.execute(query, (status,)).fetchall()
        return self.conn.execute(query).fetchall()

    def update_task_status(self, task_id, status):
        query = 'UPDATE tasks SET status = ? WHERE id = ?'
        self.conn.execute(query, (status, task_id))
        self.conn.commit()

    def delete_task(self, task_id):
        query = 'DELETE FROM tasks WHERE id = ?'
        self.conn.execute(query, (task_id,))
        self.conn.commit()

    def __del__(self):
        self.conn.close()