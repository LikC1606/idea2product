from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from app.database import db
from app.routes import register_routes  # Assuming you have a function to register routes

def create_app():
    # Initialize Flask application
    app = Flask(__name__, template_folder='../templates', static_folder='../static', static_url_path='/static')

    # Configure application settings
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'  # Update as per your database configuration
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = 'secret-key'

    # Initialize database
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # Register routes
    register_routes(app)

    # Home route
    @app.route('/')
    def home():
        return render_template('index.html')

    return app