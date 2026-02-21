from sqlalchemy.exc import SQLAlchemyError

class DatabaseError(Exception):
    """Generic exception for database-related errors."""
    def __init__(self, message="A database error occurred"):
        self.message = message
        super().__init__(self.message)

class IntegrityError(DatabaseError):
    """Raised when a database integrity constraint is violated."""
    def __init__(self, message="An integrity constraint was violated"):
        super().__init__(message)

class OperationalError(DatabaseError):
    """Raised for operational issues (e.g., connection errors)."""
    def __init__(self, message="An operational error occurred"):
        super().__init__(message)

class DataError(DatabaseError):
    """Raised for invalid or missing data errors."""
    def __init__(self, message="Invalid or missing data encountered"):
        super().__init__(message)

def handle_sqlalchemy_error(error):
    """Utility function to map SQLAlchemy exceptions to custom exceptions."""
    if isinstance(error, SQLAlchemyError):
        if isinstance(error, error.__class__.__name__ == 'IntegrityError'):
            raise IntegrityError(str(error))
        elif isinstance(error, error.__class__.__name__ == 'OperationalError'):
            raise OperationalError(str(error))
        elif isinstance(error, error.__class__.__name__ == 'DataError'):
            raise DataError(str(error))
        else:
            raise DatabaseError(str(error))