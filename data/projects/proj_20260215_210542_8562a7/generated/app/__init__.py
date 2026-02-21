from flask import Flask, render_template
from app.database import db
from app.routes import register_routes

def create_app():
    # Initialize the Flask application
    app = Flask(
        __name__,
        template_folder='../templates',
        static_folder='../static',
        static_url_path='/static'
    )

    # Configure the app (add database configurations here if needed)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # Example: Replace with your database URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the database
    db.init_app(app)

    # Register routes (blueprints)
    register_routes(app)

    # Define the home route
    @app.route('/')
    def home():
        return render_template('index.html')

    return app