from sqlalchemy.exc import SQLAlchemyError

class DatabaseException(Exception):
    def __init__(self, message="A database error occurred", original_exception=None):
        super().__init__(message)
        self.original_exception = original_exception

def handle_database_error(func):
    """
    Decorator to handle SQLAlchemy errors in database operations.
    Wraps a function and raises a DatabaseException if a SQLAlchemyError occurs.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError as e:
            raise DatabaseException(original_exception=e) from e
    return wrapper