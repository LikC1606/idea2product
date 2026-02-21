from flask_sqlalchemy import SQLAlchemy

# Initialize the SQLAlchemy object
db = SQLAlchemy()

def init_app(app):
    """
    Initialize the database with the Flask application.

    Args:
        app: The Flask application instance.

    Returns:
        None
    """
    db.init_app(app)