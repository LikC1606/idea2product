from flask import Flask
from app.database import db
from app.routes import notes_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_secret_key_here'

    # Register the notes blueprint
    app.register_blueprint(notes_bp)

    # Initialize the database with the app
    db.init_app(app)

    # Create database tables
    with app.app_context():
        db.create_all()

    # Define a home route
    @app.route('/')
    def home():
        return "Welcome to the Simple Note-Taking App!"

    return app