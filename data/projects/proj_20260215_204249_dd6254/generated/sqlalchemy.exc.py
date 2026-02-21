from sqlalchemy.exc import SQLAlchemyError

class DatabaseException(SQLAlchemyError):
    """Base exception class for database-related errors."""
    pass

class DatabaseConnectionError(DatabaseException):
    """Raised when there is a connection issue with the database."""
    def __init__(self, message="Failed to connect to the database"):
        super().__init__(message)

class DatabaseQueryError(DatabaseException):
    """Raised when there is an error executing a database query."""
    def __init__(self, message="An error occurred while executing a database query"):
        super().__init__(message)

class DatabaseIntegrityError(DatabaseException):
    """Raised when there is an integrity constraint violation."""
    def __init__(self, message="Database integrity constraint violation"):
        super().__init__(message)