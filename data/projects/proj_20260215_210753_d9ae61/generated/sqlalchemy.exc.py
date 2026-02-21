from sqlalchemy.exc import SQLAlchemyError

class DatabaseExceptionHandler:
    @staticmethod
    def handle_exception(exception: SQLAlchemyError) -> dict:
        """
        Handles SQLAlchemy exceptions and returns a structured response.

        Args:
            exception (SQLAlchemyError): The exception raised by SQLAlchemy.

        Returns:
            dict: A structured response containing error details.
        """
        response = {
            "error": "DatabaseError",
            "message": str(exception),
            "details": exception.__class__.__name__
        }
        return response