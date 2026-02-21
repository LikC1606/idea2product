from app.database import db

class Problem:
    def __init__(self, id, title, description, difficulty, tags=None):
        self.id = id
        self.title = title
        self.description = description
        self.difficulty = difficulty
        self.tags = tags if tags else []

    def to_dict(self):
        """
        Converts the Problem instance to a dictionary format.
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "difficulty": self.difficulty,
            "tags": self.tags
        }