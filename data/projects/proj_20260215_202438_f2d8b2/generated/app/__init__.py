from flask import Flask
from app.database import engine, Base
from app.models import problem, user

def create_app():
    # Initialize the Flask app
    app = Flask(
        __name__,
        template_folder='../templates',
        static_folder='../static',
        static_url_path='/static'
    )

    # Initialize database
    Base.metadata.create_all(bind=engine)

    # Register blueprints here (example, assuming blueprints exist)
    # from app.controllers.problem_controller import problem_bp
    # from app.controllers.user_controller import user_bp
    # app.register_blueprint(problem_bp)
    # app.register_blueprint(user_bp)

    return app