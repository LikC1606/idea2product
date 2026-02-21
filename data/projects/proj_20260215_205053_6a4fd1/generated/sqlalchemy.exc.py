from sqlalchemy.exc import SQLAlchemyError

class DatabaseError(Exception):
    def __init__(self, message="A database error occurred", original_exception=None):
        super().__init__(message)
        self.original_exception = original_exception

def handle_sqlalchemy_error(error):
    # Log the original error (if logging is set up in the application)
    if isinstance(error, SQLAlchemyError):
        # Re-raise a custom exception for better error handling
        raise DatabaseError(original_exception=error)