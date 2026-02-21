from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import get_config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    config_class = get_config()
    app.config.from_object(config_class)

    db.init_app(app)
    CORS(app)

    with app.app_context():
        from app.models.note import Note
        db.create_all()

        from app.routes.notes import notes_bp
        app.register_blueprint(notes_bp, url_prefix='/api')

    return app