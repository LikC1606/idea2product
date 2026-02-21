# app/routes.py
# Purpose: Aggregate all blueprints
# Layer: assembly

from app.controllers.problem_controller import problem_blueprint
from app.controllers.user_controller import user_blueprint
from app.controllers.solution_controller import solution_blueprint

# List of all blueprints to be registered in the application
blueprints = [
    problem_blueprint,
    user_blueprint,
    solution_blueprint
]

# Export the blueprints
__all__ = ['blueprints']