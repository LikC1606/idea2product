from app.database import db

class Problem:
    def __init__(self, id=None, title=None, description=None, difficulty=None, tags=None):
        self.id = id
        self.title = title
        self.description = description
        self.difficulty = difficulty
        self.tags = tags

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "difficulty": self.difficulty,
            "tags": self.tags
        }

    @staticmethod
    def from_dict(data):
        return Problem(
            id=data.get("id"),
            title=data.get("title"),
            description=data.get("description"),
            difficulty=data.get("difficulty"),
            tags=data.get("tags")
        )