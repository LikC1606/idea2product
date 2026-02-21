from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()

def init_db(app):
    """
    Initialize the SQLAlchemy database with the given Flask application.

    Args:
        app (Flask): The Flask application instance.
    """
    db.init_app(app)
    with app.app_context():
        db.create_all()