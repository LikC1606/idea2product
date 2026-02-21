from flask import Flask, render_template
from app.routes import register_blueprints

def create_app():
    """Application factory for the ACM Problem-Solving Platform."""
    app = Flask(__name__)

    # Register routes and blueprints
    register_blueprints(app)

    # Add home route to render the main HTML page
    @app.route('/')
    def index():
        return render_template('index.html')

    return app