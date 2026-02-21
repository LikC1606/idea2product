from flask_sqlalchemy import SQLAlchemy

# Initialize the SQLAlchemy instance
db_instance = SQLAlchemy()

def db():
    """
    Returns the SQLAlchemy database instance.
    """
    return db_instance
# SQLAlchemy db instance for models
db = SQLAlchemy()
