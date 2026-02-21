from flask import Flask
from app.database import db
from app.routes import register_blueprints

def create_app():
    # Create Flask app instance
    app = Flask(__name__)

    # Configure the app (add configuration here if needed)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    db.init_app(app)

    # Register blueprints
    register_blueprints(app)

    return app