from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import get_config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Load configuration
    config_class = get_config()
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    CORS(app)

    # Import blueprints
    from app.routes.notes import notes_bp

    # Register blueprints
    app.register_blueprint(notes_bp, url_prefix='/api')

    return app
