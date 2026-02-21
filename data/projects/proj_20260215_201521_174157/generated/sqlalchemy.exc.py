from sqlalchemy.exc import SQLAlchemyError

class DatabaseException(SQLAlchemyError):
    """Custom exception class for handling database errors."""

    def __init__(self, message=None):
        super().__init__(message or "An error occurred in the database layer.")