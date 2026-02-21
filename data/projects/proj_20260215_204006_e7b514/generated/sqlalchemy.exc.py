from sqlalchemy.exc import SQLAlchemyError

class DatabaseException(SQLAlchemyError):
    """
    Custom exception for database-related errors in the ACM Problem-Solving Platform.
    This allows for more granular error handling specific to the application's needs.
    """
    def __init__(self, message=None, original_exception=None):
        """
        Initialize the DatabaseException with a custom message and the original exception.

        :param message: A custom error message describing the issue.
        :param original_exception: The original exception object (if any).
        """
        self.message = message or "An error occurred in the database layer."
        self.original_exception = original_exception
        super().__init__(self.message)

    def __str__(self):
        """
        Return a string representation of the exception, including the original exception if available.
        """
        if self.original_exception:
            return f"{self.message} (Original Exception: {str(self.original_exception)})"
        return self.message