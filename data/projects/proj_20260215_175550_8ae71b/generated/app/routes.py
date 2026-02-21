# app/routes.py
# Layer: assembly
# Purpose: Aggregate all blueprints

from app.controllers.problem_controller import problem_blueprint
from app.controllers.user_controller import user_blueprint
from app.controllers.solution_controller import solution_blueprint

# List of all blueprints to be registered
blueprints = [
    problem_blueprint,
    user_blueprint,
    solution_blueprint
]