from flask import Flask, render_template
from app.database import db
from app.routes import register_blueprints

def create_app():
    """
    Factory function to create a Flask application instance.

    Returns:
        Flask: The Flask application instance.
    """
    app = Flask(__name__)

    # Configure the app (add configurations here if needed)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    db.init_app(app)

    # Register blueprints
    register_blueprints(app)

    # Define a default route
    @app.route('/')
    def index():
        return render_template('index.html')

    return app