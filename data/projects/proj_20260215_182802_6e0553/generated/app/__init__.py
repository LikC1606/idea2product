from flask import Flask
from app.database import db
from app.routes import register_blueprints

def create_app():
    app = Flask(__name__)
    
    # Application Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize Database
    db.init_app(app)
    
    # Register Blueprints
    register_blueprints(app)
    
    return app