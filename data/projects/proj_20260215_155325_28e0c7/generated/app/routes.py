# app/routes.py
# Layer: assembly
# Purpose: Main routes aggregating all blueprints

from app.controllers.problem_controller import blueprint
from app.controllers.user_controller import blueprint
from app.controllers.solution_controller import blueprint

def register_blueprints(app):
    """
    Registers all blueprints with the Flask application instance.
    """
    app.register_blueprint(problem_blueprint, url_prefix='/problems')
    app.register_blueprint(user_blueprint, url_prefix='/users')
    app.register_blueprint(solution_blueprint, url_prefix='/solutions')