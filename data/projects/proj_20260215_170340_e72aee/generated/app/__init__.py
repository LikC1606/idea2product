from flask import Flask
from app.routes import *
from app.database import db

def create_app():
    app = Flask(__name__)

    # Configure the app (e.g., database URI, debug settings, etc.)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    db.init_app(app)

    # Register blueprints
    from app.controllers.problem_controller import problem_blueprint
    from app.controllers.user_controller import user_blueprint
    from app.controllers.solution_controller import solution_blueprint

    app.register_blueprint(problem_blueprint, url_prefix='/problems')
    app.register_blueprint(user_blueprint, url_prefix='/users')
    app.register_blueprint(solution_blueprint, url_prefix='/solutions')

    return app