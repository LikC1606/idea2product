from flask import Flask
from app.routes import problem_blueprint, user_blueprint, solution_blueprint
from app.database import db

def create_app():
    app = Flask(__name__)

    # Register blueprints for routing
    app.register_blueprint(problem_blueprint)
    app.register_blueprint(user_blueprint)
    app.register_blueprint(solution_blueprint)

    # Initialize the database
    db.init_app(app)

    return app