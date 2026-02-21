from app.controllers.problem_controller import problem_controller
from app.controllers.user_controller import user_controller
from app.controllers.solution_controller import solution_controller

def register_blueprints(app):
    """
    Function to register all blueprints to the Flask application.

    Args:
        app (Flask): The Flask application instance.
    """
    app.register_blueprint(problem_controller)
    app.register_blueprint(user_controller)
    app.register_blueprint(solution_controller)