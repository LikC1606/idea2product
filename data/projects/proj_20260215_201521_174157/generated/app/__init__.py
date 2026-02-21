from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize the database instance
db = SQLAlchemy()

def create_app():
    # Create the Flask application
    app = Flask(__name__, template_folder='../templates', static_folder='../static', static_url_path='/static')
    
    # Configure the application
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    # Register blueprints here
    # Example: app.register_blueprint(problem_bp)
    
    return app

# Must Export
__all__ = ['db', 'create_app']