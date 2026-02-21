from flask import Flask
from app.routes import problem_controller, user_controller, solution_controller
from app.database import db

def create_app():
    app = Flask(__name__)

    # Configure the app (e.g., database settings)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the database
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(problem_controller)
    app.register_blueprint(user_controller)
    app.register_blueprint(solution_controller)

    return app