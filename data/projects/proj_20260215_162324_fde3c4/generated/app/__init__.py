from flask import Flask
from app.routes import problem_controller, user_controller, solution_controller

def create_app():
    app = Flask(__name__)

    # Register blueprints from the controllers
    app.register_blueprint(problem_controller)
    app.register_blueprint(user_controller)
    app.register_blueprint(solution_controller)

    return app