from flask import Flask
from app.database import db
from app.routes import register_blueprints

def create_app():
    app = Flask(__name__)
    
    # Configure the app (you can replace this with actual configuration as needed)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///acm_platform.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the database
    db.init_app(app)
    
    # Register routes
    register_blueprints(app)
    
    return app