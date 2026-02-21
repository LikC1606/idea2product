from flask import Flask
from app.database import db
from app.controllers.problem_controller import problem_bp
from app.controllers.user_controller import user_bp
from app.controllers.solution_controller import solution_bp

def create_app():
    app = Flask(__name__)

    # Configuration can be set here if needed
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(problem_bp, url_prefix='/problems')
    app.register_blueprint(user_bp, url_prefix='/users')
    app.register_blueprint(solution_bp, url_prefix='/solutions')

    # Return the app instance
    return app