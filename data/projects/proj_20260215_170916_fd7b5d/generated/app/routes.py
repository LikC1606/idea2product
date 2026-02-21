# app/routes.py
# 聚合所有blueprints
# Layer: assembly

from app.controllers.problem_controller import problem_blueprint
from app.controllers.user_controller import user_blueprint
from app.controllers.solution_controller import solution_blueprint

def register_blueprints(app):
    """
    Register all blueprints to the given Flask application.

    :param app: Flask application instance
    """
    app.register_blueprint(problem_blueprint, url_prefix='/problems')
    app.register_blueprint(user_blueprint, url_prefix='/users')
    app.register_blueprint(solution_blueprint, url_prefix='/solutions')