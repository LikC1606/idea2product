from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    # Import models before creating the database
    from app.models.note import Note
    with app.app_context():
        db.create_all()
    
    # Register routes
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app