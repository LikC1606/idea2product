from flask import Flask
from app.database import engine, Base
from app.controllers.problem_controller import problem_bp
from app.controllers.user_controller import user_bp
from app.controllers.solution_controller import solution_bp
from app.routes import app as main_app

def create_app():
    # Initialize the Flask app
    app = Flask(__name__, template_folder='../templates', static_folder='../static', static_url_path='/static')

    # Register blueprints
    app.register_blueprint(problem_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(solution_bp)

    # Create database tables
    Base.metadata.create_all(bind=engine)

    # Register main app routes
    app.register_blueprint(main_app)

    return app