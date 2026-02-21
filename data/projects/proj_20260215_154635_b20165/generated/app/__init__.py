from flask import Flask
from app.database import db
from app.routes import problem_blueprint, user_blueprint, solution_blueprint

def create_app():
    app = Flask(__name__)

    # Configure the app
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(problem_blueprint)
    app.register_blueprint(user_blueprint)
    app.register_blueprint(solution_blueprint)

    return app