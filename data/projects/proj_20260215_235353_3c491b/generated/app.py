from flask import Flask
from app.database import db
from app.routes import notes_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_secret_key_here'

    # Register blueprints
    app.register_blueprint(notes_bp)

    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    # Create database tables
    with app.app_context():
        db.create_all()

    # Home route
    @app.route('/')
    def home():
        return 'Welcome to the Note-Taking App!'

    return app