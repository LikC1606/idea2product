from app.database import db

class Problem:
    def __init__(self, id, title, description, difficulty):
        self.id = id
        self.title = title
        self.description = description
        self.difficulty = difficulty

    def __repr__(self):
        return f"<Problem {self.title} (Difficulty: {self.difficulty})>"