from sqlalchemy.exc import SQLAlchemyError

class DatabaseError(SQLAlchemyError):
    """Custom exception for database-related errors in the ACM Problem-Solving Platform."""
    pass


class IntegrityError(SQLAlchemyError):
    """Custom exception for integrity-related issues in the database."""
    pass


class ConnectionError(SQLAlchemyError):
    """Custom exception for database connection errors."""
    pass


class QueryExecutionError(SQLAlchemyError):
    """Custom exception for errors during query execution."""
    pass


# Utility function to handle and log exceptions
def handle_database_error(error):
    """Handles database errors and logs them appropriately.
    
    Args:
        error (SQLAlchemyError): The exception raised during database operations.
    
    Returns:
        str: A user-friendly error message.
    """
    # Logging can be added here as per application requirements
    if isinstance(error, IntegrityError):
        return "A database integrity error occurred."
    elif isinstance(error, ConnectionError):
        return "A database connection error occurred."
    elif isinstance(error, QueryExecutionError):
        return "An error occurred while executing a database query."
    else:
        return "An unexpected database error occurred."