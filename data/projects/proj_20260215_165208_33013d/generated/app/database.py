from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
_db = SQLAlchemy()

def db():
    """Returns the SQLAlchemy database instance."""
    return _db