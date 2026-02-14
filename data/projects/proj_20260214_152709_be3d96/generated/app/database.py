import sqlite3
from config.database_config import DATABASE_PATH

class Database:
    def __init__(self):
        self.connection = None

    def connect(self):
        try:
            self.connection = sqlite3.connect(DATABASE_PATH)
            self.connection.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            print(f"Error connecting to the database: {e}")
            raise

    def close(self):
        if self.connection:
            self.connection.close()

    def execute_query(self, query, params=None):
        if not self.connection:
            raise Exception("Database connection is not established.")
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            return cursor
        except sqlite3.Error as e:
            print(f"Error executing query: {e}")
            raise

    def fetch_all(self, query, params=None):
        cursor = self.execute_query(query, params)
        return cursor.fetchall()

    def fetch_one(self, query, params=None):
        cursor = self.execute_query(query, params)
        return cursor.fetchone()

    def insert(self, query, params):
        cursor = self.execute_query(query, params)
        return cursor.lastrowid

    def update(self, query, params):
        self.execute_query(query, params)

    def delete(self, query, params):
        self.execute_query(query, params)