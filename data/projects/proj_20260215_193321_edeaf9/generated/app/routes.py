from flask import Flask
from app.controllers.problem_controller import problem_bp
from app.controllers.user_controller import user_bp
from app.controllers.solution_controller import solution_bp

def register_blueprints(app: Flask):
    """
    Registers all the blueprints to the Flask application.
    
    Args:
        app (Flask): The Flask application instance.
    """
    app.register_blueprint(problem_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(solution_bp)