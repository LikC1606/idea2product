from flask_sqlalchemy import SQLAlchemy

# Initialize the SQLAlchemy database instance
db = SQLAlchemy()

def setup_database(app):
    """
    Configures the database for the Flask application.
    
    Args:
        app (Flask): The Flask application instance.
    """
    # Set the SQLAlchemy configurations
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Bind SQLAlchemy to the Flask app
    db.init_app(app)
    
    with app.app_context():
        # Create all database tables if they don't exist
        db.create_all()