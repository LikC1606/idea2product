from flask import Flask
from app.database import init_db
from app.routes import register_routes

from app.models.problem import Problem, get_problem
from app.models.user import User, get_user
from app.models.leaderboard import Leaderboard, get_leaderboard

def create_app():
    # Initialize the Flask application
    app = Flask(__name__)

    # Set up configurations (you can replace this with actual config setup)
    app.config.from_object('config.Config')

    # Initialize the database
    init_db(app)

    # Register routes
    register_routes(app)

    return app

# Must export
__all__ = ['create_app']