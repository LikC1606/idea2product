from flask_sqlalchemy import SQLAlchemy

# Initialize the SQLAlchemy instance
db = SQLAlchemy()

def init_db(app):
    """
    Initialize the database with the Flask application.

    Args:
        app: The Flask application instance.
    """
    db.init_app(app)

    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()