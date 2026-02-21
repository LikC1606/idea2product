from flask import Flask
from app.database import db
from app.routes import register_blueprints

def create_app():
    # Create the Flask app instance
    app = Flask(__name__)

    # Configure the app
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the database with the app
    db.init_app(app)

    # Register blueprints for routing
    register_blueprints(app)

    return app