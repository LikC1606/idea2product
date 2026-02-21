from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.routes import register_routes

# Initialize the database
db = SQLAlchemy()

def create_app():
    # Initialize the Flask application
    app = Flask(__name__)

    # Configure the SQLAlchemy database URI
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///acm_platform.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the database with the app
    db.init_app(app)

    # Register routes with the app
    register_routes(app)

    return app