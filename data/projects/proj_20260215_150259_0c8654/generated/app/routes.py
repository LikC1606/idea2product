from flask import Blueprint
from app.controllers.problem_controller import problem_blueprint
from app.controllers.user_controller import user_blueprint
from app.controllers.leaderboard_controller import leaderboard_blueprint

def register_routes(app):
    """
    Registers all routes and blueprints for the application.
    """
    # Register problem routes
    app.register_blueprint(problem_blueprint, url_prefix='/problems')

    # Register user routes
    app.register_blueprint(user_blueprint, url_prefix='/users')

    # Register leaderboard routes
    app.register_blueprint(leaderboard_blueprint, url_prefix='/leaderboard')