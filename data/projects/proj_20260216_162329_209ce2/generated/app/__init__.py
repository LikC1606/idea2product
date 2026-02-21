from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import get_config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')

    config_class = get_config()
    app.config.from_object(config_class)

    db.init_app(app)
    CORS(app)

    # Import and register blueprints
    from app.routes.notes import notes_bp
    app.register_blueprint(notes_bp, url_prefix='/api')

    return app
