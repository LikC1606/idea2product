from flask import Flask
from app.database import db
from app.routes import register_blueprints

def create_app():
    app = Flask(__name__)
    
    # Configure the app (add configuration settings if needed)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    db.init_app(app)

    # Register blueprints
    register_blueprints(app)
    
    return app