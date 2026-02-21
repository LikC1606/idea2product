from flask import Flask
from app.database import db
from app.routes import problem_blueprint, user_blueprint, solution_blueprint

def create_app():
    # Create a Flask application instance
    app = Flask(__name__)

    # Configure the app (e.g., database URI, secret key, etc.)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///acm_platform.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the database
    db.init_app(app)

    # Register blueprints for routing
    app.register_blueprint(problem_blueprint, url_prefix='/problems')
    app.register_blueprint(user_blueprint, url_prefix='/users')
    app.register_blueprint(solution_blueprint, url_prefix='/solutions')

    return app