from flask import Flask
from app.routes import *

def create_app():
    app = Flask(__name__)

    # Register blueprints from routes or controllers
    app.register_blueprint(problem_blueprint)
    app.register_blueprint(user_blueprint)
    app.register_blueprint(solution_blueprint)

    # Additional setup can go here (e.g., configuration, middleware)

    return app