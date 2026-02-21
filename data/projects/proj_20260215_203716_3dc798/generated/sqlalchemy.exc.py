from sqlalchemy.exc import SQLAlchemyError

class DatabaseException(SQLAlchemyError):
    """Base exception class for database-related errors."""
    pass

class IntegrityError(DatabaseException):
    """Raised when a database integrity constraint is violated."""
    pass

class DataError(DatabaseException):
    """Raised for errors in data processing or input."""
    pass

class OperationalError(DatabaseException):
    """Raised for errors related to the database operation."""
    pass

class ProgrammingError(DatabaseException):
    """Raised for errors in the database programming or invalid queries."""
    pass

class TimeoutError(DatabaseException):
    """Raised when a database operation exceeds its timeout."""
    pass

class ConnectionError(DatabaseException):
    """Raised when a connection to the database fails."""
    pass