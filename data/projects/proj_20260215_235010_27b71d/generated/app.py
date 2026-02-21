from flask import Flask
from app.database import db
from app.routes import notes_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_secret_key'  # Set a secret key for session security

    # Configure the database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the database
    db.init_app(app)

    # Register the blueprint
    app.register_blueprint(notes_bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    # Define the home route
    @app.route('/')
    def home():
        return 'Welcome to the Note-Taking App!'

    return app