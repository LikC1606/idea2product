from flask import Flask
from app.database import db
from app.config import Config
from app.blueprints.problem import problem_bp
from app.blueprints.user import user_bp
from app.blueprints.auth import auth_bp
from app.extensions import migrate
from app.errors import handle_404


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    app.register_blueprint(problem_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)

    # Error handlers
    app.register_error_handler(404, handle_404)

    return app