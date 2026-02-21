from sqlalchemy.exc import SQLAlchemyError
import logging

class DatabaseExceptionHandler:
    @staticmethod
    def handle_exception(error: SQLAlchemyError):
        """
        Handles SQLAlchemy exceptions and logs them appropriately.

        Parameters:
            error (SQLAlchemyError): The exception raised by SQLAlchemy.

        Returns:
            dict: A dictionary containing error details.
        """
        logging.error(f"Database error occurred: {str(error)}")
        return {
            "error": "A database error occurred.",
            "details": str(error)
        }