from flask import Flask
from app.routes import *
from app.database import db
from app.controllers.problem_controller import problem_blueprint
from app.controllers.user_controller import user_blueprint
from app.controllers.solution_controller import solution_blueprint

def create_app():
    # Initialize the Flask app
    app = Flask(__name__)

    # Configure app settings if needed
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # Example configuration
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the database
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(problem_blueprint, url_prefix='/problems')
    app.register_blueprint(user_blueprint, url_prefix='/users')
    app.register_blueprint(solution_blueprint, url_prefix='/solutions')

    return app