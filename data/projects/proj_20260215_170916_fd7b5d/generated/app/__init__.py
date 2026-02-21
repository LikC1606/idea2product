from flask import Flask
from app.routes import register_blueprints
from app.database import db

def create_app():
    """
    Flask application factory for ACM Problem-Solving Platform.
    """
    app = Flask(__name__)

    # Load configuration (can be extended with actual configuration files or objects)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///acm_platform.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    db.init_app(app)

    # Register blueprints
    register_blueprints(app)

    return app