from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.routes import register_routes

# Initialize SQLAlchemy
db = SQLAlchemy()

def create_app(config_filename=None):
    app = Flask(__name__)

    # Load configurations
    if config_filename:
        app.config.from_pyfile(config_filename)
    
    # Initialize database with app
    db.init_app(app)

    # Register blueprints
    register_routes(app)

    return app