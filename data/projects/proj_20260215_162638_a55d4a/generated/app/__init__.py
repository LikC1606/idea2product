from flask import Flask
from app.database import db
from app.routes import problem_controller, user_controller, solution_controller

def create_app():
    app = Flask(__name__)

    # Configuration setup
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # Replace with your actual database URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(problem_controller, url_prefix='/problems')
    app.register_blueprint(user_controller, url_prefix='/users')
    app.register_blueprint(solution_controller, url_prefix='/solutions')

    return app