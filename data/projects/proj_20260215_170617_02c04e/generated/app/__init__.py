from flask import Flask
from app.routes import register_blueprints

def create_app():
    """Flask application factory."""
    app = Flask(__name__)

    # Register all blueprints
    register_blueprints(app)

    return app