from flask import Flask, render_template
from app.database import db
from app.routes import register_blueprints

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    db.init_app(app)

    # Register blueprints
    register_blueprints(app)

    # Define home route
    @app.route('/')
    def index():
        return render_template('index.html')

    return app
