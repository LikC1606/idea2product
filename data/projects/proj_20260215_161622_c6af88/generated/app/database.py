from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db_instance = SQLAlchemy()

def db():
    """
    Provides access to the SQLAlchemy instance.

    Returns:
        SQLAlchemy: The initialized SQLAlchemy instance.
    """
    return db_instance
# SQLAlchemy db instance for models
db = SQLAlchemy()
