# app/routes.py
# Purpose: Aggregate all blueprints
# Layer: assembly

from app.controllers.problem_controller import blueprint
from app.controllers.user_controller import user_bp
from app.controllers.solution_controller import solution_bp

# List of all blueprints to be registered
blueprints = [
    problem_blueprint,
    user_blueprint,
    solution_blueprint
]

def register_blueprints(app):
    """
    Register all blueprints to the Flask application instance.
    
    Args:
        app (Flask): The Flask application instance.
    """
    for blueprint in blueprints:
        app.register_blueprint(blueprint)