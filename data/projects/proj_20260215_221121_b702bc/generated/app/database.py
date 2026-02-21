from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app import db

def setup_database(app: Flask):
    """
    Set up the database connection and handle migrations.

    Args:
        app (Flask): The Flask application instance.
    """
    # Bind SQLAlchemy to the Flask app
    db.init_app(app)

    # Set up Flask-Migrate for database migrations
    Migrate(app, db)

def initialize_database(app: Flask):
    """
    Initialize the database by creating all tables.

    Args:
        app (Flask): The Flask application instance.
    """
    with app.app_context():
        db.create_all()
# SQLAlchemy db instance for models
db = SQLAlchemy()
