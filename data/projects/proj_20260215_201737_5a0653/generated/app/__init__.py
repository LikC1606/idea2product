from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

def create_app():
    # Initialize Flask app
    app = Flask(__name__, template_folder='../templates', static_folder='../static', static_url_path='/static')

    # Configure the app
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # Replace with your database URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)

    # Import and register blueprints (add your blueprints here)
    # Example: from app.controllers.problem_controller import problem_bp
    # app.register_blueprint(problem_bp)

    return app