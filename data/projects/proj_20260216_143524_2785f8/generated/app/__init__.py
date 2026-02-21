from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Correctly import the Config class
    from config.config import Config  # Adjusted import path
    app.config.from_object(Config)

    # Initialize database
    db.init_app(app)

    # Import models before db.create_all()
    with app.app_context():
        from app.models import Note  # Ensure models are correctly imported
        db.create_all()

    # Import and register blueprints
    from app.routes.notes import notes_bp
    app.register_blueprint(notes_bp, url_prefix='/api')

    return app