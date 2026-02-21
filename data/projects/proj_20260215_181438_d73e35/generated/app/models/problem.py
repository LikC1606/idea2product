class Problem:
    """
    Represents a problem in the ACM Problem-Solving Platform.

    Attributes:
        id (int): Unique identifier for the problem.
        title (str): The title of the problem.
        description (str): A detailed description of the problem.
        difficulty (str): The difficulty level of the problem (e.g., Easy, Medium, Hard).
        tags (list): A list of tags related to the problem.
    """

    def __init__(self, id: int, title: str, description: str, difficulty: str, tags: list = None):
        """
        Initializes a Problem instance.

        Args:
            id (int): Unique identifier for the problem.
            title (str): The title of the problem.
            description (str): A detailed description of the problem.
            difficulty (str): The difficulty level of the problem.
            tags (list, optional): A list of tags related to the problem. Defaults to None.
        """
        self.id = id
        self.title = title
        self.description = description
        self.difficulty = difficulty
        self.tags = tags or []

    def __repr__(self):
        """
        Returns a string representation of the Problem instance.
        """
        return f"<Problem {self.id} - {self.title}>"