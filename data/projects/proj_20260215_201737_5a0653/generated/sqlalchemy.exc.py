from sqlalchemy.exc import SQLAlchemyError

class DatabaseError(Exception):
    """
    Custom exception class to handle database errors.
    """
    def __init__(self, message=None, original_exception=None):
        super().__init__(message)
        self.original_exception = original_exception

def handle_sqlalchemy_error(error: SQLAlchemyError):
    """
    Function to handle SQLAlchemy errors, log them, and raise a custom exception.
    """
    error_message = f"Database error occurred: {str(error)}"
    # Log the error (implementation of logging not included in this module)
    # Example: logger.error(error_message)
    raise DatabaseError(message=error_message, original_exception=error)