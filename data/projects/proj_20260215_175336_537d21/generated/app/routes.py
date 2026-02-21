# app/routes.py
# Purpose: Aggregate all blueprints
# Layer: assembly

from app.controllers.problem_controller import problem_blueprint
from app.controllers.user_controller import user_blueprint
from app.controllers.solution_controller import solution_blueprint

def register_blueprints(app):
    app.register_blueprint(problem_blueprint)
    app.register_blueprint(user_blueprint)
    app.register_blueprint(solution_blueprint)