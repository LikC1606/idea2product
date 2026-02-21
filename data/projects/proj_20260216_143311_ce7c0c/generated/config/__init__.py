from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.settings')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Import models before db.create_all()
    with app.app_context():
        from app.models import Note
        db.create_all()

    # Register blueprints
    from app.routes import notes_bp
    app.register_blueprint(notes_bp, url_prefix='/notes')

    return app