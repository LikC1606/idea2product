# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Initialize the database
db = SQLAlchemy()

# Initialize migration
migrate = Migrate()

# Initialize login manager
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object('config.Config')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Register blueprints
    from .tasks import tasks_bp
    app.register_blueprint(tasks_bp, url_prefix='/tasks')

    from .auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app