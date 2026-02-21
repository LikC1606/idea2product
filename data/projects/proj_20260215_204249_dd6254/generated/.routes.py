from app.controllers.problem_controller import problem_controller
from app.controllers.user_controller import user_controller

def register_blueprints(app):
    app.register_blueprint(problem_controller)
    app.register_blueprint(user_controller)