from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from config import Config

# Initialize extensions
db = SQLAlchemy()

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    config_class = Config
    app.config.from_object(config_class)

    db.init_app(app)

    # Import models
    from app.models import Note  # Replace with actual models

    # Create database tables
    with app.app_context():
        db.create_all()

    # Import and register blueprints
    from app.routes.notes import notes_bp
    app.register_blueprint(notes_bp, url_prefix='/api')

    # Home route
    @app.route('/')
    def index():
        return render_template('index.html')

    # Notes route
    @app.route('/notes')
    def notes():
        return render_template('notes.html')

    return app