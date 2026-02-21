from app.controllers.problem_controller import blueprint
from app.controllers.user_controller import user_bp
from app.controllers.solution_controller import solution_bp

def register_blueprints(app):
    """
    Register all blueprints with the given Flask application instance.

    Args:
        app (Flask): The Flask application instance.
    """
    app.register_blueprint(problem_blueprint)
    app.register_blueprint(user_blueprint)
    app.register_blueprint(solution_blueprint)