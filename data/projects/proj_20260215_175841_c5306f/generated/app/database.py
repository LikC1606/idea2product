from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()

def init_db(app):
    """
    Initialize the database with the Flask app.

    Args:
        app (Flask): The Flask application instance.
    """
    db.init_app(app)

    with app.app_context():
        # Create all tables in the database based on the defined models
        db.create_all()