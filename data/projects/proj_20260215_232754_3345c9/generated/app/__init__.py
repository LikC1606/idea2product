from flask import Flask
from app.database import db
from app.routes import notes_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_secret_key'

    # Register Blueprints
    app.register_blueprint(notes_bp)

    # Configure Database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    # Create Database Tables
    with app.app_context():
        db.create_all()

    # Default Home Route
    @app.route('/')
    def home():
        return 'Welcome to the Simple Note-Taking App!'

    return app