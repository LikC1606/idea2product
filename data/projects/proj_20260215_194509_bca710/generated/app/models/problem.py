from app.database import db


class Problem:
    def __init__(self, title, description, difficulty_level):
        self.title = title
        self.description = description
        self.difficulty_level = difficulty_level

    def to_dict(self):
        """
        Converts the Problem instance to a dictionary representation.
        """
        return {
            "title": self.title,
            "description": self.description,
            "difficulty_level": self.difficulty_level,
        }