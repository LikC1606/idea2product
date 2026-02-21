from flask import Flask
from app.database import db
from app.routes import notes_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_secret_key_here'  # Set your secret key for session management
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(notes_bp)

    # Home route
    @app.route('/')
    def home():
        return "Welcome to the Simple Note-Taking App!"

    # Create database tables
    with app.app_context():
        db.create_all()

    return app