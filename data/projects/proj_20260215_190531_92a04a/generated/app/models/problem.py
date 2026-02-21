from app.database import db

class Problem:
    def __init__(self, id, title, description, difficulty, tags=None):
        """
        Initialize a Problem instance.

        :param id: Unique identifier for the problem
        :param title: Title of the problem
        :param description: Detailed description of the problem
        :param difficulty: Difficulty level of the problem (e.g., 'Easy', 'Medium', 'Hard')
        :param tags: Optional list of tags associated with the problem
        """
        self.id = id
        self.title = title
        self.description = description
        self.difficulty = difficulty
        self.tags = tags or []

    def to_dict(self):
        """
        Convert the Problem instance to a dictionary.

        :return: Dictionary representation of the problem
        """
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'difficulty': self.difficulty,
            'tags': self.tags
        }