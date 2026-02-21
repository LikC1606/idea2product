from flask import Flask
from app.routes import problem_blueprint, user_blueprint, solution_blueprint

def create_app():
    app = Flask(__name__)

    # Register blueprints for modular route handling
    app.register_blueprint(problem_blueprint)
    app.register_blueprint(user_blueprint)
    app.register_blueprint(solution_blueprint)

    return app