# config/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    """Application factory function for the Note-Taking Application."""
    app = Flask(__name__)

    # Configuration setup
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Import models (to ensure they are registered before db.create_all())
    from app.models import Note

    # Create database tables
    with app.app_context():
        db.create_all()

    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app