# app/routes.py
# Layer: assembly
# Purpose: Aggregate all blueprints
# Interface Specifications:
# - Module: routes
# - Layer: assembly
# - Database: none

from app.controllers.problem_controller import problem_blueprint
from app.controllers.user_controller import user_blueprint
from app.controllers.solution_controller import solution_blueprint

# List of blueprints to be registered
blueprints = [
    problem_blueprint,
    user_blueprint,
    solution_blueprint
]

__all__ = ['blueprints']