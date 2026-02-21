from flask import Flask
from app.database import db
from app.routes import register_blueprints

def create_app():
    app = Flask(__name__)

    # App configuration (add configuration settings here if needed)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # Example configuration
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    register_blueprints(app)

    return app